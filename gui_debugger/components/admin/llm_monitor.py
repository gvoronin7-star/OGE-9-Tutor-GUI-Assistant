# -*- coding: utf-8 -*-
"""
Мониторинг LLM.

Статус GigaChat, лимиты, ошибки.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, Optional, cast


class LLMMonitor(ttk.Frame):
    """Монитор LLM."""

    def __init__(self, parent: tk.Widget, llm_client: Any = None) -> None:
        """
        Инициализация монитора LLM.

        Args:
            parent: Родительский виджет
            llm_client: LLM-клиент
        """
        super().__init__(parent)
        self.llm_client = llm_client

        self._create_widgets()
        self._refresh_status()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(
            self, text="🤖 МОНИТОРИНГ LLM", font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10)

        # Статус соединения
        status_frame = ttk.LabelFrame(self, text="Статус соединения", padding=15)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        self.status_indicator = ttk.Label(
            status_frame,
            text="● Неизвестно",
            font=("Segoe UI", 14, "bold"),
            foreground="#ffb900",
        )
        self.status_indicator.pack(anchor=tk.W)

        self.status_details = ttk.Label(
            status_frame,
            text="GigaChat-Max через ProxyAPI",
            font=("Segoe UI", 10),
            foreground="#808080",
        )
        self.status_details.pack(anchor=tk.W, pady=5)

        # Лимиты
        limits_frame = ttk.LabelFrame(self, text="Лимиты API", padding=15)
        limits_frame.pack(fill=tk.X, padx=20, pady=10)

        # Прогресс-бар лимита
        ttk.Label(limits_frame, text="Дневной лимит:").pack(anchor=tk.W)

        self.limit_progress = ttk.Progressbar(
            limits_frame, orient=tk.HORIZONTAL, length=400, mode="determinate"
        )
        self.limit_progress.pack(fill=tk.X, pady=5)

        self.limit_label = ttk.Label(
            limits_frame,
            text="0 / 1000 запросов (0%)",
            font=("Segoe UI", 10),
            foreground="#808080",
        )
        self.limit_label.pack(anchor=tk.W)

        # Статистика
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        # Карточки
        cards_frame = ttk.Frame(stats_frame)
        cards_frame.pack(fill=tk.X)

        self.requests_card = self._create_stat_card(
            cards_frame, "Запросов сегодня", "0", 0, 0
        )
        self.avg_time_card = self._create_stat_card(
            cards_frame, "Ср. время", "0с", 0, 1
        )
        self.errors_card = self._create_stat_card(cards_frame, "Ошибок", "0", 0, 2)
        self.success_card = self._create_stat_card(cards_frame, "Успешно", "100%", 0, 3)

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)

        # Логи ошибок
        errors_frame = ttk.LabelFrame(self, text="Последние ошибки", padding=10)
        errors_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.errors_text = tk.Text(
            errors_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            height=10,
        )
        self.errors_text.pack(fill=tk.BOTH, expand=True)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        refresh_btn = ttk.Button(
            btn_frame, text="🔄 Обновить", command=self._refresh_status
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        test_btn = ttk.Button(
            btn_frame, text="🧪 Тест соединения", command=self._test_connection
        )
        test_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(
            btn_frame, text="🗑️ Очистить логи", command=self._clear_logs
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)

    def _create_stat_card(
        self, parent: tk.Widget, title: str, value: str, row: int, col: int
    ) -> ttk.Frame:
        """Создание карточки статистики."""
        card = ttk.Frame(parent, padding=10)
        card.configure(relief="raised", borderwidth=1)

        title_label = ttk.Label(
            card, text=title, font=("Segoe UI", 9), foreground="#808080"
        )
        title_label.pack(anchor=tk.W)

        value_label = ttk.Label(
            card, text=value, font=("Segoe UI", 16, "bold"), foreground="#303030"
        )
        value_label.pack(anchor=tk.W)

        return card

    def _refresh_status(self) -> None:
        """Обновление статуса."""
        # Демо-данные (в реальной версии — запрос к API)
        self.status_indicator.configure(
            text="● GigaChat-Max (онлайн)", foreground="#107c10"
        )

        # Лимиты
        used = 342
        limit = 1000
        percentage = (used / limit) * 100

        self.limit_progress.configure(value=percentage)
        self.limit_label.configure(
            text=f"{used} / {limit} запросов ({percentage:.0f}%)"
        )

        # Статистика
        cast(ttk.Label, self.requests_card.winfo_children()[1]).configure(
            text=str(used)
        )
        cast(ttk.Label, self.avg_time_card.winfo_children()[1]).configure(text="1.23с")
        cast(ttk.Label, self.errors_card.winfo_children()[1]).configure(text="2")
        cast(ttk.Label, self.success_card.winfo_children()[1]).configure(text="99.4%")

        # Логи ошибок
        self.errors_text.delete(1.0, tk.END)
        errors = [
            {"time": "14:30:15", "error": "Timeout: превышено время ожидания (30с)"},
            {"time": "12:15:42", "error": "RateLimit: превышен лимит запросов"},
        ]

        for err in errors:
            self.errors_text.insert(tk.END, f"[{err['time']}] {err['error']}\n")

        self.errors_text.configure(state=tk.DISABLED)

    def _test_connection(self) -> None:
        """Тест соединения."""
        self.status_indicator.configure(text="⏳ Тестирование...", foreground="#ffb900")

        # В реальной версии — тестовый запрос к LLM
        self.after(
            2000,
            lambda: self.status_indicator.configure(
                text="● GigaChat-Max (онлайн)", foreground="#107c10"
            ),
        )

        messagebox.showinfo("Тест", "Соединение с GigaChat установлено успешно!")

    def _clear_logs(self) -> None:
        """Очистка логов ошибок."""
        self.errors_text.configure(state=tk.NORMAL)
        self.errors_text.delete(1.0, tk.END)
        self.errors_text.configure(state=tk.DISABLED)
