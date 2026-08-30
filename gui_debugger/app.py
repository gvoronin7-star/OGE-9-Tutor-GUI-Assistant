# -*- coding: utf-8 -*-
"""
Главное приложение GUI отладчика v2.0.

Двухрежимное приложение:
- Пользовательский режим (подготовка к ОГЭ)
- Административный режим (отладка и мониторинг)
"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import ttkbootstrap as tb

# Добавляем путь к проекту (родительская директория)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui_debugger.modes.admin_mode import AdminMode
from gui_debugger.modes.mode_selector import ModeSelector
from gui_debugger.modes.user_mode import UserMode

# Импорт после добавления пути
from gui_debugger.styles.theme import Theme


class OGEDebuggerApp:
    """Главное приложение отладчика v2.0."""

    def __init__(
        self,
        rag_pipeline=None,
        cache_manager=None,
        test_generator=None,
        forced_mode=None,
    ) -> None:
        """
        Инициализация приложения.

        Args:
            rag_pipeline: RAG-пайплайн (опционально)
            cache_manager: Менеджер кэша (опционально)
            test_generator: Генератор тестов (опционально)
            forced_mode: Принудительный режим ("user" или "admin")
        """
        self.rag_pipeline = rag_pipeline
        self.cache_manager = cache_manager
        self.test_generator = test_generator
        self.forced_mode = forced_mode
        self.theme = Theme(mode="dark")

        self._create_window()

        # Показ экрана выбора режима или сразу режима
        if forced_mode:
            self._show_mode(forced_mode)
        else:
            self._show_mode_selector()

    def _create_window(self) -> None:
        """Создание главного окна."""
        self.root = tb.Window(themename=self.theme.get_style_config()["theme"])
        self.root.title("OGE TUTOR — GUI v2.0")
        self.root.geometry("1400x900")

        # Конфигурация сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Статус бар
        self.status_bar = ttk.Label(
            self.root,
            text="GUI запущен | RAG_data_base: "
            + (
                "активна"
                if self.rag_pipeline and self.rag_pipeline.use_existing
                else "неактивна"
            ),
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=2)

        # Применение кастомных стилей поверх темы ttkbootstrap
        self.theme.apply_custom_styles(self.root.style)

    def _show_mode_selector(self) -> None:
        """Показ экрана выбора режима."""
        self.mode_selector = ModeSelector(
            self.root,
            on_user_mode=lambda: self._show_mode("user"),
            on_admin_mode=lambda: self._show_mode("admin"),
        )
        self.mode_selector.grid(row=0, column=0, sticky="nsew")

    def _show_mode(self, mode: str) -> None:
        """
        Показ режима.

        Args:
            mode: "user" или "admin"
        """
        # Очистка
        if hasattr(self, "mode_selector"):
            self.mode_selector.grid_forget()
            self.mode_selector.destroy()

        if hasattr(self, "current_mode"):
            self.current_mode.grid_forget()
            self.current_mode.destroy()

        # Создание режима с кнопкой возврата
        if mode == "user":
            self.current_mode = UserMode(
                self.root,
                rag_pipeline=self.rag_pipeline,
                test_generator=self.test_generator,
                on_back_to_selector=self._show_mode_selector,
            )
            self.status_bar.configure(
                text="👤 Пользовательский режим | Подготовка к ОГЭ"
            )
        else:
            self.current_mode = AdminMode(
                self.root,
                rag_pipeline=self.rag_pipeline,
                cache_manager=self.cache_manager,
                on_back_to_selector=self._show_mode_selector,
            )
            self.status_bar.configure(
                text="⚙️ Административный режим | Отладка и мониторинг"
            )

        self.current_mode.grid(row=0, column=0, sticky="nsew")

        # Правый клик больше не нужен - есть кнопка
        # self.root.bind("<Button-3>", lambda e: self._show_mode_selector())

    def run(self) -> None:
        """Запуск приложения."""
        self.root.mainloop()

    def destroy(self) -> None:
        """Закрытие приложения."""
        self.root.destroy()


def create_app(
    rag_pipeline=None, cache_manager=None, test_generator=None, forced_mode=None
) -> OGEDebuggerApp:
    """
    Создание приложения.

    Args:
        rag_pipeline: RAG-пайплайн
        cache_manager: Менеджер кэша
        test_generator: Генератор тестов
        forced_mode: Принудительный режим

    Returns:
        OGEDebuggerApp: Экземпляр приложения
    """
    return OGEDebuggerApp(rag_pipeline, cache_manager, test_generator, forced_mode)
