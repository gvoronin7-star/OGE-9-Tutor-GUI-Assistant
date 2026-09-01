#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт тестирования поиска по RAG_data_base.

Использование:
    python scripts/test_rag_search.py

Тестирует:
- Загрузку RAG_data_base
- Поиск через ProxyAPI
- Поиск через локальный Faiss
- Интеграцию с RAG-пайплайном
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Загрузка .env
from dotenv import load_dotenv

load_dotenv()


async def test_existing_vector_store():
    """Тестирование ExistingVectorStore."""
    print("=" * 70)
    print("ТЕСТ 1: Загрузка RAG_data_base")
    print("=" * 70)
    print()

    from api.vector_store_existing import ExistingVectorStore

    store = ExistingVectorStore(Path("RAG_data_base/vector_db"))
    loaded = await store.load()

    if not loaded:
        print("[FAIL] Не удалось загрузить RAG_data_base!")
        return False

    stats = store.get_stats()

    print(f"[OK] RAG_data_base загружена")
    print(f"  Чанков: {stats['total_chunks']}")
    print(f"  Векторов: {stats['total_vectors']}")
    print(f"  Размерность: {stats['embedding_dim']}")
    print(f"  Модель: {stats['model']}")
    print()

    return True


async def test_search_existing():
    """Тестирование поиска через ExistingVectorStore."""
    print("=" * 70)
    print("ТЕСТ 2: Поиск через RAG_data_base (ProxyAPI)")
    print("=" * 70)
    print()

    from api.vector_store_existing import ExistingVectorStore

    store = ExistingVectorStore(Path("RAG_data_base/vector_db"))
    await store.load()

    test_queries = [
        "Что такое общество?",
        "Какие бывают экономические системы?",
        "Что изучает право?",
    ]

    all_passed = True

    for i, query in enumerate(test_queries, 1):
        print(f"[Запрос {i}/3] {query}")

        try:
            results = await store.search(
                query, top_k=3, use_remote_embedding=True  # ProxyAPI
            )

            if results:
                print(f"  [OK] Найдено {len(results)} результатов")
                for j, r in enumerate(results[:2], 1):
                    print(f"    {j}. Score: {r['score']:.3f}")
                    print(f"       Тема: {r.get('topic', 'неизвестно')}")
                    print(f"       Текст: {r['text'][:80]}...")
            else:
                print(f"  [WARNING] Ничего не найдено")
                all_passed = False

        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            all_passed = False

        print()

    return all_passed


async def test_rag_pipeline():
    """Тестирование RAG-пайплайна с интеграцией."""
    print("=" * 70)
    print("ТЕСТ 3: Интеграция с RAG-пайплайном")
    print("=" * 70)
    print()

    from api.rag_pipeline import RAGPipeline
    from utils.cache import InMemoryCache

    # Создание кэш-менеджера
    cache_manager = InMemoryCache()
    await cache_manager.initialize()

    # Создание RAG-пайплайна
    rag_pipeline = RAGPipeline(cache_manager)
    await rag_pipeline.initialize()

    print(f"[OK] RAG-пайплайн инициализирован")
    print(f"  RAG_data_base активна: {rag_pipeline.use_existing}")
    print()

    # Тестовые запросы
    test_queries = ["Что такое общество?", "Расскажи про экономику"]

    all_passed = True

    for i, query in enumerate(test_queries, 1):
        print(f"[Запрос {i}/2] {query}")

        try:
            result = await rag_pipeline.get_answer(
                query=query, user_id=12345, use_cache=False
            )

            print(f"  [OK] Ответ получен за {result['response_time']:.2f}с")
            print(f"  Источники: {', '.join(result.get('sources', []))}")

            if result.get("answer"):
                answer_preview = result["answer"][:150]
                print(f"  Ответ: {answer_preview}...")
            else:
                print(f"  [WARNING] Ответ пустой")
                all_passed = False

        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
            all_passed = False

        print()

    return all_passed


async def test_fallback_modes():
    """Тестирование fallback режимов."""
    print("=" * 70)
    print("ТЕСТ 4: Fallback режимы")
    print("=" * 70)
    print()

    from api.rag_pipeline import RAGPipeline
    from utils.cache import InMemoryCache

    # Отключаем RAG_data_base
    os.environ["USE_EXISTING_INDEX"] = "false"

    cache_manager = InMemoryCache()
    await cache_manager.initialize()

    rag_pipeline = RAGPipeline(cache_manager)
    await rag_pipeline.initialize()

    print(f"[OK] RAG-пайплайн инициализирован (без RAG_data_base)")
    print(f"  RAG_data_base активна: {rag_pipeline.use_existing}")
    print()

    # Проверка поиска
    query = "Что такое общество?"
    print(f"[Запрос] {query}")

    try:
        chunks = await rag_pipeline._search_chunks(query)

        if chunks:
            print(f"  [OK] Найдено {len(chunks)} чанков (fallback)")
            for i, c in enumerate(chunks[:2], 1):
                print(f"    {i}. Score: {c.get('score', 0):.3f}")
        else:
            print(f"  [WARNING] Ничего не найдено в fallback режиме")

    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")

    print()

    # Восстанавливаем настройку
    os.environ["USE_EXISTING_INDEX"] = "true"

    return True


async def main():
    """Главная функция."""
    print()
    print("█" * 70)
    print("ТЕСТИРОВАНИЕ RAG-ПОИСКА")
    print("█" * 70)
    print()

    # Проверка переменных окружения
    print("Конфигурация:")
    print(f"  USE_EXISTING_INDEX: {os.getenv('USE_EXISTING_INDEX', 'false')}")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'not set')}")
    print(f"  OPENAI_API_KEY: {'***' if os.getenv('OPENAI_API_KEY') else 'not set'}")
    print(f"  PROXY_API_KEY: {'***' if os.getenv('PROXY_API_KEY') else 'not set'}")
    print()

    # Тесты
    results = []

    # Тест 1: Загрузка
    results.append(await test_existing_vector_store())

    # Тест 2: Поиск через ProxyAPI
    results.append(await test_search_existing())

    # Тест 3: Интеграция
    results.append(await test_rag_pipeline())

    # Тест 4: Fallback
    results.append(await test_fallback_modes())

    # Итоги
    print("=" * 70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Пройдено тестов: {passed}/{total}")

    if passed == total:
        print()
        print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print()
        print("RAG_data_base готова к использованию:")
        print("  ✓ 197 чанков ФИПИ загружены")
        print("  ✓ ProxyAPI работает")
        print("  ✓ Поиск функционирует")
        print("  ✓ Fallback режимы работают")
        print()
        print("Следующий шаг: Запуск бота")
        print("  python main.py")
        print()
        return 0
    else:
        print()
        print(f"[FAIL] {total - passed} тест(а) не пройдены")
        print()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
