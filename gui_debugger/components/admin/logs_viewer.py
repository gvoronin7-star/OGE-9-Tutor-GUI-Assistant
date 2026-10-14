# -*- coding: utf-8 -*-
"""
Просмотр логов запросов.

Анализ logs/requests_detailed.csv (пишет DetailedRequestLogger).
"""

import csv
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List

from utils.advanced_logger import detailed_logger
from utils.log_rows import (
    ALL_COMPONENTS,
    compute_stats,
    load_rows,
    row_to_values,
    unique_components,
)


class LogsViewer(ttk.Frame):
    """Просмотрщик логов."""

    def __init__(self, parent: tk.Widget) -> None:
        """
        Инициализация просмотрщика логов.

        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)

        self.logs_file = detailed_logger.requests_file
        self.logs_data: List[Dict[str, Any]] = []

        self._create_widgets()
        self._load_logs()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(
            self, text="📝 ПРОСМОТР ЛОГОВ", font=("Segoe UI", 14, "bold")
        )
        header.pack(pady=10)

        # Фильтры
        filters_frame = ttk.LabelFrame(self, text="Фильтры", padding=10)
        filters_frame.pack(fill=tk.X, padx=20, pady=10)

        # Дата
        ttk.Label(filters_frame, text="Дата:").grid(row=0, column=0, padx=5, pady=5)
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(filters_frame, textvariable=self.date_var, width=15)
        date_entry.grid(row=0, column=1, padx=5, pady=5)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Пользователь
        ttk.Label(filters_frame, text="User ID:").grid(row=0, column=2, padx=5, pady=5)
        self.user_var = tk.StringVar()
        user_entry = ttk.Entry(filters_frame, textvariable=self.user_var, width=15)
        user_entry.grid(row=0, column=3, padx=5, pady=5)

        # Компонент
        ttk.Label(filters_frame, text="Компонент:").grid(
            row=0, column=4, padx=5, pady=5
        )
        self.component_var = tk.StringVar()
        self.component_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.component_var,
            values=[ALL_COMPONENTS],
            state="readonly",
            width=20,
        )
        self.component_combo.grid(row=0, column=5, padx=5, pady=5)
        self.component_combo.set(ALL_COMPONENTS)

        # Кнопки
        apply_btn = ttk.Button(
            filters_frame, text="Применить", command=self._apply_filters
        )
        apply_btn.grid(row=0, column=6, padx=10, pady=5)

        clear_btn = ttk.Button(filters_frame, text="Сброс", command=self._clear_filters)
        clear_btn.grid(row=0, column=7, padx=5, pady=5)

        # Таблица логов
        table_frame = ttk.LabelFrame(self, text="Логи запросов", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Создание таблицы
        columns = ("time", "user", "component", "action", "time_ms", "status")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=15
        )

        # Настройка колонок
        self.tree.heading("time", text="Время")
        self.tree.heading("user", text="User ID")
        self.tree.heading("component", text="Компонент")
        self.tree.heading("action", text="Действие")
        self.tree.heading("time_ms", text="Время (мс)")
        self.tree.heading("status", text="Статус")

        self.tree.column("time", width=120)
        self.tree.column("user", width=80)
        self.tree.column("component", width=150)
        self.tree.column("action", width=200)
        self.tree.column("time_ms", width=80)
        self.tree.column("status", width=80)

        # Scrollbars
        v_scroll = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        h_scroll = ttk.Scrollbar(
            table_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Статистика
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        self.total_label = ttk.Label(stats_frame, text="Всего: 0", foreground="#808080")
        self.total_label.pack(side=tk.LEFT, padx=10)

        self.avg_time_label = ttk.Label(
            stats_frame, text="Ср. время: 0мс", foreground="#808080"
        )
        self.avg_time_label.pack(side=tk.LEFT, padx=10)

        self.errors_label = ttk.Label(
            stats_frame, text="Ошибки: 0%", foreground="#808080"
        )
        self.errors_label.pack(side=tk.LEFT, padx=10)

        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        export_btn = ttk.Button(
            btn_frame, text="📤 Экспорт CSV", command=self._export_logs
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(btn_frame, text="🔄 Обновить", command=self._load_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Кнопка для расширенного просмотрщика
        advanced_btn = ttk.Button(
            btn_frame,
            text="🔍 Расширенный просмотр",
            command=self._open_advanced_viewer,
        )
        advanced_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = ttk.Button(
            btn_frame, text="🗑️ Очистить логи", command=self._clear_logs
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)

    def _clear_table(self) -> None:
        """Удалить все строки таблицы."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _load_logs(self) -> None:
        """Загрузка логов."""
        self._clear_table()
        self.logs_data = []

        try:
            self.logs_data = load_rows(self.logs_file)
        except Exception as e:
            self.component_combo.configure(values=[ALL_COMPONENTS])
            self._update_stats()
            self.total_label.configure(text=f"Ошибка чтения логов: {str(e)}")
            return

        self.component_combo.configure(values=unique_components(self.logs_data))
        if self.component_var.get() not in self.component_combo.cget("values"):
            self.component_combo.set(ALL_COMPONENTS)

        for row in self.logs_data:
            self.tree.insert("", tk.END, values=row_to_values(row))

        self._update_stats()
        if not self.logs_file.exists():
            self.total_label.configure(text="Всего: 0 (файл не найден)")

    def _apply_filters(self) -> None:
        """Применение фильтров."""
        self._clear_table()

        date_filter = self.date_var.get()
        user_filter = self.user_var.get()
        component_filter = self.component_var.get()

        filtered = []
        for row in self.logs_data:
            if date_filter and date_filter not in row.get("timestamp", ""):
                continue
            if user_filter and user_filter not in row.get("user_id", ""):
                continue
            if (
                component_filter
                and component_filter != ALL_COMPONENTS
                and component_filter != row.get("component", "")
            ):
                continue

            filtered.append(row)
            self.tree.insert("", tk.END, values=row_to_values(row))

        self.total_label.configure(
            text=f"Всего: {len(filtered)} (из {len(self.logs_data)})"
        )

    def _clear_filters(self) -> None:
        """Сброс фильтров."""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.user_var.set("")
        self.component_var.set(ALL_COMPONENTS)
        self._load_logs()

    def _update_stats(self) -> None:
        """Обновление статистики."""
        total, avg_ms, error_rate, errors = compute_stats(self.logs_data)

        self.total_label.configure(text=f"Всего: {total}")
        self.avg_time_label.configure(text=f"Ср. время: {avg_ms:.0f}мс")
        self.errors_label.configure(
            text=f"Ошибки: {error_rate:.1f}% ({errors}/{total})"
        )

    def _export_logs(self) -> None:
        """Экспорт логов."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=list(detailed_logger.REQUESTS_HEADER),
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(self.logs_data)

            # Уведомление
            self.total_label.configure(
                text=f"✅ Экспортировано: {len(self.logs_data)} записей"
            )

        except Exception as e:
            self.total_label.configure(text=f"❌ Ошибка экспорта: {str(e)}")

    def _clear_logs(self) -> None:
        """Очистка логов."""
        if messagebox.askyesno(
            "Очистка логов", "Вы уверены? Это действие нельзя отменить."
        ):
            try:
                detailed_logger.clear()
                self._load_logs()

            except Exception as e:
                self.total_label.configure(text=f"❌ Ошибка: {str(e)}")

    def _open_advanced_viewer(self) -> None:
        """Открытие расширенного просмотрщика логов."""
        from gui_debugger.components.log_viewer import create_log_viewer

        create_log_viewer(self.winfo_toplevel())
