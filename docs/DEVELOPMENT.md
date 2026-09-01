# Руководство разработчика OGE Tutor GUI

## Содержание

1. [Требования](#требования)
2. [Установка](#установка)
3. [Настройка](#настройка)
4. [Запуск](#запуск)
5. [Разработка](#разработка)
6. [Тестирование](#тестирование)
7. [Структура проекта](#структура-проекта)
8. [Стиль кода](#стиль-кода)

## Требования

### Программное обеспечение

- **Python**: 3.11+
- **Git**: 2.30+

### Аппаратные требования

- **ОЗУ**: минимум 4 ГБ (рекомендуется 8 ГБ)
- **CPU**: 2 ядра
- **Место на диске**: 5 ГБ

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd OGE-9-Tutor-GUI-Assistant
```

### 2. Создание виртуального окружения

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Установка дополнительных компонентов

Для работы векторного поиска может потребоваться:

```bash
# Linux (Ubuntu)
sudo apt-get install build-essential

# macOS
xcode-select --install
```

## Настройка

### 1. Переменные окружения

Скопируйте файл `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

**Обязательные переменные:**

| Переменная | Описание | Пример |
|------------|----------|--------|
| `PROXY_API_KEY` | API-ключ для LLM (GPT-4o-mini через ProxyAPI) | `your_key_here` |
| `PROXY_API_URL` | URL ProxyAPI | `https://proxyapi.ru/openai` |
| `REDIS_HOST` | Хост Redis (опционально) | `localhost` |
| `REDIS_PORT` | Порт Redis (опционально) | `6379` |
| `LOG_LEVEL` | Уровень логирования (FastAPI backend) | `INFO` |

**Дополнительные переменные** (для реальной базы ФИПИ вместо пустого
локального индекса — см. `USE_EXISTING_INDEX` в `.env.example`):

| Переменная | Описание | Пример |
|------------|----------|--------|
| `USE_EXISTING_INDEX` | Включить `ExistingVectorStore` (157 чанков ФИПИ) вместо пустого локального индекса | `true` |
| `OPENAI_API_KEY` | Ключ для эмбеддингов `text-embedding-3-small` на пути `USE_EXISTING_INDEX=true` (falls back на `PROXY_API_KEY`, если не задан) | `sk-...` |
| `OPENAI_BASE_URL` | Базовый URL для запроса эмбеддингов | `https://api.proxyapi.ru/openai/v1` |

### 2. Настройка Redis (опционально)

Приложение работает без Redis, используя in-memory кэш. Для production рекомендуется Redis через Docker:

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

## Запуск

### GUI Приложение (рекомендуется)

```bash
# Пользовательский режим
python -m gui_debugger.main --mode user

# Административный режим (для разработчиков)
python -m gui_debugger.main --mode admin
```

### FastAPI Backend

```bash
# Запуск FastAPI сервера
python main.py

# Или через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Проверка работы

После запуска FastAPI откройте в браузере:
- http://localhost:8000 — главная страница
- http://localhost:8000/health — проверка здоровья
- http://localhost:8000/metrics — метрики

## Структура проекта

```
OGE-9-Tutor-GUI-Assistant/
├── README.md                     # Основной документ
├── CHANGELOG.md                  # История изменений
├── KODA.md                       # Инструкции для AI
├── requirements.txt              # Зависимости
├── main.py                       # FastAPI сервер
│
├── api/                          # RAG-пайплайн и API
│   ├── __init__.py
│   ├── rag_pipeline.py           # RAG-пайплайн
│   ├── vector_store.py           # Векторный поиск (Faiss)
│   ├── text_search.py            # Полнотекстовый поиск (Whoosh)
│   ├── llm_client.py             # LLM-клиент
│   └── test_generator.py         # Генератор тестов
│
├── gui_debugger/                 # GUI приложение
│   ├── __init__.py
│   ├── main.py                   # Точка входа
│   ├── app.py                    # Главное окно
│   ├── modes/                    # Режимы работы
│   │   ├── user_mode.py          # Пользовательский режим
│   │   └── admin_mode.py         # Административный режим
│   ├── components/               # Компоненты GUI
│   │   ├── user/                 # Пользовательские компоненты
│   │   │   ├── main_menu.py
│   │   │   ├── topic_study.py
│   │   │   ├── test_solver.py
│   │   │   └── progress.py
│   │   └── admin/                # Административные компоненты
│   ├── styles/                   # Тема оформления (ttkbootstrap)
│   └── utils/                    # Хелперы GUI (async, логирование)
│
├── utils/                        # Утилиты
│   ├── __init__.py
│   ├── logger.py                 # Логирование
│   └── cache.py                  # Кэширование
│
├── data/                         # Данные
│   ├── chunks/                   # Чанки знаний
│   ├── metadata/                 # Метаданные
│   ├── indices/                  # Индексы поиска
│   ├── backup/                   # Резервные копии
│   └── tests/                    # Тесты
│
├── logs/                         # Логи
├── docs/                         # Документация
├── tests/                        # Тесты
└── scripts/                      # Скрипты
```

## Стиль кода

Проект следует стандартам:
- **PEP 8** — Python
- **snake_case** — переменные и функции
- **PascalCase** — классы
- **Комментарии** — на русском языке
- **Docstrings** — формат Google

### Добавление новых тем

1. Создайте файл в `data/chunks/`:
   ```markdown
   # Название темы

   ## Подтема

   Содержание...
   ```

2. Запустите переиндексацию:
   ```bash
   python -c "from api.rag_pipeline import RAGPipeline; from utils.cache import CacheManager; import asyncio; asyncio.run(RAGPipeline(CacheManager())._reindex())"
   ```

### Добавление новых компонентов GUI

1. Создайте файл в `gui_debugger/components/user/` или `gui_debugger/components/admin/`
2. Наследуйтесь от `ttk.Frame`
3. Зарегистрируйте компонент в соответствующем режиме (`user_mode.py` или `admin_mode.py`)

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=. --cov-report=html

# Конкретный файл
pytest tests/test_rag_pipeline.py -v
```

### Структура тестов

```
tests/
├── __init__.py
└── test_rag_pipeline.py    # Тесты RAG-пайплайна
```

### Покрытие тестами

Минимальное требуемое покрытие: 80%

```bash
# Проверка покрытия
pytest --cov=. --cov-report=term-missing

# HTML-отчёт
pytest --cov=. --cov-report=html
```

## Устранение проблем

### Ошибка подключения к Redis

Приложение работает и без Redis (переключается на in-memory кэш), но
если нужен именно Redis:

```bash
# Проверка запущенных контейнеров
docker ps --filter "ancestor=redis:7-alpine"

# Перезапуск контейнера с Redis
docker restart <container_id>
```

### Ошибка загрузки модели

```bash
# Очистка кэша модели
rm -rf ~/.cache/huggingface
```

### Проблемы с GUI

```bash
# Проверка версии Python
python --version

# Перезапуск GUI
python -m gui_debugger.main --mode user

# Просмотр логов
cat logs/app.log
```

## Контакты

Для вопросов и предложений создавайте issue в репозитории.

---

*Обновлено: Апрель 2026*
