# -*- coding: utf-8 -*-
"""
Тесты «честных отказов» (находки аудита В-11 и В-9).

В-11: тест из демо-банка при отказе LLM помечается is_demo / demo_questions.
В-9: ExistingVectorStore не имеет локального эмбеддинга; без ключа API
поиск возвращает [] и пишет warning.

Без сети, без Tk. TestGenerator пишет файл теста только в tmp_path.
"""

import ast
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import api.test_generator as tg
from api.vector_store_existing import ExistingVectorStore
from utils.test_status import loaded_status_text

ROOT = Path(__file__).resolve().parent.parent

ALL_TOPICS = [
    "человек и общество",
    "экономика",
    "право",
    "политика",
    "социальная сфера",
    "сфера духовной культуры",
]


def _llm_questions(n: int, topic: str = "т") -> Dict[str, Any]:
    return {
        f"q_{i}": {
            "question": f"LLM вопрос {topic} {i}",
            "answers": ["a", "b", "c", "d"],
            "correct_answer": 0,
        }
        for i in range(n)
    }


def _make_generator(tmp_path, monkeypatch, generate_questions) -> Any:
    # DATA_DIR подменяется до конструктора: он создаёт tests_dir
    monkeypatch.setattr(tg, "DATA_DIR", tmp_path)
    pipeline = SimpleNamespace(
        _search_chunks=AsyncMock(return_value=[{"text": "материал"}]),
        _build_context=lambda chunks: "контекст",
        llm_client=SimpleNamespace(generate_questions=generate_questions),
    )
    return tg.TestGenerator(pipeline)  # type: ignore[arg-type]


def _per_topic_llm(failing_topics: List[str]):
    async def fake(topic, difficulty, num_questions, context):
        if topic in failing_topics:
            raise RuntimeError("отказ LLM")
        return _llm_questions(num_questions, topic)

    return fake


# ---------------------------------------------------------------- generate_test


async def test_generate_test_llm_raises_marks_demo(tmp_path, monkeypatch, caplog):
    gen = _make_generator(
        tmp_path, monkeypatch, AsyncMock(side_effect=RuntimeError("LLM сломалась"))
    )
    with caplog.at_level(logging.WARNING, logger="api.test_generator"):
        test = await gen.generate_test("экономика", "easy", 3)
    assert test["is_demo"] is True
    assert test["total_questions"] > 0
    assert test["demo_questions"] == test["total_questions"]
    assert len(test["questions"]) == test["total_questions"]
    assert "LLM сломалась" in caplog.text


async def test_generate_test_llm_empty_marks_demo(tmp_path, monkeypatch):
    gen = _make_generator(tmp_path, monkeypatch, AsyncMock(return_value={}))
    test = await gen.generate_test("право", "medium", 3)
    assert test["is_demo"] is True
    assert test["total_questions"] > 0
    assert test["demo_questions"] == test["total_questions"]


async def test_generate_test_llm_ok_not_demo(tmp_path, monkeypatch):
    gen = _make_generator(
        tmp_path, monkeypatch, AsyncMock(return_value=_llm_questions(4))
    )
    test = await gen.generate_test("право", "medium", 4)
    assert test["is_demo"] is False
    assert test["demo_questions"] == 0
    assert test["total_questions"] == 4


# ------------------------------------------------------ generate_all_topics_test


async def test_all_topics_llm_ok_zero_demo(tmp_path, monkeypatch):
    gen = _make_generator(tmp_path, monkeypatch, _per_topic_llm([]))
    test = await gen.generate_all_topics_test(10)
    assert test["is_demo"] is False
    assert test["demo_questions"] == 0
    assert test["total_questions"] == 10


async def test_all_topics_llm_down_all_demo(tmp_path, monkeypatch):
    gen = _make_generator(tmp_path, monkeypatch, _per_topic_llm(ALL_TOPICS))
    test = await gen.generate_all_topics_test(10)
    assert test["is_demo"] is True
    assert test["total_questions"] == 10
    assert test["demo_questions"] == 10


