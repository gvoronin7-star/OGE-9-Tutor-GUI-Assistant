# -*- coding: utf-8 -*-
"""
Unit-тесты для RAG-пайплайна.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.llm_client import GenerationResult
from api.rag_pipeline import RAGPipeline
from utils.cache import CacheManager


class TestRAGPipeline:
    """Тесты для RAG-пайплайна."""

    @pytest.fixture
    def temp_dir(self):
        """Создание временной директории."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_cache_manager(self):
        """Создание мока CacheManager."""
        manager = Mock(spec=CacheManager)
        manager.get = AsyncMock(return_value=None)
        manager.set = AsyncMock(return_value=True)
        manager.get_query_stats = AsyncMock(
            return_value={"top_queries": [], "medium_queries": []}
        )
        return manager

    @pytest.fixture
    def rag_pipeline(self, temp_dir, mock_cache_manager):
        """Создание RAG-пайплайна для тестов."""
        return RAGPipeline(mock_cache_manager)

    @pytest.mark.asyncio
    async def test_initialize(self, rag_pipeline, temp_dir):
        """
        Тест инициализации RAG-пайплайна.

        Раньше мокался атрибут экземпляра (patch.object(rag_pipeline,
        "vector_store")), но initialize() первым делом делает
        self.vector_store = VectorStore(self.indices_dir) - реальный
        конструктор и реальный load()/initialize(), стирая мок до того,
        как он мог на что-то повлиять. VectorStore тянет
        sentence-transformers (rubert-tiny2) - реальный сетевой поход в
        HuggingFace Hub при каждом прогоне этого теста. Патчим классы на
        уровне модуля (api.rag_pipeline.VectorStore и т.д. - именно так
        initialize() их резолвит, через `from ... import` в этом же
        модуле), а не атрибуты уже созданного экземпляра. Найдено
        зональным аудитом хаба 2026-09-08 (В-7 отчёта).
        """
        mock_vs = Mock()
        mock_vs.load = AsyncMock()
        mock_vs.initialize = AsyncMock()
        mock_ts = Mock()
        mock_ts.load = AsyncMock()
        mock_ts.initialize = AsyncMock()
        mock_llm = Mock()
        mock_llm.initialize = AsyncMock()

        with patch(
            "api.rag_pipeline.VectorStore", return_value=mock_vs
        ) as mock_vs_cls, patch(
            "api.rag_pipeline.TextSearchEngine", return_value=mock_ts
        ) as mock_ts_cls, patch(
            "api.rag_pipeline.LLMClient", return_value=mock_llm
        ) as mock_llm_cls:

            await rag_pipeline.initialize()

            mock_vs_cls.assert_called_once_with(rag_pipeline.indices_dir)
            mock_ts_cls.assert_called_once_with(rag_pipeline.indices_dir)
            mock_llm_cls.assert_called_once_with(rag_pipeline.cache_manager)
            mock_vs.load.assert_awaited_once()
            mock_ts.load.assert_awaited_once()
            mock_llm.initialize.assert_awaited_once()
            assert rag_pipeline.vector_store is mock_vs
            assert rag_pipeline.text_search is mock_ts
            assert rag_pipeline.llm_client is mock_llm
            assert rag_pipeline.cache_manager is not None

    @pytest.mark.asyncio
    async def test_get_answer_basic(self, rag_pipeline, mock_cache_manager):
        """Тест базового получения ответа."""
        # Мок компонентов
        with patch.object(rag_pipeline, "vector_store") as mock_vs, patch.object(
            rag_pipeline, "text_search"
        ) as mock_ts, patch.object(rag_pipeline, "llm_client") as mock_llm:

            # Настройка моков
            mock_vs.search = AsyncMock(
                return_value=[
                    {
                        "chunk_id": "test_1",
                        "topic": "Тестовая тема",
                        "content": "Тестовое содержание",
                        "score": 0.9,
                    }
                ]
            )

            mock_ts.search = AsyncMock(return_value=[])

            mock_llm.generate = AsyncMock(
                return_value=GenerationResult(text="Тестовый ответ", is_fallback=False)
            )

            # Вызов
            result = await rag_pipeline.get_answer(query="Тестовый вопрос", user_id=123)

            # Проверки
            assert "answer" in result
            assert result["answer"] == "Тестовый ответ"
            assert "sources" in result
            assert result["is_cached"] is False
            assert result["is_fallback"] is False
            mock_cache_manager.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_answer_fallback_not_cached(
        self, rag_pipeline, mock_cache_manager
    ):
        """
        Отказ LLM (is_fallback=True) должен пробрасываться в результат и
        НЕ кэшироваться - иначе после починки ключа/сети пользователь до
        истечения TTL (1-24 ч) продолжает получать старую заглушку со
        status="success". Найдено зональным аудитом хаба 2026-09-08 (К-4).
        """
        with patch.object(rag_pipeline, "vector_store") as mock_vs, patch.object(
            rag_pipeline, "text_search"
        ) as mock_ts, patch.object(rag_pipeline, "llm_client") as mock_llm:

            mock_vs.search = AsyncMock(return_value=[])
            mock_ts.search = AsyncMock(return_value=[])
            mock_llm.generate = AsyncMock(
                return_value=GenerationResult(
                    text="Демо-ответ по ключевым словам", is_fallback=True
                )
            )

            result = await rag_pipeline.get_answer(query="Тестовый вопрос", user_id=123)

            assert result["is_fallback"] is True
            mock_cache_manager.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_answer_cached(self, rag_pipeline, mock_cache_manager):
        """Тест получения ответа из кэша."""
        # Настройка мока кэша
        mock_cache_manager.get = AsyncMock(
            return_value={"answer": "Кэшированный ответ", "sources": ["Тема 1"]}
        )

        result = await rag_pipeline.get_answer(
            query="Тестовый вопрос", user_id=123, use_cache=True
        )

        # Проверки
        assert result["answer"] == "Кэшированный ответ"
        assert result["is_cached"] is True

    def test_build_context(self, rag_pipeline):
        """Тест формирования контекста."""
        chunks = [
            {"topic": "Тема 1", "content": "Содержание 1"},
            {"topic": "Тема 2", "content": "Содержание 2"},
        ]

        context = rag_pipeline._build_context(chunks)

        assert "Тема 1" in context
        assert "Тема 2" in context
        assert "Содержание 1" in context

    def test_system_prompt_format(self, rag_pipeline):
        """Тест формата системного промпта."""
        prompt = rag_pipeline.SYSTEM_PROMPT

        assert "Ты — репетитор по обществознанию" in prompt
        assert "{context}" in prompt
        assert "{query}" in prompt
        assert "500 слов" in prompt

    @pytest.mark.asyncio
    async def test_generate_demo_questions(self, rag_pipeline):
        """Тест генерации демо-вопросов."""
        questions = rag_pipeline._generate_demo_questions(
            topic="экономика", difficulty="medium", num_questions=3
        )

        assert isinstance(questions, dict)
        assert len(questions) > 0

        # Проверка структуры вопроса
        first_q = list(questions.values())[0]
        assert "question" in first_q
        assert "answers" in first_q
        assert len(first_q["answers"]) == 4
        assert "correct_answer" in first_q

    def test_get_metrics(self, rag_pipeline):
        """Тест получения метрик."""
        # Установка тестовых значений
        rag_pipeline.metrics = {
            "total_requests": 10,
            "cache_hits": 3,
            "avg_response_time": 1.5,
            "errors": 1,
        }

        metrics = rag_pipeline.get_metrics()

        assert metrics["rag_total_requests"] == 10
        assert metrics["rag_cache_hits"] == 3
        assert metrics["rag_cache_hit_rate"] == 30.0


