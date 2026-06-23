"""Voyage Framework — a local Project Knowledge OS / Development Memory System.

Voyage Framework provides structured development workflows, task memory,
context packaging, audit logs, and external AI tool handoff for solo developers
and small teams. It is not an AI Agent Framework, autonomous runtime,
orchestration framework, or replacement for LangGraph/CrewAI/AutoGen.
"""

__version__ = "4.0.0"
__author__ = "AndreyVoyage"

# Legacy / deprecated / non-canonical compatibility exports.
# These names are preserved only for backward compatibility with earlier v4.0
# code. They are not part of the canonical Project Knowledge OS core API.
from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
from voyage_framework.ast_tools import ASTParser, CodeIndexer
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
