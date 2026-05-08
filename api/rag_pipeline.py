# -*- coding: utf-8 -*-
"""
RAG-пайплайн для поиска и генерации ответов.

Основной модуль системы, объединяющий:
- Векторный поиск (Faiss)
- Полнотекстовый поиск (Whoosh)
- Генерацию ответов через LLM
- Кэширование результатов

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from api.llm_client import LLMClient
from api.vector_store import VectorStore
from api.vector_store_existing import ExistingVectorStore
from api.text_search import TextSearchEngine
from utils.cache import CacheManager
from utils.advanced_logger import logger_rag, detailed_logger


logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Основной класс RAG-пайплайна.
    
    Обеспечивает поиск релевантной информации и генерацию ответов.
    
    Attributes:
        vector_store: Векторное хранилище (Faiss)
        text_search: Полнотекстовый поиск (Whoosh)
        llm_client: Клиент для работы с LLM
        cache_manager: Менеджер кэширования
    """
    
    # Промпт для LLM
    SYSTEM_PROMPT = """Ты — репетитор по обществознанию для 9 класса, готовящий учеников к ОГЭ. 

Правила ответа:
1. Отвечай кратко и понятно, как для ученика 9 класса
2. Используй простой язык, избегай сложных терминов без объяснений
3. Если вопрос выходит за рамки ОГЭ, скажи: «Это не входит в программу ОГЭ, но...»
4. Структурируй ответ: сначала главное, потом пояснения
5. Приводи примеры из реальной жизни
6. Не более 500 слов

Контекст из базы знаний:
{context}

Вопрос ученика: {query}

Ответ (структурированный, с объяснением логики):"""

    def __init__(self, cache_manager: CacheManager) -> None:
        """
        Инициализация RAG-пайплайна.
        
        Args:
            cache_manager: Менеджер кэширования
        """
        self.cache_manager = cache_manager
        self.vector_store: Optional[VectorStore] = None
        self.existing_store: Optional[ExistingVectorStore] = None  # RAG_data_base
        self.text_search: Optional[TextSearchEngine] = None
        self.llm_client: Optional[LLMClient] = None
        
        # Флаг использования RAG_data_base
        self.use_existing = False
        
        # Метрики
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "errors": 0
        }
        
        # Директории
        self.data_dir = Path("data")
        self.chunks_dir = self.data_dir / "chunks"
        self.metadata_dir = self.data_dir / "metadata"
        self.indices_dir = self.data_dir / "indices"
    
    async def initialize(self) -> None:
        """
        Инициализация компонентов RAG-пайплайна.
        
        Загружает индексы, настраивает поиск и LLM-клиент.
        """
        logger.info("Инициализация RAG-пайплайна...")
        
        # Создание директорий
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        # Загрузка RAG_data_base (приоритет)
        use_existing_index = os.getenv("USE_EXISTING_INDEX", "false").lower() == "true"
        
        if use_existing_index:
            logger.info("Попытка загрузки RAG_data_base...")
            try:
                self.existing_store = ExistingVectorStore(Path("RAG_data_base/vector_db"))
                loaded = await self.existing_store.load()
                
                if loaded:
                    logger.info("✓ RAG_data_base загружена (204 чанка ФИПИ)")
                    self.use_existing = True
                else:
                    logger.warning("Не удалось загрузить RAG_data_base, используем fallback")
                    self.use_existing = False
            except Exception as e:
                logger.warning(f"Ошибка загрузки RAG_data_base: {e}")
                self.use_existing = False
        
        try:
            # Инициализация векторного хранилища (fallback)
            self.vector_store = VectorStore(self.indices_dir)
            await self.vector_store.load()
            logger.info("Векторное хранилище загружено")
        except Exception as e:
            logger.warning(f"Не удалось загрузить векторное хранилище: {e}. Будет создано новое.")
            self.vector_store = VectorStore(self.indices_dir)
            await self.vector_store.initialize()
        
        try:
            # Инициализация полнотекстового поиска
            self.text_search = TextSearchEngine(self.indices_dir)
            await self.text_search.load()
            logger.info("Полнотекстовый поиск загружен")
        except Exception as e:
            logger.warning(f"Не удалось загрузить полнотекстовый поиск: {e}. Будет создан новый.")
            self.text_search = TextSearchEngine(self.indices_dir)
            await self.text_search.initialize()
        
        try:
            # Инициализация LLM-клиента
            self.llm_client = LLMClient(self.cache_manager)
            await self.llm_client.initialize()
            logger.info("LLM-клиент инициализирован")
        except Exception as e:
            logger.error(f"Не удалось инициализировать LLM-клиент: {e}")
            self.llm_client = None
        
        # Создание демонстрационных данных, если их нет
        if not self.use_existing:
            await self._ensure_demo_data()
        
        logger.info("RAG-пайплайн инициализирован")
    
    async def _ensure_demo_data(self) -> None:
        """Создание демонстрационных данных, если они отсутствуют."""
        # Проверка наличия чанков
        chunks = list(self.chunks_dir.glob("*.md"))
        if not chunks:
            logger.info("Создание демонстрационных данных...")
            await self._create_demo_chunks()
    
    async def _create_demo_chunks(self) -> None:
        """Создание демонстрационных чанков по обществознанию."""
        demo_topics = {
            "человек_и_общество.md": """# Человек и общество

## Что такое общество?

Общество — это совокупность людей, объединённых общими интересами, культурой, историей и социальными связями. Общество возникло в процессе эволюции человека и представляет собой качественно новый уровень организации жизни.

## Общество и природа

Человек — часть природы, но общество — результат социальной эволюции. Взаимодействие общества и природы — важнейшая тема экологии. Природа предоставляет ресурсы для жизни, а общество влияет на окружающую среду.

## Социальные институты

Социальные институты — это устойчивые формы организации общественной жизни. К ним относятся: семья, образование, религия, государство, экономика. Каждый институт выполняет определённые функции в обществе.

## Культура

Культура — это всё, что создано человеком: материальные ценности, духовные достижения, нормы и правила поведения. Культура передаётся от поколения к поколению через социализацию.

## Социализация

Социализация — процесс усвоения индивидом социальных норм, ценностей и навыков. Она происходит в семье, школе, через СМИ и общение со сверстниками. Благодаря социализации человек становится полноценным членом общества.
""",
            "экономика.md": """# Экономика

## Что такое экономика?

Экономика — это наука о том, как люди и общество удовлетворяют свои потребности в условиях ограниченных ресурсов. Экономика изучает производство, распределение и потребление товаров и услуг.

## Экономические системы

Существует три основных типа экономических систем:
- Традиционная — основана на обычаях и традициях
- Командная (плановая) — государство контролирует производство
- Рыночная — цены определяются спросом и предложением
- Смешанная — сочетает элементы рынка и государства

## Рынок и конкуренция

Рынок — это место, где встречаются продавцы и покупатели. Конкуренция — это соперничество между производителями за потребителя. Конкуренция стимулирует улучшение качества и снижение цен.

## Деньги и банки

Деньги — это универсальный эквивалент стоимости. Они выполняют функции: средства платежа, меры стоимости, средства накопления. Банки принимают вклады и выдают кредиты.

## Труд и занятость

Труд — это целесообразная деятельность человека. Занятость — это участие в экономической деятельности. Безработица — это отсутствие работы у трудоспособного населения, которое её ищет.
""",
            "право.md": """# Право

## Что такое право?

Право — это система обязательных правил поведения, установленных государством. Право регулирует отношения между людьми, защищает их интересы и обеспечивает порядок в обществе.

## Источники права

Основные источники права в России:
- Конституция — главный закон страны
- Законы — нормативные акты, принятые Государственной Думой
- Подзаконные акты — указы президента, постановления правительства
- Международные договоры

## Конституция РФ

Конституция Российской Федерации принята в 1993 году. Она определяет основы государственного устройства, права и свободы человека, федеративное устройство России.

## Права человека

Основные права человека:
- Гражданские (право на жизнь, свободу, собственность)
- Политические (право на участие в управлении, свобода слова)
- Социальные (право на труд, образование, медицину)
- Экономические (право на предпринимательство, собственность)

## Правонарушения

Правонарушение — это нарушение закона. Виды:
- Проступок — нарушение с менее строгим наказанием
- Преступление — нарушение с уголовной ответственностью

За правонарушения предусмотрены: штраф, арест, лишение свободы.
"""
        }
        
        # Запись чанков
        for filename, content in demo_topics.items():
            chunk_path = self.chunks_dir / filename
            chunk_path.write_text(content, encoding="utf-8")
        
        # Создание метаданных
        metadata = {
            "topics": list(demo_topics.keys()),
            "created": "2026-03-05"
        }
        metadata_path = self.metadata_dir / "topics.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Переиндексация
        await self._reindex()
    
    async def _reindex(self) -> None:
        """Переиндексация всех чанков."""
        logger.info("Переиндексация чанков...")
        
        chunks_data = []
        
        # Чтение всех чанков
        for chunk_file in self.chunks_dir.glob("*.md"):
            try:
                content = chunk_file.read_text(encoding="utf-8")
                chunk_id = chunk_file.stem
                
                # Определение темы по имени файла
                topic = chunk_file.stem.replace("_", " ").title()
                
                chunks_data.append({
                    "chunk_id": chunk_id,
                    "topic": topic,
                    "content": content,
                    "source": str(chunk_file)
                })
            except Exception as e:
                logger.error(f"Ошибка чтения чанка {chunk_file}: {e}")
        
        if chunks_data:
            # Индексация в векторное хранилище
            if self.vector_store:
                await self.vector_store.index_chunks(chunks_data)
            
            # Индексация для полнотекстового поиска
            if self.text_search:
                await self.text_search.index_chunks(chunks_data)
            
            logger.info(f"Проиндексировано {len(chunks_data)} чанков")
    
    async def get_answer(
        self,
        query: str,
        user_id: int,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Получение ответа на вопрос пользователя.
        
        Выполняет поиск релевантных чанков, формирует промпт и отправляет в LLM.
        
        Args:
            query: Вопрос пользователя
            user_id: ID пользователя
            use_cache: Использовать ли кэширование
            
        Returns:
            Dict[str, Any]: Результат с ответом и источниками
        """
        request_start = time.time()
        self.metrics["total_requests"] += 1
        
        logger_rag.info(f"Запрос от user_id={user_id}: {query[:50]}...")
        
        # Проверка кэша
        if use_cache:
            cache_key = f"query:{user_id}:{hash(query)}"
            cached = await self.cache_manager.get(cache_key)
            
            if cached:
                self.metrics["cache_hits"] += 1
                duration = (time.time() - request_start) * 1000
                logger_rag.info(f"Ответ из кэша за {duration:.2f}ms")
                
                detailed_logger.log_request(
                    component="rag",
                    action="get_answer_cached",
                    input_data={"query": query, "user_id": user_id},
                    output_data={"answer": cached["answer"][:100]},
                    duration_ms=duration,
                    status="success",
                    user_id=user_id
                )
                
                return {
                    "answer": cached["answer"],
                    "sources": cached.get("sources", []),
                    "is_cached": True,
                    "response_time": time.time() - request_start
                }
        
        try:
            # Поиск релевантных чанков
            search_start = time.time()
            relevant_chunks = await self._search_chunks(query)
            search_duration = (time.time() - search_start) * 1000
            
            logger_rag.debug(f"Поиск чанков: {len(relevant_chunks)} найдено за {search_duration:.2f}ms")
            
            # Формирование контекста
            context = self._build_context(relevant_chunks)
            
            # Генерация ответа через LLM
            if self.llm_client:
                llm_start = time.time()
                answer = await self.llm_client.generate(
                    prompt=self.SYSTEM_PROMPT.format(
                        context=context,
                        query=query
                    )
                )
                llm_duration = (time.time() - llm_start) * 1000
                logger_rag.info(f"LLM ответ за {llm_duration:.2f}ms")
            else:
                # Демо-ответ, если LLM недоступен
                answer = self._generate_demo_answer(query, relevant_chunks)
                llm_duration = 0
            
            # Сохранение в кэш
            if use_cache:
                cache_ttl = await self._get_cache_ttl(query)
                await self.cache_manager.set(
                    cache_key,
                    {
                        "answer": answer,
                        "sources": [c["topic"] for c in relevant_chunks[:3]]
                    },
                    ttl=cache_ttl
                )
            
            total_duration = (time.time() - request_start) * 1000
            
            # Логирование успешного запроса
            detailed_logger.log_request(
                component="rag",
                action="get_answer",
                input_data={"query": query[:100], "user_id": user_id},
                output_data={"answer": answer[:100], "chunks_found": len(relevant_chunks)},
                duration_ms=total_duration,
                status="success",
                user_id=user_id
            )
        
            response_time = time.time() - request_start
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["total_requests"] - 1) + response_time)
                / self.metrics["total_requests"]
            )
        
            return {
                "answer": answer,
                "sources": [c["topic"] for c in relevant_chunks[:3]],
                "is_cached": False,
                "response_time": response_time
            }
        
        except Exception as e:
            self.metrics["errors"] += 1
            error_msg = f"Ошибка при генерации ответа: {e}"
            logger_rag.error(error_msg, exc_info=True)
            
            # Логирование ошибки
            detailed_logger.log_request(
                component="rag",
                action="get_answer",
                input_data={"query": query[:100], "user_id": user_id},
                output_data=None,
                duration_ms=(time.time() - request_start) * 1000,
                status="error",
                error_message=str(e),
                user_id=user_id
            )
            
            return {
                "answer": "Извини, произошла ошибка при обработке запроса. Попробуй ещё раз.",
                "sources": [],
                "is_cached": False,
                "error": str(e)
            }
    
    async def _search_chunks(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск релевантных чанков через Faiss и Whoosh.
        
        Приоритет: RAG_data_base → локальный Faiss → Whoosh
        
        Args:
            query: Поисковый запрос
            
        Returns:
            List[Dict[str, Any]]: Список релевантных чанков
        """
        results = []
        logger_rag.debug(f"Поиск чанков для запроса: {query[:50]}...")
        
        # Приоритет 1: RAG_data_base (ExistingVectorStore через ProxyAPI)
        if self.use_existing and self.existing_store:
            try:
                search_start = time.time()
                existing_results = await self.existing_store.search(
                    query, top_k=5,
                    use_remote_embedding=True  # ProxyAPI
                )
                search_duration = (time.time() - search_start) * 1000
                results.extend(existing_results)
                logger_rag.info(f"RAG_data_base: {len(existing_results)} чанков за {search_duration:.2f}ms")
                
                detailed_logger.log_request(
                    component="database",
                    action="search_rag_base",
                    input_data={"query": query[:100]},
                    output_data={"found": len(existing_results)},
                    duration_ms=search_duration,
                    status="success"
                )
            except Exception as e:
                logger_rag.warning(f"Ошибка поиска в RAG_data_base: {e}")
                detailed_logger.log_request(
                    component="database",
                    action="search_rag_base",
                    input_data={"query": query[:100]},
                    output_data=None,
                    duration_ms=0,
                    status="error",
                    error_message=str(e)
                )
        
        # Приоритет 2: Векторный поиск (Faiss) - fallback
        if not results and self.vector_store:
            try:
                search_start = time.time()
                faiss_results = await self.vector_store.search(query, top_k=5)
                search_duration = (time.time() - search_start) * 1000
                results.extend(faiss_results)
                logger_rag.info(f"Faiss fallback: {len(faiss_results)} чанков за {search_duration:.2f}ms")
            except Exception as e:
                logger_rag.warning(f"Ошибка векторного поиска: {e}")
                detailed_logger.log_request(
                    component="database",
                    action="search_faiss",
                    input_data={"query": query[:100]},
                    output_data=None,
                    duration_ms=0,
                    status="error",
                    error_message=str(e)
                )
        
        # Приоритет 3: Полнотекстовый поиск (Whoosh) - fallback
        if not results and self.text_search:
            try:
                search_start = time.time()
                whoosh_results = await self.text_search.search(query, top_k=3)
                search_duration = (time.time() - search_start) * 1000
                results.extend(whoosh_results)
                logger_rag.info(f"Whoosh fallback: {len(whoosh_results)} чанков за {search_duration:.2f}ms")
            except Exception as e:
                logger_rag.warning(f"Ошибка полнотекстового поиска: {e}")
                detailed_logger.log_request(
                    component="database",
                    action="search_whoosh",
                    input_data={"query": query[:100]},
                    output_data=None,
                    duration_ms=0,
                    status="error",
                    error_message=str(e)
                )
        
        # Объединение и дедупликация результатов
        unique_results = []
        seen_ids = set()
        
        for result in results:
            if result["chunk_id"] not in seen_ids:
                seen_ids.add(result["chunk_id"])
                unique_results.append(result)
        
        # Сортировка по релевантности
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        logger_rag.debug(f"Итого найдено уникальных чанков: {len(unique_results)}")
        
        return unique_results[:5]
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Формирование контекста для LLM из чанков.
        
        Args:
            chunks: Список чанков
            
        Returns:
            str: Текст контекста
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")[:1000]  # Ограничение длины
            topic = chunk.get("topic", "Неизвестная тема")
            
            context_parts.append(f"[{i}] Тема: {topic}\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _generate_demo_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Генерация демо-ответа без LLM.
        
        Args:
            query: Вопрос пользователя
            chunks: Найденные чанки
            
        Returns:
            str: Демо-ответ
        """
        if not chunks:
            return (
                "Я пока не нашёл информации по этому вопросу в базе знаний. "
                "Попробуй сформулировать вопрос иначе или выбери тему из меню."
            )
        
        # Использование первого наиболее релевантного чанка
        best_chunk = chunks[0]
        content = best_chunk.get("content", "")[:800]
        
        answer = f"Вот что я нашёл по теме «{best_chunk.get('topic', 'вопрос')}»:\n\n"
        answer += content
        
        if len(answer) > 1500:
            answer = answer[:1500] + "..."
        
        return answer
    
    async def _get_cache_ttl(self, query: str) -> int:
        """
        Определение TTL для кэша на основе частотности запроса.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            int: TTL в секундах
        """
        # Проверка частотности запроса
        stats = await self.cache_manager.get_query_stats()
        
        query_hash = hash(query.lower().strip())
        
        if query_hash in stats.get("top_queries", []):
            # Топ-20% запросов - 24 часа
            return 86400
        elif query_hash in stats.get("medium_queries", []):
            # Средние запросы - 6 часов
            return 21600
        else:
            # Редкие запросы - 1 час
            return 3600
    
    async def generate_test(
        self,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Генерация теста по теме.
        
        Args:
            topic: Название темы
            difficulty: Сложность (easy, medium, hard)
            num_questions: Количество вопросов
            
        Returns:
            Dict[str, Any]: Сгенерированный тест
        """
        # Поиск информации по теме
        relevant_chunks = await self._search_chunks(topic)
        
        if not relevant_chunks:
            return {
                "error": "Не удалось найти информацию по теме",
                "questions": {}
            }
        
        # Формирование контекста для генерации вопросов
        context = self._build_context(relevant_chunks)
        
        # Генерация вопросов через LLM или демо-режим
        if self.llm_client:
            questions = await self.llm_client.generate_questions(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions,
                context=context
            )
        else:
            questions = self._generate_demo_questions(topic, difficulty, num_questions)
        
        return {
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "total_questions": len(questions),
            "current_question": 0
        }
    
    def _generate_demo_questions(
        self,
        topic: str,
        difficulty: str,
        num_questions: int
    ) -> Dict[str, Any]:
        """
        Генерация демо-вопросов без LLM.
        
        Args:
            topic: Название темы
            difficulty: Сложность
            num_questions: Количество вопросов
            
        Returns:
            Dict[str, Any]: Словарь вопросов
        """
        # Демо-вопросы по темам
        demo_questions = {
            "человек и общество": {
                "easy": [
                    {
                        "question": "Что такое общество?",
                        "answers": [
                            "Совокупность людей с общими интересами",
                            "Группа животных",
                            "Компьютерная сеть",
                            "Государственная организация"
                        ],
                        "correct_answer": 0,
                        "explanation": "Общество — это совокупность людей, объединённых общими интересами, культурой и социальными связями.",
                        "difficulty": "easy"
                    },
                    {
                        "question": "Что такое социализация?",
                        "answers": [
                            "Процесс обучения в школе",
                            "Усвоение социальных норм и ценностей",
                            "Общение в интернете",
                            "Работа в коллективе"
                        ],
                        "correct_answer": 1,
                        "explanation": "Социализация — это процесс усвоения индивидом социальных норм, ценностей и навыков.",
                        "difficulty": "easy"
                    }
                ],
                "medium": [
                    {
                        "question": "Какие социальные институты существуют в обществе?",
                        "answers": [
                            "Семья, образование, государство, религия",
                            "Компьютер, телефон, интернет",
                            "Магазин, больница, парк",
                            "Армия, полиция, суд"
                        ],
                        "correct_answer": 0,
                        "explanation": "Социальные институты — это устойчивые формы организации общественной жизни.",
                        "difficulty": "medium"
                    }
                ],
                "hard": [
                    {
                        "question": "Как взаимосвязаны человек и общество в процессе исторического развития?",
                        "answers": [
                            "Человек формируется обществом и одновременно влияет на его развитие",
                            "Человек полностью независим от общества",
                            "Общество не влияет на личность",
                            "Человек и общество развиваются изолированно"
                        ],
                        "correct_answer": 0,
                        "explanation": "Человек и общество находятся в диалектическом единстве: общество формирует личность, а человек влияет на общество.",
                        "difficulty": "hard"
                    }
                ]
            },
            "экономика": {
                "easy": [
                    {
                        "question": "Что изучает экономика?",
                        "answers": [
                            "Удовлетворение потребностей в условиях ограниченных ресурсов",
                            "Природу и окружающую среду",
                            "Историю государства",
                            "Психологию человека"
                        ],
                        "correct_answer": 0,
                        "explanation": "Экономика изучает производство, распределение и потребление товаров и услуг.",
                        "difficulty": "easy"
                    },
                    {
                        "question": "Какие функции выполняют деньги?",
                        "answers": [
                            "Мера стоимости, средство платежа, средство накопления",
                            "Только средство платежа",
                            "Только средство накопления",
                            "Только средство обмена"
                        ],
                        "correct_answer": 0,
                        "explanation": "Деньги выполняют три основные функции: мера стоимости, средство платежа, средство накопления.",
                        "difficulty": "easy"
                    }
                ],
                "medium": [
                    {
                        "question": "Какая экономическая система основана на частной собственности и рыночном регулировании?",
                        "answers": [
                            "Рыночная экономика",
                            "Командная экономика",
                            "Традиционная экономика",
                            "Смешанная экономика"
                        ],
                        "correct_answer": 0,
                        "explanation": "Рыночная экономика характеризуется частной собственностью и регулированием через спрос и предложение.",
                        "difficulty": "medium"
                    },
                    {
                        "question": "Что такое инфляция?",
                        "answers": [
                            "Повышение общего уровня цен на товары и услуги",
                            "Понижение цен на товары",
                            "Увеличение производства",
                            "Снижение безработицы"
                        ],
                        "correct_answer": 0,
                        "explanation": "Инфляция — это устойчивое повышение общего уровня цен, приводящее к снижению покупательной способности денег.",
                        "difficulty": "medium"
                    }
                ],
                "hard": [
                    {
                        "question": "Как центральные банки используют процентные ставки для борьбы с инфляцией?",
                        "answers": [
                            "Повышают ставки, чтобы сократить денежную массу",
                            "Понижают ставки, чтобы увеличить денежную массу",
                            "Оставляют ставки без изменений",
                            "Устраняют инфляцию через фиксацию цен"
                        ],
                        "correct_answer": 0,
                        "explanation": "Повышение процентных ставок делает кредиты дороже, сокращает потребление и инвестиции, что снижает инфляционное давление.",
                        "difficulty": "hard"
                    }
                ]
            },
            "право": {
                "easy": [
                    {
                        "question": "Что такое право?",
                        "answers": [
                            "Система обязательных правил поведения, установленных государством",
                            "Совет директоров компании",
                            "Суд и полиция",
                            "Законы природы"
                        ],
                        "correct_answer": 0,
                        "explanation": "Право — это система обязательных правил поведения, установленных государством.",
                        "difficulty": "easy"
                    },
                    {
                        "question": "Какой закон является главным в России?",
                        "answers": [
                            "Конституция РФ",
                            "Гражданский кодекс",
                            "Уголовный кодекс",
                            "Федеральный закон"
                        ],
                        "correct_answer": 0,
                        "explanation": "Конституция РФ — главный закон страны, принятый в 1993 году.",
                        "difficulty": "easy"
                    }
                ],
                "medium": [
                    {
                        "question": "Чем проступок отличается от преступления?",
                        "answers": [
                            "Проступок — менее тяжкое нарушение",
                            "Ничем",
                            "Преступление — менее тяжкое нарушение",
                            "Это одно и то же"
                        ],
                        "correct_answer": 0,
                        "explanation": "Проступок — нарушение с менее строгим наказанием, преступление — с уголовной ответственностью.",
                        "difficulty": "medium"
                    }
                ],
                "hard": [
                    {
                        "question": "Каковы пределы допустимого ограничения прав человека в чрезвычайном положении?",
                        "answers": [
                            "Права могут быть ограничены только в той мере, в какой это необходимо для стабилизации обстановки",
                            "Все права могут быть полностью отменены",
                            "Права не могут быть ограничены ни при каких обстоятельствах",
                            "Только имущественные права могут быть ограничены"
                        ],
                        "correct_answer": 0,
                        "explanation": "В ЧП права могут быть ограничены только пропорционально угрозе, при этом некоторые права (жизнь, достоинство) не подлежат ограничению.",
                        "difficulty": "hard"
                    }
                ]
            }
        }
        
        # Выбор вопросов по теме и сложности
        topic_lower = topic.lower()
        questions_list = []
        
        for key, difficulties in demo_questions.items():
            if key in topic_lower:
                # Получаем вопросы по сложности
                questions_list = difficulties.get(difficulty, difficulties.get("easy", []))
                break
        
        if not questions_list:
            # Использование вопросов по умолчанию
            if "человек и общество" in demo_questions:
                questions_list = demo_questions["человек и общество"].get(difficulty, [])
        
        # Если нет вопросов, берём любые
        if not questions_list:
            for key, difficulties in demo_questions.items():
                questions_list = difficulties.get(difficulty, [])
                if questions_list:
                    break
        
        # Ограничение количества вопросов
        questions_list = questions_list[:num_questions]
        
        # Форматирование в словарь
        questions_dict = {}
        for i, q in enumerate(questions_list):
            questions_dict[f"q_{i}"] = q
        
        return questions_dict
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик RAG-пайплайна.
        
        Returns:
            Dict[str, Any]: Метрики работы системы
        """
        cache_hit_rate = 0.0
        if self.metrics["total_requests"] > 0:
            cache_hit_rate = self.metrics["cache_hits"] / self.metrics["total_requests"] * 100
        
        return {
            "rag_total_requests": self.metrics["total_requests"],
            "rag_cache_hits": self.metrics["cache_hits"],
            "rag_cache_hit_rate": cache_hit_rate,
            "rag_avg_response_time": self.metrics["avg_response_time"],
            "rag_errors": self.metrics["errors"]
        }
    
    async def close(self) -> None:
        """Закрытие соединений и очистка ресурсов."""
        logger.info("Закрытие RAG-пайплайна...")
        
        if self.vector_store:
            await self.vector_store.close()
        
        if self.existing_store:
            await self.existing_store.close()
        
        if self.text_search:
            await self.text_search.close()
        
        if self.llm_client:
            await self.llm_client.close()
        
        logger.info("RAG-пайплайн закрыт")
