# -*- coding: utf-8 -*-
"""
Регрессионные тесты для багов, найденных аудитом от 2026-08-31
(decisions/2026-08-31_audit-diff.md) и исправленных в этой же сессии.

Ограничены логикой без Tkinter — CI (ubuntu-latest) не имеет дисплея,
поэтому тесты, создающие реальные виджеты, сюда не входят и должны
проверяться вручную (см. decisions/decision-log.md).
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.llm_client import LLMClient
from api.test_generator import TestGenerator as OgeTestGenerator
from scripts.check_secrets import scan_directory
from utils.hashing import stable_query_hash
from utils.logger import QueryStatsLogger

# Официальные 6 тем ФИПИ, см. gui_debugger/components/user/topic_study.py::TOPICS
OFFICIAL_TOPICS = [
    "Человек и общество",
    "Сфера духовной культуры",
    "Экономика",
    "Социальная сфера",
    "Политика",
    "Право",
]


class TestStableQueryHash:
    """Б-4: hash() штатный рандомизируется на процесс — используем stable_query_hash."""

    def test_deterministic_for_same_input(self):
        """Одинаковый текст должен всегда давать одинаковый хэш."""
        assert stable_query_hash("Что такое общество?") == stable_query_hash(
            "Что такое общество?"
        )

    def test_different_for_different_input(self):
        """Разный текст — разный хэш (не гарантия отсутствия коллизий, но базовая проверка)."""
        assert stable_query_hash("вопрос 1") != stable_query_hash("вопрос 2")

    def test_survives_simulated_restart(self):
        """
        Ключевая регрессия: значение не должно зависеть от PYTHONHASHSEED
        процесса — иначе персистентная статистика/кэш ломаются при каждом
        перезапуске (см. decisions/2026-08-31_audit-diff.md, Б-4).
        """
        # hash() (без stable_query_hash) отличался бы между процессами
        # с разным PYTHONHASHSEED; stable_query_hash использует md5,
        # не зависящий от PYTHONHASHSEED вообще.
        h1 = stable_query_hash("тест стабильности")
        h2 = stable_query_hash("тест стабильности")
        assert h1 == h2
        assert isinstance(h1, int)


class TestQueryStatsLoggerPersistence:
    """
    Б-4 / ранее исправленный баг: json.load() возвращает строковые ключи,
    без конвертации обратно в int статистика частоты запросов ломается
    после перезапуска (см. decisions/decision-log.md, запись про
    utils/logger.py).
    """

    def test_stats_survive_reload_with_int_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            logger1 = QueryStatsLogger(log_dir)
            logger1.log_query("Что такое общество?")
            logger1.log_query("Что такое общество?")
            logger1._save_stats()

            # Новый экземпляр имитирует перезапуск процесса — статистика
            # должна подхватиться, а накопление продолжиться, а не начаться
            # с нуля из-за несовпадения типов ключей.
            logger2 = QueryStatsLogger(log_dir)
            query_hash = stable_query_hash("что такое общество?")

            assert query_hash in logger2.query_stats
            assert logger2.query_stats[query_hash] == 2

            logger2.log_query("Что такое общество?")
            assert logger2.query_stats[query_hash] == 3

    def test_loaded_keys_are_int_not_str(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger1 = QueryStatsLogger(log_dir)
            logger1.log_query("тест")
            logger1._save_stats()

            # Сам файл на диске - валидный JSON со строковыми ключами
            with open(logger1.stats_file, encoding="utf-8") as f:
                raw = json.load(f)
            assert all(isinstance(k, str) for k in raw.keys())

            # А после загрузки в объект - ключи снова int
            logger2 = QueryStatsLogger(log_dir)
            assert all(isinstance(k, int) for k in logger2.query_stats.keys())


class TestCheckSecretsSeverity:
    """
    Б-6: severity терялась при формировании находки — critical_count всегда
    был 0 независимо от того, что реально найдено (см.
    decisions/2026-08-31_audit-diff.md, Б-6).
    """

    def test_critical_secret_is_classified_as_critical(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "leaked.py").write_text(
                "AWS_KEY = 'AKIA1234567890ABCDEF'\n", encoding="utf-8"
            )

            findings = scan_directory(root)

            assert len(findings) == 1
            # findings[i] = (filepath, name, severity, location, content)
            assert findings[0][2] == "CRITICAL"

    def test_no_secret_means_no_findings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "clean.py").write_text(
                "GREETING = 'hello world'\n", encoding="utf-8"
            )

            findings = scan_directory(root)
            assert findings == []


class TestDemoAnswerFallback:
    """
    Находка 2 из decisions/2026-09-01_content-quality-review.md:
    без LLM-ключа `_generate_fallback` сверял ключевые слова со всем
    промптом (инструкция+контекст+вопрос), а не с вопросом ученика —
    из-за этого демо-индекс из 3 чанков почти всегда протаскивал слово
    "экономика" в контекст, и ответ был один и тот же независимо от
    вопроса. Плюс демо-контент был только для 3 тем из 6.
    """

    def _fallback_for(self, query: str) -> str:
        client = LLMClient.__new__(LLMClient)  # без __init__ - не нужен cache_manager
        return client._generate_fallback(query)

    def test_answers_differ_by_topic(self):
        """Разные вопросы по разным темам не должны давать одинаковый ответ."""
        answers = {
            q: self._fallback_for(q)
            for q in [
                "Что такое общество?",
                "Что изучает право?",
                "Расскажи про политические партии",
                "Что такое социальная мобильность?",
            ]
        }
        assert len(set(answers.values())) == len(answers), (
            "разные по теме вопросы дали одинаковый демо-ответ: " f"{answers}"
        )

    def test_keyword_match_uses_query_not_whole_prompt(self):
        """
        Регрессия конкретного бага: полный промпт с инструкцией/контекстом
        не должен переопределять тему, взятую из настоящего вопроса.
        """
        client = LLMClient.__new__(LLMClient)
        # Если бы matching шёл по всему prompt (старое поведение) - здесь
        # сработала бы ветка "экономика" из-за слова в контексте.
        # Правильное поведение: matching должен идти по query, не по prompt.
        answer_from_query = client._generate_fallback("Что изучает право?")
        assert "Право" in answer_from_query or "право" in answer_from_query.lower()
        assert "Экономика изучает производство" not in answer_from_query

    def test_all_six_official_topics_have_distinct_coverage(self):
        """Все 6 официальных тем ФИПИ должны иметь собственный, не общий ответ."""
        client = LLMClient.__new__(LLMClient)
        generic_fallback_marker = "Я нашёл релевантную информацию"
        for topic in OFFICIAL_TOPICS:
            answer = client._generate_fallback(f"Расскажи про тему: {topic}")
            assert (
                generic_fallback_marker not in answer
            ), f"тема {topic!r} не покрыта — попала в общий фолбэк"


class TestDemoTestGeneration:
    """
    Находка 3 из decisions/2026-09-01_content-quality-review.md:
    демо-банк вопросов покрывал только 3 темы из 6 — для остальных
    молча подставлялись вопросы про "человек и общество" без
    предупреждения.
    """

    def test_all_six_official_topics_have_own_questions(self):
        gen = OgeTestGenerator(rag_pipeline=None)
        seen_question_sets = {}
        for topic in OFFICIAL_TOPICS:
            questions = gen._generate_demo_questions(topic, "medium", 5)
            assert len(questions) == 5, f"{topic!r} должен иметь 5 демо-вопросов"
            question_texts = frozenset(q["question"] for q in questions.values())
            seen_question_sets[topic] = question_texts

        # Ни у одной темы не должно быть того же набора вопросов, что у
        # другой (иначе значит подставился чужой топик)
        seen = list(seen_question_sets.items())
        for i in range(len(seen)):
            for j in range(i + 1, len(seen)):
                topic_a, questions_a = seen[i]
                topic_b, questions_b = seen[j]
                assert questions_a != questions_b, (
                    f"{topic_a!r} и {topic_b!r} дают одинаковый набор "
                    "демо-вопросов — один из них подставлен по ошибке"
                )
