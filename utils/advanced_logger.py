# -*- coding: utf-8 -*-
"""
Расширенная система логирования для отладки.

Включает:
- Разные уровни логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Разные файлы для разных компонентов
- Цветной вывод в консоль
- Временные метки с миллисекундами
- Контекстная информация (user_id, запрос, время выполнения)
- JSON формат для машинного чтения
- GUI просмотрщик логов

Автор: KODA
Дата: Апрель 2026
"""

import csv
import json
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ============================================================================
# ЦВЕТНОЙ ФОРМАТТЕР ДЛЯ КОНСОЛИ
# ============================================================================


class ColorizedFormatter(logging.Formatter):
    """Цветной форматтер для консоли."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи с цветом."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ============================================================================
# КОНТЕКСТНЫЙ ЛОГГЕР
# ============================================================================


class ContextLogger:
    """
    Логгер с контекстной информацией.

    Позволяет добавлять контекст (user_id, request_id, etc.) ко всем сообщениям.
    """

    _context: Dict[str, Any] = {}
    _lock = threading.Lock()

    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """Установка контекста."""
        with cls._lock:
            cls._context.update(kwargs)

    @classmethod
    def clear_context(cls) -> None:
        """Очистка контекста."""
        with cls._lock:
            cls._context.clear()

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Получение текущего контекста."""
        return cls._context.copy()

    @classmethod
    def contextualize(cls, **kwargs: Any) -> Callable:
        """Декоратор для добавления контекста к функции."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **func_kwargs):
                old_context = cls.get_context()
                try:
                    cls.set_context(**kwargs)
                    return func(*args, **func_kwargs)
                finally:
                    with cls._lock:
                        cls._context.clear()
                        cls._context.update(old_context)

            return wrapper

        return decorator


# ============================================================================
# МЕНЕДЖЕР ЛОГОВ
# ============================================================================


class LogManager:
    """
    Менеджер логирования для всего приложения.

    Создает и управляет логгерами для разных компонентов.
    """

    _instance: Optional["LogManager"] = None
    _lock = threading.Lock()
    _initialized: bool

    def __new__(cls) -> "LogManager":
        """Singleton паттерн."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Инициализация менеджера логов."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self.log_dir = Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.loggers: Dict[str, logging.Logger] = {}
        self.handlers: Dict[str, List[logging.Handler]] = {}

        self._setup_global_handlers()

    def _setup_global_handlers(self) -> None:
        """Настройка глобальных обработчиков."""
        # Формат для файлов
        file_format = logging.Formatter(
            "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Формат для JSON
        json_format = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )

        # Консольный обработчик (цветной)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            ColorizedFormatter(
                "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        console_handler.setLevel(logging.DEBUG)

        # Общий файл для всех логов
        all_handler = logging.FileHandler(self.log_dir / "all.log", encoding="utf-8")
        all_handler.setFormatter(file_format)
        all_handler.setLevel(logging.DEBUG)

        # JSON файл для машинного чтения
        json_handler = logging.FileHandler(self.log_dir / "app.json", encoding="utf-8")
        json_handler.setFormatter(json_format)
        json_handler.setLevel(logging.INFO)

        # Сохранение handlers
        self.handlers["console"] = [console_handler]
        self.handlers["file"] = [all_handler]
        self.handlers["json"] = [json_handler]

    def get_logger(self, name: str, level: int = logging.DEBUG) -> logging.Logger:
        """
        Получение или создание логгера.

        Args:
            name: Имя логгера (например, 'rag', 'llm', 'gui')
            level: Уровень логирования

        Returns:
            logging.Logger: Настроенный логгер
        """
        if name in self.loggers:
            return self.loggers[name]

        # Создание логгера
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False  # Не передавать в root logger

        # Добавление handlers
        for handler in self.handlers["console"]:
            logger.addHandler(handler)

        # Отдельный файл для каждого компонента
        file_handler = logging.FileHandler(
            self.log_dir / f"{name}.log", encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        self.loggers[name] = logger
        self.handlers[name] = [file_handler]

        logger.info(f"Логгер '{name}' инициализирован")

        return logger

    def set_level(self, name: str, level: int) -> None:
        """
        Установка уровня логирования.

        Args:
            name: Имя логгера
            level: Уровень (logging.DEBUG, INFO, etc.)
        """
        if name in self.loggers:
            self.loggers[name].setLevel(level)

    def get_log_file(self, name: str) -> Path:
        """
        Получение пути к файлу лога.

        Args:
            name: Имя логгера

        Returns:
            Path: Путь к файлу
        """
        return self.log_dir / f"{name}.log"

    def clear_logs(self) -> None:
        """Очистка всех логов."""
        for log_file in self.log_dir.glob("*.log"):
            log_file.unlink()
        for json_file in self.log_dir.glob("*.json"):
            json_file.unlink()


# ============================================================================
# ЛОГГЕР ЗАПРОСОВ С ДЕТАЛИЗАЦИЕЙ
# ============================================================================


class DetailedRequestLogger:
    """
    Детальный логгер запросов с метриками.

    Записывает полную информацию о каждом запросе:
    - Входные данные
    - Время выполнения каждого этапа
    - Выходные данные
    - Ошибки
    """

    def __init__(self, log_dir: Path) -> None:
        """Инициализация."""
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.requests_file = self.log_dir / "requests_detailed.csv"
        self.errors_file = self.log_dir / "errors.csv"

        self._init_files()

    def _init_files(self) -> None:
        """Инициализация файлов."""
        # Requests CSV
        if not self.requests_file.exists():
            with open(self.requests_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "request_id",
                        "user_id",
                        "component",
                        "action",
                        "input_data",
                        "output_data",
                        "duration_ms",
                        "status",
                        "error_message",
                    ]
                )

        # Errors CSV
        if not self.errors_file.exists():
            with open(self.errors_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "request_id",
                        "component",
                        "error_type",
                        "error_message",
                        "stack_trace",
                    ]
                )

    def log_request(
        self,
        component: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        duration_ms: float,
        status: str = "success",
        error_message: Optional[str] = None,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Запись запроса в лог.

        Args:
            component: Компонент (rag, llm, gui, etc.)
            action: Действие (query, generate, search, etc.)
            input_data: Входные данные
            output_data: Выходные данные
            duration_ms: Время выполнения в мс
            status: Статус (success, error, timeout)
            error_message: Сообщение об ошибке
            user_id: ID пользователя
            request_id: Уникальный ID запроса
        """
        import uuid

        request_id = request_id or str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        # Сериализация данных
        input_str = json.dumps(input_data, ensure_ascii=False, default=str)[:500]
        output_str = (
            json.dumps(output_data, ensure_ascii=False, default=str)[:500]
            if output_data
            else ""
        )

        with open(self.requests_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    request_id,
                    user_id or "",
                    component,
                    action,
                    input_str,
                    output_str,
                    f"{duration_ms:.2f}",
                    status,
                    error_message or "",
                ]
            )

        # Логирование ошибок
        if status == "error" and error_message:
            # log_request(status="error", ...) вызывается изнутри активного
            # except-блока — sys.exc_info() даёт реальный класс исключения,
            # а не type(error_message) (всегда str, т.к. вызывающие передают
            # уже сформированную строку через str(e))
            exc_type = sys.exc_info()[0]
            error_type_name = exc_type.__name__ if exc_type else "Unknown"

            with open(self.errors_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        timestamp,
                        request_id,
                        component,
                        error_type_name,
                        error_message,
                        traceback.format_exc()[:1000],
                    ]
                )

    def get_requests(
        self,
        component: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Получение запросов из лога.

        Args:
            component: Фильтр по компоненту
            status: Фильтр по статусу
            limit: Максимальное количество записей

        Returns:
            List[Dict[str, Any]]: Список запросов
        """
        requests: List[Dict[str, Any]] = []

        try:
            with open(self.requests_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break

                    if component and row.get("component") != component:
                        continue
                    if status and row.get("status") != status:
                        continue

                    requests.append(row)
        except Exception as e:
            logging.error(f"Ошибка чтения логов: {e}")

        return requests

    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики по запросам."""
        stats: Dict[str, Any] = {
            "total": 0,
            "success": 0,
            "error": 0,
            "avg_duration_ms": 0.0,
            "by_component": {},
        }

        try:
            with open(self.requests_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                durations = []

                for row in reader:
                    stats["total"] += 1

                    if row.get("status") == "success":
                        stats["success"] += 1
                    elif row.get("status") == "error":
                        stats["error"] += 1

                    try:
                        durations.append(float(row.get("duration_ms", 0)))
                    except (ValueError, TypeError):
                        pass

                    component = row.get("component", "unknown")
                    if component not in stats["by_component"]:
                        stats["by_component"][component] = 0
                    stats["by_component"][component] += 1

                if durations:
                    stats["avg_duration_ms"] = sum(durations) / len(durations)
        except Exception as e:
            logging.error(f"Ошибка чтения статистики: {e}")

        return stats


# ============================================================================
# ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ
# ============================================================================

# Менеджер логов (singleton)
log_manager = LogManager()

# Детальный логгер запросов
detailed_logger = DetailedRequestLogger(Path("logs"))

# Логгеры для компонентов
logger_rag = log_manager.get_logger("rag")
logger_llm = log_manager.get_logger("llm")
logger_gui = log_manager.get_logger("gui")
logger_db = log_manager.get_logger("database")
logger_cache = log_manager.get_logger("cache")
logger_bot = log_manager.get_logger("bot")


# ============================================================================
# УТИЛИТЫ
# ============================================================================


def log_execution_time(logger: logging.Logger, action: str) -> Callable:
    """
    Декоратор для логирования времени выполнения функции.

    Args:
        logger: Логгер для записи
        action: Название действия

    Returns:
        Callable: Декоратор
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start).total_seconds() * 1000
                logger.debug(f"{action} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (datetime.now() - start).total_seconds() * 1000
                logger.error(f"{action} failed after {duration:.2f}ms: {e}")
                raise

        return wrapper

    return decorator


def setup_logging(level: str = "DEBUG") -> None:
    """
    Настройка логирования для всего приложения.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.DEBUG)

    # Установка уровня для всех логгеров
    for name, logger in log_manager.loggers.items():
        logger.setLevel(log_level)

    # Логирование настройки
    log_manager.get_logger("system").info(
        f"Логирование настроено: уровень={level}, директория={log_manager.log_dir.absolute()}"
    )
