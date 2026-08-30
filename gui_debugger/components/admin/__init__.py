# -*- coding: utf-8 -*-
"""Административные компоненты GUI."""

# Существующие компоненты (из v1.0)
from ..chat_panel import ChatPanel
from ..database_panel import DatabasePanel
from ..metrics_panel import MetricsPanel
from ..rag_panel import RAGPanel
from .cache_manager import CacheManager
from .config_panel import ConfigPanel
from .llm_monitor import LLMMonitor

# Новые компоненты
from .logs_viewer import LogsViewer
from .rag_manager import RAGManager
from .users_panel import UsersPanel

__all__ = [
    # Существующие
    "ChatPanel",
    "RAGPanel",
    "MetricsPanel",
    "DatabasePanel",
    # Новые
    "LogsViewer",
    "CacheManager",
    "LLMMonitor",
    "ConfigPanel",
    "UsersPanel",
    "RAGManager",
]
