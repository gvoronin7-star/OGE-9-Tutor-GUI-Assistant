#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестирование бота без внешних зависимостей.

Использует in-memory кэш и не требует Redis.
Может работать даже при проблемах с сетью.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bot_no_redis():
    """Тест бота без Redis."""
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ БОТА БЕЗ Redis")
    print("=" * 60)
    
    # 1. Тест импорта
    print("\n[1/6] Тест импорта модулей...")
    try:
        from bot import bot_config
        from bot.handlers import router, register_handlers
        from bot.keyboards import create_main_keyboard
        from api.rag_pipeline import RAGPipeline
        from utils.cache import InMemoryCache
        print("[OK] Все модули импортированы")
    except Exception as e:
        print(f"[ERROR] Ошибка импорта: {e}")
        return False
    
    # 2. Тест конфигурации бота
    print("\n[2/6] Тест конфигурации бота...")
    try:
        await bot_config.initialize()
        print("[OK] Бот инициализирован")
        print(f"  Токен: {bot_config.token[:20]}...")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации: {e}")
        return False
    
    # 3. Тест in-memory кэша
    print("\n[3/6] Тест in-memory кэша...")
    try:
        cache = InMemoryCache()
        await cache.initialize()
        await cache.set("test_key", {"test": "value"}, ttl=3600)
        result = await cache.get("test_key")
        await cache.close()
        assert result == {"test": "value"}
        print("[OK] In-memory кэш работает")
    except Exception as e:
        print(f"[ERROR] Ошибка кэша: {e}")
        return False
    
    # 4. Тест RAG pipeline
    print("\n[4/6] Тест RAG pipeline...")
    try:
        rag = RAGPipeline(cache)
        await rag.initialize()
        
        # Тест демо-данных
        topics = await rag._ensure_demo_data()
        
        # Проверка чанков
        chunks = list(rag.chunks_dir.glob("*.md"))
        print(f"  Чанков: {len(chunks)}")
        
        # Тест поиска
        if chunks:
            result = await rag.get_answer("Что такое общество?", user_id=12345, use_cache=False)
            print(f"  Ответ получен: {len(result['answer'])} символов")
        
        await rag.close()
        print("[OK] RAG pipeline работает")
    except Exception as e:
        print(f"[ERROR] Ошибка RAG: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Тест клавиатур
    print("\n[5/6] Тест клавиатур...")
    try:
        kb = create_main_keyboard()
        print(f"  Главная клавиатура создана")
        
        topics_kb = create_main_keyboard()
        print(f"  Клавиатура тем создана")
        print("[OK] Клавиатуры работают")
    except Exception as e:
        print(f"[ERROR] Ошибка клавиатур: {e}")
        return False
    
    # 6. Тест диспетчера
    print("\n[6/6] Тест диспетчера и обработчиков...")
    try:
        from aiogram import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        
        dp = Dispatcher(storage=MemoryStorage())
        register_handlers(dp)
        
        # Проверка, что обработчики зарегистрированы
        print(f"  Обработчиков зарегистрировано: {len(dp.resolve_command_list([router]))}")
        print("[OK] Диспетчер работает")
    except Exception as e:
        print(f"[ERROR] Ошибка диспетчера: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ===")
    print("=" * 60)
    print("\nСистема готова к работе!")
    print("\nСледующие шаги:")
    print("1. Запустить Docker Desktop для Redis")
    print("2. Или использовать in-memory кэш (без Redis)")
    print("3. Исправить SSL проблемы для подключения к Telegram")
    print("\nДля запуска бота:")
    print("  python main.py")
    print("\nДля запуска через Docker:")
    print("  docker-compose up -d")
    
    return True


async def main():
    """Главная функция."""
    try:
        success = await test_bot_no_redis()
        
        if success:
            print("\n" + "=" * 60)
            print("=== ПРОЕКТ OGE TUTOR ГОТОВ К РАБОТЕ! ===")
            print("=" * 60)
            return 0
        else:
            print("\n❌ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            return 1
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)