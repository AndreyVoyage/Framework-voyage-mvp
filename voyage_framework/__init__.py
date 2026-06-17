"""Voyage AI Dev Framework v4.0 — AI-Native Engineering Operating System.

Фреймворк для solo-разработчика, который делегирует рутину AI,
но контролирует критичные моменты через governance layer.
"""

__version__ = "4.0.0"
__author__ = "AndreyVoyage"

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import (
    AgentState,
    Event,
    ProjectContext,
    SecurityPolicy,
    ToolResult,
)
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.specs.task_generator import TaskGenerator

__all__ = [
    "Event",
    "AgentState",
    "ToolResult",
    "ProjectContext",
    "EventEngine",
    "SecureExecutor",
    "SecurityPolicy",
    "TaskGenerator",
]
