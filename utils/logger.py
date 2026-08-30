# -*- coding: utf-8 -*-
"""
Модуль логирования.

Настраивает логирование в приложении с записью в CSV и файлы.

Автор: KODA
Дата: Март 2026
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pythonjsonlogger import jsonlogger


class RequestLogger:
    """
    Логгер для записи запросов и ответов в CSV.

    Attributes:
        log_dir: Директория для логов
        request_log_file: Файл для логов запросов
    """

    def __init__(self, log_dir: Path) -> None:
        """
        Инициализация логгера запросов.

        Args:
            log_dir: Директория для логов
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.request_log_file = self.log_dir / "requests.csv"
        self._init_csv_file()

    def _init_csv_file(self) -> None:
        """Инициализация CSV-файла с заголовками."""
        if not self.request_log_file.exists():
            with open(self.request_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "user_id",
                        "query_text",
                        "retrieved_chunks",
                        "llm_response_time",
                        "total_response_time",
                        "is_cached",
                        "feedback_rating",
                        "topic",
                    ]
                )

    def log_request(
        self,
        user_id: int,
        query_text: str,
        retrieved_chunks: List[str],
        llm_response_time: float,
        total_response_time: float,
        is_cached: bool,
        feedback_rating: Optional[int] = None,
        topic: Optional[str] = None,
    ) -> None:
        """
        Запись запроса в лог.

        Args:
            user_id: ID пользователя
            query_text: Текст запроса
            retrieved_chunks: Список найденных чанков
            llm_response_time: Время ответа LLM
            total_response_time: Общее время ответа
            is_cached: Из кэша ли ответ
            feedback_rating: Оценка пользователя
            topic: Тема запроса
        """
        # Обрезка текста для экономии места
        query_text = query_text[:500]
        retrieved_str = "; ".join(retrieved_chunks[:3])[:200]

        with open(self.request_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    user_id,
                    query_text,
                    retrieved_str,
                    f"{llm_response_time:.3f}",
                    f"{total_response_time:.3f}",
                    "1" if is_cached else "0",
                    str(feedback_rating) if feedback_rating else "",
                    topic or "",
                ]
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по логам.

        Returns:
            Dict[str, Any]: Статистика
        """
        if not self.request_log_file.exists():
            return {
                "total_requests": 0,
                "avg_response_time": 0.0,
                "cache_hit_rate": 0.0,
            }

        total = 0
        response_times = []
        cached = 0

        try:
            with open(self.request_log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += 1
                    try:
                        response_times.append(float(row.get("total_response_time", 0)))
                    except (ValueError, TypeError):
                        pass

                    if row.get("is_cached") == "1":
                        cached += 1

            avg_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )
            cache_rate = cached / total * 100 if total > 0 else 0

            return {
                "total_requests": total,
                "avg_response_time": avg_time,
                "cache_hit_rate": cache_rate,
            }
        except Exception as e:
            logging.error(f"Ошибка чтения статистики: {e}")
            return {"error": str(e)}


class QueryStatsLogger:
    """
    Логгер для отслеживания частотности запросов.

    Используется для динамического кэширования.

    Attributes:
        stats_file: Файл для хранения статистики
        query_stats: Словарь статистики запросов
    """

    def __init__(self, log_dir: Path) -> None:
        """
        Инициализация логгера статистики запросов.

        Args:
            log_dir: Директория для логов
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.stats_file = self.log_dir / "query_stats.json"
        self.query_stats: Dict[str, int] = {}
        self._load_stats()

    def _load_stats(self) -> None:
        """Загрузка статистики из файла."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self.query_stats = json.load(f)
            except Exception:
                self.query_stats = {}

    def _save_stats(self) -> None:
        """Сохранение статистики в файл."""
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.query_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения статистики: {e}")

    def log_query(self, query: str) -> None:
        """
        Запрос в статистику.

        Args:
            query: Текст запроса
        """
        # Нормализация запроса
        query_hash = hash(query.lower().strip())

        if query_hash in self.query_stats:
            self.query_stats[query_hash] += 1
        else:
            self.query_stats[query_hash] = 1

        # Сохранение каждые 10 запросов
        if len(self.query_stats) % 10 == 0:
            self._save_stats()

    def get_top_queries(self, top_percent: float = 0.2) -> List[int]:
        """
        Получение хэшей наиболее частых запросов.

        Args:
            top_percent: Процент от общего числа уникальных запросов

        Returns:
            List[int]: Список хэшей популярных запросов
        """
        if not self.query_stats:
            return []

        # Сортировка по частоте
        sorted_queries = sorted(
            self.query_stats.items(), key=lambda x: x[1], reverse=True
        )

        # Выбор топ-N%
        top_count = max(1, int(len(sorted_queries) * top_percent))

        return [q[0] for q in sorted_queries[:top_count]]

    def get_medium_queries(self) -> List[int]:
        """
        Получение хэшей средних по частоте запросов.

        Returns:
            List[int]: Список хэшей
        """
        if not self.query_stats:
            return []

        sorted_queries = sorted(
            self.query_stats.items(), key=lambda x: x[1], reverse=True
        )

        # Запросы со средней частотой (20-50%)
        start = int(len(sorted_queries) * 0.2)
        end = int(len(sorted_queries) * 0.5)

        return [q[0] for q in sorted_queries[start:end]]


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настройка логирования для приложения.

    Args:
        log_level: Уровень логирования
    """
    # Создание директории для логов
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Настройка корневого логгера
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            # Лог в файл
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            # Лог в консоль
            logging.StreamHandler(),
        ],
    )

    # JSON-логгер для структурированного вывода
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        """Кастомный JSON-форматтер."""

        def add_fields(
            self,
            log_record: Dict[str, Any],
            record: logging.LogRecord,
            message_dict: Dict[str, Any],
        ) -> None:
            """Добавление полей в JSON."""
            super().add_fields(log_record, record, message_dict)
            log_record["timestamp"] = datetime.now().isoformat()
            log_record["level"] = record.levelname

    # Настройка JSON-логгера для отдельного файла
    json_handler = logging.FileHandler(log_dir / "app.json", encoding="utf-8")
    json_handler.setFormatter(
        CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    )

    # Логгеры для отдельных компонентов
    for logger_name in ["bot", "api", "utils"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))

    logging.info("Логирование настроено")


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера для компонента.

    Args:
        name: Имя компонента

    Returns:
        logging.Logger: Логгер
    """
    return logging.getLogger(name)


# Глобальный экземпляр логгера запросов
request_logger = RequestLogger(Path("logs"))
query_stats_logger = QueryStatsLogger(Path("logs"))
