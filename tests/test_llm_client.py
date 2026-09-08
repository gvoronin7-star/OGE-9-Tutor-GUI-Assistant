# -*- coding: utf-8 -*-
"""
Unit-тесты для LLMClient.generate_questions() - в частности, для
pydantic-валидации структуры JSON-ответа LLM (Г-7 зонального аудита
хаба, 2026-09-08).
"""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.llm_client import GenerationResult, LLMClient
from utils.cache import CacheManager


class TestGenerateQuestionsValidation:
    """generate_questions() не должен падать и не должен пропускать
    структурно неверные вопросы дальше по стеку - там их ждут
    _shuffle_answers (десктоп) и парсинг ответа на мобильном клиенте,
    которые доверяют форме данных."""

    @pytest.fixture
    def client(self):
        return LLMClient(Mock(spec=CacheManager))

    @pytest.mark.asyncio
    async def test_valid_response_parsed(self, client):
        raw = (
            '{"questions": [{"question": "Что такое право?", '
            '"answers": ["Наука", "Система норм", "Игра", "Танец"], '
            '"correct_answer": 1, "explanation": "Пояснение"}]}'
        )
        with patch.object(
            client,
            "generate",
            AsyncMock(return_value=GenerationResult(text=raw, is_fallback=False)),
        ):
            result = await client.generate_questions(
                topic="право", difficulty="medium", num_questions=1, context="..."
            )

        assert list(result.keys()) == ["q_0"]
        assert result["q_0"]["correct_answer"] == 1
        assert result["q_0"]["difficulty"] == "medium"

    @pytest.mark.asyncio
    async def test_correct_answer_out_of_range_rejected(self, client):
        raw = (
            '{"questions": [{"question": "Вопрос", '
            '"answers": ["А", "Б"], "correct_answer": 5}]}'
        )
        with patch.object(
            client,
            "generate",
            AsyncMock(return_value=GenerationResult(text=raw, is_fallback=False)),
        ):
            result = await client.generate_questions(
                topic="право", difficulty="medium", num_questions=1, context="..."
            )

        assert result == {}

    @pytest.mark.asyncio
    async def test_missing_answers_field_rejected(self, client):
        raw = '{"questions": [{"question": "Вопрос", "correct_answer": 0}]}'
        with patch.object(
            client,
            "generate",
            AsyncMock(return_value=GenerationResult(text=raw, is_fallback=False)),
        ):
            result = await client.generate_questions(
                topic="право", difficulty="medium", num_questions=1, context="..."
            )

        assert result == {}

    @pytest.mark.asyncio
    async def test_question_not_a_dict_rejected(self, client):
        raw = '{"questions": ["просто строка вместо вопроса"]}'
        with patch.object(
            client,
            "generate",
            AsyncMock(return_value=GenerationResult(text=raw, is_fallback=False)),
        ):
            result = await client.generate_questions(
                topic="право", difficulty="medium", num_questions=1, context="..."
            )

        assert result == {}
