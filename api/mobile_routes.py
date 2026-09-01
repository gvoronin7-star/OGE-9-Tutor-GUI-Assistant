# -*- coding: utf-8 -*-
"""
REST-эндпоинты для мобильного клиента (Фаза 3 мобильного плана).

Десктопная GUI вызывает RAGPipeline/TestGenerator in-process, напрямую
из Python — до этого файла у приложения не было ни одного HTTP-пути
к реальной функциональности (только /, /health, /metrics в main.py).
Этот роутер даёт мобильному приложению в серверном режиме доступ к
той же логике по сети. См.
decisions/2026-09-01_flutter-mobile-app-concept-plan.md, Фаза 3.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["mobile"])

# Тот же canonical список, что gui_debugger/components/user/topic_study.py::TOPICS.
TOPICS: List[str] = [
    "Человек и общество",
    "Сфера духовной культуры",
    "Экономика",
    "Социальная сфера",
    "Политика",
    "Право",
]


class AskRequest(BaseModel):
    question: str
    user_id: int = 0


class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class GenerateTestRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5


@router.get("/topics")
async def list_topics() -> List[str]:
    """Официальные темы ФИПИ — тот же список, что у десктопной GUI."""
    return TOPICS


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, request: Request) -> AskResponse:
    """Вопрос по базе знаний — тот же путь, что RAGPipeline.get_answer()."""
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG-пайплайн не инициализирован")

    result = await rag_pipeline.get_answer(payload.question, payload.user_id)
    return AskResponse(answer=result["answer"], sources=result.get("sources", []))


@router.post("/tests/generate")
async def generate_test(
    payload: GenerateTestRequest, request: Request
) -> Dict[str, Any]:
    """Генерация теста по теме — тот же путь, что TestGenerator.generate_test()."""
    if payload.topic not in TOPICS:
        raise HTTPException(status_code=400, detail=f"Неизвестная тема: {payload.topic}")

    test_generator = getattr(request.app.state, "test_generator", None)
    if test_generator is None:
        raise HTTPException(status_code=503, detail="Генератор тестов не инициализирован")

    return await test_generator.generate_test(
        topic=payload.topic,
        difficulty=payload.difficulty,
        num_questions=payload.num_questions,
    )
