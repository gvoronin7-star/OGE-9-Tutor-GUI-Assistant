# -*- coding: utf-8 -*-
"""
Панель чата для отладки бота.

Имитирует общение с ботом без Telegram API.
"""

import asyncio
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk
from typing import Any, Optional


class ChatPanel(ttk.Frame):
    """Панель чата."""

    def __init__(self, parent: tk.Widget, rag_pipeline: Any) -> None:
        """
        Инициализация панели чата.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн для запросов
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.chat_history = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="📱 CHAT", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Область чата
        self.chat_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Настройка тегов для форматирования
        self.chat_area.tag_configure(
            "user", foreground="#0078d4", font=("Segoe UI", 10, "bold")
        )
        self.chat_area.tag_configure("bot", foreground="#ffffff", font=("Segoe UI", 10))
        self.chat_area.tag_configure("meta", foreground="#808080", font=("Segoe UI", 9))
        self.chat_area.tag_configure(
            "timestamp", foreground="#606060", font=("Segoe UI", 8)
        )

        # Приветственное сообщение
        self._add_bot_message(
            "👋 Привет! Я — репетитор по обществознанию для подготовки к ОГЭ.\n\n"
            "Задай мне любой вопрос по темам:\n"
            "• Человек и общество\n"
            "• Экономика\n"
            "• Право\n"
            "• Политика\n"
            "• Социальная сфера\n"
            "• Духовная культура",
            show_timestamp=False,
        )

        # Панель ввода
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.input_field = ttk.Entry(input_frame, font=("Segoe UI", 10))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self._send_message())

        send_btn = ttk.Button(input_frame, text="Отправить", command=self._send_message)
        send_btn.pack(side=tk.RIGHT)

        # Панель быстрых команд
        commands_frame = ttk.Frame(self)
        commands_frame.pack(fill=tk.X, padx=10, pady=5)

        quick_commands = [
            "/start",
            "/help",
            "/progress",
            "Что такое общество?",
            "Расскажи про экономику",
        ]

        for cmd in quick_commands:
            btn = ttk.Button(
                commands_frame,
                text=cmd,
                command=lambda c=cmd: self._quick_command(c),
                width=15,
            )
            btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Статус
        self.status_label = ttk.Label(
            self, text="● Готов к работе", foreground="#107c10"
        )
        self.status_label.pack(pady=5)

    def _add_user_message(self, text: str) -> None:
        """Добавление сообщения пользователя."""
        timestamp = datetime.now().strftime("%H:%M")

        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\n[{timestamp}] Вы: ", "timestamp")
        self.chat_area.insert(tk.END, f"{text}\n", "user")
        self.chat_area.configure(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _add_bot_message(self, text: str, show_timestamp: bool = True) -> None:
        """Добавление сообщения бота."""
        timestamp = datetime.now().strftime("%H:%M")

        self.chat_area.configure(state=tk.NORMAL)
        if show_timestamp:
            self.chat_area.insert(tk.END, f"\n[{timestamp}] Бот: ", "timestamp")
        self.chat_area.insert(tk.END, f"{text}\n", "bot")
        self.chat_area.configure(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _add_meta_message(self, text: str) -> None:
        """Добавление мета-информации."""
        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"  {text}\n", "meta")
        self.chat_area.configure(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _send_message(self) -> None:
        """Отправка сообщения."""
        query = self.input_field.get().strip()

        if not query:
            return

        # Добавление сообщения пользователя
        self._add_user_message(query)

        # Очистка поля ввода
        self.input_field.delete(0, tk.END)

        # Обновление статуса
        self.status_label.configure(text="● Думаю...", foreground="#ffb900")

        # Асинхронный запрос к RAG
        self._process_query(query)

    def _quick_command(self, command: str) -> None:
        """Быстрая команда."""
        self.input_field.delete(0, tk.END)
        self.input_field.insert(0, command)
        self._send_message()

    async def _async_query(self, query: str) -> dict:
        """Асинхронный запрос к RAG-пайплайну."""
        if self.rag_pipeline:
            return await self.rag_pipeline.get_answer(
                query, user_id=999999, use_cache=True
            )
        else:
            return {
                "answer": "RAG-пайплайн не инициализирован",
                "sources": [],
                "response_time": 0,
                "is_cached": False,
            }

    def _process_query(self, query: str) -> None:
        """Обработка запроса."""
        try:
            # Запуск асинхронного запроса
            from gui_debugger.utils.async_helper import async_helper

            result = async_helper.run_async(self._async_query(query))

            # Отображение ответа
            answer = result.get("answer", "Нет ответа")
            sources = result.get("sources", [])
            response_time = result.get("response_time", 0)
            is_cached = result.get("is_cached", False)

            self._add_bot_message(answer)

            # Мета-информация
            meta = f"⏱️ {response_time:.2f}с"
            if sources:
                meta += f"  |  📚 Источники: {', '.join(sources[:3])}"
            if is_cached:
                meta += "  |  💾 Из кэша"

            self._add_meta_message(meta)

            # Обновление статуса
            self.status_label.configure(text="● Готов к работе", foreground="#107c10")

        except Exception as e:
            self._add_bot_message(f"❌ Ошибка: {str(e)}")
            self.status_label.configure(text="● Ошибка", foreground="#e81123")

    def clear_chat(self) -> None:
        """Очистка чата."""
        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.configure(state=tk.DISABLED)
        self._add_bot_message("Чат очищен", show_timestamp=False)
