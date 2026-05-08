# -*- coding: utf-8 -*-
"""
Главное меню пользовательского режима.

4 основные кнопки согласно USER_GUIDE.md:
- 📚 Изучить тему
- ✍️ Решить тест
- 📊 Прогресс
- ❓ Помощь
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any


class MainMenu(ttk.Frame):
    """Главное меню пользователя."""
    
    def __init__(
        self,
        parent: tk.Widget,
        callbacks: Optional[Dict[str, Callable]] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Инициализация главного меню.
        
        Args:
            parent: Родительский виджет
            callbacks: Callbacks для кнопок
            user_data: Данные пользователя (имя, прогресс)
        """
        super().__init__(parent)
        self.callbacks = callbacks or {}
        self.user_data = user_data or {"name": "Ученик", "progress": {}}
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок с приветствием
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=20)
        
        greeting = ttk.Label(
            header_frame,
            text=f"👋 Привет, {self.user_data.get('name', 'Ученик')}!",
            font=("Segoe UI", 16, "bold"),
            foreground="#0078d4"
        )
        greeting.pack(side=tk.LEFT)
        
        # Кнопки меню
        menu_frame = ttk.Frame(self)
        menu_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # 📚 Изучить тему
        self._create_menu_button(
            menu_frame,
            "📚 ИЗУЧИТЬ ТЕМУ",
            "Выберите тему из списка и получите объяснение",
            self.callbacks.get("study_topic"),
            row=0
        )
        
        # ✍️ Решить тест
        self._create_menu_button(
            menu_frame,
            "✍️ РЕШИТЬ ТЕСТ",
            "Пройдите тест по теме с выбором сложности",
            self.callbacks.get("solve_test"),
            row=1
        )
        
        # 📊 Прогресс
        self._create_menu_button(
            menu_frame,
            "📊 ПРОГРЕСС",
            "Посмотрите статистику подготовки",
            self.callbacks.get("show_progress"),
            row=2
        )
        
        # ❓ Помощь
        self._create_menu_button(
            menu_frame,
            "❓ ПОМОЩЬ",
            "Справка и советы по подготовке",
            self.callbacks.get("show_help"),
            row=3
        )
        
        # Быстрая статистика
        stats_frame = ttk.LabelFrame(self, text="Быстрая статистика", padding=10)
        stats_frame.pack(fill=tk.X, padx=40, pady=10)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text=self._get_stats_text(),
            font=("Segoe UI", 10),
            foreground="#303030"
        )
        self.stats_label.pack()
    
    def _create_menu_button(
        self,
        parent: tk.Widget,
        title: str,
        description: str,
        command: Optional[Callable],
        row: int
    ) -> None:
        """
        Создание кнопки меню.
        
        Args:
            parent: Родительский виджет
            title: Заголовок кнопки
            description: Описание
            command: Callback
            row: Строка в сетке
        """
        button = ttk.Button(
            parent,
            text=title,
            command=command,
            style="Accent.TButton"
        )
        button.grid(row=row, column=0, sticky="ew", pady=5, padx=5)
        
        desc_label = ttk.Label(
            parent,
            text=description,
            font=("Segoe UI", 9),
            foreground="#808080"
        )
        desc_label.grid(row=row, column=1, padx=10, pady=5)
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=3)
    
    def _get_stats_text(self) -> str:
        """Получение текста статистики."""
        progress = self.user_data.get("progress", {})
        
        topics = progress.get("topics_studied", 0)
        tests = progress.get("tests_completed", 0)
        accuracy = progress.get("accuracy", 0)
        
        return f"📚 Тем изучено: {topics}  |  ✍️ Тестов пройдено: {tests}  |  ✅ Точность: {accuracy}%"
    
    def update_stats(self, progress: Dict[str, Any]) -> None:
        """
        Обновление статистики.
        
        Args:
            progress: Данные прогресса
        """
        self.user_data["progress"] = progress
        self.stats_label.configure(text=self._get_stats_text())
