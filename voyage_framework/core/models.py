"""Core Pydantic models для Voyage Framework v4.0.

Все сущности системы: Event, AgentState, ToolResult, SecurityPolicy и др.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_serializer
from ulid import ULID


class EventType(str, Enum):
    """Типы событий в системе."""

    PLAN_CREATED = "plan_created"
    IMPLEMENTATION_DONE = "implementation_done"
    ERROR_LOGGED = "error_logged"
    RULE_ADDED = "rule_added"
    TOOL_EXECUTED = "tool_executed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    SESSION_STARTED = "session_started"
    TASK_COMPLETED = "task_completed"
    RETRY_ATTEMPTED = "retry_attempted"
    DEAD_LETTER_CREATED = "dead_letter_created"
    COMPLEXITY_LIMIT_EXCEEDED = "complexity_limit_exceeded"


class Event(BaseModel):
    """Центральная сущность системы — событие.

    Всё, что происходит в фреймворке, логируется как Event.
    Append-only, replayable, с correlation_id для трассировки.
    """

    event_id: str = Field(default_factory=lambda: str(ULID()), description="ULID — сортируемый ID")
    event_type: EventType = Field(..., description="Тип события")
    payload: dict[str, Any] = Field(default_factory=dict, description="Данные события")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    project_id: str = Field(default="default", description="ID проекта (ADR-005)")
    micro_phase: Optional[str] = Field(default=None, description="Микро-фаза")
    correlation_id: Optional[str] = Field(default=None, description="ID сессии/задачи")
    causation_id: Optional[str] = Field(default=None, description="ID вызвавшего события")
    agent_id: Optional[str] = Field(default=None, description="ID агента")
    role: Optional[str] = Field(default=None, description="Роль агента")

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()

    def to_jsonl(self) -> str:
        """Сериализация в JSONL для append-only хранения."""
        return json.dumps(self.model_dump(), ensure_ascii=False, default=str)

    @classmethod
    def from_jsonl(cls, line: str) -> "Event":
        """Десериализация из JSONL."""
        data = json.loads(line)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)


class AgentStatus(str, Enum):
    """Статусы жизненного цикла агента."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentState(BaseModel):
    """Состояние агента в runtime.

    Сохраняется в checkpoint после каждого node.
    """

    agent_id: str = Field(default_factory=lambda: str(ULID()))
    role: str = Field(..., description="Роль агента")
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    task: str = Field(default="", description="Текущая задача")
    plan: list[str] = Field(default_factory=list)
    current_step: int = Field(default=0)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    results: list[ToolResult] = Field(default_factory=list)
    project_id: str = Field(default="default")
    correlation_id: Optional[str] = None
    checkpoint_id: Optional[str] = None


class ToolResult(BaseModel):
    """Результат выполнения инструмента через SecureExecutor."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    blocked: bool = False
    reason: Optional[str] = None
    approval_required: bool = False
    execution_time_ms: Optional[float] = None


class NodeResult(BaseModel):
    """Результат выполнения узла workflow."""

    node_name: str
    success: bool
    state: AgentState
    output: dict[str, Any] = Field(default_factory=dict)
    transition_to: Optional[str] = None


class SecurityLevel(str, Enum):
    """Уровни безопасности команд."""

    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


class SecurityPolicy(BaseModel):
    """Политика безопасности для SecureExecutor.

    Определяет, какие команды разрешены, какие требуют approval.
    """

    project_root: Path = Field(default=Path("."))
    allowed_commands: set[str] = Field(default_factory=lambda: {
        "git", "pytest", "mypy", "ruff", "python", "pip", "cat", "grep", "find",
        "ls", "pwd", "echo", "df", "ps", "mkdir", "touch",
    })
    dangerous_commands: set[str] = Field(default_factory=lambda: {
        "systemctl", "ssh", "curl", "wget", "rm", "sudo", "chmod", "chown",
        "eval", "exec", "compile", "nc", "nmap", "telnet",
    })
    dangerous_patterns: list[str] = Field(default_factory=lambda: [
        r"rm\s+-rf\s+/",
        r"eval\s*\(",
        r"exec\s*\(",
        r"sudo\s+",
        r"curl\s+.*\|.*sh",
        r"wget\s+.*\|.*sh",
        r">\s*/dev/(null|zero|random)",
        r"mkfs\.",
        r"dd\s+if=",
    ])
    allow_network: bool = False
    max_command_length: int = 4096

    class Config:
        arbitrary_types_allowed = True


class ApprovalStatus(str, Enum):
    """Статусы approval запросов."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Запрос на human approval для dangerous tier команд."""

    request_id: str = Field(default_factory=lambda: str(ULID()))
    command: list[str] = Field(..., description="Команда, требующая approval")
    agent_id: str
    role: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    reason: Optional[str] = None
    ttl_hours: int = Field(default=24, description="Время жизни запроса")

    @field_serializer("timestamp", "approval_timestamp")
    def serialize_dt(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class ProjectContext(BaseModel):
    """Контекст проекта для агентов."""

    project_id: str = Field(default="default")
    name: str = Field(default="")
    description: str = Field(default="")
    tech_stack: list[str] = Field(default_factory=list)
    adr_ids: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    max_tokens: int = Field(default=12000)
    complexity_budget: dict[str, Any] = Field(default_factory=dict)


class TaskSpec(BaseModel):
    """Спецификация задачи для Kimi Code.

    Генерируется TaskGenerator, превращается в TASK.md + CONTEXT.json.
    """

    task_id: str = Field(default_factory=lambda: str(ULID()))
    role: str = Field(..., description="Роль, которая выполняет задачу")
    task: str = Field(..., description="Описание задачи")
    micro_phase: Optional[str] = None
    project_id: str = Field(default="default")
    context_summary: str = Field(default="")
    relevant_files: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    adrs: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    task_markdown: str = Field(default="", description="Готовый TASK.md")
    context_json: dict[str, Any] = Field(default_factory=dict, description="Готовый CONTEXT.json")


class RuleSuggestion(BaseModel):
    """Предложение нового правила от Self-Improving Engine."""

    rule_id: str = Field(default_factory=lambda: str(ULID()))
    pattern: str = Field(..., description="Паттерн ошибки")
    rule_text: str = Field(..., description="Текст правила")
    severity: Literal["must", "should", "may", "experimental"] = "should"
    category: Literal["arch", "ops", "style"] = "ops"
    source_event_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def hash(self) -> str:
        """SHA256 хеш для deduplication."""
        import hashlib
        return hashlib.sha256(f"{self.pattern}:{self.rule_text}".encode()).hexdigest()[:16]
