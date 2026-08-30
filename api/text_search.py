# -*- coding: utf-8 -*-
"""
Полнотекстовый поиск на базе Whoosh.

Обеспечивает точный поиск по ключевым словам в текстах чанков.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from whoosh import index
from whoosh.fields import ID, KEYWORD, TEXT, Schema
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.query import And, Or, Term

logger = logging.getLogger(__name__)


class TextSearchEngine:
    """
    Полнотекстовый поисковик на базе Whoosh.

    Обеспечивает точный поиск по ключевым словам
    с использованием морфологического анализа.

    Attributes:
        index_dir: Директория для хранения индекса
        ix: Whoosh-индекс
        chunks_data: Данные чанков
    """

    def __init__(self, index_dir: Path) -> None:
        """
        Инициализация поискового движка.

        Args:
            index_dir: Директория для хранения индекса
        """
        self.index_dir = index_dir
        self.ix: Optional[index.Index] = None
        self.chunks_data: Dict[str, Dict[str, Any]] = {}

        # Определение схемы индекса
        self.schema = Schema(
            chunk_id=ID(stored=True, unique=True),
            topic=TEXT(stored=True, sortable=True),
            content=TEXT(stored=True),
            keywords=KEYWORD(stored=True, commas=True),
        )

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Инициализация поискового индекса.
        """
        logger.info("Инициализация полнотекстового поиска...")

        # Создание индекса
        try:
            if index.exists_in(str(self.index_dir)):
                self.ix = index.open_dir(str(self.index_dir))
            else:
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.ix = index.create_in(str(self.index_dir), self.schema)

            logger.info("Whoosh-индекс инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Whoosh: {e}")
            raise

    async def load(self) -> None:
        """
        Загрузка индекса из файлов.
        """
        logger.info("Загрузка Whoosh-индекса...")

        index_file = self.index_dir / "whoosh"
        metadata_file = self.index_dir / "whoosh_chunks.json"

        if not index.exists_in(str(self.index_dir)):
            logger.info("Whoosh-индекс не найден, будет создан новый")
            await self.initialize()
            return

        try:
            self.ix = index.open_dir(str(self.index_dir))

            # Загрузка метаданных
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    self.chunks_data = json.load(f)

            logger.info("Whoosh-индекс загружен")

        except Exception as e:
            logger.error(f"Ошибка загрузки Whoosh-индекса: {e}")
            await self.initialize()

    async def save(self) -> None:
        """
        Сохранение метаданных чанков.
        """
        try:
            metadata_file = self.index_dir / "whoosh_chunks.json"

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks_data, f, ensure_ascii=False, indent=2)

            logger.info("Метаданные Whoosh сохранены")

        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")

    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Индексация чанков для полнотекстового поиска.

        Args:
            chunks: Список чанков для индексации
        """
        async with self._lock:
            if not self.ix:
                await self.initialize()

            logger.info(f"Индексация {len(chunks)} чанков в Whoosh...")

            # Пересоздание индекса (перезаписывает старый целиком)
            self.ix = index.create_in(str(self.index_dir), self.schema)
            writer = self.ix.writer()

            # Индексация чанков
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id", "")
                topic = chunk.get("topic", "")
                content = chunk.get("content", "")

                # Извлечение ключевых слов
                keywords = self._extract_keywords(content)

                writer.add_document(
                    chunk_id=chunk_id,
                    topic=topic,
                    content=content,
                    keywords=", ".join(keywords),
                )

                self.chunks_data[chunk_id] = {
                    "chunk_id": chunk_id,
                    "topic": topic,
                    "content": content,
                    "source": chunk.get("source", ""),
                    "keywords": keywords,
                }

            writer.commit()

            logger.info(f"Проиндексировано {len(chunks)} чанков в Whoosh")

            # Сохранение метаданных
            await self.save()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Извлечение ключевых слов из текста.

        Args:
            text: Текст для анализа

        Returns:
            List[str]: Список ключевых слов
        """
        # Простое извлечение слов (можно улучшить с помощью NLTK)
        words = text.lower().split()

        # Фильтрация стоп-слов
        stop_words = {
            "и",
            "в",
            "на",
            "по",
            "это",
            "что",
            "как",
            "из",
            "к",
            "с",
            "для",
            "от",
            "о",
            "за",
            "до",
            "при",
            "или",
            "но",
            "не",
            "а",
            "то",
            "же",
            "так",
            "его",
            "её",
            "их",
            "который",
            "которая",
        }

        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # Уникальные слова
        unique_keywords = list(set(keywords))[:20]

        return unique_keywords

    async def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Поиск чанков по ключевым словам.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов

        Returns:
            List[Dict[str, Any]]: Список релевантных чанков
        """
        if not self.ix:
            logger.warning("Whoosh-индекс недоступен")
            return []

        try:
            with self.ix.searcher() as searcher:
                # Парсинг запроса (поиск по нескольким полям)
                parser = MultifieldParser(
                    ["topic", "content", "keywords"], schema=self.schema
                )
                q = parser.parse(query)

                # Выполнение поиска
                results = searcher.search(q, limit=top_k * 2)

                # Форматирование результатов
                search_results = []
                seen_topics = set()

                for hit in results:
                    topic = hit.get("topic", "")

                    if topic not in seen_topics:
                        seen_topics.add(topic)

                        # Вычисление score на основе ранга
                        score = 1.0 - (hit.rank / len(results))

                        search_results.append(
                            {
                                "chunk_id": hit.get("chunk_id", ""),
                                "topic": topic,
                                "content": hit.get("content", ""),
                                "source": hit.get("source", ""),
                                "score": score,
                                "search_type": "text",
                            }
                        )

                        if len(search_results) >= top_k:
                            break

                return search_results

        except Exception as e:
            logger.error(f"Ошибка полнотекстового поиска: {e}")
            return []

    async def close(self) -> None:
        """Закрытие поискового движка."""
        if self.ix:
            self.ix.close()

        logger.info("Полнотекстовый поиск закрыт")
