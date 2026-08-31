# -*- coding: utf-8 -*-
"""
Панель решения тестов v2.0.

Улучшения:
- Таймер (секундомер)
- Подсветка ответов (зелёный/красный)
- Автопереход к следующему вопросу
- Предзагрузка тестов
- Индикация количества доступных тестов
"""

import functools
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable, Dict, List, Optional, cast

from gui_debugger.utils.gui_logger import gui_action_logger, log_action, log_error


class TestSolver(ttk.Frame):
    """Панель решения тестов."""

    TOPICS = [
        "Человек и общество",
        "Сфера духовной культуры",
        "Экономика",
        "Социальная сфера",
        "Политика",
        "Право",
    ]

    def __init__(
        self,
        parent: tk.Widget,
        test_generator: Any = None,
        on_back: Optional[Callable] = None,
        on_test_complete: Optional[Callable] = None,
    ) -> None:
        """
        Инициализация панели тестов.

        Args:
            parent: Родительский виджет
            test_generator: Генератор тестов
            on_back: Callback для кнопки "Назад"
            on_test_complete: Callback при завершении теста
        """
        super().__init__(parent)
        self.test_generator = test_generator
        self.on_back = on_back
        self.on_test_complete = on_test_complete

        self.current_test: Optional[Dict[str, Any]] = None
        self.current_question_index = 0
        self.user_answers: List[int] = []
        self.score = 0

        # Таймер
        self.start_time: float = 0
        self.timer_running = False
        self.elapsed_time: float = 0
        self.timer_job: Optional[str] = None
        self.auto_advance_job: Optional[str] = None

        # Предзагруженные тесты
        self.preloaded_tests: Dict[str, Dict] = {}
        self.available_tests_count: Dict[str, int] = {}

        # Текущий тест и вопрос
        self.current_test = None
        self.current_question_index = 0
        self.current_question_data: Optional[Dict[str, Any]] = None
        self.user_answers = []
        self.score = 0

        self._create_widgets()
        self._update_available_count()

    def _create_widgets(self) -> None:
        """Создание виджетов."""
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=10)

        back_btn = ttk.Button(
            header,
            text="🔙 Назад",
            command=cast(Callable[[], Any], self.on_back),
            width=15,
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        title = ttk.Label(
            header,
            text="✍️ РЕШЕНИЕ ТЕСТОВ",
            font=("Segoe UI", 14, "bold"),
            foreground="#0078d4",
        )
        title.pack()

        # Разделитель
        ttk.Separator(header, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)

        # Панель выбора режима
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill=tk.X, padx=20, pady=10)

        # Режим 1: По теме
        ttk.Label(mode_frame, text="По теме:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, padx=10, pady=5
        )

        # Выбор темы
        ttk.Label(mode_frame, text="Тема:", font=("Segoe UI", 9)).grid(
            row=1, column=0, padx=5, pady=5
        )
        self.topic_var = tk.StringVar(value=self.TOPICS[0])
        topic_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.topic_var,
            values=self.TOPICS,
            state="readonly",
            width=25,
        )
        topic_combo.grid(row=1, column=1, padx=5, pady=5)
        topic_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._update_available_count()
        )

        # Информация о доступных вопросах
        self.available_count_label = ttk.Label(
            mode_frame,
            text="📊 Доступно: -- вопросов",
            font=("Segoe UI", 9),
            foreground="#808080",
        )
        self.available_count_label.grid(row=1, column=2, padx=15, pady=5)

        # Кнопка начала теста по теме
        start_btn = ttk.Button(
            mode_frame,
            text="▶️ Начать тест",
            command=self._start_test,
            style="Accent.TButton",
        )
        start_btn.grid(row=1, column=3, padx=20, pady=5)

        # Разделитель
        ttk.Separator(mode_frame, orient=tk.VERTICAL).grid(
            row=1, column=4, rowspan=2, padx=20
        )

        # Режим 2: Все темы
        ttk.Label(mode_frame, text="Все темы:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=5, padx=10, pady=5
        )

        # Индикация общего количества вопросов
        self.all_questions_count_label = ttk.Label(
            mode_frame,
            text="📚 Всего: -- вопросов",
            font=("Segoe UI", 9),
            foreground="#0078d4",
        )
        self.all_questions_count_label.grid(row=1, column=5, padx=10, pady=5)

        # Выбор количества вопросов
        ttk.Label(mode_frame, text="Количество:", font=("Segoe UI", 9)).grid(
            row=2, column=5, padx=10, pady=5
        )
        self.num_questions_var = tk.StringVar(value="10")
        num_questions_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.num_questions_var,
            values=["5", "10", "15", "20", "21"],
            state="readonly",
            width=10,
        )
        num_questions_combo.grid(row=2, column=6, padx=5, pady=5)

        # Кнопка теста по всем темам
        all_topics_btn = ttk.Button(
            mode_frame,
            text="🎲 Тест по всем темам",
            command=self._start_all_topics_test,
            style="Accent.TButton",
        )
        all_topics_btn.grid(row=3, column=5, columnspan=2, padx=20, pady=10)

        # Область вопроса
        question_frame = ttk.LabelFrame(self, text="Вопрос", padding=10)
        question_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Таймер
        timer_frame = ttk.Frame(question_frame)
        timer_frame.pack(fill=tk.X, pady=(0, 10))

        self.timer_label = ttk.Label(
            timer_frame,
            text="⏱️ Время: 0:00",
            font=("Segoe UI", 11, "bold"),
            foreground="#0078d4",
        )
        self.timer_label.pack(side=tk.RIGHT)

        self.question_num_label = ttk.Label(
            timer_frame,
            text="Вопрос 0 / 0",
            font=("Segoe UI", 10),
            foreground="#808080",
        )
        self.question_num_label.pack(side=tk.LEFT)

        self.question_label = ttk.Label(
            question_frame,
            text="Выберите тему и нажмите «Начать тест»",
            font=("Segoe UI", 11),
            foreground="#303030",
            wraplength=800,
            justify=tk.CENTER,
        )
        self.question_label.pack(pady=20)

        # Варианты ответов
        self.answers_frame = ttk.Frame(question_frame)
        self.answers_frame.pack(fill=tk.X, pady=10)

        self.answer_buttons = []
        for i in range(4):
            btn = ttk.Button(
                self.answers_frame,
                text=f"Вариант {chr(65+i)}",
                command=functools.partial(self._select_answer, i),
                width=40,
            )
            btn.pack(fill=tk.X, pady=3)
            self.answer_buttons.append(btn)

        # Статус ответа
        self.answer_status_label = ttk.Label(
            question_frame, text="", font=("Segoe UI", 10), wraplength=800
        )
        self.answer_status_label.pack(pady=10)

        # Кнопки навигации убраны - используется автопереход
        # self.next_btn и skip_btn удалены

        # Результат
        self.result_frame = ttk.LabelFrame(self, text="Результат", padding=10)
        self.result_frame.pack(fill=tk.X, padx=20, pady=10)

        self.result_label = ttk.Label(
            self.result_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            foreground="#303030",
        )
        self.result_label.pack()

        self.result_details = ttk.Label(
            self.result_frame, text="", font=("Segoe UI", 10), foreground="#808080"
        )
        self.result_details.pack()

        self.time_result_label = ttk.Label(
            self.result_frame, text="", font=("Segoe UI", 9), foreground="#0078d4"
        )
        self.time_result_label.pack()

        # Скрыть результат изначально
        self.result_frame.pack_forget()

        # Статус
        self.status_label = ttk.Label(self, text="", foreground="#808080")
        self.status_label.pack(pady=5)

        # Индикатор загрузки тестов (изначально пустой)
        self.loading_label = ttk.Label(
            self, text="", font=("Segoe UI", 10), foreground="#0078d4"
        )
        self.loading_label.pack(pady=5)

    def _update_all_questions_count(self) -> None:
        """Обновление общего количества вопросов по всем темам."""
        # Реальное общее количество: 5+5+5+2+2+2 = 21
        total = 21

        self.all_questions_count_label.configure(
            text=f"📚 Всего: {total} вопросов",
            foreground="#107c10" if total > 0 else "#808080",
        )

    def _update_available_count(self) -> None:
        """Обновление счётчика доступных вопросов."""
        topic = self.topic_var.get()

        # Реальное количество демо-вопросов по каждой теме из test_generator.py
        # "человек и общество": 5 вопросов
        # "экономика": 5 вопросов
        # "право": 5 вопросов
        # "политика": 2 вопроса (из _get_demo_questions_by_topic)
        # "социальная сфера": 2 вопроса
        # "сфера духовной культуры": 2 вопроса

        topic_counts = {
            "Человек и общество": 5,
            "Экономика": 5,
            "Право": 5,
            "Политика": 2,
            "Социальная сфера": 2,
            "Сфера духовной культуры": 2,
        }

        total_questions = topic_counts.get(topic, 0)

        # Обновление индикатора
        if total_questions > 0:
            self.available_count_label.configure(
                text=f"📊 Доступно: {total_questions} вопросов", foreground="#107c10"
            )
        else:
            self.available_count_label.configure(
                text="📊 Доступно: 0 вопросов", foreground="#e81123"
            )

        # Обновление общего количества
        self._update_all_questions_count()

    def _start_test(self) -> None:
        """Начало теста по теме."""
        topic = self.topic_var.get()

        # Логирование начала теста
        gui_action_logger.log_test_start(topic, "mixed", 5)

        # Индикатор загрузки
        self.loading_label.configure(text="⏳ Загрузка тестов...")
        self.status_label.configure(text=f"Генерация теста: {topic}")

        if self.test_generator:
            self._generate_test_async(topic)
        else:
            self._use_demo_test(topic)

    def _start_all_topics_test(self) -> None:
        """Начало теста по всем темам (случайная выборка)."""
        # Получаем выбранное количество вопросов
        try:
            num_questions = int(self.num_questions_var.get())
        except ValueError:
            num_questions = 10

        self.status_label.configure(
            text=f"⏳ Генерация теста по всем темам ({num_questions} вопросов)..."
        )

        if self.test_generator:
            self._generate_all_topics_test_async(num_questions)
        else:
            self._use_demo_all_topics_test(num_questions)

    def _start_timer(self) -> None:
        """Запуск таймера."""
        self.start_time = time.time()
        self.elapsed_time = 0
        self.timer_running = True
        self._update_timer()

    def _stop_timer(self) -> None:
        """Остановка таймера."""
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def cleanup(self) -> None:
        """
        Отмена всех отложенных `after()`-колбэков перед уничтожением панели.

        Без этого выход из теста ("Назад") посреди прохождения оставляет
        висящий таймер и/или автопереход к следующему вопросу, которые
        стреляют уже после `destroy()` — `_tkinter.TclError: invalid
        command name`.
        """
        self._stop_timer()
        if self.auto_advance_job:
            self.after_cancel(self.auto_advance_job)
            self.auto_advance_job = None

    def _update_timer(self) -> None:
        """Обновление таймера."""
        if not self.timer_running:
            return

        self.elapsed_time = time.time() - self.start_time
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        self.timer_label.configure(text=f"⏱️ Время: {minutes}:{seconds:02d}")

        self.timer_job = self.after(100, self._update_timer)

    def _generate_test_async(self, topic: str) -> None:
        """Асинхронная генерация теста (без блокировки GUI)."""
        from gui_debugger.utils.async_helper import async_helper

        self.loading_label.configure(text="⏳ Загрузка тестов...")

        def on_success(test: Optional[Dict[str, Any]]) -> None:
            self.loading_label.configure(text="")
            if test and "error" not in test:
                self._load_test(test)
            else:
                messagebox.showerror(
                    "Ошибка",
                    (test or {}).get("error", "Не удалось сгенерировать тест"),
                )
                self._use_demo_test(topic)

        def on_error(e: BaseException) -> None:
            self.loading_label.configure(text="")
            messagebox.showerror("Ошибка", f"Ошибка генерации: {str(e)}")
            self._use_demo_test(topic)

        async_helper.run_async_in_background(
            self,
            self.test_generator.generate_test(topic, "mixed", num_questions=5),
            on_success,
            on_error,
        )

    def _generate_all_topics_test_async(self, num_questions: int = 10) -> None:
        """Асинхронная генерация теста по всем темам (без блокировки GUI)."""
        from gui_debugger.utils.async_helper import async_helper

        self.loading_label.configure(text="⏳ Загрузка тестов...")

        def on_success(test: Optional[Dict[str, Any]]) -> None:
            self.loading_label.configure(text="")
            if test and "error" not in test:
                self._load_test(test)
            else:
                messagebox.showerror(
                    "Ошибка",
                    (test or {}).get("error", "Не удалось сгенерировать тест"),
                )
                self._use_demo_all_topics_test(num_questions)

        def on_error(e: BaseException) -> None:
            self.loading_label.configure(text="")
            messagebox.showerror("Ошибка", f"Ошибка генерации: {str(e)}")
            self._use_demo_all_topics_test(num_questions)

        async_helper.run_async_in_background(
            self,
            self.test_generator.generate_all_topics_test(num_questions=num_questions),
            on_success,
            on_error,
        )

    def _use_demo_test(self, topic: str) -> None:
        """Использование демо-теста по теме."""
        demo_test: Dict[str, Any] = {
            "test_id": f"demo_{topic}",
            "topic": topic,
            "difficulty": "mixed",
            "questions": {
                "q_0": {
                    "question": f"Что изучает {topic.lower()}?",
                    "answers": [
                        "Вариант А - Неверный",
                        "Вариант Б - Верный",
                        "Вариант В - Неверный",
                        "Вариант Г - Неверный",
                    ],
                    "correct_answer": 1,
                    "explanation": f"Это демонстрационный вопрос по теме: {topic}",
                    "difficulty": "medium",
                },
                "q_1": {
                    "question": "Какой термин относится к теме?",
                    "answers": ["Термин 1", "Термин 2", "Термин 3", "Термин 4"],
                    "correct_answer": 0,
                    "explanation": "Термин 1 наиболее точно отражает суть темы.",
                    "difficulty": "easy",
                },
                "q_2": {
                    "question": "Что верно для этой темы?",
                    "answers": [
                        "Утверждение А",
                        "Утверждение Б",
                        "Утверждение В",
                        "Утверждение Г",
                    ],
                    "correct_answer": 2,
                    "explanation": "Утверждение В является правильным.",
                    "difficulty": "medium",
                },
                "q_3": {
                    "question": "Какой пример иллюстрирует тему?",
                    "answers": ["Пример 1", "Пример 2", "Пример 3", "Пример 4"],
                    "correct_answer": 1,
                    "explanation": "Пример 2 лучше всего подходит.",
                    "difficulty": "hard",
                },
                "q_4": {
                    "question": "Что следует из темы?",
                    "answers": ["Вывод А", "Вывод Б", "Вывод В", "Вывод Г"],
                    "correct_answer": 3,
                    "explanation": "Вывод Г логически следует.",
                    "difficulty": "medium",
                },
            },
            "total_questions": 5,
        }

        self._load_test(demo_test)

    def _shuffle_answers(self, question: Dict) -> Dict:
        """
        Перемешивание ответов в вопросе.

        Args:
            question: Вопрос с ответами

        Returns:
            Dict: Вопрос с перемешанными ответами
        """
        import random
        import time

        # Инициализация генератора случайных чисел текущим временем
        # для лучшей случайности при каждом запуске
        random.seed(time.time() * 1000)

        answers = question.get("answers", [])
        correct_idx = question.get("correct_answer", 0)

        if len(answers) < 2:
            return question  # Нечего перемешивать

        # Создаём список (ответ, является_ли_правильным)
        answer_list = [(ans, i == correct_idx) for i, ans in enumerate(answers)]

        # Перемешиваем
        random.shuffle(answer_list)

        # Извлекаем перемешанные ответы и новый индекс правильного
        shuffled_answers = [ans for ans, _ in answer_list]
        new_correct_idx = next(
            i for i, (_, is_correct) in enumerate(answer_list) if is_correct
        )

        question["answers"] = shuffled_answers
        question["correct_answer"] = new_correct_idx

        return question

    def _use_demo_all_topics_test(self, num_questions: int = 10) -> None:
        """Использование демо-теста по всем темам."""
        demo_test: Dict[str, Any] = {
            "test_id": "demo_all_topics",
            "topic": "Все темы",
            "difficulty": "mixed",
            "questions": {
                "q_0": {
                    "question": "Что такое общество?",
                    "answers": [
                        "Совокупность людей",
                        "Группа животных",
                        "Компьютерная сеть",
                        "Государство",
                    ],
                    "correct_answer": 0,
                    "explanation": "Общество — это совокупность людей с общими интересами.",
                    "difficulty": "easy",
                    "topic": "Человек и общество",
                },
                "q_1": {
                    "question": "Что изучает экономика?",
                    "answers": [
                        "Производство товаров",
                        "Природу",
                        "Историю",
                        "Психологию",
                    ],
                    "correct_answer": 0,
                    "explanation": "Экономика изучает производство и потребление.",
                    "difficulty": "easy",
                    "topic": "Экономика",
                },
                "q_2": {
                    "question": "Какой закон главный в России?",
                    "answers": [
                        "Конституция",
                        "Гражданский кодекс",
                        "Уголовный кодекс",
                        "ФЗ",
                    ],
                    "correct_answer": 0,
                    "explanation": "Конституция РФ — главный закон страны.",
                    "difficulty": "easy",
                    "topic": "Право",
                },
                "q_3": {
                    "question": "Что такое инфляция?",
                    "answers": [
                        "Рост цен",
                        "Падение цен",
                        "Увеличение производства",
                        "Снижение безработицы",
                    ],
                    "correct_answer": 0,
                    "explanation": "Инфляция — это рост общего уровня цен.",
                    "difficulty": "medium",
                    "topic": "Экономика",
                },
                "q_4": {
                    "question": "Какие функции выполняют деньги?",
                    "answers": [
                        "Мера стоимости, средство платежа",
                        "Только обмен",
                        "Только накопление",
                        "Только платёж",
                    ],
                    "correct_answer": 0,
                    "explanation": "Деньги выполняют 3 функции: мера стоимости, средство платежа, накопления.",
                    "difficulty": "medium",
                    "topic": "Экономика",
                },
                "q_5": {
                    "question": "Что такое социализация?",
                    "answers": ["Усвоение норм", "Обучение в школе", "Работа", "Отдых"],
                    "correct_answer": 0,
                    "explanation": "Социализация — усвоение социальных норм и ценностей.",
                    "difficulty": "easy",
                    "topic": "Человек и общество",
                },
                "q_6": {
                    "question": "Какая власть исполнительная?",
                    "answers": ["Правительство", "Госдума", "Суд", "Президент"],
                    "correct_answer": 0,
                    "explanation": "Правительство — орган исполнительной власти.",
                    "difficulty": "medium",
                    "topic": "Политика",
                },
                "q_7": {
                    "question": "Что такое культура?",
                    "answers": [
                        "Духовные и материальные ценности",
                        "Только искусство",
                        "Только наука",
                        "Только религия",
                    ],
                    "correct_answer": 0,
                    "explanation": "Культура включает духовные и материальные ценности.",
                    "difficulty": "medium",
                    "topic": "Сфера духовной культуры",
                },
                "q_8": {
                    "question": "Какой возраст совершеннолетия в РФ?",
                    "answers": ["18 лет", "16 лет", "21 год", "14 лет"],
                    "correct_answer": 0,
                    "explanation": "Совершеннолетие наступает в 18 лет.",
                    "difficulty": "easy",
                    "topic": "Право",
                },
                "q_9": {
                    "question": "Что такое безработица?",
                    "answers": [
                        "Отсутствие работы у трудоспособных",
                        "Отсутствие работы у всех",
                        "Декрет",
                        "Учеба",
                    ],
                    "correct_answer": 0,
                    "explanation": "Безработица — отсутствие работы у экономически активного населения.",
                    "difficulty": "medium",
                    "topic": "Экономика",
                },
            },
            "total_questions": 10,
        }

        # Обрезаем до выбранного количества вопросов
        if num_questions != 10:
            # Получаем первые num_questions вопросов
            questions = dict(list(demo_test["questions"].items())[:num_questions])
            demo_test["questions"] = questions
            demo_test["total_questions"] = num_questions

        # Перемешиваем ответы для каждого вопроса
        for q_key in demo_test["questions"]:
            demo_test["questions"][q_key] = self._shuffle_answers(
                demo_test["questions"][q_key]
            )

        self._load_test(demo_test)

    def _load_test(self, test: Dict[str, Any]) -> None:
        """
        Загрузка теста.

        Args:
            test: Данные теста
        """
        self.current_test = test
        self.current_question_index = 0
        self.user_answers = []
        self.score = 0

        # Скрытие результата и индикатора
        self.result_frame.pack_forget()
        self.loading_label.configure(text="")
        self.status_label.configure(
            text=f"✅ Тест загружен: {test['total_questions']} вопросов"
        )

        # Запуск таймера
        self._start_timer()

        # Отображение первого вопроса
        self._show_question(0)

    def _show_question(self, index: int) -> None:
        """
        Показ вопроса.

        Args:
            index: Индекс вопроса
        """
        if not self.current_test:
            return

        questions = self.current_test.get("questions", {})
        question_key = f"q_{index}"

        if question_key not in questions:
            return

        q = questions[question_key]

        # Определение эмодзи сложности
        difficulty = q.get("difficulty", self.current_test.get("difficulty", "medium"))
        diff_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(difficulty, "⚪")

        # Определение темы вопроса (если есть)
        question_topic = q.get("topic", self.current_test.get("topic", ""))
        topic_indicator = f" [{question_topic}]" if question_topic else ""

        # Обновление вопроса с индикатором сложности и темы
        self.question_label.configure(
            text=f"{index + 1}. {diff_emoji}{topic_indicator} {q.get('question', 'Нет вопроса')}"
        )

        # Обновление кнопок ответов
        answers = q.get("answers", [])
        for i, btn in enumerate(self.answer_buttons):
            if i < len(answers):
                btn.configure(text=f"{chr(65+i)}) {answers[i]}", state=tk.NORMAL)
                # Сброс стиля
                btn.configure(style="TButton")
            else:
                btn.configure(text="", state=tk.DISABLED)

        # Обновление информации
        self.question_num_label.configure(
            text=f"Вопрос {index + 1} / {self.current_test['total_questions']}  |  {diff_emoji.upper()} {difficulty.upper()}"
        )

        # Сброс статуса
        self.answer_status_label.configure(text="")

        # Сохранение текущего вопроса для автоперехода
        self.current_question_data = q

        # Логирование показа вопроса
        log_action(
            "question_shown",
            {
                "question_num": index + 1,
                "topic": self.current_test.get("topic", ""),
                "difficulty": difficulty,
            },
        )

    def _select_answer(self, answer_index: int) -> None:
        """
        Выбор ответа с автопереходом.

        Args:
            answer_index: Индекс выбранного ответа
        """
        assert self.current_question_data is not None, "Вопрос не загружен"

        # Блокировка кнопок
        for btn in self.answer_buttons:
            btn.configure(state=tk.DISABLED)

        # Проверка ответа
        is_correct = answer_index == self.current_question_data.get("correct_answer")

        # Подсветка
        for i, btn in enumerate(self.answer_buttons):
            if i == answer_index:
                if is_correct:
                    btn.configure(style="success.TButton")
                else:
                    btn.configure(style="danger.TButton")
            elif i == self.current_question_data.get("correct_answer"):
                # Показываем правильный ответ если ошиблись
                btn.configure(style="success.TButton")

        # Статус
        if is_correct:
            self.answer_status_label.configure(
                text="✅ Верно! " + self.current_question_data.get("explanation", ""),
                foreground="#107c10",
            )
        else:
            self.answer_status_label.configure(
                text="❌ Неверно. " + self.current_question_data.get("explanation", ""),
                foreground="#d13438",
            )

        # Сохранение ответа
        self.user_answers.append(answer_index)
        self.score += 1 if is_correct else 0

        # Логирование ответа
        question_time = (
            time.time() - self.start_time if hasattr(self, "start_time") else 0
        )
        gui_action_logger.log_test_answer(
            self.current_question_index + 1, answer_index, is_correct, question_time
        )

        # Автопереход через 5 секунд (увеличено с 2 для удобства чтения)
        self.auto_advance_job = self.after(5000, self._next_question)

    def _next_question(self) -> None:
        """Переход к следующему вопросу."""
        assert self.current_test is not None, "Тест не загружен"

        # Переход к следующему
        self.current_question_index += 1

        if self.current_question_index < self.current_test["total_questions"]:
            self._show_question(self.current_question_index)
        else:
            self._finish_test()

    def _skip_question(self) -> None:
        """Пропуск вопроса."""
        self.user_answers.append(-1)  # -1 = пропущен
        self._next_question()

    def _finish_test(self) -> None:
        """Завершение теста."""
        assert self.current_test is not None, "Тест не загружен"

        # Остановка таймера
        self._stop_timer()

        total = self.current_test["total_questions"]
        percentage = (self.score / total) * 100 if total > 0 else 0

        # Определение оценки
        if percentage >= 80:
            grade = "5 (Отлично)"
            emoji = "🎉"
            message = "Прекрасный результат!"
        elif percentage >= 50:
            grade = "4 (Хорошо)"
            emoji = "💪"
            message = "Есть над чем работать"
        else:
            grade = "3 (Повторить)"
            emoji = "📚"
            message = "Советую повторить тему"

        # Отображение результата
        self.result_frame.pack(fill=tk.X, padx=20, pady=10)
        self.result_label.configure(
            text=f"{emoji} Результат: {self.score}/{total} ({percentage:.0f}%) - {grade}"
        )
        self.result_details.configure(text=f"{message} | Точность: {percentage:.1f}%")

        # Время теста
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        avg_time = self.elapsed_time / total if total > 0 else 0
        self.time_result_label.configure(
            text=f"⏱️ Время теста: {minutes} мин {seconds} сек | Среднее на вопрос: {avg_time:.1f} сек"
        )

        self.question_label.configure(text="Тест завершён!")
        for btn in self.answer_buttons:
            btn.configure(state=tk.DISABLED)

        self.status_label.configure(text=f"✅ Тест завершён: {self.score}/{total}")

        # Вызов callback при завершении теста
        if self.on_test_complete:
            self.on_test_complete(self.current_test.get("topic", ""), self.score, total)

        # Логирование завершения теста
        log_action(
            "test_completed",
            {
                "topic": self.current_test.get("topic", ""),
                "difficulty": self.current_test.get("difficulty", ""),
                "score": self.score,
                "total": total,
                "percentage": percentage,
                "time_sec": self.elapsed_time,
            },
        )
