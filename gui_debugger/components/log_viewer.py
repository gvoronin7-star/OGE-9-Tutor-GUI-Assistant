# -*- coding: utf-8 -*-
"""
GUI просмотрщик логов для отладки.

Позволяет просматривать логи в реальном времени с фильтрацией.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from typing import Optional, List, Dict, Any
import csv
import json
from datetime import datetime
import threading


class LogViewer(ttk.Frame):
    """Просмотрщик логов."""
    
    def __init__(self, parent: tk.Widget, log_dir: Path) -> None:
        """Инициализация."""
        super().__init__(parent)
        self.log_dir = log_dir
        self.current_logs: List[Dict[str, Any]] = []
        
        self._create_widgets()
        self._load_logs()
    
    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Верхняя панель
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Выбор типа лога
        ttk.Label(top_frame, text="Тип лога:").pack(side=tk.LEFT, padx=5)
        
        self.log_type_var = tk.StringVar(value="requests")
        log_types = [
            ("Requests", "requests"),
            ("Errors", "errors"),
            ("RAG", "rag"),
            ("LLM", "llm"),
            ("GUI", "gui"),
            ("All", "all")
        ]
        
        for text, value in log_types:
            rb = ttk.Radiobutton(
                top_frame,
                text=text,
                variable=self.log_type_var,
                value=value,
                command=self._on_log_type_changed
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # Фильтры
        ttk.Label(top_frame, text="|").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(top_frame, text="Компонент:").pack(side=tk.LEFT, padx=5)
        self.component_var = tk.StringVar(value="")
        component_combo = ttk.Combobox(
            top_frame,
            textvariable=self.component_var,
            values=["", "rag", "llm", "gui", "cache", "database"],
            width=15,
            state="readonly"
        )
        component_combo.pack(side=tk.LEFT, padx=5)
        component_combo.bind("<<ComboboxSelected>>", lambda e: self._load_logs())
        
        ttk.Label(top_frame, text="Статус:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="")
        status_combo = ttk.Combobox(
            top_frame,
            textvariable=self.status_var,
            values=["", "success", "error", "timeout"],
            width=10,
            state="readonly"
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._load_logs())
        
        # Кнопки
        ttk.Button(top_frame, text="🔄 Обновить", command=self._load_logs).pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="🗑️ Очистить", command=self._clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="📤 Экспорт", command=self._export_logs).pack(side=tk.LEFT, padx=5)
        
        # Статистика
        self.stats_label = ttk.Label(top_frame, text="", foreground="#808080")
        self.stats_label.pack(side=tk.RIGHT, padx=10)
        
        # Таблица логов
        table_frame = ttk.LabelFrame(self, text="Логи", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Создание таблицы
        columns = ("timestamp", "component", "action", "duration", "status", "input", "output")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # Настройка колонок
        self.tree.heading("timestamp", text="Время")
        self.tree.heading("component", text="Компонент")
        self.tree.heading("action", text="Действие")
        self.tree.heading("duration", text="Время (мс)")
        self.tree.heading("status", text="Статус")
        self.tree.heading("input", text="Вход")
        self.tree.heading("output", text="Выход")
        
        self.tree.column("timestamp", width=150)
        self.tree.column("component", width=80)
        self.tree.column("action", width=100)
        self.tree.column("duration", width=80)
        self.tree.column("status", width=70)
        self.tree.column("input", width=300)
        self.tree.column("output", width=300)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Детали
        details_frame = ttk.LabelFrame(self, text="Детали", padding=5)
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=8
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Привязка выбора
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Автообновление
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self._start_auto_refresh()
    
    def _on_log_type_changed(self) -> None:
        """Изменение типа лога."""
        self._load_logs()
    
    def _load_logs(self) -> None:
        """Загрузка логов."""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получение типа лога
        log_type = self.log_type_var.get()
        component = self.component_var.get()
        status = self.status_var.get()
        
        # Загрузка из CSV
        if log_type == "requests":
            file_path = self.log_dir / "requests_detailed.csv"
        elif log_type == "errors":
            file_path = self.log_dir / "errors.csv"
        else:
            file_path = self.log_dir / f"{log_type}.log"
        
        self.current_logs = []
        
        if not file_path.exists():
            self.stats_label.configure(text="Логи отсутствуют")
            return
        
        try:
            if file_path.suffix == ".csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Фильтрация
                        if component and row.get('component') != component:
                            continue
                        if status and row.get('status') != status:
                            continue
                        
                        self.current_logs.append(row)
                        
                        # Добавление в таблицу
                        values = (
                            row.get('timestamp', '')[:19],
                            row.get('component', ''),
                            row.get('action', ''),
                            row.get('duration_ms', ''),
                            row.get('status', ''),
                            row.get('input_data', '')[:50],
                            row.get('output_data', '')[:50]
                        )
                        
                        # Цвет для ошибок
                        tags = ()
                        if row.get('status') == 'error':
                            tags = ('error',)
                        
                        self.tree.insert("", tk.END, values=values, tags=tags)
            
            elif file_path.suffix == ".log":
                # Чтение текстового лога (последние 100 строк)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]
                    for line in lines:
                        self.current_logs.append({'line': line})
                        self.tree.insert("", tk.END, values=(
                            line[:19] if len(line) > 19 else '',
                            '', '', '', '', line[:50], ''
                        ))
            
            # Обновление статистики
            self.stats_label.configure(text=f"Записей: {len(self.current_logs)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить логи: {e}")
    
    def _on_select(self, event: tk.Event) -> None:
        """Выбор записи."""
        selection = self.tree.selection()
        
        if not selection or not self.current_logs:
            return
        
        # Получение индекса
        index = self.tree.index(selection[0])
        
        if index < len(self.current_logs):
            log_entry = self.current_logs[index]
            
            # Отображение деталей
            self.details_text.delete(1.0, tk.END)
            
            if isinstance(log_entry, dict):
                details = json.dumps(log_entry, indent=2, ensure_ascii=False, default=str)
            else:
                details = str(log_entry)
            
            self.details_text.insert(tk.END, details)
    
    def _clear_logs(self) -> None:
        """Очистка логов."""
        if messagebox.askyesno("Очистка", "Вы уверены? Это удалит все логи."):
            try:
                for log_file in self.log_dir.glob("*.csv"):
                    log_file.unlink()
                for log_file in self.log_dir.glob("*.log"):
                    log_file.unlink()
                
                self._load_logs()
                messagebox.showinfo("Очистка", "Логи очищены")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить логи: {e}")
    
    def _export_logs(self) -> None:
        """Экспорт логов."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("Text files", "*.txt")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        json.dump(self.current_logs, f, indent=2, ensure_ascii=False, default=str)
                    elif file_path.endswith('.csv'):
                        if self.current_logs:
                            writer = csv.DictWriter(f, fieldnames=self.current_logs[0].keys())
                            writer.writeheader()
                            writer.writerows(self.current_logs)
                    else:
                        for log in self.current_logs:
                            f.write(str(log) + '\n')
                
                messagebox.showinfo("Экспорт", f"Логи экспортированы в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать логи: {e}")
    
    def _start_auto_refresh(self) -> None:
        """Запуск автообновления."""
        def refresh():
            if self.auto_refresh_var.get():
                self._load_logs()
            self.after(5000, refresh)
        
        refresh()


def create_log_viewer(root: tk.Tk) -> None:
    """Создание окна просмотрщика логов."""
    from utils.advanced_logger import log_manager
    
    viewer_window = tk.Toplevel(root)
    viewer_window.title("Просмотр логов")
    viewer_window.geometry("1200x800")
    
    log_viewer = LogViewer(viewer_window, log_manager.log_dir)
    log_viewer.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    # Тестовый запуск
    root = tk.Tk()
    root.title("Log Viewer")
    root.geometry("1200x800")
    
    log_dir = Path("logs")
    log_viewer = LogViewer(root, log_dir)
    log_viewer.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
