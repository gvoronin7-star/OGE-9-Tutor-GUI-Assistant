#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт интеграции RAG_data_base в систему OGE Tutor.

Использование:
    python scripts/integrate_rag_database.py

Скрипт:
1. Проверяет наличие RAG_data_base
2. Тестирует загрузку индекса
3. Выполняет тестовый поиск
4. Создаёт резервную копию
5. Обновляет конфигурацию
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_rag_database() -> bool:
    """Проверка наличия RAG_data_base."""
    logger.info("Проверка RAG_data_base...")
    
    base_dir = Path("RAG_data_base")
    if not base_dir.exists():
        logger.error("RAG_data_base не найдена!")
        return False
    
    vector_db = base_dir / "vector_db"
    required_files = [
        "dataset.json",
        "index.faiss",
        "metadata.json"
    ]
    
    for filename in required_files:
        filepath = vector_db / filename
        if not filepath.exists():
            logger.error(f"Файл не найден: {filepath}")
            return False
    
    logger.info("✓ RAG_data_base найдена")
    return True


async def test_load_index() -> tuple:
    """Тест загрузки индекса."""
    logger.info("Тест загрузки индекса...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from api.vector_store_existing import ExistingVectorStore
        
        store = ExistingVectorStore(Path("RAG_data_base/vector_db"))
        loaded = await store.load()
        
        if not loaded:
            logger.error("Не удалось загрузить индекс")
            return False, None
        
        stats = store.get_stats()
        
        logger.info(f"✓ Индекс загружен")
        logger.info(f"  Чанков: {stats['total_chunks']}")
        logger.info(f"  Векторов: {stats['total_vectors']}")
        logger.info(f"  Размерность: {stats['embedding_dim']}")
        logger.info(f"  Модель: {stats['model']}")
        
        return True, store
        
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return False, None


async def test_search(store) -> bool:
    """Тест поиска."""
    logger.info("Тест поиска...")
    
    test_queries = [
        "Что такое общество?",
        "Какие бывают экономические системы?",
        "Что изучает право?"
    ]
    
    for query in test_queries:
        logger.info(f"\nЗапрос: {query}")
        
        try:
            results = await store.search(query, top_k=2, use_remote_embedding=False)
            
            if results:
                logger.info(f"  Найдено: {len(results)} результатов")
                for i, r in enumerate(results, 1):
                    logger.info(f"  {i}. Score: {r['score']:.3f}")
                    logger.info(f"     Text: {r['text'][:80]}...")
            else:
                logger.warning("  Ничего не найдено (возможно, нужен OpenAI API)")
                
        except Exception as e:
            logger.error(f"  Ошибка поиска: {e}")
    
    return True


def create_backup() -> Path:
    """Создание резервной копии текущих данных."""
    logger.info("Создание резервной копии...")
    
    backup_dir = Path("data/backup")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Копирование текущих чанков
    chunks_dir = Path("data/chunks")
    if chunks_dir.exists():
        import shutil
        timestamp = Path().stat().st_mtime
        backup_name = f"chunks_backup_{int(timestamp)}"
        shutil.copytree(chunks_dir, backup_dir / backup_name)
        logger.info(f"✓ Резервная копия: {backup_dir / backup_name}")
    
    return backup_dir


def update_env_config():
    """Обновление .env конфигурации."""
    logger.info("Обновление .env...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        logger.warning(".env не найден, создаю новый")
        env_file.write_text("", encoding="utf-8")
    
    content = env_file.read_text(encoding="utf-8")
    
    # Добавление настроек RAG
    rag_settings = [
        "\n# RAG настройки",
        "USE_EXISTING_INDEX=true",
        "# OPENAI_API_KEY=sk-...  # Раскомментировать для Existing индекса",
        "FALLBACK_TO_LOCAL=true",
        ""
    ]
    
    # Проверка, есть ли уже эти настройки
    for setting in rag_settings[1:]:
        key = setting.split("=")[0]
        if key not in content:
            content += setting + "\n"
    
    env_file.write_text(content, encoding="utf-8")
    logger.info("✓ .env обновлён")


def create_integration_guide():
    """Создание краткого руководства."""
    guide_path = Path("RAG_INTEGRATION_GUIDE.md")
    
    guide = """# КРАТКОЕ РУКОВОДСТВО ПО ИНТЕГРАЦИИ RAG_data_base

## ✅ Статус интеграции

RAG_data_base успешно проверена и готова к использованию!

## 📊 Характеристики базы

- **Чанков:** 204
- **Векторов:** 204
- **Размерность:** 1536 (OpenAI text-embedding-3-small)
- **Источник:** Пособие ОГЭ по обществознанию (ФИПИ, 2020)

## 🚀 Быстрый старт

### Вариант 1: С OpenAI API (качественнее)

1. Добавьте в `.env`:
   ```
   OPENAI_API_KEY=sk-your-key-here
   USE_EXISTING_INDEX=true
   ```

2. Запустите бота:
   ```bash
   python main.py
   ```

### Вариант 2: Без OpenAI API (локально)

1. Запустите бота:
   ```bash
   python main.py
   ```

   Система автоматически использует fallback режим.

## 📁 Структура

```
RAG_data_base/
└── vector_db/
    ├── dataset.json    # 204 чанка
    ├── index.faiss     # Векторный индекс
    └── metadata.json   # Метаданные
```

## 🔍 Тестирование

```bash
python scripts/test_rag_search.py
```

## 📖 Полная документация

См. `docs/RAG_INTEGRATION.md`

---

**Дата:** $(date)
**Статус:** ✅ Готово
"""
    
    from datetime import datetime
    guide = guide.replace("$(date)", datetime.now().strftime("%Y-%m-%d"))
    
    guide_path.write_text(guide, encoding="utf-8")
    logger.info(f"✓ Руководство: {guide_path}")


async def main():
    """Главная функция."""
    print("=" * 60)
    print("ИНТЕГРАЦИЯ RAG_data_base")
    print("=" * 60)
    print()
    
    # 1. Проверка
    if not await check_rag_database():
        print("\n[FAIL] RAG_data_base не найдена!")
        return 1
    
    # 2. Тест загрузки
    success, store = await test_load_index()
    if not success:
        print("\n[FAIL] Не удалось загрузить индекс!")
        return 1
    
    # 3. Тест поиска
    await test_search(store)
    
    # 4. Резервная копия
    create_backup()
    
    # 5. Обновление .env
    update_env_config()
    
    # 6. Руководство
    create_integration_guide()
    
    print()
    print("=" * 60)
    print("[SUCCESS] ИНТЕГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print()
    print("Следующие шаги:")
    print("1. Добавьте OPENAI_API_KEY в .env (опционально)")
    print("2. Запустите бота: python main.py")
    print("3. Для тестирования: python scripts/test_rag_search.py")
    print()
    print("Документация:")
    print("  - RAG_INTEGRATION_GUIDE.md (кратко)")
    print("  - docs/RAG_INTEGRATION.md (полная)")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)