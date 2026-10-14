# -*- coding: utf-8 -*-
"""
Единый источник корня проекта и производных путей.

Пути считаются от расположения этого файла, а не от текущего каталога
процесса, поэтому не зависят от того, откуда запущена программа.
Модуль использует только стандартную библиотеку.
"""

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

LOGS_DIR: Path = PROJECT_ROOT / "logs"
DATA_DIR: Path = PROJECT_ROOT / "data"
RAG_DB_DIR: Path = PROJECT_ROOT / "RAG_data_base"
ENV_FILE: Path = PROJECT_ROOT / ".env"
GUI_CONFIG_FILE: Path = PROJECT_ROOT / "gui_debugger" / "config.json"
