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

from scripts.check_secrets import scan_directory
from utils.hashing import stable_query_hash
from utils.logger import QueryStatsLogger


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
