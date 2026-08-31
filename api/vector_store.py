# -*- coding: utf-8 -*-
"""
Векторное хранилище на базе Faiss.

Обеспечивает семантический поиск по чанкам с использованием
индекса HNSW и эмбеддингов sentence-transformers.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Векторное хранилище для семантического поиска.

    Использует Faiss с индексом HNSW для быстрого поиска
    по эмбеддингам текстов.

    Attributes:
        index_dir: Директория для хранения индекса
        model: Модель для создания эмбеддингов
        index: Faiss-индекс
        chunks_data: Данные чанков
    """

    def __init__(self, index_dir: Path) -> None:
        """
        Инициализация векторного хранилища.

        Args:
            index_dir: Директория для хранения индекса
        """
        self.index_dir = index_dir
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[Any] = None
        self.chunks_data: Dict[str, Dict[str, Any]] = {}
        self.embedding_dim = 768  # Размерность эмбеддингов

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Инициализация модели и индекса.
        """
        logger.info("Инициализация векторного хранилища...")

        # Загрузка модели для эмбеддингов
        try:
            # Использование легкой модели для скорости
            self.model = SentenceTransformer("cointegrated/rubert-tiny2")
            self.embedding_dim = self.model.get_sentence_embedding_dimension()  # type: ignore[assignment]
            logger.info(f"Модель загружена, размерность: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise

        # Создание индекса HNSW
        try:
            import faiss

            # HNSW для быстрого поиска с хорошим качеством
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 50

            logger.info("Faiss-индекс HNSW создан")
        except ImportError:
            logger.warning("Faiss не установлен. Использую упрощённый поиск.")
            self.index = None

    async def load(self) -> None:
        """
        Загрузка индекса из файлов.
        """
        logger.info("Загрузка векторного индекса...")

        index_file = self.index_dir / "faiss.index"
        metadata_file = self.index_dir / "chunks_metadata.json"

        if not index_file.exists() or not metadata_file.exists():
            logger.info("Индексные файлы не найдены, будет создан новый индекс")
            await self.initialize()
            return

        try:
            import json

            import faiss

            # Загрузка индекса
            self.index = faiss.read_index(str(index_file))
            logger.info(f"Индекс загружен, размер: {self.index.ntotal}")

            # Загрузка метаданных
            with open(metadata_file, "r", encoding="utf-8") as f:
                self.chunks_data = json.load(f)

            # Загрузка модели
            self.model = SentenceTransformer("cointegrated/rubert-tiny2")
            self.embedding_dim = self.model.get_sentence_embedding_dimension()  # type: ignore[assignment]

        except Exception as e:
            logger.error(f"Ошибка загрузки индекса: {e}")
            await self.initialize()

    async def save(self) -> None:
        """
        Сохранение индекса в файлы.
        """
        if not self.index or not self.chunks_data:
            return

        try:
            import json

            import faiss

            index_file = self.index_dir / "faiss.index"
            metadata_file = self.index_dir / "chunks_metadata.json"

            # Сохранение индекса
            faiss.write_index(self.index, str(index_file))

            # Сохранение метаданных
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks_data, f, ensure_ascii=False, indent=2)

            logger.info("Векторный индекс сохранён")

        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")

    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Индексация чанков в векторном хранилище.

        Args:
            chunks: Список чанков для индексации
        """
        import faiss

        async with self._lock:
            if not self.model or not self.index:
                await self.initialize()

            logger.info(f"Индексация {len(chunks)} чанков...")

            # Очистка старого индекса
            if self.index:
                self.index.reset()
            self.chunks_data = {}

            # Создание эмбеддингов
            texts = []
            chunk_ids = []

            for chunk in chunks:
                # Использование первых 512 токенов для эмбеддинга
                content = chunk.get("content", "")[:2000]
                texts.append(content)
                chunk_ids.append(chunk.get("chunk_id", ""))

            # Генерация эмбеддингов батчами
            batch_size = 32
            embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_embeddings = self.model.encode(batch, show_progress_bar=False)
                embeddings.append(batch_embeddings)

            embeddings = np.vstack(embeddings).astype("float32")  # type: ignore[assignment]

            # Нормализация эмбеддингов через numpy (надёжнее для Python 3.14)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms

            # Добавление в индекс
            self.index.add(embeddings)

            # Сохранение метаданных
            for i, chunk in enumerate(chunks):
                chunk_id = chunk_ids[i]
                self.chunks_data[chunk_id] = {
                    "chunk_id": chunk_id,
                    "topic": chunk.get("topic", ""),
                    "content": chunk.get("content", ""),
                    "source": chunk.get("source", ""),
                    "index": i,
                }

            logger.info(
                f"Проиндексировано {len(chunks)} чанков, размер индекса: {self.index.ntotal}"
            )

            # Сохранение индекса
            await self.save()

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск релевантных чанков по запросу.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов

        Returns:
            List[Dict[str, Any]]: Список релевантных чанков
        """
        import faiss

        if not self.model or not self.index or not self.chunks_data:
            logger.warning("Векторный поиск недоступен")
            return []

        try:
            # Генерация эмбеддинга запроса
            query_embedding = self.model.encode([query], show_progress_bar=False)

            # Нормализация через numpy (надёжнее для Python 3.14)
            norms = np.linalg.norm(query_embedding, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            query_embedding = (query_embedding / norms).astype("float32")

            # Поиск
            distances, indices = self.index.search(
                query_embedding.astype("float32"), min(top_k * 2, self.index.ntotal)
            )

            # Формирование результатов
            results = []
            seen_topics = set()

            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue

                # Поиск чанка по индексу
                chunk_info = None
                for chunk_id, data in self.chunks_data.items():
                    if data.get("index") == idx:
                        chunk_info = data
                        break

                if chunk_info and chunk_info["topic"] not in seen_topics:
                    seen_topics.add(chunk_info["topic"])

                    # Преобразование расстояния в score (чем больше, тем лучше)
                    score = float(1 / (1 + dist))

                    results.append(
                        {
                            "chunk_id": chunk_info["chunk_id"],
                            "topic": chunk_info["topic"],
                            "content": chunk_info["content"],
                            "source": chunk_info.get("source", ""),
                            "score": score,
                            "search_type": "vector",
                        }
                    )

                    if len(results) >= top_k:
                        break

            return results

        except Exception as e:
            logger.error(f"Ошибка векторного поиска: {e}")
            return []

    async def close(self) -> None:
        """Закрытие хранилища и освобождение ресурсов."""
        if self.index:
            # Сохранение перед закрытием
            await self.save()

        logger.info("Векторное хранилище закрыто")
