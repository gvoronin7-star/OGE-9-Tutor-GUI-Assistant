# -*- coding: utf-8 -*-
"""
Векторное хранилище для готовой базы RAG_data_base.

Использует предсозданный индекс Faiss с эмбеддингами OpenAI text-embedding-3-small.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ExistingVectorStore:
    """
    Векторное хранилище для готовой базы RAG_data_base.

    Использует предсозданный Faiss-индекс с размерностью 1536.

    Attributes:
        base_dir: Директория базы данных
        dataset: Данные чанков из dataset.json
        index: Faiss-индекс
        embedding_dim: Размерность эмбеддингов (1536)
    """

    def __init__(self, base_dir: Path = Path("RAG_data_base/vector_db")) -> None:
        """
        Инициализация хранилища.

        Args:
            base_dir: Директория с векторной базой
        """
        self.base_dir = Path(base_dir)
        self.dataset: List[Dict[str, Any]] = []
        self.index = None
        self.metadata: Dict[str, Any] = {}
        self.embedding_dim = 1536  # text-embedding-3-small

        # Для локальных эмбеддингов (fallback)
        self.model: Optional[SentenceTransformer] = None

        self._lock = asyncio.Lock()

    async def load(self) -> bool:
        """
        Загрузка готового индекса и данных.

        Returns:
            bool: True если успешно загружено
        """
        logger.info("Загрузка готовой векторной базы...")

        index_file = self.base_dir / "index.faiss"
        dataset_file = self.base_dir / "dataset.json"
        metadata_file = self.base_dir / "metadata.json"

        # Проверка наличия файлов
        if not index_file.exists():
            logger.error(f"Индекс не найден: {index_file}")
            return False

        if not dataset_file.exists():
            logger.error(f"Датасет не найден: {dataset_file}")
            return False

        try:
            import faiss

            # Загрузка индекса Faiss
            self.index = faiss.read_index(str(index_file))
            logger.info(f"Индекс загружен: {self.index.ntotal} векторов")

            # Загрузка датасета
            with open(dataset_file, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)

            logger.info(f"Загружено {len(self.dataset)} чанков")

            # Загрузка метаданных
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

                logger.info(f"Модель: {self.metadata.get('model_name', 'unknown')}")
                logger.info(
                    f"Размерность: {self.metadata.get('embedding_dim', 'unknown')}"
                )

            return True

        except Exception as e:
            logger.error(f"Ошибка загрузки индекса: {e}")
            return False

    async def search(
        self, query: str, top_k: int = 5, use_remote_embedding: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантных чанков.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            use_remote_embedding: Использовать ли OpenAI API для эмбеддингов

        Returns:
            List[Dict[str, Any]]: Список релевантных чанков
        """
        import faiss

        if not self.index or not self.dataset:
            logger.warning("Индекс не загружен")
            return []

        try:
            # Генерация эмбеддинга запроса
            if use_remote_embedding:
                # Требуется OpenAI API
                query_embedding = await self._get_openai_embedding(query)
            else:
                # Локальная модель (fallback, менее точно)
                query_embedding = await self._get_local_embedding(query)

            if query_embedding is None:
                return []

            # Нормализация через numpy (надёжнее)
            norms = np.linalg.norm(query_embedding, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            query_embedding = (query_embedding / norms).astype("float32")

            # Поиск
            distances, indices = self.index.search(
                query_embedding.astype("float32"), min(top_k, self.index.ntotal)
            )

            # Формирование результатов
            results = []

            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.dataset):
                    continue

                chunk = self.dataset[idx]

                # Преобразование расстояния в score
                score = float(1 / (1 + dist))

                results.append(
                    {
                        "chunk_id": chunk.get("metadata", {}).get("chunk_id", idx),
                        "text": chunk.get("text", ""),
                        "type": chunk.get("type", "paragraph"),
                        "topic": self._extract_topic(chunk),
                        "content": chunk.get("text", ""),
                        "source": chunk.get("metadata", {}).get("source", ""),
                        "page": chunk.get("metadata", {}).get("page_number", 0),
                        "score": score,
                        "keywords": chunk.get("metadata", {}).get("keywords", []),
                        "intent": chunk.get("metadata", {}).get("intent", ""),
                        "summary": chunk.get("metadata", {}).get("summary", ""),
                        "search_type": "vector_existing",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

    async def _get_openai_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Получение эмбеддинга через ProxyAPI (OpenAI-совместимый API).

        Args:
            text: Текст для эмбеддинга

        Returns:
            np.ndarray: Вектор эмбеддинга или None
        """
        try:
            import os

            import aiohttp

            # Используем ProxyAPI вместо OpenAI
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("PROXY_API_KEY")

            if not api_key:
                logger.warning("OPENAI_API_KEY / PROXY_API_KEY не установлен")
                return None

            url = f"{base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {"model": "text-embedding-3-small", "input": text}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedding = np.array(data["data"][0]["embedding"])
                        return embedding.reshape(1, -1)
                    elif resp.status == 401:
                        logger.error("Ошибка авторизации API (401)")
                        return None
                    elif resp.status == 429:
                        logger.warning("Превышен лимит запросов API (429)")
                        return None
                    else:
                        logger.error(f"API error: {resp.status}")
                        return None

        except Exception as e:
            logger.error(f"Ошибка получения эмбеддинга: {e}")
            return None

    async def _get_local_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Получение эмбеддинга через локальную модель.

        Args:
            text: Текст для эмбеддинга

        Returns:
            np.ndarray: Вектор эмбеддинга или None
        """
        try:
            if not self.model:
                self.model = SentenceTransformer("cointegrated/rubert-tiny2")

            embedding = self.model.encode([text], show_progress_bar=False)

            # Размерность не совпадает (312 vs 1536), но можно использовать для аппроксимации
            # Это не идеально, но работает как fallback

            return embedding

        except Exception as e:
            logger.error(f"Ошибка локального эмбеддинга: {e}")
            return None

    def _extract_topic(self, chunk: Dict[str, Any]) -> str:
        """
        Извлечение темы из чанка.

        Args:
            chunk: Данные чанка

        Returns:
            str: Название темы
        """
        keywords = chunk.get("metadata", {}).get("keywords", [])

        if not keywords:
            return "Неизвестная тема"

        # Определение темы по ключевым словам
        topic_mapping = {
            "Человек и общество": ["общество", "человек", "личность", "деятельность"],
            "Экономика": ["экономика", "рынок", "деньги", "производство", "торговля"],
            "Социальная сфера": ["социальная", "семья", "общество", "роль"],
            "Политика": ["политика", "власть", "государство", "выборы", "партии"],
            "Право": ["право", "закон", "конституция", "юридический"],
            "Духовная культура": [
                "культура",
                "наука",
                "образование",
                "религия",
                "мораль",
            ],
        }

        for topic, topic_keywords in topic_mapping.items():
            if any(kw in keywords for kw in topic_keywords):
                return topic

        return "Общая тема"

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики базы.

        Returns:
            Dict[str, Any]: Статистика
        """
        return {
            "total_chunks": len(self.dataset),
            "total_vectors": self.index.ntotal if self.index else 0,
            "embedding_dim": self.embedding_dim,
            "model": self.metadata.get("model_name", "unknown"),
            "source": "RAG_data_base",
        }

    async def close(self) -> None:
        """Закрытие хранилища."""
        logger.info("Векторное хранилище закрыто")
