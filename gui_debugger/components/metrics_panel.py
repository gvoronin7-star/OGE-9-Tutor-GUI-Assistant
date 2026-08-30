# -*- coding: utf-8 -*-
"""
Панель метрик и статистики.
"""

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from typing import Any, Optional


class MetricsPanel(ttk.Frame):
    """Панель метрик."""

    def __init__(self, parent: tk.Widget, rag_pipeline: Any) -> None:
        """
        Инициализация панели метрик.

        Args:
            parent: Родительский виджет
            rag_pipeline: RAG-пайплайн
        """
        super().__init__(parent)
        self.rag_pipeline = rag_pipeline
        self.request_times = []

        self._create_widgets()
        self._start_auto_refresh()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Label(self, text="📊 METRICS", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Карточки статистики
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # Запросов
        self.requests_card = self._create_stat_card(stats_frame, "Запросов", "0", 0, 0)
        self.requests_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Кэш
        self.cache_card = self._create_stat_card(stats_frame, "Кэш", "0 (0%)", 0, 1)
        self.cache_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Ошибок
        self.errors_card = self._create_stat_card(stats_frame, "Ошибок", "0", 0, 2)
        self.errors_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        # Время ответа
        self.time_card = self._create_stat_card(
            stats_frame, "Время ответа", "~0с", 0, 3
        )
        self.time_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)

        # Детальная статистика
        detail_frame = ttk.LabelFrame(self, text="Детальная статистика", padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.detail_text = tk.Text(
            detail_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            height=15,
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        refresh_btn = ttk.Button(
            btn_frame, text="🔄 Обновить", command=self._refresh_metrics
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        export_btn = ttk.Button(
            btn_frame, text="📤 Экспорт", command=self._export_metrics
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Button(btn_frame, text="🗑️ Сброс", command=self._reset_metrics)
        reset_btn.pack(side=tk.LEFT, padx=5)

        # Автообновление
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(
            btn_frame, text="Автообновление (10с)", variable=self.auto_refresh_var
        )
        auto_refresh_check.pack(side=tk.RIGHT, padx=5)

    def _create_stat_card(
        self, parent: tk.Widget, title: str, value: str, row: int, col: int
    ) -> ttk.Frame:
        """Создание карточки статистики."""
        card = ttk.Frame(parent, padding=10)
        card.configure(relief="raised", borderwidth=1)

        title_label = ttk.Label(
            card, text=title, font=("Segoe UI", 9), foreground="#606060"
        )
        title_label.pack(anchor=tk.W)

        value_label = ttk.Label(
            card, text=value, font=("Segoe UI", 16, "bold"), foreground="#303030"
        )
        value_label.pack(anchor=tk.W)

        return card

    def _refresh_metrics(self) -> None:
        """Обновление метрик."""
        if not self.rag_pipeline:
            return

        try:
            metrics = self.rag_pipeline.get_metrics()

            # Обновление карточек
            total = metrics.get("rag_total_requests", 0)
            cache_hits = metrics.get("rag_cache_hits", 0)
            cache_rate = metrics.get("rag_cache_hit_rate", 0)
            errors = metrics.get("rag_errors", 0)
            avg_time = metrics.get("rag_avg_response_time", 0)

            self.requests_card.winfo_children()[1].configure(text=str(total))
            self.cache_card.winfo_children()[1].configure(
                text=f"{cache_hits} ({cache_rate:.1f}%)"
            )
            self.errors_card.winfo_children()[1].configure(text=str(errors))
            self.time_card.winfo_children()[1].configure(text=f"~{avg_time:.2f}с")

            # Детальная статистика
            self.detail_text.delete(1.0, tk.END)

            detail = (
                f"=== Метрики RAG-пайплайна ===\n"
                f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Запросов всего: {total}\n"
                f"Попаданий в кэш: {cache_hits}\n"
                f"Cache Hit Rate: {cache_rate:.1f}%\n"
                f"Ошибок: {errors}\n"
                f"Среднее время ответа: {avg_time:.3f}с\n\n"
            )

            if self.rag_pipeline.use_existing:
                stats = (
                    self.rag_pipeline.existing_store.get_stats()
                    if self.rag_pipeline.existing_store
                    else {}
                )
                detail += (
                    f"=== RAG_data_base ===\n"
                    f"Чанков: {stats.get('total_chunks', 0)}\n"
                    f"Векторов: {stats.get('total_vectors', 0)}\n"
                    f"Модель: {stats.get('model', 'unknown')}\n"
                )

            self.detail_text.insert(tk.END, detail)

            # Сохранение истории
            self.request_times.append((datetime.now(), avg_time))
            if len(self.request_times) > 100:
                self.request_times.pop(0)

        except Exception as e:
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, f"Ошибка обновления метрик: {str(e)}\n")

    def _export_metrics(self) -> None:
        """Экспорт метрик."""
        if not self.rag_pipeline:
            return

        try:
            metrics = self.rag_pipeline.get_metrics()

            export_text = (
                f"METRICS EXPORT - {datetime.now().isoformat()}\n"
                f"{'='*50}\n"
                f"Total Requests: {metrics.get('rag_total_requests', 0)}\n"
                f"Cache Hits: {metrics.get('rag_cache_hits', 0)}\n"
                f"Cache Hit Rate: {metrics.get('rag_cache_hit_rate', 0):.2f}%\n"
                f"Errors: {metrics.get('rag_errors', 0)}\n"
                f"Avg Response Time: {metrics.get('rag_avg_response_time', 0):.3f}s\n"
            )

            # Копирование в буфер
            self.clipboard_clear()
            self.clipboard_append(export_text)

            # Уведомление
            self.detail_text.insert(tk.END, "\n✅ Метрики скопированы в буфер обмена\n")

        except Exception as e:
            self.detail_text.insert(tk.END, f"\n❌ Ошибка экспорта: {str(e)}\n")

    def _reset_metrics(self) -> None:
        """Сброс метрик."""
        if self.rag_pipeline:
            self.rag_pipeline.metrics = {
                "total_requests": 0,
                "cache_hits": 0,
                "avg_response_time": 0.0,
                "errors": 0,
            }
            self.request_times = []
            self._refresh_metrics()
            self.detail_text.insert(tk.END, "\n✅ Метрики сброшены\n")

    def _start_auto_refresh(self) -> None:
        """Запуск автообновления."""
        self._refresh_metrics()
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        """Планирование следующего обновления."""
        if self.auto_refresh_var.get():
            self.after(10000, self._refresh_and_schedule)

    def _refresh_and_schedule(self) -> None:
        """Обновление и планирование."""
        self._refresh_metrics()
        self._schedule_refresh()
