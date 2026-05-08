# -*- coding: utf-8 -*-
"""
Панель визуализации RAG-пайплайна.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Any


class RAGPanel(ttk.Frame):
    """Панель RAG-пайплайна."""
    
    def __init__(self, parent: tk.Widget, rag_pipeline: Any) -> None:
        """
        Инициализация RAG панели.
        
        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="🔍 RAG PIPELINE", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)
        
        # Панель настроек
        settings_frame = ttk.LabelFrame(self, text="Настройки поиска", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Top-K
        ttk.Label(settings_frame, text="Top-K:").grid(row=0, column=0, padx=5)
        self.top_k_var = tk.StringVar(value="5")
        top_k_spinbox = ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.top_k_var, width=5)
        top_k_spinbox.grid(row=0, column=1, padx=5)
        
        # Threshold
        ttk.Label(settings_frame, text="Threshold:").grid(row=0, column=2, padx=5)
        self.threshold_var = tk.StringVar(value="0.5")
        threshold_spinbox = ttk.Spinbox(settings_frame, from_=0.0, to=1.0, increment=0.1, textvariable=self.threshold_var, width=5)
        threshold_spinbox.grid(row=0, column=3, padx=5)
        
        # Источник
        ttk.Label(settings_frame, text="Источник:").grid(row=0, column=4, padx=5)
        self.source_var = tk.StringVar(value="RAG_data_base")
        source_combo = ttk.Combobox(settings_frame, textvariable=self.source_var, values=["RAG_data_base", "Local Faiss", "Whoosh"], width=15, state="readonly")
        source_combo.grid(row=0, column=5, padx=5)
        
        # Статус RAG
        status_frame = ttk.LabelFrame(self, text="Статус", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.rag_status_label = ttk.Label(status_frame, text="RAG_data_base: Неактивна", foreground="#e81123")
        self.rag_status_label.pack(anchor=tk.W)
        
        # Обновление статуса
        self._update_rag_status()
        
        # Область результатов
        results_frame = ttk.LabelFrame(self, text="Результаты поиска", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_area = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        self.results_area.pack(fill=tk.BOTH, expand=True)
        
        # Тестовый поиск
        test_frame = ttk.Frame(self)
        test_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(test_frame, text="Тестовый запрос:").pack(side=tk.LEFT, padx=5)
        self.test_query_var = tk.StringVar(value="Что такое общество?")
        test_entry = ttk.Entry(test_frame, textvariable=self.test_query_var, width=40)
        test_entry.pack(side=tk.LEFT, padx=5)
        
        test_btn = ttk.Button(test_frame, text="Тест", command=self._test_search)
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # Лог
        log_frame = ttk.LabelFrame(self, text="Лог операций", padding=10)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_label = ttk.Label(log_frame, text="Ожидание...", foreground="#808080")
        self.log_label.pack(anchor=tk.W)
    
    def _update_rag_status(self) -> None:
        """Обновление статуса RAG."""
        if self.rag_pipeline and self.rag_pipeline.use_existing:
            stats = self.rag_pipeline.existing_store.get_stats() if self.rag_pipeline.existing_store else {}
            status = (
                f"✅ RAG_data_base активна\n"
                f"  Чанков: {stats.get('total_chunks', 0)}\n"
                f"  Векторов: {stats.get('total_vectors', 0)}\n"
                f"  Модель: {stats.get('model', 'unknown')}\n"
                f"  Размерность: {stats.get('embedding_dim', 0)}"
            )
            self.rag_status_label.configure(text=status, foreground="#107c10")
        else:
            self.rag_status_label.configure(
                text="⚠️ RAG_data_base не активна (используется локальный индекс)",
                foreground="#ffb900"
            )
    
    def _test_search(self) -> None:
        """Тестовый поиск."""
        query = self.test_query_var.get()
        top_k = int(self.top_k_var.get())
        
        self.log_label.configure(text=f"Поиск: {query}", foreground="#0078d4")
        
        try:
            from gui_debugger.utils.async_helper import async_helper
            
            if self.rag_pipeline:
                results = async_helper.run_async(self.rag_pipeline._search_chunks(query))
                
                # Отображение результатов
                self.results_area.delete(1.0, tk.END)
                
                if results:
                    self.results_area.insert(tk.END, f"Найдено чанков: {len(results)}\n\n")
                    
                    for i, result in enumerate(results, 1):
                        chunk_info = (
                            f"[{i}] Score: {result.get('score', 0):.3f}\n"
                            f"    Тема: {result.get('topic', 'unknown')}\n"
                            f"    Type: {result.get('search_type', 'unknown')}\n"
                            f"    Текст: {result.get('text', '')[:200]}...\n\n"
                        )
                        self.results_area.insert(tk.END, chunk_info)
                    
                    self.log_label.configure(text=f"✅ Успешно найдено: {len(results)}", foreground="#107c10")
                else:
                    self.results_area.insert(tk.END, "Ничего не найдено\n")
                    self.log_label.configure(text="⚠️ Ничего не найдено", foreground="#ffb900")
            else:
                self.results_area.insert(tk.END, "RAG-пайплайн не инициализирован\n")
                
        except Exception as e:
            self.results_area.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log_label.configure(text=f"❌ Ошибка: {str(e)}", foreground="#e81123")
    
    def clear_results(self) -> None:
        """Очистка результатов."""
        self.results_area.delete(1.0, tk.END)
