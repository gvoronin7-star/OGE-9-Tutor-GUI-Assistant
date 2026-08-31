# -*- coding: utf-8 -*-
"""
Пользовательский режим.

Подготовка к ОГЭ: изучение тем, тесты, прогресс.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional


class UserMode(ttk.Frame):
    """Пользовательский режим."""

    def __init__(
        self,
        parent: tk.Widget,
        rag_pipeline: Any = None,
        test_generator: Any = None,
        on_back_to_selector: Optional[Any] = None,
    ) -> None:
        """
        Инициализация пользовательского режима.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
            test_generator: Генератор тестов
            on_back_to_selector: Callback для возврата к выбору режима
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.test_generator = test_generator
        self.on_back_to_selector = on_back_to_selector

        self.current_panel: Optional[tk.Widget] = None
        self.user_data: Dict[str, Any] = {
            "name": "Ученик",
            "progress": {
                "topics_studied": 0,
                "topics_completed": [],
                "tests_completed": 0,
                "accuracy": 0,
            },
        }

        self._create_widgets()
        self._show_main_menu()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Верхняя панель с кнопкой возврата
        top_bar = ttk.Frame(self)
        top_bar.pack(fill=tk.X)

        if self.on_back_to_selector:
            back_btn = ttk.Button(
                top_bar, text="🏠 К выбору режима", command=self.on_back_to_selector
            )
            back_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Контейнер для панелей
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

    def _clear_container(self) -> None:
        """Очистка контейнера."""
        if self.current_panel:
            self.current_panel.pack_forget()
            self.current_panel.destroy()

    def _show_main_menu(self) -> None:
        """Показ главного меню."""
        from gui_debugger.components.user import MainMenu

        self._clear_container()

        callbacks = {
            "study_topic": self._show_topic_study,
            "solve_test": self._show_test_solver,
            "show_progress": self._show_progress,
            "show_help": self._show_help,
        }

        self.main_menu = MainMenu(
            self.container, callbacks=callbacks, user_data=self.user_data
        )
        self.main_menu.pack(fill=tk.BOTH, expand=True)
        self.current_panel = self.main_menu

    def _show_topic_study(self) -> None:
        """Показ панели изучения тем."""
        from gui_debugger.components.user import TopicStudy

        self._clear_container()

        def on_topic_complete(topic: str):
            """Обновление прогресса при завершении темы."""
            # Сохраняем в user_data
            if "topics_completed" not in self.user_data["progress"]:
                self.user_data["progress"]["topics_completed"] = []

            if topic not in self.user_data["progress"]["topics_completed"]:
                self.user_data["progress"]["topics_completed"].append(topic)
                self.user_data["progress"]["topics_studied"] = len(
                    self.user_data["progress"]["topics_completed"]
                )

        self.topic_study = TopicStudy(
            self.container,
            rag_pipeline=self.rag_pipeline,
            on_back=self._show_main_menu,
            on_topic_complete=on_topic_complete,
        )
        self.topic_study.pack(fill=tk.BOTH, expand=True)
        self.current_panel = self.topic_study

    def _show_test_solver(self) -> None:
        """Показ панели тестов."""
        from gui_debugger.components.user import TestSolver

        self._clear_container()

        def on_test_complete(topic: str, score: int, total: int):
            """Обновление прогресса при завершении теста."""
            # Сохраняем в user_data
            self.user_data["progress"]["tests_completed"] = (
                self.user_data["progress"].get("tests_completed", 0) + 1
            )
            self.user_data["progress"]["total_questions"] = (
                self.user_data["progress"].get("total_questions", 0) + total
            )
            self.user_data["progress"]["correct_answers"] = (
                self.user_data["progress"].get("correct_answers", 0) + score
            )

            # Пересчёт точности
            if self.user_data["progress"]["total_questions"] > 0:
                self.user_data["progress"]["accuracy"] = (
                    self.user_data["progress"]["correct_answers"]
                    / self.user_data["progress"]["total_questions"]
                ) * 100

            # Добавление в историю
            from datetime import datetime

            percentage = (score / total) * 100
            self.user_data.setdefault("history", []).append(
                {
                    "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "action": f"Тест: {topic}",
                    "result": f"{score}/{total} ({percentage:.0f}%)",
                }
            )

        self.test_solver = TestSolver(
            self.container,
            test_generator=self.test_generator,
            on_back=self._show_main_menu,
            on_test_complete=on_test_complete,
        )
        self.test_solver.pack(fill=tk.BOTH, expand=True)
        self.current_panel = self.test_solver

    def _show_progress(self) -> None:
        """Показ панели прогресса."""
        from gui_debugger.components.user import ProgressPanel

        self._clear_container()

        self.progress_panel = ProgressPanel(
            self.container, user_data=self.user_data, on_back=self._show_main_menu
        )
        self.progress_panel.pack(fill=tk.BOTH, expand=True)
        self.current_panel = self.progress_panel

    def _show_help(self) -> None:
        """Показ панели помощи."""
        from gui_debugger.components.user import HelpPanel

        self._clear_container()

        self.help_panel = HelpPanel(self.container, on_back=self._show_main_menu)
        self.help_panel.pack(fill=tk.BOTH, expand=True)
        self.current_panel = self.help_panel
