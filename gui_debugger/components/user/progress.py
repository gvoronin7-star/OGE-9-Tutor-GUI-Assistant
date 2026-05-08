# -*- coding: utf-8 -*-
"""
Панель прогресса пользователя.

Отслеживание статистики подготовки к ОГЭ.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime


class ProgressPanel(ttk.Frame):
    """Панель прогресса."""
    
    def __init__(
        self,
        parent: tk.Widget,
        user_data: Optional[Dict[str, Any]] = None,
        on_back: Optional[Callable] = None
    ) -> None:
        """
        Инициализация панели прогресса.
        
        Args:
            parent: Родительский виджет
            user_data: Данные пользователя
            on_back: Callback для кнопки "Назад"
        """
        super().__init__(parent)
        self.user_data = user_data or self._get_default_data()
        self.on_back = on_back
        
        self._create_widgets()
        self._update_display()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Данные по умолчанию."""
        return {
            "user_id": 999999,
            "name": "Ученик",
            "started_at": datetime.now().strftime("%d.%m.%Y"),
            "progress": {
                "topics_studied": 0,
                "topics_completed": [],
                "tests_completed": 0,
                "tests_passed": [],
                "total_questions": 0,
                "correct_answers": 0,
                "accuracy": 0
            },
            "history": []
        }
    
    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=10)
        
        back_btn = ttk.Button(
            header,
            text="🔙 Назад",
            command=self.on_back,
            width=15
        )
        back_btn.pack(side=tk.LEFT, padx=10)
        
        title = ttk.Label(
            header,
            text="📊 ПРОГРЕСС ПОДГОТОВКИ",
            font=("Segoe UI", 14, "bold"),
            foreground="#0078d4"
        )
        title.pack()
        
        # Основная статистика
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Карточки статистики - сохраняем ссылки на value_label
        self.topics_card_value = None
        self.tests_card_value = None
        self.accuracy_card_value = None
        self.grade_card_value = None
        
        # Карточка 1: Темы
        topics_card = self._create_stat_card(
            self.stats_frame,
            "📚 Тем изучено",
            "0 / 6"
        )
        topics_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.topics_card_value = topics_card.winfo_children()[1]
        
        # Карточка 2: Тесты
        tests_card = self._create_stat_card(
            self.stats_frame,
            "✍️ Тестов пройдено",
            "0"
        )
        tests_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.tests_card_value = tests_card.winfo_children()[1]
        
        # Карточка 3: Точность
        accuracy_card = self._create_stat_card(
            self.stats_frame,
            "✅ Точность",
            "0%"
        )
        accuracy_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.accuracy_card_value = accuracy_card.winfo_children()[1]
        
        # Карточка 4: Оценка
        grade_card = self._create_stat_card(
            self.stats_frame,
            "🏆 Оценка",
            "—"
        )
        grade_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        self.grade_card_value = grade_card.winfo_children()[1]
        
        self.stats_frame.columnconfigure(0, weight=1)
        self.stats_frame.columnconfigure(1, weight=1)
        self.stats_frame.columnconfigure(2, weight=1)
        self.stats_frame.columnconfigure(3, weight=1)
        
        # Прогресс по темам
        topics_progress_frame = ttk.LabelFrame(self, text="Прогресс по темам", padding=10)
        topics_progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.topics_list = []
        topics = [
            "Человек и общество",
            "Сфера духовной культуры",
            "Экономика",
            "Социальная сфера",
            "Политика",
            "Право"
        ]
        
        for i, topic in enumerate(topics):
            frame = ttk.Frame(topics_progress_frame)
            frame.pack(fill=tk.X, pady=2)
            
            label = ttk.Label(frame, text=topic, width=30, anchor=tk.W)
            label.pack(side=tk.LEFT)
            
            progress_bar = ttk.Progressbar(
                frame,
                orient=tk.HORIZONTAL,
                length=300,
                mode='determinate'
            )
            progress_bar.pack(side=tk.LEFT, padx=10)
            
            status = ttk.Label(frame, text="Не начата", width=15)
            status.pack(side=tk.LEFT)
            
            self.topics_list.append({
                "topic": topic,
                "label": label,
                "bar": progress_bar,
                "status": status
            })
        
        # История
        history_frame = ttk.LabelFrame(self, text="История занятий", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.history_text = tk.Text(
            history_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            height=10
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        export_btn = ttk.Button(btn_frame, text="📤 Экспорт", command=self._export_progress)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = ttk.Button(btn_frame, text="🗑️ Сброс", command=self._reset_progress)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(btn_frame, text="🔄 Обновить", command=self._update_display)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_stat_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str
    ) -> ttk.Frame:
        """Создание карточки статистики."""
        card = ttk.Frame(parent, padding=15)
        card.configure(relief="raised", borderwidth=1)
        
        title_label = ttk.Label(
            card,
            text=title,
            font=("Segoe UI", 9),
            foreground="#808080"
        )
        title_label.pack(anchor=tk.W)
        
        value_label = ttk.Label(
            card,
            text=value,
            font=("Segoe UI", 16, "bold"),
            foreground="#303030"
        )
        value_label.pack(anchor=tk.W)
        
        return card
    
    def _update_display(self) -> None:
        """Обновление отображения."""
        progress = self.user_data.get("progress", {})
        
        # Обновление карточек через сохранённые ссылки
        if self.topics_card_value:
            topics_studied = progress.get("topics_studied", 0)
            self.topics_card_value.configure(text=f"{topics_studied} / 6")
        
        if self.tests_card_value:
            tests_completed = progress.get("tests_completed", 0)
            self.tests_card_value.configure(text=str(tests_completed))
        
        if self.accuracy_card_value:
            accuracy = progress.get("accuracy", 0)
            self.accuracy_card_value.configure(text=f"{accuracy:.0f}%")
        
        if self.grade_card_value:
            accuracy = progress.get("accuracy", 0)
            if accuracy >= 80:
                grade = "5.0"
            elif accuracy >= 50:
                grade = "4.0"
            elif accuracy > 0:
                grade = "3.0"
            else:
                grade = "—"
            self.grade_card_value.configure(text=grade)
        
        # Прогресс по темам
        completed_topics = progress.get("topics_completed", [])
        for i, item in enumerate(self.topics_list):
            topic = item["topic"]
            if topic in completed_topics:
                item["bar"].configure(value=100)
                item["status"].configure(text="✅ Изучена", foreground="#107c10")
            else:
                item["bar"].configure(value=0)
                item["status"].configure(text="Не начата", foreground="#808080")
        
        # История
        self.history_text.delete(1.0, tk.END)
        history = self.user_data.get("history", [])
        
        if history:
            for record in history[-10:]:  # Последние 10 записей
                date = record.get("date", "Неизвестно")
                action = record.get("action", "")
                result = record.get("result", "")
                self.history_text.insert(tk.END, f"[{date}] {action}: {result}\n")
        else:
            self.history_text.insert(tk.END, "История пуста. Начните заниматься!\n")
    
    def add_topic(self, topic: str) -> None:
        """
        Добавление изученной темы.
        
        Args:
            topic: Название темы
        """
        progress = self.user_data.get("progress", {})
        
        if topic not in progress.get("topics_completed", []):
            progress.setdefault("topics_completed", []).append(topic)
            progress["topics_studied"] = len(progress["topics_completed"])
        
        # Добавление в историю
        self.user_data.setdefault("history", []).append({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "action": "Изучена тема",
            "result": topic
        })
        
        self._update_display()
    
    def add_test_result(self, topic: str, score: int, total: int) -> None:
        """
        Добавление результата теста.
        
        Args:
            topic: Тема теста
            score: Количество правильных ответов
            total: Всего вопросов
        """
        progress = self.user_data.get("progress", {})
        
        progress["tests_completed"] = progress.get("tests_completed", 0) + 1
        progress["total_questions"] = progress.get("total_questions", 0) + total
        progress["correct_answers"] = progress.get("correct_answers", 0) + score
        
        # Пересчёт точности
        if progress["total_questions"] > 0:
            progress["accuracy"] = (progress["correct_answers"] / progress["total_questions"]) * 100
        
        # Добавление в историю
        percentage = (score / total) * 100
        self.user_data.setdefault("history", []).append({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "action": f"Тест: {topic}",
            "result": f"{score}/{total} ({percentage:.0f}%)"
        })
        
        self._update_display()
    
    def _export_progress(self) -> None:
        """Экспорт прогресса."""
        # Копирование в буфер
        progress = self.user_data.get("progress", {})
        
        export_text = (
            f"ПРОГРЕСС ПОДГОТОВКИ - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"{'='*50}\n"
            f"Тем изучено: {progress.get('topics_studied', 0)} / 6\n"
            f"Тестов пройдено: {progress.get('tests_completed', 0)}\n"
            f"Точность: {progress.get('accuracy', 0):.1f}%\n"
            f"Всего вопросов: {progress.get('total_questions', 0)}\n"
            f"Правильных ответов: {progress.get('correct_answers', 0)}\n"
        )
        
        self.clipboard_clear()
        self.clipboard_append(export_text)
        
        # Уведомление
        self.history_text.insert(tk.END, "\n✅ Прогресс скопирован в буфер обмена\n")
    
    def _reset_progress(self) -> None:
        """Сброс прогресса."""
        if messagebox.askyesno("Сброс прогресса", "Вы уверены? Это действие нельзя отменить."):
            self.user_data = self._get_default_data()
            self._update_display()
            self.history_text.insert(tk.END, "\n✅ Прогресс сброшен\n")
