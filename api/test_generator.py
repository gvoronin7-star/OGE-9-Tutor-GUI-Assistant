# -*- coding: utf-8 -*-
"""
Генератор тестов для ОГЭ.

Создаёт тестовые задания на основе базы знаний.

Автор: KODA
Дата: Март 2026
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.rag_pipeline import RAGPipeline


logger = logging.getLogger(__name__)


class TestGenerator:
    """
    Генератор тестов для ОГЭ по обществознанию.
    
    Создаёт вопросы разных типов и сложности на основе
    материала из базы знаний.
    
    Attributes:
        rag_pipeline: RAG-пайплайн для поиска материала
        tests_dir: Директория для хранения тестов
    """
    
    def __init__(self, rag_pipeline: RAGPipeline) -> None:
        """
        Инициализация генератора тестов.
        
        Args:
            rag_pipeline: RAG-пайпайн
        """
        self.rag_pipeline = rag_pipeline
        self.tests_dir = Path("data/tests")
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Сопоставление сложности и типов вопросов
        self.difficulty_params = {
            "easy": {
                "question_types": ["fact", "definition"],
                "num_options": 4,
                "complexity": "базовый"
            },
            "medium": {
                "question_types": ["understanding", "application"],
                "num_options": 4,
                "complexity": "повышенный"
            },
            "hard": {
                "question_types": ["analysis", "evaluation"],
                "num_options": 4,
                "complexity": "высокий"
            }
        }
    
    async def generate_test(
        self,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Генерация теста по теме.
        
        Args:
            topic: Название темы
            difficulty: Сложность (easy, medium, hard)
            num_questions: Количество вопросов
            
        Returns:
            Dict[str, Any]: Сгенерированный тест
        """
        logger.info(f"Генерация теста по теме '{topic}', сложность: {difficulty}")
        
        # Получение материала по теме
        chunks = await self.rag_pipeline._search_chunks(topic)
        
        if not chunks:
            return {
                "error": "Не удалось найти материал по теме",
                "questions": {}
            }
        
        # Формирование контекста
        context = self.rag_pipeline._build_context(chunks)
        
        # Параметры сложности
        params = self.difficulty_params.get(difficulty, self.difficulty_params["medium"])
        
        # Генерация вопросов через LLM или демо-режим
        try:
            questions = await self.rag_pipeline.llm_client.generate_questions(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions,
                context=context
            )
            
            if not questions:
                raise Exception("LLM не вернул вопросы")
                
        except Exception as e:
            logger.warning(f"LLM генерация недоступна: {e}. Использую демо-вопросы.")
            questions = self._generate_demo_questions(topic, difficulty, num_questions)
        
        # Сохранение теста
        test_id = f"test_{topic}_{difficulty}"
        
        test_data = {
            "test_id": test_id,
            "topic": topic,
            "difficulty": difficulty,
            "complexity": params["complexity"],
            "questions": questions,
            "total_questions": len(questions),
            "created_at": "2026-03-05"
        }
        
        # Сохранение в файл
        test_file = self.tests_dir / f"{test_id}.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        return test_data
    
    def _generate_demo_questions(
        self,
        topic: str,
        difficulty: str,
        num_questions: int
    ) -> Dict[str, Any]:
        """
        Генерация демо-вопросов без LLM.
        
        Args:
            topic: Название темы
            difficulty: Сложность
            num_questions: Количество вопросов
            
        Returns:
            Dict[str, Any]: Словарь вопросов
        """
        # База демо-вопросов по темам
        demo_questions_db = {
            "человек и общество": [
                {
                    "type": "fact",
                    "question": "Что такое общество?",
                    "answers": [
                        "Совокупность людей с общими интересами",
                        "Группа животных",
                        "Компьютерная сеть",
                        "Государственная организация"
                    ],
                    "correct_answer": 0,
                    "explanation": "Общество — это совокупность людей, объединённых общими интересами, культурой и социальными связями."
                },
                {
                    "type": "definition",
                    "question": "Что такое социализация?",
                    "answers": [
                        "Процесс обучения в школе",
                        "Усвоение социальных норм и ценностей",
                        "Общение в интернете",
                        "Работа в коллективе"
                    ],
                    "correct_answer": 1,
                    "explanation": "Социализация — это процесс усвоения индивидом социальных норм, ценностей и навыков."
                },
                {
                    "type": "understanding",
                    "question": "Какие социальные институты существуют в обществе?",
                    "answers": [
                        "Семья, образование, государство",
                        "Компьютер, телефон, интернет",
                        "Магазин, больница, парк",
                        "Армия, полиция, суд"
                    ],
                    "correct_answer": 0,
                    "explanation": "Социальные институты — это устойчивые формы организации общественной жизни: семья, образование, государство, религия."
                },
                {
                    "type": "application",
                    "question": "Какую роль играет культура в обществе?",
                    "answers": [
                        "Определяет только развлечения",
                        "Передаёт ценности и нормы",
                        "Не имеет значения",
                        "Создаёт законы"
                    ],
                    "correct_answer": 1,
                    "explanation": "Культура передаёт социальные нормы и ценности от поколения к поколению."
                },
                {
                    "type": "analysis",
                    "question": "Как взаимосвязаны человек и общество?",
                    "answers": [
                        "Человек не зависит от общества",
                        "Человек формируется в обществе и влияет на него",
                        "Общество зависит от человека полностью",
                        "Они не связаны"
                    ],
                    "correct_answer": 1,
                    "explanation": "Человек является частью общества и одновременно его создаёт и изменяет."
                }
            ],
            "экономика": [
                {
                    "type": "fact",
                    "question": "Что изучает экономика?",
                    "answers": [
                        "Природу и окружающую среду",
                        "Удовлетворение потребностей в условиях ограниченных ресурсов",
                        "Историю государства",
                        "Психологию человека"
                    ],
                    "correct_answer": 1,
                    "explanation": "Экономика изучает производство, распределение и потребление товаров и услуг."
                },
                {
                    "type": "definition",
                    "question": "Какие функции выполняют деньги?",
                    "answers": [
                        "Только средство платежа",
                        "Мера стоимости, средство платежа, средство накопления",
                        "Только средство накопления",
                        "Только средство обмена"
                    ],
                    "correct_answer": 1,
                    "explanation": "Деньги выполняют три основные функции: мера стоимости, средство платежа, средство накопления."
                },
                {
                    "type": "understanding",
                    "question": "Что такое конкуренция?",
                    "answers": [
                        "Сотрудничество между производителями",
                        "Соперничество за потребителя",
                        "Государственное регулирование",
                        "Монополия на рынке"
                    ],
                    "correct_answer": 1,
                    "explanation": "Конкуренция — это соперничество между производителями за потребителя."
                },
                {
                    "type": "application",
                    "question": "Что произойдёт, если спрос на товар увеличится?",
                    "answers": [
                        "Цена снизится",
                        "Цена возрастёт",
                        "Товар исчезнет",
                        "Ничего не изменится"
                    ],
                    "correct_answer": 1,
                    "explanation": "При увеличении спроса и неизменном предложении цена товара возрастает."
                },
                {
                    "type": "analysis",
                    "question": "Почему важно рационально использовать ресурсы?",
                    "answers": [
                        "Ресурсы бесконечны",
                        "Ресурсы ограничены, нужно экономить",
                        "Это не важно",
                        "Ресурсов слишком много"
                    ],
                    "correct_answer": 1,
                    "explanation": "Ресурсы ограничены, поэтому их нужно использовать рационально."
                }
            ],
            "право": [
                {
                    "type": "fact",
                    "question": "Что такое право?",
                    "answers": [
                        "Совет директоров компании",
                        "Система обязательных правил поведения",
                        "Суд и полиция",
                        "Законы природы"
                    ],
                    "correct_answer": 1,
                    "explanation": "Право — это система обязательных правил поведения, установленных государством."
                },
                {
                    "type": "definition",
                    "question": "Какой закон является главным в России?",
                    "answers": [
                        "Гражданский кодекс",
                        "Уголовный кодекс",
                        "Конституция РФ",
                        "Федеральный закон"
                    ],
                    "correct_answer": 2,
                    "explanation": "Конституция РФ — главный закон страны, принятый в 1993 году."
                },
                {
                    "type": "understanding",
                    "question": "Чем проступок отличается от преступления?",
                    "answers": [
                        "Ничем",
                        "Проступок — менее тяжкое нарушение",
                        "Преступление — менее тяжкое нарушение",
                        "Это одно и то же"
                    ],
                    "correct_answer": 1,
                    "explanation": "Проступок — нарушение с менее строгим наказанием, преступление — с уголовной ответственностью."
                },
                {
                    "type": "application",
                    "question": "Какое право относится к гражданским правам?",
                    "answers": [
                        "Право на образование",
                        "Право на жизнь",
                        "Право на труд",
                        "Право на социальное обеспечение"
                    ],
                    "correct_answer": 1,
                    "explanation": "Гражданские права включают право на жизнь, свободу, собственность."
                },
                {
                    "type": "analysis",
                    "question": "Почему права человека должны быть защищены?",
                    "answers": [
                        "Это не обязательно",
                        "Для защиты достоинства и свободы каждого",
                        "Только для некоторых людей",
                        "Это создаёт проблемы"
                    ],
                    "correct_answer": 1,
                    "explanation": "Права человека защищают его достоинство, свободу и возможность полноценной жизни."
                }
            ]
        }
        
        # Выбор вопросов по теме
        topic_lower = topic.lower()
        questions_list = []
        
        for key, questions in demo_questions_db.items():
            if key in topic_lower:
                questions_list.extend(questions)
                break
        
        if not questions_list:
            # Использование общих вопросов
            questions_list = demo_questions_db["человек и общество"]
        
        # Фильтрация по сложности
        params = self.difficulty_params.get(difficulty, self.difficulty_params["medium"])
        
        if difficulty != "medium":
            filtered = [q for q in questions_list if q["type"] in params["question_types"]]
            if filtered:
                questions_list = filtered
        
        # Ограничение количества
        questions_list = questions_list[:num_questions]
        
        # Форматирование в словарь
        questions_dict = {}
        for i, q in enumerate(questions_list):
            questions_dict[f"q_{i}"] = q
        
        return questions_dict
    
    async def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение сохранённого теста.
        
        Args:
            test_id: ID теста
            
        Returns:
            Optional[Dict[str, Any]]: Данные теста
        """
        test_file = self.tests_dir / f"{test_id}.json"
        
        if not test_file.exists():
            return None
        
        with open(test_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def list_tests(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех тестов.
        
        Returns:
            List[Dict[str, Any]]: Список тестов
        """
        tests = []
        
        for test_file in self.tests_dir.glob("*.json"):
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
                tests.append({
                    "test_id": test_data.get("test_id"),
                    "topic": test_data.get("topic"),
                    "difficulty": test_data.get("difficulty"),
                    "total_questions": test_data.get("total_questions")
                })
        
        return tests

    async def generate_all_topics_test(self, num_questions: int = 10) -> Dict[str, Any]:
        """
        Генерация теста по всем темам (случайная выборка).
        
        Args:
            num_questions: Общее количество вопросов
            
        Returns:
            Dict[str, Any]: Сгенерированный тест
        """
        logger.info(f"Генерация теста по всем темам, количество: {num_questions}")
        
        # Получение вопросов по каждой теме
        topics = ["человек и общество", "экономика", "право", "политика", "социальная сфера", "сфера духовной культуры"]
        all_questions = []
        
        for topic in topics:
            try:
                chunks = await self.rag_pipeline._search_chunks(topic)
                if chunks:
                    context = self.rag_pipeline._build_context(chunks)
                    questions = await self.rag_pipeline.llm_client.generate_questions(
                        topic=topic,
                        difficulty="mixed",
                        num_questions=2,  # 2 вопроса от каждой темы
                        context=context
                    )
                    
                    # Добавляем метку темы
                    for q_key, q_data in questions.items():
                        q_data["topic"] = topic
                        all_questions.append((q_data, topic))
                        
            except Exception as e:
                logger.warning(f"Ошибка генерации вопросов по теме {topic}: {e}")
        
        # Если не хватило вопросов через LLM, используем демо-вопросы
        if len(all_questions) < num_questions:
            all_questions.extend(self._get_demo_questions_by_topic())
        
        # Перемешивание вопросов
        import random
        random.shuffle(all_questions)
        
        # Ограничение количества
        all_questions = all_questions[:num_questions]
        
        # Форматирование в словарь
        questions_dict = {}
        for i, (q_data, topic) in enumerate(all_questions):
            questions_dict[f"q_{i}"] = q_data
        
        # Сохранение теста
        test_id = f"test_all_topics_{len(all_questions)}"
        
        test_data = {
            "test_id": test_id,
            "topic": "Все темы",
            "difficulty": "mixed",
            "complexity": "смешанный",
            "questions": questions_dict,
            "total_questions": len(all_questions),
            "created_at": "2026-03-05"
        }
        
        return test_data
    
    def _get_demo_questions_by_topic(self) -> List[tuple]:
        """
        Получение демо-вопросов по всем темам.
        
        Returns:
            List[tuple]: Список кортежей (вопрос, тема)
        """
        demo_questions = {
            "человек и общество": [
                {
                    "question": "Что такое общество?",
                    "answers": ["Совокупность людей", "Группа животных", "Компьютерная сеть", "Государство"],
                    "correct_answer": 0,
                    "explanation": "Общество — это совокупность людей с общими интересами.",
                    "difficulty": "easy"
                },
                {
                    "question": "Что такое социализация?",
                    "answers": ["Усвоение норм", "Обучение в школе", "Работа", "Отдых"],
                    "correct_answer": 0,
                    "explanation": "Социализация — усвоение социальных норм и ценностей.",
                    "difficulty": "easy"
                }
            ],
            "экономика": [
                {
                    "question": "Что изучает экономика?",
                    "answers": ["Производство товаров", "Природу", "Историю", "Психологию"],
                    "correct_answer": 0,
                    "explanation": "Экономика изучает производство и потребление.",
                    "difficulty": "easy"
                },
                {
                    "question": "Что такое инфляция?",
                    "answers": ["Рост цен", "Падение цен", "Увеличение производства", "Снижение безработицы"],
                    "correct_answer": 0,
                    "explanation": "Инфляция — это рост общего уровня цен.",
                    "difficulty": "medium"
                }
            ],
            "право": [
                {
                    "question": "Какой закон главный в России?",
                    "answers": ["Конституция", "Гражданский кодекс", "Уголовный кодекс", "ФЗ"],
                    "correct_answer": 0,
                    "explanation": "Конституция РФ — главный закон страны.",
                    "difficulty": "easy"
                },
                {
                    "question": "Какой возраст совершеннолетия в РФ?",
                    "answers": ["18 лет", "16 лет", "21 год", "14 лет"],
                    "correct_answer": 0,
                    "explanation": "Совершеннолетие наступает в 18 лет.",
                    "difficulty": "easy"
                }
            ],
            "политика": [
                {
                    "question": "Какая власть исполнительная?",
                    "answers": ["Правительство", "Госдума", "Суд", "Президент"],
                    "correct_answer": 0,
                    "explanation": "Правительство — орган исполнительной власти.",
                    "difficulty": "medium"
                },
                {
                    "question": "Что такое демократия?",
                    "answers": ["Народовластие", "Правление элиты", "Монархия", "Диктатура"],
                    "correct_answer": 0,
                    "explanation": "Демократия — это народовластие.",
                    "difficulty": "easy"
                }
            ],
            "социальная сфера": [
                {
                    "question": "Что такое социальная стратификация?",
                    "answers": ["Разделение на слои", "Равенство всех", "Отсутствие различий", "Одинаковый доход"],
                    "correct_answer": 0,
                    "explanation": "Стратификация — неравенство и деление на слои.",
                    "difficulty": "medium"
                },
                {
                    "question": "Что такое семья?",
                    "answers": ["Союз людей", "Компания", "Государство", "Школа"],
                    "correct_answer": 0,
                    "explanation": "Семья — основанный на браке или кровном родстве союз.",
                    "difficulty": "easy"
                }
            ],
            "сфера духовной культуры": [
                {
                    "question": "Что такое культура?",
                    "answers": ["Духовные и материальные ценности", "Только искусство", "Только наука", "Только религия"],
                    "correct_answer": 0,
                    "explanation": "Культура включает духовные и материальные ценности.",
                    "difficulty": "medium"
                },
                {
                    "question": "Что такое мораль?",
                    "answers": ["Нормы поведения", "Законы государства", "Правила игры", "Технические стандарты"],
                    "correct_answer": 0,
                    "explanation": "Мораль — нормы поведения в обществе.",
                    "difficulty": "easy"
                }
            ]
        }
        
        result = []
        for topic, questions in demo_questions.items():
            for q in questions:
                result.append((q, topic))
        
        return result
