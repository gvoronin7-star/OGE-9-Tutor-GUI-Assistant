# -*- coding: utf-8 -*-
"""Тесты путей от корня проекта, разбора журнала и очистки логов (В-14)."""

import csv
import re
from pathlib import Path

from utils.advanced_logger import DetailedRequestLogger
from utils.log_rows import (
    ALL_COMPONENTS,
    compute_stats,
    format_time,
    load_rows,
    parse_duration,
    row_to_values,
    unique_components,
)
from utils.paths import (
    DATA_DIR,
    GUI_CONFIG_FILE,
    LOGS_DIR,
    PROJECT_ROOT,
    RAG_DB_DIR,
)


def _read(path: Path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_paths_independent_of_cwd(tmp_path, monkeypatch):
    """Красный, если пути снова станут относительными или от cwd."""
    monkeypatch.chdir(tmp_path)
    for p in (PROJECT_ROOT, LOGS_DIR, DATA_DIR, RAG_DB_DIR, GUI_CONFIG_FILE):
        assert p.is_absolute()
        assert PROJECT_ROOT == p or PROJECT_ROOT in p.parents
        assert tmp_path not in p.parents
    assert (PROJECT_ROOT / "utils" / "paths.py").exists()
    assert LOGS_DIR == PROJECT_ROOT / "logs"


def test_load_rows_missing_file(tmp_path):
    """Красный, если отсутствие файла роняет вкладку."""
    rows = load_rows(tmp_path / "nope.csv")
    assert rows == []
    assert compute_stats(rows) == (0, 0.0, 0.0, 0)
    assert unique_components(rows) == [ALL_COMPONENTS]


def test_load_rows_skips_broken_and_parses(tmp_path):
    """Красный, если битая строка попадает в таблицу или ломает разбор."""
    logger = DetailedRequestLogger(tmp_path)
    logger.log_request("rag", "query", {"q": 1}, {"a": 2}, 12.5, user_id=7)
    logger.log_request("llm", "generate", {}, None, 30, status="error")
    with open(logger.requests_file, "a", encoding="utf-8", newline="") as f:
        f.write("\n,,\n")  # пустая и обрезанная строки (без timestamp)
    rows = load_rows(logger.requests_file)
    assert len(rows) == 2
    values = row_to_values(rows[0])
    assert values[1:] == ("7", "rag", "query", "12.50", "success")
    assert re.match(r"^\d{2}:\d{2}:\d{2}$", values[0])
    assert unique_components(rows) == [ALL_COMPONENTS, "llm", "rag"]


def test_row_to_values_short_row():
    """Красный, если None в коротком ряду падает на срезе/конкатенации."""
    assert row_to_values({"timestamp": "2026-01-01T10:20:30", "user_id": None}) == (
        "10:20:30",
        "",
        "",
        "",
        "",
        "",
    )


def test_format_time_microseconds_and_garbage():
    """Красный, если время снова режется по символам (7.486426) или
    неразбираемая метка превращается в пустую строку/исключение."""
    assert format_time("2026-10-14T23:43:17.486426") == "23:43:17"
    assert format_time("2026-10-14T23:43:17") == "23:43:17"
    assert format_time("garbage") == "garbage"


def test_stats_skip_bad_duration_and_count_errors():
    """Красный, если пустой/нечисловой duration_ms роняет среднее или
    ошибка считается по другому признаку, чем status != success."""
    rows = [
        {"duration_ms": "10", "status": "success"},
        {"duration_ms": "30.00", "status": "error"},
        {"duration_ms": "", "status": "timeout"},
        {"duration_ms": "abc", "status": "success"},
        {"duration_ms": None, "status": "success"},
    ]
    total, avg, rate, errors = compute_stats(rows)
    assert (total, avg, errors) == (5, 20.0, 2)
    assert rate == 40.0
    assert parse_duration("nan") is None and parse_duration("1e3") == 1000.0


def test_clear_keeps_file_and_logger_keeps_working(tmp_path):
    """Красный, если clear() удаляет файл/теряет заголовок или после него
    log_request перестаёт дописывать."""
    logger = DetailedRequestLogger(tmp_path)
    logger.log_request("rag", "query", {}, None, 1.0)
    logger.log_request(
        "rag", "query", {}, None, 2.0, status="error", error_message="boom"
    )
    assert len(_read(logger.requests_file)) == 3

    logger.clear()
    assert _read(logger.requests_file) == [list(logger.REQUESTS_HEADER)]
    assert _read(logger.errors_file) == [list(logger.ERRORS_HEADER)]

    logger.clear()  # повторная очистка - без ошибки
    assert _read(logger.requests_file) == [list(logger.REQUESTS_HEADER)]

    logger.log_request("llm", "generate", {}, None, 3.0)
    rows = _read(logger.requests_file)
    assert len(rows) == 2 and rows[1][3] == "llm"
    assert load_rows(logger.requests_file)[0]["component"] == "llm"


def test_clear_does_not_touch_other_log_files(tmp_path):
    """Красный, если очистка снова удаляет *.log/*.json."""
    logger = DetailedRequestLogger(tmp_path)
    (tmp_path / "all.log").write_text("x", encoding="utf-8")
    (tmp_path / "app.json").write_text("{}", encoding="utf-8")
    logger.clear()
    assert (tmp_path / "all.log").read_text(encoding="utf-8") == "x"
    assert (tmp_path / "app.json").exists()
