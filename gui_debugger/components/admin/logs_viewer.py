# -*- coding: utf-8 -*-
"""
Просмотр логов запросов.

Анализ logs/requests.csv
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import csv


class LogsViewer(ttk.Frame):
    """Просмотрщик логов."""
    
    def __init__(self, parent: tk.Widget) -> None:
        """
        Инициализация просмотрщика логов.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.logs_file = Path("logs/requests.csv")
        self.logs_data = []
        
        self._create_widgets()
        self._load_logs()
    
    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="📝 ПРОСМОТР ЛОГОВ", font=("Segoe UI", 14, "bold"))
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
        
        # Тема
        ttk.Label(filters_frame, text="Тема:").grid(row=0, column=4, padx=5, pady=5)
        self.topic_var = tk.StringVar()
        topic_combo = ttk.Combobox(filters_frame, textvariable=self.topic_var, values=[
            "Все", "Человек и общество", "Экономика", "Право",
            "Политика", "Социальная сфера", "Духовная культура"
        ], state="readonly", width=20)
        topic_combo.grid(row=0, column=5, padx=5, pady=5)
        topic_combo.set("Все")
        
        # Кнопки
        apply_btn = ttk.Button(filters_frame, text="Применить", command=self._apply_filters)
        apply_btn.grid(row=0, column=6, padx=10, pady=5)
        
        clear_btn = ttk.Button(filters_frame, text="Сброс", command=self._clear_filters)
        clear_btn.grid(row=0, column=7, padx=5, pady=5)
        
        # Таблица логов
        table_frame = ttk.LabelFrame(self, text="Логи запросов", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Создание таблицы
        columns = ("time", "user", "query", "topic", "time_ms", "cached")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Настройка колонок
        self.tree.heading("time", text="Время")
        self.tree.heading("user", text="User ID")
        self.tree.heading("query", text="Запрос")
        self.tree.heading("topic", text="Тема")
        self.tree.heading("time_ms", text="Время (мс)")
        self.tree.heading("cached", text="Кэш")
        
        self.tree.column("time", width=120)
        self.tree.column("user", width=80)
        self.tree.column("query", width=300)
        self.tree.column("topic", width=150)
        self.tree.column("time_ms", width=80)
        self.tree.column("cached", width=60)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
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
        
        self.avg_time_label = ttk.Label(stats_frame, text="Ср. время: 0мс", foreground="#808080")
        self.avg_time_label.pack(side=tk.LEFT, padx=10)
        
        self.cache_label = ttk.Label(stats_frame, text="Кэш: 0%", foreground="#808080")
        self.cache_label.pack(side=tk.LEFT, padx=10)
        
        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        export_btn = ttk.Button(btn_frame, text="📤 Экспорт CSV", command=self._export_logs)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(btn_frame, text="🔄 Обновить", command=self._load_logs)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка для расширенного просмотрщика
        advanced_btn = ttk.Button(btn_frame, text="🔍 Расширенный просмотр", command=self._open_advanced_viewer)
        advanced_btn.pack(side=tk.LEFT, padx=10)
        
        clear_btn = ttk.Button(btn_frame, text="🗑️ Очистить логи", command=self._clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=5)
    
    def _load_logs(self) -> None:
        """Загрузка логов."""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.logs_data = []
        
        if not self.logs_file.exists():
            self.total_label.configure(text="Всего: 0 (файл не найден)")
            return
        
        try:
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.logs_data.append(row)
                    self.tree.insert("", tk.END, values=[
                        row.get("timestamp", "")[-8:],  # Только время
                        row.get("user_id", ""),
                        row.get("query_text", "")[:50],
                        row.get("topic", ""),
                        row.get("total_response_time", ""),
                        "✅" if row.get("is_cached") == "True" else "❌"
                    ])
            
            self._update_stats()
            
        except Exception as e:
            self.total_label.configure(text=f"Ошибка: {str(e)}")
    
    def _apply_filters(self) -> None:
        """Применение фильтров."""
        # Очистка
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        date_filter = self.date_var.get()
        user_filter = self.user_var.get()
        topic_filter = self.topic_var.get()
        
        filtered = []
        for row in self.logs_data:
            # Фильтр по дате
            if date_filter and date_filter not in row.get("timestamp", ""):
                continue
            
            # Фильтр по пользователю
            if user_filter and user_filter not in row.get("user_id", ""):
                continue
            
            # Фильтр по теме
            if topic_filter != "Все" and topic_filter not in row.get("topic", ""):
                continue
            
            filtered.append(row)
            self.tree.insert("", tk.END, values=[
                row.get("timestamp", "")[-8:],
                row.get("user_id", ""),
                row.get("query_text", "")[:50],
                row.get("topic", ""),
                row.get("total_response_time", ""),
                "✅" if row.get("is_cached") == "True" else "❌"
            ])
        
        self.total_label.configure(text=f"Всего: {len(filtered)} (из {len(self.logs_data)})")
    
    def _clear_filters(self) -> None:
        """Сброс фильтров."""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.user_var.set("")
        self.topic_var.set("Все")
        self._load_logs()
    
    def _update_stats(self) -> None:
        """Обновление статистики."""
        total = len(self.logs_data)
        
        if total == 0:
            self.avg_time_label.configure(text="Ср. время: 0мс")
            self.cache_label.configure(text="Кэш: 0%")
            return
        
        # Среднее время
        times = []
        cache_hits = 0
        
        for row in self.logs_data:
            try:
                time_val = float(row.get("total_response_time", 0))
                times.append(time_val)
            except:
                pass
            
            if row.get("is_cached") == "True":
                cache_hits += 1
        
        avg_time = sum(times) / len(times) if times else 0
        cache_rate = (cache_hits / total) * 100 if total > 0 else 0
        
        self.avg_time_label.configure(text=f"Ср. время: {avg_time:.2f}с")
        self.cache_label.configure(text=f"Кэш: {cache_rate:.1f}% ({cache_hits}/{total})")
        self.total_label.configure(text=f"Всего: {total}")
    
    def _export_logs(self) -> None:
        """Экспорт логов."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.logs_data[0].keys() if self.logs_data else [])
                writer.writeheader()
                writer.writerows(self.logs_data)
            
            # Уведомление
            self.total_label.configure(text=f"✅ Экспортировано: {len(self.logs_data)} записей")
            
        except Exception as e:
            self.total_label.configure(text=f"❌ Ошибка экспорта: {str(e)}")
    
    def _clear_logs(self) -> None:
        """Очистка логов."""
        if messagebox.askyesno("Очистка логов", "Вы уверены? Это действие нельзя отменить."):
            try:
                if self.logs_file.exists():
                    self.logs_file.unlink()
                self.logs_data = []
                
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                self.total_label.configure(text="Всего: 0")
                self.avg_time_label.configure(text="Ср. время: 0мс")
                self.cache_label.configure(text="Кэш: 0%")
                
            except Exception as e:
                self.total_label.configure(text=f"❌ Ошибка: {str(e)}")

    def _open_advanced_viewer(self) -> None:
        """Открытие расширенного просмотрщика логов."""
        from gui_debugger.components.log_viewer import create_log_viewer
        create_log_viewer(self.winfo_toplevel())
