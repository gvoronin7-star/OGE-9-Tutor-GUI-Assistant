# -*- coding: utf-8 -*-
"""
Темы и стили для GUI.

Использует ttkbootstrap для современных тем.
"""

from typing import Dict, Any

import ttkbootstrap as tb


class Theme:
    """Управление темами и стилями."""
    
    # Цветовые схемы
    COLORS = {
        "dark": {
            "bg": "#1e1e1e",          # Основной фон
            "fg": "#ffffff",          # Основной текст
            "accent": "#0078d4",      # Акцентный цвет
            "success": "#107c10",     # Успех
            "warning": "#ffb900",     # Предупреждение
            "error": "#e81123",       # Ошибка
            "chat_user": "#0078d4",   # Сообщения пользователя
            "chat_bot": "#2d2d2d",    # Сообщения бота
            "card_bg": "#2d2d30",     # Фон карточек (тёмный для контраста)
            "border": "#3e3e42",      # Границы
            "text_light": "#d0d0d0",  # Светлый текст (для читаемости)
            "text_dim": "#808080"     # Тусклый текст
        },
        "light": {
            "bg": "#ffffff",
            "fg": "#000000",
            "accent": "#0078d4",
            "success": "#107c10",
            "warning": "#ffb900",
            "error": "#e81123",
            "chat_user": "#0078d4",
            "chat_bot": "#f0f0f0",
            "card_bg": "#f5f5f5",
            "border": "#d0d0d0",
            "text_light": "#303030",
            "text_dim": "#808080"
        }
    }
    
    # Шрифты
    FONTS = {
        "heading": ("Segoe UI", 14, "bold"),
        "normal": ("Segoe UI", 10),
        "small": ("Segoe UI", 9),
        "code": ("Consolas", 9),
        "chat_user": ("Segoe UI", 10, "bold"),
        "chat_bot": ("Segoe UI", 10)
    }
    
    def __init__(self, mode: str = "dark") -> None:
        """
        Инициализация темы.

        Args:
            mode: "dark" или "light"
        """
        self.mode = mode
        self.colors = self.COLORS[mode]
        self.style: tb.Style | None = None

    def get_style_config(self) -> Dict[str, Any]:
        """
        Конфигурация для ttkbootstrap.

        Returns:
            Словарь конфигурации
        """
        return {
            "theme": "darkly" if self.mode == "dark" else "cosmo",
            "font": self.FONTS["normal"]
        }

    def apply_custom_styles(self, style: tb.Style) -> None:
        """
        Применение кастомных стилей поверх темы ttkbootstrap.

        Args:
            style: Объект Style ttkbootstrap (совместим с ttk.Style)
        """
        self.style = style

        # Бледные версии success/danger для подсветки вариантов ответа
        # (сами "success.TButton"/"danger.TButton" уже определены ttkbootstrap)
        style.configure(
            "PaleSuccess.TButton",
            background="#2d5a2d",
            foreground="#ffffff"
        )

        style.configure(
            "PaleDanger.TButton",
            background="#5a2d2d",
            foreground="#ffffff"
        )

        # Стили, используемые в коде, но не входящие в стандартный набор
        # ttkbootstrap — строим их поверх акцентного цвета темы (primary),
        # чтобы при переключении тёмная/светлая цвет брался из текущей темы
        style.configure(
            "Accent.TButton",
            font=self.FONTS["normal"],
            background=style.colors.primary,
            foreground=style.colors.get_foreground("primary")
        )
        style.map(
            "Accent.TButton",
            background=[("active", style.colors.active)]
        )
        style.configure(
            "Card.TFrame",
            background=style.colors.bg,
            relief="raised",
            borderwidth=1
        )

    def toggle_mode(self) -> str:
        """
        Переключение режима темы (тёмная/светлая) во время работы приложения.

        Требует, чтобы apply_custom_styles() уже был вызван — иначе
        меняется только self.mode/self.colors без визуального эффекта.

        Returns:
            Новый режим
        """
        self.mode = "light" if self.mode == "dark" else "dark"
        self.colors = self.COLORS[self.mode]
        if self.style is not None:
            self.style.theme_use(self.get_style_config()["theme"])
        return self.mode
