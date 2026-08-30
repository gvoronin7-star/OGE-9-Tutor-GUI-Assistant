# -*- coding: utf-8 -*-
"""
Панель базы знаний (RAG_data_base).
"""

import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk
from typing import Any, Optional


class DatabasePanel(ttk.Frame):
    """Панель базы знаний."""

    def __init__(self, parent: tk.Widget, rag_pipeline: Any) -> None:
        """
        Инициализация панели базы.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.current_chunk_index = 0
        self.chunks = []

        self._create_widgets()
        self._load_database_info()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(
            self, text="📚 DATABASE (RAG_data_base)", font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10)

        # Общая статистика
        stats_frame = ttk.LabelFrame(self, text="Статистика", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.stats_text = tk.Text(
            stats_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            height=6,
        )
        self.stats_text.pack(fill=tk.X)

        # Поиск по базе
        search_frame = ttk.LabelFrame(self, text="Поиск по базе", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Запрос:").pack(side=tk.LEFT, padx=5)
        self.search_query_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame, textvariable=self.search_query_var, width=40
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self._search_database())

        search_btn = ttk.Button(
            search_frame, text="Найти", command=self._search_database
        )
        search_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(
            search_frame, text="Очистить", command=self._clear_search
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Список чанков
        chunks_frame = ttk.LabelFrame(self, text="Чанки", padding=10)
        chunks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Список
        list_frame = ttk.Frame(chunks_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chunks_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            selectbackground="#0078d4",
            selectforeground="#ffffff",
        )
        self.chunks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.chunks_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chunks_listbox.configure(yscrollcommand=scrollbar.set)
        self.chunks_listbox.bind("<<ListboxSelect>>", self._on_chunk_select)

        # Детали чанка
        details_frame = ttk.LabelFrame(chunks_frame, text="Детали", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#252526",
            fg="#ffffff",
            width=50,
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Навигация
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)

        prev_btn = ttk.Button(nav_frame, text="← Предыдущий", command=self._prev_chunk)
        prev_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(nav_frame, text="0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=5)

        next_btn = ttk.Button(nav_frame, text="Следующий →", command=self._next_chunk)
        next_btn.pack(side=tk.LEFT, padx=5)

    def _load_database_info(self) -> None:
        """Загрузка информации о базе."""
        if not self.rag_pipeline or not self.rag_pipeline.use_existing:
            self.stats_text.insert(tk.END, "RAG_data_base не активна\n")
            return

        try:
            if self.rag_pipeline.existing_store:
                stats = self.rag_pipeline.existing_store.get_stats()

                info = (
                    f"Чанков: {stats.get('total_chunks', 0)}\n"
                    f"Векторов: {stats.get('total_vectors', 0)}\n"
                    f"Модель: {stats.get('model', 'unknown')}\n"
                    f"Размерность: {stats.get('embedding_dim', 0)}\n"
                    f"Источник: {stats.get('source', 'unknown')}\n"
                )

                self.stats_text.insert(tk.END, info)

                # Загрузка чанков для списка
                self.chunks = self.rag_pipeline.existing_store.dataset

                # Заполнение списка (все чанки)
                for i, chunk in enumerate(self.chunks):
                    topic = (
                        chunk.get("metadata", {}).get("keywords", ["unknown"])[0]
                        if chunk.get("metadata", {}).get("keywords")
                        else "unknown"
                    )
                    chunk_type = chunk.get("type", "unknown")
                    self.chunks_listbox.insert(
                        tk.END, f"[{i:03d}] {topic} ({chunk_type})"
                    )

                self.page_label.configure(text=f"1 / {len(self.chunks)}")

        except Exception as e:
            self.stats_text.insert(tk.END, f"Ошибка загрузки: {str(e)}\n")

    def _on_chunk_select(self, event: tk.Event) -> None:
        """Выбор чанка из списка."""
        selection = self.chunks_listbox.curselection()

        if not selection or not self.chunks:
            return

        index = selection[0]
        chunk = self.chunks[index]

        # Отображение деталей
        self.details_text.delete(1.0, tk.END)

        details = (
            f"ID: {chunk.get('metadata', {}).get('chunk_id', index)}\n"
            f"Type: {chunk.get('type', 'unknown')}\n"
            f"Topic: {self._extract_topic(chunk)}\n"
            f"Keywords: {', '.join(chunk.get('metadata', {}).get('keywords', []))}\n"
            f"Intent: {chunk.get('metadata', {}).get('intent', 'unknown')}\n"
            f"Page: {chunk.get('metadata', {}).get('page_number', 0)}\n\n"
            f"Text:\n{chunk.get('text', '')}\n"
        )

        self.details_text.insert(tk.END, details)
        self.page_label.configure(text=f"{index + 1} / {len(self.chunks)}")

    def _extract_topic(self, chunk: dict) -> str:
        """Извлечение темы из чанка."""
        keywords = chunk.get("metadata", {}).get("keywords", [])

        if not keywords:
            return "Неизвестная тема"

        topic_mapping = {
            "Человек и общество": ["общество", "человек", "личность"],
            "Экономика": ["экономика", "рынок", "деньги"],
            "Право": ["право", "закон", "конституция"],
            "Политика": ["политика", "власть", "государство"],
            "Социальная сфера": ["социальная", "семья", "роль"],
            "Духовная культура": ["культура", "наука", "образование"],
        }

        for topic, topic_keywords in topic_mapping.items():
            if any(kw in keywords for kw in topic_keywords):
                return topic

        return "Общая тема"

    def _search_database(self) -> None:
        """Поиск по базе."""
        query = self.search_query_var.get().strip().lower()

        if not query:
            return

        # Очистка списка
        self.chunks_listbox.delete(0, tk.END)

        # Поиск
        results = []
        for i, chunk in enumerate(self.chunks):
            text = chunk.get("text", "").lower()
            keywords = chunk.get("metadata", {}).get("keywords", [])

            if query in text or any(query in kw.lower() for kw in keywords):
                results.append(i)

        # Отображение результатов
        if results:
            for idx in results[:50]:  # Максимум 50 результатов
                chunk = self.chunks[idx]
                topic = (
                    chunk.get("metadata", {}).get("keywords", ["unknown"])[0]
                    if chunk.get("metadata", {}).get("keywords")
                    else "unknown"
                )
                self.chunks_listbox.insert(tk.END, f"[{idx:03d}] {topic} (match)")

            self.page_label.configure(text=f"Найдено: {len(results)}")
        else:
            self.chunks_listbox.insert(tk.END, "Ничего не найдено")

    def _clear_search(self) -> None:
        """Очистка поиска."""
        self.search_query_var.set("")
        self.chunks_listbox.delete(0, tk.END)

        # Восстановление списка (все чанки)
        for i, chunk in enumerate(self.chunks):
            topic = (
                chunk.get("metadata", {}).get("keywords", ["unknown"])[0]
                if chunk.get("metadata", {}).get("keywords")
                else "unknown"
            )
            self.chunks_listbox.insert(
                tk.END, f"[{i:03d}] {topic} ({chunk.get('type', 'unknown')})"
            )

        self.page_label.configure(text=f"1 / {len(self.chunks)}")

    def _prev_chunk(self) -> None:
        """Предыдущий чанк."""
        current = self.chunks_listbox.curselection()

        if current and current[0] > 0:
            self.chunks_listbox.selection_clear(0, tk.END)
            self.chunks_listbox.selection_set(current[0] - 1)
            self.chunks_listbox.see(current[0] - 1)
            self._on_chunk_select(None)

    def _next_chunk(self) -> None:
        """Следующий чанк."""
        current = self.chunks_listbox.curselection()

        if current and current[0] < self.chunks_listbox.size() - 1:
            self.chunks_listbox.selection_clear(0, tk.END)
            self.chunks_listbox.selection_set(current[0] + 1)
            self.chunks_listbox.see(current[0] + 1)
            self._on_chunk_select(None)
