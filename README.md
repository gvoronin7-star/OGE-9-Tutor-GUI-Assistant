# OGE Tutor GUI

📚 **Десктопное приложение для подготовки к ОГЭ по обществознанию** с RAG-пайплайном и интеллектуальной генерацией вопросов.

[![Python Tests](https://github.com/gvoronin7-star/oge-tutor/actions/workflows/python-test.yml/badge.svg)](https://github.com/gvoronin7-star/oge-tutor/actions/workflows/python-test.yml)
[![Lint](https://github.com/gvoronin7-star/oge-tutor/actions/workflows/lint.yml/badge.svg)](https://github.com/gvoronin7-star/oge-tutor/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Быстрый старт

### Запуск приложения

```bash
# Пользовательский режим
python -m gui_debugger.main --mode user

# Административный режим (для разработчиков)
python -m gui_debugger.main --mode admin
```

### Требования

- Python 3.11+
- 4 ГБ ОЗУ (рекомендуется 8 ГБ)
- 5 ГБ свободного места на диске

---

## 📖 Документация

| Документ | Описание |
|----------|----------|
| [📚 Руководство пользователя](docs/USER_GUIDE.md) | Как использовать приложение |
| 🔧 [Руководство разработчика](docs/DEVELOPMENT.md) | Установка и разработка |
| 🏗️ [Архитектура системы](docs/ARCHITECTURE.md) | Техническая архитектура |
| 📋 [История изменений](CHANGELOG.md) | Версии и обновления |

---

## ✨ Основные функции

### Для учащихся

- 📖 **Изучение тем** — подробные объяснения по 6 темам ОГЭ
- ✍️ **Решение тестов** — автоматическая генерация вопросов
- 📊 **Отслеживание прогресса** — статистика обучения
- 🎲 **Тест по всем темам** — комплексная подготовка

### Особенности

- **RAG-пайплайн** — поиск релевантной информации в базе знаний
- **Интеллектуальная генерация** — вопросы создаются LLM (GPT-4o-mini)
- **Система сложности** — вопросы easy/medium/hard
- **Мгновенная проверка** — ответы проверяются с пояснениями
- **Автопереход** — плавная навигация между вопросами

---

## 🛠️ Технологический стек

| Компонент | Технология |
|-----------|------------|
| GUI | Tkinter + ttkbootstrap |
| Backend | FastAPI 0.109.0 |
| Векторный поиск | Faiss 1.7.4 |
| Полнотекстовый поиск | Whoosh 2.7.4 |
| LLM | GPT-4o-mini (via ProxyAPI) |
| Embeddings | sentence-transformers 2.3.1 |
| Кэширование | Redis / In-memory |

---

## 📦 Установка

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd oge-tutor

# 2. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Редактировать .env и добавить PROXY_API_KEY

# 5. Запустить приложение
python -m gui_debugger.main --mode user
```

---

## 📚 Темы для изучения

1. Человек и общество
2. Экономика
3. Социальная сфера
4. Политика
5. Право
6. Сфера духовной культуры

---

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием кода
pytest --cov=. --cov-report=html
```

---

## 📝 Структура проекта

```
oge-tutor/
├── README.md                     # Этот файл
├── CHANGELOG.md                  # История изменений
├── KODA.md                       # Инструкции для AI-ассистентов
├── requirements.txt              # Зависимости Python
├── main.py                       # FastAPI сервер
├── docker-compose.yml            # Оркестрация сервисов
│
├── api/                          # RAG-пайплайн и API
│   ├── rag_pipeline.py           # Основной пайплайн
│   ├── vector_store.py           # Векторный поиск (Faiss)
│   ├── text_search.py            # Полнотекстовый поиск (Whoosh)
│   ├── llm_client.py             # LLM-клиент
│   └── test_generator.py         # Генератор тестов
│
├── gui_debugger/                 # GUI приложение
│   ├── main.py                   # Точка входа
│   ├── modes/                    # Режимы работы
│   └── components/               # Компоненты GUI
│
├── utils/                        # Утилиты
│   ├── logger.py                 # Логирование
│   └── cache.py                  # Кэширование
│
├── data/                         # Данные
│   ├── chunks/                   # Чанки знаний
│   ├── metadata/                 # Метаданные
│   └── indices/                  # Индексы поиска
│
├── docs/                         # Документация
└── tests/                        # Тесты
```

---

## 🤝 Вклад

В настоящее время проект находится в активной разработке. Если вы хотите внести вклад:

1. Создайте issue с описанием проблемы или предложения
2. Fork репозиторий
3. Создайте ветку для изменений
4. Отправьте Pull Request

---

## 📄 Лицензия

MIT License

---

**Версия:** 2.3  
**Последнее обновление:** Апрель 2026  
**Статус:** ✅ Готово к использованию
