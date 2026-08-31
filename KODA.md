# KODA.md — Инструкции для AI-ассистентов

## Обзор проекта

**OGE Tutor GUI** — десктопное приложение для подготовки к ОГЭ по обществознанию с RAG-пайплайном.

---

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| GUI | Tkinter + ttkbootstrap |
| Backend | FastAPI 0.109.0 |
| Vector Search | Faiss 1.13.2 |
| Text Search | Whoosh 2.7.4 |
| LLM | GPT-4o-mini (via ProxyAPI) |
| Embeddings | OpenAI `text-embedding-3-small` (основная база ФИПИ) / sentence-transformers 2.3.1 (локальный fallback) |

---

## Команды запуска

```bash
# GUI (пользовательский режим)
python -m gui_debugger.main --mode user

# GUI (административный режим)
python -m gui_debugger.main --mode admin

# FastAPI
python main.py
```

---

## Основные компоненты

| Компонент | Файл | Описание |
|-----------|------|----------|
| GUI | `gui_debugger/main.py` | Точка входа |
| RAG | `api/rag_pipeline.py` | Поиск + генерация |
| Векторный поиск | `api/vector_store.py` | Faiss + HNSW |
| Полнотекстовый поиск | `api/text_search.py` | Whoosh |
| LLM | `api/llm_client.py` | GPT-4o-mini |
| Тесты | `api/test_generator.py` | Генератор вопросов |
| Кэш | `utils/cache.py` | Redis / In-memory |
