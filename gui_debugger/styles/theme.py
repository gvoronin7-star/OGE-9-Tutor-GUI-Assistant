# -*- coding: utf-8 -*-
"""
Темы и стили для GUI.

Использует ttkbootstrap для современных тем.
"""

import tkinter as tk
from typing import Dict, Any


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
    
    def configure_window(self, window: tk.Tk) -> None:
        """
        Настройка окна с темой.
        
        Args:
            window: Окно Tkinter
        """
        window.configure(bg=self.colors["bg"])
    
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
    
    def apply_custom_styles(self, style: Any) -> None:
        """
        Применение кастомных стилей.
        
        Args:
            style: Объект стиля ttk
        """
        # Стили для кнопок ответов
        style.configure(
            "success.TButton",
            background=self.colors["success"],
            foreground="#ffffff"
        )
        
        style.configure(
            "danger.TButton",
            background=self.colors["error"],
            foreground="#ffffff"
        )
        
        # Бледные версии для подсветки
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
    
    def toggle_mode(self) -> str:
        """
        Переключение режима темы.
        
        Returns:
            Новый режим
        """
        self.mode = "light" if self.mode == "dark" else "dark"
        self.colors = self.COLORS[self.mode]
        return self.mode
