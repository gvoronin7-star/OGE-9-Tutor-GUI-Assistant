# -*- coding: utf-8 -*-
"""
Логирование для GUI компонентов.

Отслеживает действия пользователя, навигацию, ошибки интерфейса.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from utils.advanced_logger import detailed_logger, logger_gui


class GUIActionLogger:
    """
    Логгер действий пользователя в GUI.

    Отслеживает:
    - Переключение между вкладками
    - Выбор тем
    - Запуск тестов
    - Навигацию
    """

    def __init__(self) -> None:
        """Инициализация."""
        self.session_start = time.time()
        self.actions_count = 0

    def log_action(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """
        Логирование действия.

        Args:
            action: Название действия
            details: Детали действия
            user_id: ID пользователя
        """
        self.actions_count += 1
        elapsed = time.time() - self.session_start

        logger_gui.info(f"Действие #{self.actions_count} ({elapsed:.1f}s): {action}")

        if details:
            logger_gui.debug(f"Детали: {details}")

        detailed_logger.log_request(
            component="gui",
            action=action,
            input_data=details or {},
            output_data=None,
            duration_ms=0,
            status="success",
            user_id=user_id,
        )

    def log_navigation(
        self, from_screen: str, to_screen: str, mode: Optional[str] = None
    ) -> None:
        """
        Логирование навигации.

        Args:
            from_screen: Откуда
            to_screen: Куда
            mode: Режим (user/admin)
        """
        details = {"from": from_screen, "to": to_screen, "mode": mode}

        self.log_action("navigation", details)
        logger_gui.debug(f"Навигация: {from_screen} → {to_screen}")

    def log_topic_selection(self, topic: str, topic_id: int) -> None:
        """
        Логирование выбора темы.

        Args:
            topic: Название темы
            topic_id: ID темы
        """
        details = {"topic": topic, "topic_id": topic_id}

        self.log_action("topic_selected", details)
        logger_gui.info(f"Выбрана тема: {topic}")

    def log_test_start(self, topic: str, difficulty: str, num_questions: int) -> None:
        """
        Логирование начала теста.

        Args:
            topic: Тема теста
            difficulty: Сложность
            num_questions: Количество вопросов
        """
        details = {
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
        }

        self.log_action("test_started", details)
        logger_gui.info(f"Начат тест: {topic}, {difficulty}, {num_questions} вопросов")

    def log_test_answer(
        self,
        question_num: int,
        selected_answer: int,
        is_correct: bool,
        time_spent: float,
    ) -> None:
        """
        Логирование ответа на вопрос.

        Args:
            question_num: Номер вопроса
            selected_answer: Выбранный вариант
            is_correct: Правильность
            time_spent: Время ответа
        """
        details = {
            "question_num": question_num,
            "selected_answer": selected_answer,
            "is_correct": is_correct,
            "time_spent_ms": time_spent * 1000,
        }

        self.log_action("test_answered", details)

        if is_correct:
            logger_gui.debug(f"Вопрос {question_num}: правильный ответ")
        else:
            logger_gui.debug(f"Вопрос {question_num}: ошибка")

    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Логирование ошибки GUI.

        Args:
            error_type: Тип ошибки
            error_message: Сообщение
            context: Контекст
        """
        details = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
        }

        self.log_action("gui_error", details)
        logger_gui.error(f"Ошибка GUI: {error_type} - {error_message}")

        detailed_logger.log_request(
            component="gui",
            action="error",
            input_data=details,
            output_data=None,
            duration_ms=0,
            status="error",
            error_message=error_message,
        )

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Получение статистики сессии.

        Returns:
            Dict[str, Any]: Статистика
        """
        return {
            "session_duration_sec": time.time() - self.session_start,
            "total_actions": self.actions_count,
        }


# Глобальный экземпляр
gui_action_logger = GUIActionLogger()


def log_action(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Удобная функция для логирования действий."""
    gui_action_logger.log_action(action, details)


def log_navigation(from_screen: str, to_screen: str) -> None:
    """Удобная функция для логирования навигации."""
    gui_action_logger.log_navigation(from_screen, to_screen)


def log_error(error_type: str, error_message: str) -> None:
    """Удобная функция для логирования ошибок."""
    gui_action_logger.log_error(error_type, error_message)
