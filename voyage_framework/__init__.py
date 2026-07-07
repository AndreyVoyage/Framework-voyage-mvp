"""Voyage Framework — a local Project Knowledge OS / Development Memory System.

Voyage Framework provides structured development workflows, task memory,
context packaging, audit logs, and external AI tool handoff for solo developers
and small teams. It is not an AI Agent Framework, autonomous runtime,
orchestration framework, or replacement for LangGraph/CrewAI/AutoGen.
"""

from __future__ import annotations

import importlib
from typing import Any

__version__ = "4.3.0"
__author__ = "AndreyVoyage"

# Legacy / deprecated / non-canonical compatibility exports.
# These names are preserved only for backward compatibility with earlier v4.0
# code. They are not part of the canonical Project Knowledge OS core API.
from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
from voyage_framework.chronicler import (
    DecisionLog,
    DocsBuilder,
    ProcessJournal,
    ReplayGenerator,
    TutorialDraft,
    TutorialGenerator,
)
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import (
    AgentState,
    Event,
    ProjectContext,
    SecurityPolicy,
    ToolResult,
)
from voyage_framework.improvement import (
    Evaluator,
    FeedbackLoop,
    GoldenDataset,
    GoldenSolution,
    RuleEngine,
)
from voyage_framework.langgraph_tools import MermaidExporter, VoyageGraphBuilder
from voyage_framework.memory import CodeSearch, SemanticStore
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.specs.task_generator import TaskGenerator

# Optional exports that require the ``ast`` extra (e.g. ``tree-sitter``).
# These are loaded lazily via ``__getattr__`` so that ``import voyage_framework``
# succeeds in environments without the optional dependency.
_OPTIONAL_EXPORTS = {
    "ASTParser": ("voyage_framework.ast_tools", "ASTParser"),
    "CodeIndexer": ("voyage_framework.ast_tools", "CodeIndexer"),
}


def __getattr__(name: str) -> Any:
    if name in _OPTIONAL_EXPORTS:
        module_name, attr_name = _OPTIONAL_EXPORTS[name]
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise AttributeError(
                f"{name} requires the optional 'ast' extra. Install with: pip install -e \".[ast]\""
            ) from exc
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(name)


__all__ = [
    # Canonical core surfaces
    "Event",
    "AgentState",
    "ToolResult",
    "ProjectContext",
    "EventEngine",
    "SecureExecutor",
    "SecurityPolicy",
    "TaskGenerator",
    "SemanticStore",
    "CodeSearch",
    "ASTParser",
    "CodeIndexer",
    "GoldenDataset",
    "GoldenSolution",
    "RuleEngine",
    "Evaluator",
    "FeedbackLoop",
    "ProcessJournal",
    "ReplayGenerator",
    "DecisionLog",
    "TutorialDraft",
    "TutorialGenerator",
    "DocsBuilder",
    # Legacy / deprecated / non-canonical compatibility surfaces
    "VoyageGraphBuilder",
    "MermaidExporter",
    "LangGraphRuntime",
]
