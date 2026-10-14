# -*- coding: utf-8 -*-
"""
Чистые функции разбора журнала запросов (requests_detailed.csv).

Модуль не импортирует tkinter и ttkbootstrap: его используют вкладка
«Logs» админ-режима и тесты, которые работают без дисплея.
"""

import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ALL_COMPONENTS = "Все"
SUCCESS_STATUS = "success"

# (время, user_id, компонент, действие, длительность мс, статус)
TableRow = Tuple[str, str, str, str, str, str]


def _field(row: Dict[Any, Any], key: str) -> str:
    """Значение поля как строка; None (короткая строка CSV) -> пустая строка."""
    value = row.get(key)
    return value if isinstance(value, str) else ""


def is_valid_row(row: Dict[Any, Any]) -> bool:
    """Строка пригодна, если в ней есть метка времени (обрезанные строки - нет)."""
    return bool(_field(row, "timestamp").strip())


def load_rows(path: Path) -> List[Dict[str, str]]:
    """
    Прочитать журнал запросов.

    Нет файла - пустой список. Битые строки (без timestamp) пропускаются.
    Ошибки чтения файла (права, кодировка) не глотаются - их показывает
    вызывающий код.
    """
    if not path.exists():
        return []
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if is_valid_row(row):
                rows.append({k: v for k, v in row.items() if isinstance(k, str)})
    return rows


def format_time(timestamp: str) -> str:
    """Метка ISO (в т.ч. с микросекундами) -> ЧЧ:ММ:СС; неразбираемая - как есть."""
    try:
        return datetime.fromisoformat(timestamp.strip()).strftime("%H:%M:%S")
    except ValueError:
        return timestamp


def row_to_values(row: Dict[Any, Any]) -> TableRow:
    """Строка CSV -> кортеж значений для таблицы."""
    return (
        format_time(_field(row, "timestamp")),
        _field(row, "user_id"),
        _field(row, "component"),
        _field(row, "action"),
        _field(row, "duration_ms"),
        _field(row, "status"),
    )


def unique_components(rows: Iterable[Dict[Any, Any]]) -> List[str]:
    """Значения фильтра «Компонент»: «Все» плюс отсортированные уникальные."""
    found = {_field(r, "component") for r in rows}
    found.discard("")
    return [ALL_COMPONENTS] + sorted(found)


def parse_duration(value: Optional[str]) -> Optional[float]:
    """duration_ms -> число; пустое, нечисловое, NaN и inf -> None."""
    try:
        number = float(value) if value is not None else math.nan
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def compute_stats(rows: List[Dict[Any, Any]]) -> Tuple[int, float, float, int]:
    """
    Статистика: (всего, среднее duration_ms, доля ошибок в %, число ошибок).

    Ошибка - status, отличный от "success". Строки с пустым или нечисловым
    duration_ms в среднее не входят. Пустой вход - нули.
    """
    total = len(rows)
    if total == 0:
        return 0, 0.0, 0.0, 0
    durations = [
        d
        for d in (parse_duration(_field(r, "duration_ms")) for r in rows)
        if d is not None
    ]
    avg = sum(durations) / len(durations) if durations else 0.0
    errors = sum(1 for r in rows if _field(r, "status") != SUCCESS_STATUS)
    return total, avg, errors / total * 100, errors
