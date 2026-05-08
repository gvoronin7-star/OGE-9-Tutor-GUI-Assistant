# -*- coding: utf-8 -*-
"""Административные компоненты GUI."""

# Существующие компоненты (из v1.0)
from ..chat_panel import ChatPanel
from ..rag_panel import RAGPanel
from ..metrics_panel import MetricsPanel
from ..database_panel import DatabasePanel

# Новые компоненты
from .logs_viewer import LogsViewer
from .cache_manager import CacheManager
from .llm_monitor import LLMMonitor
from .config_panel import ConfigPanel
from .users_panel import UsersPanel
from .rag_manager import RAGManager

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
    "RAGManager"
]
