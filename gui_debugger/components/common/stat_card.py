# -*- coding: utf-8 -*-
"""
Общая карточка статистики («заголовок» + крупное «значение»).

Раньше каждая панель (CacheManager, LLMMonitor, ProgressPanel и другие)
реализовывала свой собственный "_create_stat_card()" с одинаковой
разметкой, но с захардкоженным foreground="#303030" у значения — цвет
читаемый только на светлой теме, а тёмная тема у приложения включена
по умолчанию (`app.py`, `Theme(mode="dark")`). Здесь цвет берётся из
именованных стилей "CardTitle.TLabel"/"CardValue.TLabel"
(`styles/theme.py`), которые сами подстраиваются под активную тему
ttkbootstrap, а не зашиты в коде карточки.
"""

import tkinter as tk
from tkinter import ttk


class StatCard(ttk.Frame):
    """Карточка «заголовок + значение» с темозависимым цветом текста."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        value: str = "0",
        padding: int = 10,
    ) -> None:
        """
        Args:
            parent: Родительский виджет.
            title: Подпись карточки (например, "Ключей").
            value: Начальное значение (например, "0").
            padding: Внутренний отступ карточки.
        """
        super().__init__(parent, padding=padding, relief="raised", borderwidth=1)

        self._title_label = ttk.Label(self, text=title, style="CardTitle.TLabel")
        self._title_label.pack(anchor=tk.W)

        self._value_label = ttk.Label(self, text=value, style="CardValue.TLabel")
        self._value_label.pack(anchor=tk.W)

    def set_value(self, value: str) -> None:
        """Обновить отображаемое значение."""
        self._value_label.configure(text=value)

    def set_value_color(self, color: str) -> None:
        """
        Точечно переопределить цвет значения — например, чтобы показать
        статус (успех/ошибка) конкретным семантическим цветом вместо
        обычного текстового.
        """
        self._value_label.configure(foreground=color)

    @property
    def value_label(self) -> ttk.Label:
        """Прямой доступ к Label значения, если нужен сам виджет."""
        return self._value_label