class TestCacheManager:
    """Тесты для CacheManager."""

    @pytest.mark.asyncio
    async def test_get_ttl_category_top(self):
        """
        Тест определения TTL для частых запросов.

        Раньше мок get_top_queries возвращал буквальное [12345], не
        имеющее отношения к хэшу реального запроса - категория не могла
        оказаться ничем, кроме "rare", а assert проверял членство в
        полном списке всех трёх возможных значений (истинно всегда,
        независимо от поведения кода). Найдено зональным аудитом хаба
        2026-09-08 (В-8 отчёта, "тавтологичные тесты").
        """
        from utils.cache import CacheManager
        from utils.hashing import stable_query_hash

        manager = CacheManager()
        manager.query_stats = Mock()
        query_hash = stable_query_hash("тестовый запрос")
        manager.query_stats.get_top_queries = Mock(return_value=[query_hash])
        manager.query_stats.get_medium_queries = Mock(return_value=[])

        category = manager._get_ttl_category("тестовый запрос")

        assert category == "top"

    @pytest.mark.asyncio
    async def test_get_ttl_category_medium(self):
        """Хэш в medium-списке, но не в top -> категория medium."""
        from utils.cache import CacheManager
        from utils.hashing import stable_query_hash

        manager = CacheManager()
        manager.query_stats = Mock()
        query_hash = stable_query_hash("тестовый запрос")
        manager.query_stats.get_top_queries = Mock(return_value=[])
        manager.query_stats.get_medium_queries = Mock(return_value=[query_hash])

        category = manager._get_ttl_category("тестовый запрос")

        assert category == "medium"

    @pytest.mark.asyncio
    async def test_get_ttl_category_rare(self):
        """Хэш не найден ни в top, ни в medium -> категория rare."""
        from utils.cache import CacheManager

        manager = CacheManager()
        manager.query_stats = Mock()
        manager.query_stats.get_top_queries = Mock(return_value=[])
        manager.query_stats.get_medium_queries = Mock(return_value=[])

        category = manager._get_ttl_category("никогда не виденный запрос")

        assert category == "rare"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
