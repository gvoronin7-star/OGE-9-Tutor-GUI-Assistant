# -*- coding: utf-8 -*-
"""
Панель изучения тем.

Выбор темы из 6 разделов ФИПИ и получение объяснения от RAG.
"""

import asyncio
import functools
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Any, Callable, Dict, List, Optional, cast

from gui_debugger.utils.gui_logger import gui_action_logger, log_action, log_error


class TopicStudy(ttk.Frame):
    """Панель изучения тем."""

    # 6 тем ФИПИ
    TOPICS = [
        "Человек и общество",
        "Сфера духовной культуры",
        "Экономика",
        "Социальная сфера",
        "Политика",
        "Право",
    ]

    def __init__(
        self,
        parent: tk.Widget,
        rag_pipeline: Any = None,
        on_back: Optional[Callable] = None,
        on_topic_complete: Optional[Callable] = None,
    ) -> None:
        """
        Инициализация панели изучения тем.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн для запросов
            on_back: Callback для кнопки "Назад"
            on_topic_complete: Callback при завершении изучения темы
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.on_back = on_back
        self.on_topic_complete = on_topic_complete

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=10)

        back_btn = ttk.Button(
            header,
            text="🔙 Назад",
            command=cast(Callable[[], Any], self.on_back),
            width=15,
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        title = ttk.Label(
            header,
            text="📚 ИЗУЧЕНИЕ ТЕМ",
            font=("Segoe UI", 14, "bold"),
            foreground="#0078d4",
        )
        title.pack()

        # Выбор темы
        topics_frame = ttk.LabelFrame(self, text="Выберите тему", padding=10)
        topics_frame.pack(fill=tk.X, padx=20, pady=10)

        # Сетка кнопок тем (2x3)
        for i, topic in enumerate(self.TOPICS):
            row = i // 3
            col = i % 3

            btn = ttk.Button(
                topics_frame,
                text=topic,
                command=functools.partial(self._select_topic, topic),
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        topics_frame.columnconfigure(0, weight=1)
        topics_frame.columnconfigure(1, weight=1)
        topics_frame.columnconfigure(2, weight=1)

        # Область ответа
        answer_frame = ttk.LabelFrame(self, text="Объяснение", padding=10)
        answer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Индикатор прогресса (скрыт по умолчанию)
        self.progress_frame = ttk.Frame(answer_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, mode="indeterminate", length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(
            self.progress_frame, text="", font=("Segoe UI", 9), foreground="#0078d4"
        )
        self.progress_label.pack()

        self.answer_area = scrolledtext.ScrolledText(
            answer_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ffffff",
        )
        self.answer_area.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов
        self.answer_area.tag_configure(
            "title", font=("Segoe UI", 12, "bold"), foreground="#0078d4"
        )
        self.answer_area.tag_configure(
            "text", font=("Segoe UI", 10), foreground="#ffffff"
        )
        self.answer_area.tag_configure(
            "meta", font=("Segoe UI", 9), foreground="#808080"
        )

        # Обратная связь
        feedback_frame = ttk.Frame(self)
        feedback_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(feedback_frame, text="Оцените ответ:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=10
        )

        ttk.Button(
            feedback_frame,
            text="👍 Полезно",
            command=lambda: self._give_feedback("good"),
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            feedback_frame,
            text="👎 Неполезно",
            command=lambda: self._give_feedback("bad"),
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            feedback_frame, text="🔄 Переспросить", command=self._retry, width=15
        ).pack(side=tk.LEFT, padx=5)

        # Статус
        self.status_label = ttk.Label(self, text="", foreground="#808080")
        self.status_label.pack(pady=5)

        # Приветственное сообщение
        self._show_welcome()

    def _show_welcome(self) -> None:
        """Показ приветственного сообщения."""
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.insert(
            tk.END,
            "Выберите тему из списка выше, чтобы получить подробное объяснение.\n\n",
            "text",
        )
        self.answer_area.insert(tk.END, "Доступные темы:\n", "title")
        for i, topic in enumerate(self.TOPICS, 1):
            self.answer_area.insert(tk.END, f"{i}. {topic}\n", "text")

    def _select_topic(self, topic: str) -> None:
        """
        Выбор темы.

        Args:
            topic: Название темы
        """
        # Логирование выбора темы
        topic_id = self.TOPICS.index(topic) if topic in self.TOPICS else -1
        gui_action_logger.log_topic_selection(topic, topic_id)

        # Показ индикатора прогресса
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar.start(10)
        self.progress_label.configure(text="⏳ Запрос к LLM (gpt-4o-mini)...")

        self.status_label.configure(
            text=f"⏳ Запрос по теме: {topic}", foreground="#ffb900"
        )
        self.answer_area.delete(1.0, tk.END)
        self.answer_area.insert(
            tk.END, f"Загрузка материала по теме: {topic}...\n", "meta"
        )

        # Асинхронный запрос к RAG
        self._process_topic(topic)

    async def _async_query(self, query: str) -> dict:
        """Асинхронный запрос к RAG."""
        if self.rag_pipeline:
            return await self.rag_pipeline.get_answer(
                query, user_id=999999, use_cache=True
            )
        else:
            return {
                "answer": f"Материал по теме: {query}\n\nRAG-пайплайн не инициализирован. Демонстрационный режим.",
                "sources": [],
                "response_time": 0,
                "is_cached": False,
            }

    def _process_topic(self, topic: str) -> None:
        """Обработка запроса к теме."""
        try:
            from gui_debugger.utils.async_helper import async_helper

            result = async_helper.run_async(self._async_query(f"Объясни тему: {topic}"))

            # Скрытие индикатора прогресса
            self.progress_bar.stop()
            self.progress_frame.pack_forget()

            answer = result.get("answer", "Нет ответа")
            sources = result.get("sources", [])
            response_time = result.get("response_time", 0)
            is_cached = result.get("is_cached", False)

            # Логирование успешного ответа
            log_action(
                "topic_loaded",
                {
                    "topic": topic,
                    "response_time_ms": response_time * 1000,
                    "from_cache": is_cached,
                    "answer_length": len(answer),
                },
            )

            # Отображение ответа
            self.answer_area.delete(1.0, tk.END)
            self.answer_area.insert(tk.END, f"📚 {topic}\n\n", "title")
            self.answer_area.insert(tk.END, f"{answer}\n\n", "text")

            # Мета-информация с моделью
            model_info = "gpt-4o-mini" if not is_cached else "кэш"
            meta = f"⏱️ {response_time:.2f}с  |  🤖 Модель: {model_info}"
            if sources:
                meta += f"  |  📚 Источники: {', '.join(sources[:3])}"
            if is_cached:
                meta += "  |  💾 Из кэша"

            self.answer_area.insert(tk.END, meta, "meta")

            self.status_label.configure(
                text=f"✅ Тема изучена: {topic}", foreground="#107c10"
            )

            # Вызов callback при завершении темы
            if self.on_topic_complete:
                self.on_topic_complete(topic)

        except Exception as e:
            # Скрытие индикатора прогресса при ошибке
            self.progress_bar.stop()
            self.progress_frame.pack_forget()

            log_error("topic_load_failed", str(e))
            self.answer_area.delete(1.0, tk.END)
            self.answer_area.insert(tk.END, f"❌ Ошибка: {str(e)}\n", "text")
            self.status_label.configure(text="Ошибка загрузки", foreground="#e81123")

    def _give_feedback(self, feedback: str) -> None:
        """
        Обратная связь.

        Args:
            feedback: Тип обратной связи (good/bad)
        """
        if feedback == "good":
            self.status_label.configure(
                text="✅ Спасибо за оценку!", foreground="#107c10"
            )
        else:
            self.status_label.configure(
                text="⚠️ Попробуйте переформулировать вопрос", foreground="#ffb900"
            )

    def _retry(self) -> None:
        """Повторный запрос."""
        # Получение последней темы из статуса
        status = self.status_label.cget("text")
        if "Запрос по теме:" in status:
            topic = status.split(":")[1].strip()
            self._select_topic(topic)
