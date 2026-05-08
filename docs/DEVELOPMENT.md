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
cd oge-tutor
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
| `PROXY_API_KEY` | API-ключ для LLM | `your_key_here` |
| `PROXY_API_URL` | URL ProxyAPI | `https://proxyapi.ru/gigachat` |
| `REDIS_HOST` | Хост Redis (опционально) | `localhost` |
| `REDIS_PORT` | Порт Redis (опционально) | `6379` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

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

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Проверка работы

После запуска FastAPI откройте в браузере:
- http://localhost:8000 — главная страница
- http://localhost:8000/health — проверка здоровья
- http://localhost:8000/metrics — метрики

## Структура проекта

```
oge-tutor/
├── README.md                     # Основной документ
├── CHANGELOG.md                  # История изменений
├── KODA.md                       # Инструкции для AI
├── requirements.txt              # Зависимости
├── main.py                       # FastAPI сервер
├── docker-compose.yml            # Оркестрация
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
│   └── components/               # Компоненты GUI
│       ├── user/                 # Пользовательские компоненты
│       │   ├── main_menu.py
│       │   ├── topic_study.py
│       │   ├── test_solver.py
│       │   └── progress.py
│       └── admin/                # Административные компоненты
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
├── test_bot/
│   ├── test_handlers.py
│   └── test_keyboards.py
├── test_api/
│   ├── test_rag_pipeline.py
│   ├── test_vector_store.py
│   └── test_text_search.py
└── test_utils/
    ├── test_cache.py
    └── test_logger.py
```

### Покрытие тестами

Минимальное требуемое покрытие: 80%

```bash
# Проверка покрытия
pytest --cov=. --cov-report=term-missing

# HTML-отчёт
pytest --cov=. --cov-report=html
```

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

```bash
# Проверка статуса Redis
docker-compose ps

# Перезапуск Redis
docker-compose restart redis
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
