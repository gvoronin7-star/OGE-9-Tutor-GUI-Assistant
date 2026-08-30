# -*- coding: utf-8 -*-
"""
Панель конфигурации.

Настройки RAG, LLM, кэша.
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict


class ConfigPanel(ttk.Frame):
    """Панель конфигурации."""

    def __init__(self, parent: tk.Widget) -> None:
        """
        Инициализация панели конфигурации.

        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)

        self.config_file = Path(".env")
        self.current_config = {}

        self._create_widgets()
        self._load_config()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="⚙️ КОНФИГУРАЦИЯ", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Вкладки настроек
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Вкладка RAG
        rag_tab = self._create_rag_tab(notebook)
        notebook.add(rag_tab, text="  RAG-пайплайн  ")

        # Вкладка LLM
        llm_tab = self._create_llm_tab(notebook)
        notebook.add(llm_tab, text="  LLM  ")

        # Вкладка Кэш
        cache_tab = self._create_cache_tab(notebook)
        notebook.add(cache_tab, text="  Кэш  ")

        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        save_btn = ttk.Button(btn_frame, text="💾 Сохранить", command=self._save_config)
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = ttk.Button(btn_frame, text="📂 Загрузить", command=self._load_config)
        load_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Button(btn_frame, text="🔄 Сброс", command=self._reset_config)
        reset_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(
            btn_frame, text="📤 Экспорт", command=self._export_config
        )
        export_btn.pack(side=tk.RIGHT, padx=5)

    def _create_rag_tab(self, parent: tk.Widget) -> ttk.Frame:
        """Создание вкладки RAG."""
        tab = ttk.Frame(parent, padding=20)

        # Top-K
        ttk.Label(tab, text="Top-K (количество чанков):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.top_k_var = tk.StringVar(value="5")
        top_k_spinbox = ttk.Spinbox(
            tab, from_=1, to=20, textvariable=self.top_k_var, width=10
        )
        top_k_spinbox.pack(anchor=tk.W, pady=5)

        # Threshold
        ttk.Label(tab, text="Threshold (порог схожести):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.threshold_var = tk.StringVar(value="0.5")
        threshold_spinbox = ttk.Spinbox(
            tab,
            from_=0.0,
            to=1.0,
            increment=0.1,
            textvariable=self.threshold_var,
            width=10,
        )
        threshold_spinbox.pack(anchor=tk.W, pady=5)

        # Источники
        ttk.Label(tab, text="Приоритет источников:", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )

        sources_frame = ttk.Frame(tab)
        sources_frame.pack(anchor=tk.W, pady=5)

        self.rag_base_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            sources_frame, text="RAG_data_base (FIPI)", variable=self.rag_base_var
        ).pack(side=tk.LEFT, padx=5)

        self.faiss_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            sources_frame, text="Local Faiss", variable=self.faiss_var
        ).pack(side=tk.LEFT, padx=5)

        self.whoosh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sources_frame, text="Whoosh", variable=self.whoosh_var).pack(
            side=tk.LEFT, padx=5
        )

        # Разделитель
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # Информация
        info_label = ttk.Label(
            tab,
            text="RAG_data_base: 204 чанка FIPI\nLocal Faiss: HNSW индекс (768-dim)\nWhoosh: полнотекстовый поиск",
            font=("Segoe UI", 9),
            foreground="#808080",
        )
        info_label.pack(anchor=tk.W)

        return tab

    def _create_llm_tab(self, parent: tk.Widget) -> ttk.Frame:
        """Создание вкладки LLM."""
        tab = ttk.Frame(parent, padding=20)

        # Модель
        ttk.Label(tab, text="Основная модель:", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.model_var = tk.StringVar(value="GigaChat-Max")
        model_combo = ttk.Combobox(
            tab,
            textvariable=self.model_var,
            values=["GigaChat-Max", "GigaChat-Pro", "YandexGPT-Lite"],
            state="readonly",
            width=30,
        )
        model_combo.pack(anchor=tk.W, pady=5)

        # Timeout
        ttk.Label(tab, text="Timeout (секунды):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.timeout_var = tk.StringVar(value="30")
        timeout_spinbox = ttk.Spinbox(
            tab, from_=10, to=120, textvariable=self.timeout_var, width=10
        )
        timeout_spinbox.pack(anchor=tk.W, pady=5)

        # Retries
        ttk.Label(tab, text="Попытки (Retries):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.retries_var = tk.StringVar(value="3")
        retries_spinbox = ttk.Spinbox(
            tab, from_=0, to=10, textvariable=self.retries_var, width=10
        )
        retries_spinbox.pack(anchor=tk.W, pady=5)

        # Разделитель
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # ProxyAPI
        ttk.Label(tab, text="ProxyAPI URL:", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.proxy_url_var = tk.StringVar(value="https://api.proxyapi.ru/gigachat")
        proxy_entry = ttk.Entry(tab, textvariable=self.proxy_url_var, width=50)
        proxy_entry.pack(anchor=tk.W, pady=5)

        return tab

    def _create_cache_tab(self, parent: tk.Widget) -> ttk.Frame:
        """Создание вкладки кэша."""
        tab = ttk.Frame(parent, padding=20)

        # TTL для топ-запросов
        ttk.Label(tab, text="TTL топ-запросов (часы):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.ttl_top_var = tk.StringVar(value="24")
        ttl_top_spinbox = ttk.Spinbox(
            tab, from_=1, to=72, textvariable=self.ttl_top_var, width=10
        )
        ttl_top_spinbox.pack(anchor=tk.W, pady=5)

        # TTL для обычных
        ttk.Label(tab, text="TTL обычных запросов (часы):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.ttl_normal_var = tk.StringVar(value="6")
        ttl_normal_spinbox = ttk.Spinbox(
            tab, from_=1, to=24, textvariable=self.ttl_normal_var, width=10
        )
        ttl_normal_spinbox.pack(anchor=tk.W, pady=5)

        # TTL для редких
        ttk.Label(tab, text="TTL редких запросов (часы):", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.ttl_rare_var = tk.StringVar(value="1")
        ttl_rare_spinbox = ttk.Spinbox(
            tab, from_=0, to=12, textvariable=self.ttl_rare_var, width=10
        )
        ttl_rare_spinbox.pack(anchor=tk.W, pady=5)

        # Разделитель
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # Redis
        ttk.Label(tab, text="Redis Host:", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.redis_host_var = tk.StringVar(value="localhost")
        redis_host_entry = ttk.Entry(tab, textvariable=self.redis_host_var, width=30)
        redis_host_entry.pack(anchor=tk.W, pady=5)

        ttk.Label(tab, text="Redis Port:", font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=5
        )
        self.redis_port_var = tk.StringVar(value="6379")
        redis_port_spinbox = ttk.Spinbox(
            tab, from_=1, to=65535, textvariable=self.redis_port_var, width=10
        )
        redis_port_spinbox.pack(anchor=tk.W, pady=5)

        return tab

    def _load_config(self) -> None:
        """Загрузка конфигурации."""
        # В реальной версии — загрузка из .env
        messagebox.showinfo("Конфигурация", "Загружена конфигурация по умолчанию")

    def _save_config(self) -> None:
        """Сохранение конфигурации."""
        config = {
            "rag": {
                "top_k": int(self.top_k_var.get()),
                "threshold": float(self.threshold_var.get()),
                "use_rag_base": self.rag_base_var.get(),
                "use_faiss": self.faiss_var.get(),
                "use_whoosh": self.whoosh_var.get(),
            },
            "llm": {
                "model": self.model_var.get(),
                "timeout": int(self.timeout_var.get()),
                "retries": int(self.retries_var.get()),
                "proxy_url": self.proxy_url_var.get(),
            },
            "cache": {
                "ttl_top": int(self.ttl_top_var.get()),
                "ttl_normal": int(self.ttl_normal_var.get()),
                "ttl_rare": int(self.ttl_rare_var.get()),
                "redis_host": self.redis_host_var.get(),
                "redis_port": int(self.redis_port_var.get()),
            },
        }

        # Сохранение в файл
        config_file = Path("gui_debugger/config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        messagebox.showinfo(
            "Сохранение", "Конфигурация сохранена в gui_debugger/config.json"
        )

    def _reset_config(self) -> None:
        """Сброс конфигурации."""
        if messagebox.askyesno(
            "Сброс", "Сбросить все настройки к значениям по умолчанию?"
        ):
            self.top_k_var.set("5")
            self.threshold_var.set("0.5")
            self.model_var.set("GigaChat-Max")
            self.timeout_var.set("30")
            self.retries_var.set("3")
            self.ttl_top_var.set("24")
            self.ttl_normal_var.set("6")
            self.ttl_rare_var.set("1")

            messagebox.showinfo("Сброс", "Настройки сброшены")

    def _export_config(self) -> None:
        """Экспорт конфигурации."""
        from datetime import datetime
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

        if not file_path:
            return

        config = {
            "rag": {
                "top_k": int(self.top_k_var.get()),
                "threshold": float(self.threshold_var.get()),
            },
            "llm": {
                "model": self.model_var.get(),
                "timeout": int(self.timeout_var.get()),
            },
            "cache": {
                "ttl_top": int(self.ttl_top_var.get()),
                "ttl_normal": int(self.ttl_normal_var.get()),
            },
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Экспорт", f"Конфигурация экспортирована в {file_path}")
