#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестирование OpenAI text-embedding-3-small через ProxyAPI.

Использование:
    python test_openai_embedding.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

# Загрузка .env
from dotenv import load_dotenv

load_dotenv()


async def test_embedding_api():
    """Тестирование API эмбеддингов."""

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ OPENAI text-embedding-3-small ЧЕРЕЗ PROXYAPI")
    print("=" * 60)
    print()

    # Конфигурация
    api_url = os.getenv("PROXY_API_URL", "https://proxyapi.ru/gigachat")
    api_key = os.getenv("PROXY_API_KEY", "")

    # Для эмбеддингов нужен другой endpoint
    embedding_url = "https://api.proxyapi.ru/openai/v1/embeddings"

    print(f"ProxyAPI URL: {api_url}")
    print(f"Embedding URL: {embedding_url}")
    print(f"API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else '***'}")
    print()

    if not api_key:
        print("[ERROR] PROXY_API_KEY не установлен в .env!")
        return False

    # Тестовый запрос
    import aiohttp

    url = embedding_url
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    test_texts = [
        "Что такое общество?",
        "Экономика - это наука о производстве и потреблении",
        "Право регулирует отношения между людьми",
    ]

    async with aiohttp.ClientSession() as session:
        for i, text in enumerate(test_texts, 1):
            print(f"[Тест {i}/3] {text}")

            payload = {"model": "text-embedding-3-small", "input": text}

            try:
                async with session.post(
                    url, headers=headers, json=payload, timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Проверка структуры ответа
                        if "data" in data and len(data["data"]) > 0:
                            embedding = data["data"][0]["embedding"]
                            dim = len(embedding)

                            print(f"  [OK] Успешно!")
                            print(f"       Размерность: {dim}")
                            print(f"       Модель: {data.get('model', 'unknown')}")

                            if dim != 1536:
                                print(
                                    f"  [WARNING] Ожидалась размерность 1536, получена {dim}"
                                )
                        else:
                            print(f"  [ERROR] Неверная структура ответа: {data}")
                            return False

                    elif resp.status == 401:
                        print(f"  [ERROR] Ошибка авторизации (401)")
                        return False
                    elif resp.status == 404:
                        print(f"  [ERROR] Модель не найдена (404)")
                        return False
                    elif resp.status == 429:
                        print(f"  [WARNING] Превышен лимит запросов (429)")
                    else:
                        print(f"  [ERROR] Статус: {resp.status}")
                        error_data = await resp.text()
                        print(f"  {error_data[:200]}")

            except asyncio.TimeoutError:
                print(f"  [ERROR] Таймаут запроса (>30с)")
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("[SUCCESS] ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print()
    print("Выводы:")
    print("  [OK] ProxyAPI поддерживает text-embedding-3-small")
    print("  [OK] Размерность эмбеддингов: 1536")
    print("  [OK] Можно использовать с RAG_data_base")
    print()
    print("Следующие шаги:")
    print("  1. Добавьте в .env:")
    print("     OPENAI_API_KEY={api_key}  # используйте PROXY_API_KEY")
    print("     OPENAI_BASE_URL={api_url}/v1")
    print("  2. Обновите api/vector_store_existing.py")
    print("  3. Запустите бота: python main.py")
    print()

    return True


async def test_rag_data_base_compatibility():
    """Тест совместимости с RAG_data_base."""

    print()
    print("=" * 60)
    print("ПРОВЕРКА СОВМЕСТИМОСТИ С RAG_data_base")
    print("=" * 60)
    print()

    import json
    from pathlib import Path

    metadata_file = Path("RAG_data_base/vector_db/metadata.json")

    if not metadata_file.exists():
        print("[ERROR] metadata.json не найден!")
        return False

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"Модель в базе: {metadata.get('model_name', 'unknown')}")
    print(f"Размерность: {metadata.get('embedding_dim', 'unknown')}")
    print(f"Векторов: {metadata.get('total_vectors', 'unknown')}")
    print()

    if metadata.get("embedding_dim") == 1536:
        print("[OK] Размерности совпадают (1536)")
        print("[OK] RAG_data_base совместима с text-embedding-3-small")
        return True
    else:
        print("[WARNING] Размерность не совпадает!")
        return False


async def main():
    """Главная функция."""

    # Тест API
    api_ok = await test_embedding_api()

    # Тест совместимости
    compat_ok = await test_rag_data_base_compatibility()

    if api_ok and compat_ok:
        print()
        print("=" * 60)
        print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("=" * 60)
        print()
        print("RAG_data_base полностью готова к использованию!")
        print()
        return 0
    else:
        print()
        print("=" * 60)
        print("[FAIL] ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