async def test_all_topics_partial_counts_demo_in_final_test(tmp_path, monkeypatch):
    # 3 темы из 6 падают -> от LLM 3*2 = 6 вопросов, до 10 добирает демо-банк.
    # shuffle отключён: LLM-вопросы идут первыми, обрезка оставляет 4 демо.
    gen = _make_generator(
        tmp_path, monkeypatch, _per_topic_llm(["экономика", "политика", "право"])
    )
    monkeypatch.setattr("random.shuffle", lambda seq: None)
    test = await gen.generate_all_topics_test(10)
    assert test["total_questions"] == 10
    assert test["is_demo"] is True
    assert test["demo_questions"] == 4
    llm_in_test = [
        q for q in test["questions"].values() if q["question"].startswith("LLM вопрос")
    ]
    assert len(llm_in_test) == 6


async def test_all_topics_truncation_pushes_out_llm_questions(tmp_path, monkeypatch):
    # LLM дала 6 вопросов из 12 запрошенных; пул демо добавлен; shuffle
    # разворачивает список, и демо оказываются первыми. В тест попадают
    # ровно 12 вопросов, число демо в нём — по факту, а не размер пула.
    gen = _make_generator(
        tmp_path, monkeypatch, _per_topic_llm(["экономика", "политика", "право"])
    )
    monkeypatch.setattr("random.shuffle", lambda seq: seq.reverse())
    pool = len(gen._get_demo_questions_by_topic())
    assert pool > 12
    test = await gen.generate_all_topics_test(12)
    assert test["total_questions"] == 12
    assert test["demo_questions"] == 12
    assert test["demo_questions"] != pool


async def test_all_topics_marker_not_leaked_into_question_json(tmp_path, monkeypatch):
    gen = _make_generator(tmp_path, monkeypatch, _per_topic_llm(["экономика"]))
    monkeypatch.setattr("random.shuffle", lambda seq: None)
    test = await gen.generate_all_topics_test(12)
    for q in test["questions"].values():
        assert not any("demo" in k.lower() for k in q), q.keys()


# ------------------------------------------------------- ExistingVectorStore


async def test_existing_store_search_without_key_returns_empty(
    monkeypatch, caplog, tmp_path
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PROXY_API_KEY", raising=False)
    store = ExistingVectorStore(tmp_path)
    store.index = SimpleNamespace(ntotal=1)
    store.dataset = [{"text": "x"}]
    with caplog.at_level(logging.WARNING, logger="api.vector_store_existing"):
        result = await store.search("Что такое общество?", top_k=2)
    assert result == []
    assert "PROXY_API_KEY" in caplog.text


def test_existing_store_has_no_local_embedding_path():
    assert not hasattr(ExistingVectorStore, "_get_local_embedding")
    assert not hasattr(ExistingVectorStore(Path("x")), "model")
    source = (ROOT / "api" / "vector_store_existing.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert "sentence_transformers" not in imported
    assert "use_remote_embedding" not in source


# ------------------------------------------------------------- status text


def test_status_text_normal():
    normal = {"total_questions": 10, "is_demo": False, "demo_questions": 0}
    assert loaded_status_text(normal) == "✅ Тест загружен: 10 вопросов"
    # тест без новых полей (старый файл)
    assert loaded_status_text({"total_questions": 5}) == "✅ Тест загружен: 5 вопросов"


def test_status_text_all_demo():
    text = loaded_status_text(
        {"total_questions": 10, "is_demo": True, "demo_questions": 10}
    )
    assert "демонстрационные" in text
    assert "LLM недоступна" in text
    assert "✅" not in text
    assert " из " not in text


def test_status_text_partial_demo():
    text = loaded_status_text(
        {"total_questions": 10, "is_demo": True, "demo_questions": 3}
    )
    assert "3 демонстрационных" in text
    assert "10 вопросов" in text
    assert "LLM недоступна" in text
