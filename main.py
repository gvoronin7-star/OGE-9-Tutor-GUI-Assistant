# -*- coding: utf-8 -*-
"""
Главный модуль приложения FastAPI.

Этот модуль инициализирует FastAPI-приложение, подключает RAG-пайплайн
и инициализирует все необходимые компоненты.

Автор: KODA
Дата: Апрель 2026
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.rag_pipeline import RAGPipeline
from utils.cache import CacheManager
from utils.logger import setup_logging

# Загрузка переменных окружения из .env
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print("[OK] Переменные окружения загружены из .env")


# Настройка логирования
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Контекстный менеджер для управления жизненным циклом приложения.

    Выполняет инициализацию при старте и очистку при завершении работы.

    Args:
        app: Экземпляр FastAPI-приложения

    Yields:
        None
    """
    logger.info("Запуск приложения OGE Tutor...")

    try:
        # Инициализация кэш-менеджера (с фолбэком на in-memory, если Redis недоступен)
        cache_manager: Any = CacheManager()
        await cache_manager.initialize()

        if await cache_manager.ping():
            logger.info("Кэш-менеджер инициализирован")
        else:
            logger.warning("Redis недоступен, используем in-memory кэш")
            from utils.cache import InMemoryCache

            cache_manager = InMemoryCache()
            await cache_manager.initialize()
            logger.info("Используется in-memory кэш")

        app.state.cache_manager = cache_manager

        # Инициализация RAG-пайплайна
        rag_pipeline = RAGPipeline(cache_manager)
        await rag_pipeline.initialize()
        app.state.rag_pipeline = rag_pipeline

        # Вывод статуса RAG_data_base
        if rag_pipeline.use_existing:
            logger.info("✓ RAG_data_base активна (204 чанка ФИПИ)")
        else:
            logger.info("⚠ RAG_data_base не активна, используется локальный индекс")

        logger.info("RAG-пайплайн инициализирован")

        logger.info("Приложение успешно инициализировано")

    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}", exc_info=True)
        raise

    yield

    # Очистка при завершении
    logger.info("Завершение работы приложения...")
    if hasattr(app.state, "cache_manager"):
        await app.state.cache_manager.close()
    if hasattr(app.state, "rag_pipeline"):
        await app.state.rag_pipeline.close()
    logger.info("Приложение завершено")


# Создание FastAPI-приложения
app = FastAPI(
    title="OGE Tutor API",
    description="API для RAG-ассистента подготовки к ОГЭ по обществознанию",
    version="2.3.0",
    lifespan=lifespan,
)


@app.get("/")
async def root() -> JSONResponse:
    """
    Корневой эндпоинт для проверки работоспособности.

    Returns:
        JSONResponse: Статус приложения
    """
    return JSONResponse(
        {"status": "online", "service": "OGE Tutor", "version": "2.3.0"}
    )


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Эндпоинт для проверки здоровья всех компонентов.

    Returns:
        JSONResponse: Статус всех компонентов системы
    """
    try:
        cache_status = "not_initialized"
        if hasattr(app.state, "cache_manager"):
            cache_status = "ok" if await app.state.cache_manager.ping() else "down"

        return JSONResponse(
            {
                "status": "healthy",
                "cache": cache_status,
                "rag_pipeline": (
                    "ok" if hasattr(app.state, "rag_pipeline") else "not_initialized"
                ),
            }
        )
    except Exception as e:
        logger.error(f"Ошибка health check: {e}")
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/metrics")
async def metrics() -> JSONResponse:
    """
    Эндпоинт для получения метрик системы.

    Returns:
        JSONResponse: Метрики использования
    """
    try:
        cache_manager = app.state.cache_manager
        metrics_data = await cache_manager.get_metrics()

        if hasattr(app.state, "rag_pipeline"):
            rag_metrics = app.state.rag_pipeline.get_metrics()
            metrics_data.update(rag_metrics)

        return JSONResponse(metrics_data)
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик исключений.

    Args:
        request: Объект запроса
        exc: Перехваченное исключение

    Returns:
        JSONResponse: Ответ с информацией об ошибке
    """
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Внутренняя ошибка сервера", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
