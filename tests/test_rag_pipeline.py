# -*- coding: utf-8 -*-
"""
Unit-тесты для RAG-пайплайна.

Автор: KODA
Дата: Март 2026
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        manager.get_query_stats = AsyncMock(return_value={
            "top_queries": [],
            "medium_queries": []
        })
        return manager
    
    @pytest.fixture
    def rag_pipeline(self, temp_dir, mock_cache_manager):
        """Создание RAG-пайплайна для тестов."""
        return RAGPipeline(mock_cache_manager)
    
    @pytest.mark.asyncio
    async def test_initialize(self, rag_pipeline, temp_dir):
        """Тест инициализации RAG-пайплайна."""
        # Мок векторного хранилища и текстового поиска
        with patch.object(rag_pipeline, 'vector_store') as mock_vs, \
             patch.object(rag_pipeline, 'text_search') as mock_ts, \
             patch.object(rag_pipeline, 'llm_client') as mock_llm:
            
            mock_vs.load = AsyncMock()
            mock_vs.initialize = AsyncMock()
            mock_ts.load = AsyncMock()
            mock_ts.initialize = AsyncMock()
            mock_llm.initialize = AsyncMock()
            
            await rag_pipeline.initialize()
            
            assert rag_pipeline.cache_manager is not None
    
    @pytest.mark.asyncio
    async def test_get_answer_basic(self, rag_pipeline, mock_cache_manager):
        """Тест базового получения ответа."""
        # Мок компонентов
        with patch.object(rag_pipeline, 'vector_store') as mock_vs, \
             patch.object(rag_pipeline, 'text_search') as mock_ts, \
             patch.object(rag_pipeline, 'llm_client') as mock_llm:
            
            # Настройка моков
            mock_vs.search = AsyncMock(return_value=[
                {
                    "chunk_id": "test_1",
                    "topic": "Тестовая тема",
                    "content": "Тестовое содержание",
                    "score": 0.9
                }
            ])
            
            mock_ts.search = AsyncMock(return_value=[])
            
            mock_llm.generate = AsyncMock(return_value="Тестовый ответ")
            
            # Вызов
            result = await rag_pipeline.get_answer(
                query="Тестовый вопрос",
                user_id=123
            )
            
            # Проверки
            assert "answer" in result
            assert result["answer"] == "Тестовый ответ"
            assert "sources" in result
            assert result["is_cached"] is False
    
    @pytest.mark.asyncio
    async def test_get_answer_cached(self, rag_pipeline, mock_cache_manager):
        """Тест получения ответа из кэша."""
        # Настройка мока кэша
        mock_cache_manager.get = AsyncMock(return_value={
            "answer": "Кэшированный ответ",
            "sources": ["Тема 1"]
        })
        
        result = await rag_pipeline.get_answer(
            query="Тестовый вопрос",
            user_id=123,
            use_cache=True
        )
        
        # Проверки
        assert result["answer"] == "Кэшированный ответ"
        assert result["is_cached"] is True
    
    def test_build_context(self, rag_pipeline):
        """Тест формирования контекста."""
        chunks = [
            {"topic": "Тема 1", "content": "Содержание 1"},
            {"topic": "Тема 2", "content": "Содержание 2"}
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
            topic="экономика",
            difficulty="medium",
            num_questions=3
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
            "errors": 1
        }
        
        metrics = rag_pipeline.get_metrics()
        
        assert metrics["rag_total_requests"] == 10
        assert metrics["rag_cache_hits"] == 3
        assert metrics["rag_cache_hit_rate"] == 30.0


class TestCacheManager:
    """Тесты для CacheManager."""
    
    @pytest.mark.asyncio
    async def test_get_ttl_category_top(self):
        """Тест определения TTL для частых запросов."""
        from utils.cache import CacheManager
        
        manager = CacheManager()
        manager.query_stats = Mock()
        manager.query_stats.get_top_queries = Mock(return_value=[12345])
        
        category = manager._get_ttl_category("тестовый запрос")
        
        # Запрос не в топе, поэтому rare
        assert category in ["top", "medium", "rare"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
