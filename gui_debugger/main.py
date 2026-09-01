# -*- coding: utf-8 -*-
"""
Точка входа для GUI отладчика v2.0.

Использование (из корневой папки проекта):
    python -m gui_debugger.main              # Выбор режима
    python -m gui_debugger.main --mode user  # Пользовательский режим
    python -m gui_debugger.main --mode admin # Административный режим
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Корневая папка проекта
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Загрузка .env
from dotenv import load_dotenv

env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)


def initialize_rag():
    """Инициализация RAG-пайплайна."""
    print("Initializing RAG pipeline...")

    from api.rag_pipeline import RAGPipeline
    from api.test_generator import TestGenerator
    from utils.cache import InMemoryCache

    # Используем синхронную инициализацию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def init():
        cache = InMemoryCache()
        await cache.initialize()

        rag = RAGPipeline(cache)
        await rag.initialize()

        test_gen = TestGenerator(rag)

        return rag, cache, test_gen

    try:
        rag, cache, test_gen = loop.run_until_complete(init())
        print("[OK] RAG initialized successfully")
        return rag, cache, test_gen
    except Exception as e:
        print(f"[WARNING] RAG init error: {e}")
        return None, None, None
    finally:
        # Не закрываем loop - он будет использоваться в GUI
        pass


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="OGE Tutor GUI Debugger v2.0")
    parser.add_argument("--mode", choices=["user", "admin"], help="Режим запуска")
    parser.add_argument("--no-rag", action="store_true", help="Запуск без RAG")
    parser.add_argument("--debug", action="store_true", help="Режим отладки")
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Уровень логирования",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("OGE TUTOR - GUI v2.0")
    print("=" * 60)
    print()

    # Инициализация расширенного логирования
    try:
        from utils.advanced_logger import log_manager, logger_gui, setup_logging

        setup_logging(level=args.log_level)
        logger_gui.info(f"GUI запущен в режиме: {args.mode or 'selector'}")
        print(
            f"[OK] Logging initialized (level={args.log_level}, dir={log_manager.log_dir})"
        )
    except Exception as e:
        print(f"[WARNING] Logging init error: {e}")

    # Инициализация компонентов
    rag_pipeline = None
    cache_manager = None
    test_generator = None

    if not args.no_rag:
        try:
            rag_pipeline, cache_manager, test_generator = initialize_rag()

            if rag_pipeline and rag_pipeline.use_existing:
                print(f"[OK] RAG_data_base active (197 FIPI chunks)")
            else:
                print("[WARNING] RAG_data_base not active - some features may not work")

        except Exception as e:
            print(f"[WARNING] RAG initialization error: {e}")
            print("  Running without RAG...")
    else:
        print("[INFO] Running without RAG pipeline")

    print()
    print("Starting GUI...")
    print()

    try:
        from gui_debugger.app import create_app

        app = create_app(
            rag_pipeline=rag_pipeline,
            cache_manager=cache_manager,
            test_generator=test_generator,
            forced_mode=args.mode,
        )
        app.run()

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print("GUI closed")


if __name__ == "__main__":
    main()
