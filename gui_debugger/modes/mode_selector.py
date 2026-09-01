# -*- coding: utf-8 -*-
"""
Экран выбора режима работы.

Позволяет пользователю выбрать между:
- 👤 Пользовательским режимом (подготовка к ОГЭ)
- ⚙️ Административным режимом (отладка и мониторинг)
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ModeSelector(ttk.Frame):
    """Экран выбора режима."""

    def __init__(
        self,
        parent: tk.Widget,
        on_user_mode: Optional[Callable] = None,
        on_admin_mode: Optional[Callable] = None,
    ) -> None:
        """
        Инициализация экрана выбора режима.

        Args:
            parent: Родительский виджет
            on_user_mode: Callback для пользовательского режима
            on_admin_mode: Callback для административного режима
        """
        super().__init__(parent)
        self.on_user_mode = on_user_mode
        self.on_admin_mode = on_admin_mode

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        title = ttk.Label(
            self,
            text="OGE TUTOR GUI v2.0",
            font=("Segoe UI", 18, "bold"),
            foreground="#0078d4",
        )
        title.pack(pady=(50, 10))

        subtitle = ttk.Label(
            self,
            text="Выберите режим работы",
            font=("Segoe UI", 12),
            foreground="#808080",
        )
        subtitle.pack(pady=(0, 40))

        # Карточка пользовательского режима
        user_card = self._create_mode_card(
            "👤 ПОЛЬЗОВАТЕЛЬСКИЙ РЕЖИМ",
            "Подготовка к ОГЭ\nИзучение тем • Тесты • Прогресс",
            "#0078d4",
            self._on_user_mode,
        )
        user_card.pack(pady=10, padx=50, fill=tk.X)

        # Карточка административного режима
        admin_card = self._create_mode_card(
            "⚙️ АДМИНИСТРАТИВНЫЙ РЕЖИМ",
            "Отладка и мониторинг\nRAG • Метрики • Логи • База знаний",
            "#107c10",
            self._on_admin_mode,
        )
        admin_card.pack(pady=10, padx=50, fill=tk.X)

        # Информация о версии
        version_label = ttk.Label(
            self,
            text="Версия 2.0 | 157 чанков ФИПИ | RAG-пайплайн активен",
            font=("Segoe UI", 9),
            foreground="#606060",
        )
        version_label.pack(side=tk.BOTTOM, pady=20)

    def _create_mode_card(
        self, title: str, description: str, color: str, command: Callable
    ) -> ttk.Frame:
        """
        Создание карточки режима.

        Args:
            title: Заголовок карточки
            description: Описание
            color: Цвет акцента
            command: Callback при клике

        Returns:
            ttk.Frame: Карточка режима
        """
        # Карточка с фоном
        card = ttk.Frame(self, padding=15)
        card.configure(cursor="hand2")
        card.configure(style="Card.TFrame")

        # Привязка клика на всю карточку
        card.bind("<Button-1>", lambda e: command())

        # Внутренний фрейм с цветным фоном (синий/зелёный)
        inner_frame = tk.Frame(card, bg=color)
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Заголовок
        title_label = tk.Label(
            inner_frame,
            text=title,
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg=color,
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))

        # Описание
        desc_label = tk.Label(
            inner_frame, text=description, font=("Segoe UI", 10), fg="#ffffff", bg=color
        )
        desc_label.pack(anchor=tk.W, pady=(0, 10))

        # Явная кнопка "Выбрать"
        select_btn = tk.Button(
            inner_frame,
            text="Выбрать →",
            command=command,
            width=15,
            bg="#ffffff",
            fg=color,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        select_btn.pack(anchor=tk.E, pady=(5, 0))

        return card

    def _on_user_mode(self) -> None:
        """Выбор пользовательского режима."""
        if self.on_user_mode:
            self.on_user_mode()

    def _on_admin_mode(self) -> None:
        """Выбор административного режима."""
        if self.on_admin_mode:
            self.on_admin_mode()
