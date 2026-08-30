# -*- coding: utf-8 -*-
"""
Модуль кэширования на базе Redis.

Реализует динамическое кэширование с анализом частотности запросов.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from utils.logger import query_stats_logger

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Менеджер кэширования с динамическим TTL.

    Использует Redis для хранения ответов с разным временем жизни
    в зависимости от частотности запроса.

    Attributes:
        redis_client: Асинхронный Redis-клиент
        host: Хост Redis
        port: Порт Redis
        query_stats: Статистика запросов
    """

    def __init__(self) -> None:
        """Инициализация менеджера кэширования."""
        self.redis_client: Optional[redis.Redis] = None
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.query_stats = query_stats_logger

        # TTL для разных категорий запросов
        self.ttl_categories = {
            "top": 86400,  # 24 часа для топ-20% запросов
            "medium": 21600,  # 6 часов для средних
            "rare": 3600,  # 1 час для редких
        }

        self._initialized = False

    async def initialize(self) -> None:
        """
        Инициализация подключения к Redis.
        """
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Проверка подключения
            await self.redis_client.ping()

            self._initialized = True
            logger.info(f"Подключение к Redis установлено ({self.host}:{self.port})")

            # Предварительная загрузка популярных запросов
            await self._preload_cache()

        except Exception as e:
            logger.warning(
                f"Не удалось подключиться к Redis: {e}. Кэширование недоступно."
            )
            self._initialized = False

    async def _preload_cache(self) -> None:
        """Предварительная загрузка популярных запросов из статистики."""
        try:
            # Загрузка статистики из файла
            stats_file = Path("logs/query_stats.json")
            if stats_file.exists():
                with open(stats_file, "r", encoding="utf-8") as f:
                    stats = json.load(f)

                if stats:
                    logger.info(f"Загружена статистика {len(stats)} запросов")

        except Exception as e:
            logger.warning(f"Не удалось загрузить статистику: {e}")

    async def ping(self) -> bool:
        """
        Проверка доступности Redis.

        Returns:
            bool: True если Redis доступен
        """
        if not self._initialized or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

    def _get_ttl_category(self, query: str) -> str:
        """
        Определение категории TTL для запроса.

        Args:
            query: Текст запроса

        Returns:
            str: Категория (top, medium, rare)
        """
        query_hash = hash(query.lower().strip())

        top_queries = self.query_stats.get_top_queries(0.2)
        if query_hash in top_queries:
            return "top"

        medium_queries = self.query_stats.get_medium_queries()
        if query_hash in medium_queries:
            return "medium"

        return "rare"

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получение значения из кэша.

        Args:
            key: Ключ кэша

        Returns:
            Optional[Dict[str, Any]]: Значение или None
        """
        if not self._initialized:
            return None

        try:
            value = await self.redis_client.get(key)

            if value:
                return json.loads(value)

            return None

        except Exception as e:
            logger.error(f"Ошибка чтения из кэша: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
        query: Optional[str] = None,
    ) -> bool:
        """
        Сохранение значения в кэш.

        Args:
            key: Ключ кэша
            value: Значение для сохранения
            ttl: Время жизни в секундах (если None - определяется автоматически)
            query: Текст запроса для определения TTL

        Returns:
            bool: True если успешно
        """
        if not self._initialized:
            return False

        try:
            # Определение TTL, если не указан
            if ttl is None and query:
                category = self._get_ttl_category(query)
                ttl = self.ttl_categories.get(category, self.ttl_categories["rare"])
            elif ttl is None:
                ttl = self.ttl_categories["rare"]

            # Сериализация и сохранение
            value_json = json.dumps(value, ensure_ascii=False)

            await self.redis_client.setex(key, ttl, value_json)

            return True

        except Exception as e:
            logger.error(f"Ошибка записи в кэш: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Удаление значения из кэша.

        Args:
            key: Ключ кэша

        Returns:
            bool: True если успешно
        """
        if not self._initialized:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False

    async def get_query_stats(self) -> Dict[str, Any]:
        """
        Получение статистики запросов.

        Returns:
            Dict[str, Any]: Статистика
        """
        return {
            "top_queries": self.query_stats.get_top_queries(0.2),
            "medium_queries": self.query_stats.get_medium_queries(),
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик кэширования.

        Returns:
            Dict[str, Any]: Метрики
        """
        if not self._initialized:
            return {"cache_available": False}

        try:
            # Получение информации о памяти
            info = await self.redis_client.info("memory")

            # Получение количества ключей
            keys_count = await self.redis_client.dbsize()

            return {
                "cache_available": True,
                "keys_count": keys_count,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(f"Ошибка получения метрик кэша: {e}")
            return {"cache_available": False, "error": str(e)}

    async def clear_cache(self) -> bool:
        """
        Очистка всего кэша.

        Returns:
            bool: True если успешно
        """
        if not self._initialized:
            return False

        try:
            await self.redis_client.flushdb()
            logger.info("Кэш очищен")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return False

    async def get_cache_keys(self, pattern: str = "*") -> List[str]:
        """
        Получение ключей кэша по паттерну.

        Args:
            pattern: Паттерн для поиска

        Returns:
            List[str]: Список ключей
        """
        if not self._initialized:
            return []

        try:
            keys = await self.redis_client.keys(pattern)
            return keys
        except Exception as e:
            logger.error(f"Ошибка получения ключей: {e}")
            return []

    async def close(self) -> None:
        """Закрытие соединения с Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Соединение с Redis закрыто")


class InMemoryCache:
    """
    Запасной кэш в памяти, если Redis недоступен.

    Attributes:
        cache: Словарь для хранения данных
    """

    def __init__(self) -> None:
        """Инициализация."""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttls: Dict[str, float] = {}

    async def initialize(self) -> None:
        """Инициализация (nop для in-memory)."""
        pass

    async def ping(self) -> bool:
        """Проверка доступности."""
        return True

    async def close(self) -> None:
        """Закрытие."""
        pass

    async def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик."""
        return {
            "cache_available": True,
            "in_memory": True,
            "keys_count": len(self.cache),
        }

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Получение значения."""
        if key not in self.cache:
            return None

        # Проверка TTL
        if key in self.ttls:
            import time

            if time.time() > self.ttls[key]:
                del self.cache[key]
                del self.ttls[key]
                return None

        return self.cache[key]

    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """Сохранение значения."""
        import time

        self.cache[key] = value
        self.ttls[key] = time.time() + ttl
        return True

    async def delete(self, key: str) -> bool:
        """Удаление значения."""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttls:
                del self.ttls[key]
            return True
        return False

    async def clear(self) -> bool:
        """Очистка кэша."""
        self.cache.clear()
        self.ttls.clear()
        return True

    async def get_query_stats(self) -> Dict[str, Any]:
        """Получение статистики запросов (заглушка для InMemoryCache)."""
        return {"top_queries": [], "medium_queries": []}

    async def get_cache_keys(self, pattern: str = "*") -> List[str]:
        """Получение ключей кэша."""
        return list(self.cache.keys())
