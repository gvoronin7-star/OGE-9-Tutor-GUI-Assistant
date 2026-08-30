# -*- coding: utf-8 -*-
"""
Управление кэшем.

Просмотр и управление кэшем Redis/InMemory.
"""

import asyncio
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional


class CacheManager(ttk.Frame):
    """Менеджер кэша."""

    def __init__(self, parent: tk.Widget, cache_manager: Any = None) -> None:
        """
        Инициализация менеджера кэша.

        Args:
            parent: Родительский виджет
            cache_manager: Менеджер кэша
        """
        super().__init__(parent)
        self.cache_manager = cache_manager

        self._create_widgets()
        self._refresh_stats()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(
            self, text="💾 УПРАВЛЕНИЕ КЭШЕМ", font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10)

        # Статистика кэша
        stats_frame = ttk.LabelFrame(self, text="Статистика", padding=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        # Карточки статистики
        cards_frame = ttk.Frame(stats_frame)
        cards_frame.pack(fill=tk.X)

        self.keys_card = self._create_stat_card(cards_frame, "Ключей", "0", 0, 0)
        self.memory_card = self._create_stat_card(cards_frame, "Память", "0 MB", 0, 1)
        self.hits_card = self._create_stat_card(cards_frame, "Hit Rate", "0%", 0, 2)
        self.clients_card = self._create_stat_card(cards_frame, "Клиентов", "0", 0, 3)

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)

        # Список ключей
        keys_frame = ttk.LabelFrame(self, text="Ключи кэша", padding=10)
        keys_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Список
        self.keys_listbox = tk.Listbox(
            keys_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            selectbackground="#0078d4",
        )
        self.keys_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            keys_frame, orient=tk.VERTICAL, command=self.keys_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keys_listbox.configure(yscrollcommand=scrollbar.set)

        # Детали ключа
        details_frame = ttk.LabelFrame(keys_frame, text="Детали", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        self.key_label = ttk.Label(
            details_frame, text="Ключ: —", font=("Segoe UI", 10, "bold")
        )
        self.key_label.pack(anchor=tk.W, pady=5)

        self.ttl_label = ttk.Label(details_frame, text="TTL: —", font=("Segoe UI", 10))
        self.ttl_label.pack(anchor=tk.W, pady=5)

        self.size_label = ttk.Label(
            details_frame, text="Размер: —", font=("Segoe UI", 10)
        )
        self.size_label.pack(anchor=tk.W, pady=5)

        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        refresh_btn = ttk.Button(
            btn_frame, text="🔄 Обновить", command=self._refresh_stats
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        clear_all_btn = ttk.Button(
            btn_frame, text="🗑️ Очистить всё", command=self._clear_all
        )
        clear_all_btn.pack(side=tk.LEFT, padx=5)

        clear_topic_btn = ttk.Button(
            btn_frame, text="🔍 По теме", command=self._clear_by_topic
        )
        clear_topic_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(btn_frame, text="📤 Экспорт", command=self._export_keys)
        export_btn.pack(side=tk.RIGHT, padx=5)

        # Привязка выбора
        self.keys_listbox.bind("<<ListboxSelect>>", self._on_key_select)

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

    def _refresh_stats(self) -> None:
        """Обновление статистики."""
        if not self.cache_manager:
            # Демо-данные
            self.keys_card.winfo_children()[1].configure(text="150")
            self.memory_card.winfo_children()[1].configure(text="2.5 MB")
            self.hits_card.winfo_children()[1].configure(text="45%")
            self.clients_card.winfo_children()[1].configure(text="3")

            # Демо-ключи
            self.keys_listbox.delete(0, tk.END)
            demo_keys = [
                "user:12345:query:общество",
                "user:12345:query:экономика",
                "user:67890:query:право",
                "user:67890:test:экономика_medium",
                "rag:topic:политика",
                "rag:topic:социальная сфера",
            ]
            for key in demo_keys:
                self.keys_listbox.insert(tk.END, key)

            return

        try:
            stats = asyncio.run(self.cache_manager.get_stats())

            self.keys_card.winfo_children()[1].configure(
                text=str(stats.get("keys_count", 0))
            )
            self.memory_card.winfo_children()[1].configure(
                text=f"{stats.get('used_memory', '0')} MB"
            )
            self.hits_card.winfo_children()[1].configure(
                text=f"{stats.get('hit_rate', 0):.1f}%"
            )
            self.clients_card.winfo_children()[1].configure(
                text=str(stats.get("connected_clients", 0))
            )

            # Ключи
            self.keys_listbox.delete(0, tk.END)
            keys = asyncio.run(self.cache_manager.get_keys())

            for key in keys[:100]:  # Максимум 100
                self.keys_listbox.insert(tk.END, key)

        except Exception as e:
            self.keys_card.winfo_children()[1].configure(text=f"Ошибка: {str(e)}")

    def _on_key_select(self, event: tk.Event) -> None:
        """Выбор ключа."""
        selection = self.keys_listbox.curselection()

        if not selection:
            return

        key = self.keys_listbox.get(selection[0])

        self.key_label.configure(text=f"Ключ: {key}")
        self.ttl_label.configure(text="TTL: —")
        self.size_label.configure(text="Размер: —")

    def _clear_all(self) -> None:
        """Очистка всего кэша."""
        if messagebox.askyesno(
            "Очистка кэша", "Вы уверены? Это удалит все закэшированные ответы."
        ):
            try:
                if self.cache_manager:
                    asyncio.run(self.cache_manager.clear())
                else:
                    messagebox.showinfo("Демо режим", "Кэш очищен (демо)")

                self._refresh_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка очистки: {str(e)}")

    def _clear_by_topic(self) -> None:
        """Очистка по теме."""
        dialog = tk.Toplevel(self)
        dialog.title("Очистка по теме")
        dialog.geometry("400x150")

        ttk.Label(dialog, text="Введите тему для очистки:").pack(pady=10)

        topic_var = tk.StringVar()
        topic_entry = ttk.Entry(dialog, textvariable=topic_var, width=40)
        topic_entry.pack(pady=5)

        def do_clear():
            topic = topic_var.get().strip()
            if topic:
                # Очистка ключей по теме
                count = 0
                for i in range(self.keys_listbox.size()):
                    key = self.keys_listbox.get(i)
                    if topic.lower() in key.lower():
                        count += 1

                messagebox.showinfo(
                    "Очистка", f"Найдено {count} ключей по теме '{topic}'"
                )
                dialog.destroy()

        ttk.Button(dialog, text="Очистить", command=do_clear).pack(pady=10)

    def _export_keys(self) -> None:
        """Экспорт ключей."""
        from datetime import datetime
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"cache_keys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for i in range(self.keys_listbox.size()):
                    f.write(self.keys_listbox.get(i) + "\n")

            messagebox.showinfo(
                "Экспорт", f"Экспортировано {self.keys_listbox.size()} ключей"
            )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")
