# -*- coding: utf-8 -*-
"""
Тесты для api/mobile_routes.py.

Роутер монтируется на отдельное тестовое FastAPI-приложение (не на
main.py::app) с заглушками вместо RAGPipeline/TestGenerator в
app.state - реальный RAGPipeline инициализируется через
sentence-transformers, которая, как показала эта же сессия, чувствительна
к сетевым заминкам HuggingFace Hub. Не то, на чём должны быть завязаны
модульные тесты роутинга и валидации запросов.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.mobile_routes import router


@pytest.fixture
def app_with_stubs():
    app = FastAPI()
    app.include_router(router)
    app.state.rag_pipeline = AsyncMock()
    app.state.rag_pipeline.get_answer.return_value = {
        # RAGPipeline.get_answer() возвращает sources как список названий
        # тем (str) - api/rag_pipeline.py: [c["topic"] for c in
        # relevant_chunks[:3]] - не список словарей, как этот мок изначально
        # предполагал (маскировало реальный баг схемы до первого запроса
        # с настоящего устройства).
        "answer": "Общество - это совокупность людей.",
        "sources": ["человек и общество"],
    }
    app.state.test_generator = AsyncMock()
    app.state.test_generator.generate_test.return_value = {
        "test_id": "test_право_medium",
        "topic": "Право",
        "questions": {"q_0": {"question": "Что такое право?"}},
        "total_questions": 1,
    }
    return app


@pytest.fixture
def client(app_with_stubs):
    return TestClient(app_with_stubs)


class TestListTopics:
    def test_returns_six_official_topics(self, client):
        response = client.get("/api/topics")
        assert response.status_code == 200
        topics = response.json()
        assert len(topics) == 6
        assert "Человек и общество" in topics


class TestAsk:
    def test_returns_answer_and_sources(self, client, app_with_stubs):
        response = client.post("/api/ask", json={"question": "Что такое общество?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "Общество - это совокупность людей."
        assert body["sources"] == ["человек и общество"]
        app_with_stubs.state.rag_pipeline.get_answer.assert_awaited_once_with(
            "Что такое общество?", 0
        )

    def test_503_when_rag_pipeline_not_initialized(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post("/api/ask", json={"question": "Что такое право?"})

        assert response.status_code == 503


class TestGenerateTest:
    def test_generates_test_for_known_topic(self, client):
        response = client.post(
            "/api/tests/generate",
            json={"topic": "Право", "difficulty": "medium", "num_questions": 1},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["topic"] == "Право"
        assert body["total_questions"] == 1

    def test_400_for_unknown_topic(self, client):
        response = client.post("/api/tests/generate", json={"topic": "Астрология"})
        assert response.status_code == 400
