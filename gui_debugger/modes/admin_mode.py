# -*- coding: utf-8 -*-
"""
Административный режим.

Отладка, мониторинг, управление системой.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional


class AdminMode(ttk.Frame):
    """Административный режим."""

    def __init__(
        self,
        parent: tk.Widget,
        rag_pipeline: Any = None,
        cache_manager: Any = None,
        on_back_to_selector: Optional[Any] = None,
    ) -> None:
        """
        Инициализация административного режима.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
            cache_manager: Менеджер кэша
            on_back_to_selector: Callback для возврата к выбору режима
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.cache_manager = cache_manager
        self.on_back_to_selector = on_back_to_selector

        self._create_widgets()

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

        # Вкладки
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка 1: Chat (существующая)
        from gui_debugger.components import ChatPanel

        self.chat_panel = ChatPanel(notebook, self.rag_pipeline)
        notebook.add(self.chat_panel, text="  📱 Chat  ")

        # Вкладка 2: RAG (существующая)
        from gui_debugger.components import RAGPanel

        self.rag_panel = RAGPanel(notebook, self.rag_pipeline)
        notebook.add(self.rag_panel, text="  🔍 RAG  ")

        # Вкладка 3: Metrics (существующая)
        from gui_debugger.components import MetricsPanel

        self.metrics_panel = MetricsPanel(notebook, self.rag_pipeline)
        notebook.add(self.metrics_panel, text="  📊 Metrics  ")

        # Вкладка 4: Database (существующая)
        from gui_debugger.components import DatabasePanel

        self.database_panel = DatabasePanel(notebook, self.rag_pipeline)
        notebook.add(self.database_panel, text="  📚 Database  ")

        # Вкладка 5: Logs (новая)
        from gui_debugger.components.admin import LogsViewer

        self.logs_viewer = LogsViewer(notebook)
        notebook.add(self.logs_viewer, text="  📝 Logs  ")

        # Вкладка 6: Cache (новая)
        from gui_debugger.components.admin import CacheManager

        self.cache_manager_panel = CacheManager(notebook, self.cache_manager)
        notebook.add(self.cache_manager_panel, text="  💾 Cache  ")

        # Вкладка 7: LLM (новая)
        from gui_debugger.components.admin import LLMMonitor

        self.llm_monitor = LLMMonitor(notebook, None)
        notebook.add(self.llm_monitor, text="  🤖 LLM  ")

        # Вкладка 8: Config (новая)
        from gui_debugger.components.admin import ConfigPanel

        self.config_panel = ConfigPanel(notebook)
        notebook.add(self.config_panel, text="  ⚙️ Config  ")

        # Вкладка 9: Users (новая)
        from gui_debugger.components.admin import UsersPanel

        self.users_panel = UsersPanel(notebook)
        notebook.add(self.users_panel, text="  👥 Users  ")

        # Вкладка 10: RAG Database (новая)
        from gui_debugger.components.admin import RAGManager

        self.rag_manager = RAGManager(notebook, self.rag_pipeline)
        notebook.add(self.rag_manager, text="  🗄️ RAG DB  ")
