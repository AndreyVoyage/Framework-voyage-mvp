"""Core Pydantic models для Voyage Framework v4.0.

Все сущности системы: Event, AgentState, ToolResult, SecurityPolicy и др.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from ulid import ULID


class EventType(StrEnum):
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
    MEMORY_STORED = "memory_stored"
    MEMORY_QUERIED = "memory_queried"
    AST_INDEXED = "ast_indexed"
    AST_PARSED = "ast_parsed"
    EVALUATION_COMPLETED = "evaluation_completed"
    RULE_SUGGESTED = "rule_suggested"
    GOLDEN_MATCH_FOUND = "golden_match_found"


class Event(BaseModel):
    """Центральная сущность системы — событие.

    Всё, что происходит в фреймворке, логируется как Event.
    Append-only, replayable, с correlation_id для трассировки.
    """

    event_id: str = Field(default_factory=lambda: str(ULID()), description="ULID — сортируемый ID")
    event_type: EventType = Field(..., description="Тип события")
    payload: dict[str, Any] = Field(default_factory=dict, description="Данные события")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    project_id: str = Field(default="default", description="ID проекта (ADR-005)")
    micro_phase: str | None = Field(default=None, description="Микро-фаза")
    correlation_id: str | None = Field(default=None, description="ID сессии/задачи")
    causation_id: str | None = Field(default=None, description="ID вызвавшего события")
    agent_id: str | None = Field(default=None, description="ID агента")
    role: str | None = Field(default=None, description="Роль агента")

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()

    def to_jsonl(self) -> str:
        """Сериализация в JSONL для append-only хранения."""
        return json.dumps(self.model_dump(), ensure_ascii=False, default=str)

    @classmethod
    def from_jsonl(cls, line: str) -> Event:
        """Десериализация из JSONL."""
        data = json.loads(line)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)


class AgentStatus(StrEnum):
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
    correlation_id: str | None = None
    checkpoint_id: str | None = None
    memory_context: list[SearchResult] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Результат выполнения инструмента через SecureExecutor."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    blocked: bool = False
    reason: str | None = None
    approval_required: bool = False
    execution_time_ms: float | None = None


class NodeResult(BaseModel):
    """Результат выполнения узла workflow."""

    node_name: str
    success: bool
    state: AgentState
    output: dict[str, Any] = Field(default_factory=dict)
    transition_to: str | None = None


class SecurityLevel(StrEnum):
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
        "git", "pytest", "mypy", "ruff", "python", "pip", "docker", "cat", "grep", "find",
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

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ApprovalStatus(StrEnum):
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    approved_by: str | None = None
    approval_timestamp: datetime | None = None
    reason: str | None = None
    ttl_hours: int = Field(default=24, description="Время жизни запроса")

    @field_serializer("timestamp", "approval_timestamp")
    def serialize_dt(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None


class MemoryEntry(BaseModel):
    """Документ для хранения в semantic memory."""

    id: str = Field(..., description="Уникальный ID документа")
    text: str = Field(..., description="Текст для embedding и поиска")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Метаданные документа")
    embedding: list[float] | None = Field(default=None, description="Опциональный вектор")


class SearchResult(BaseModel):
    """Результат semantic search."""

    id: str = Field(..., description="ID найденного документа")
    text: str = Field(default="", description="Текст документа")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Схожесть с запросом")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Метаданные документа")


class Symbol(BaseModel):
    """Символ исходного кода, извлечённый из AST."""

    name: str = Field(..., description="Имя символа")
    kind: Literal["function", "class", "import", "method"] = Field(..., description="Тип символа")
    start_line: int = Field(..., ge=0, description="Начальная строка")
    end_line: int = Field(..., ge=0, description="Конечная строка")
    file: str = Field(..., description="Путь к файлу")
    source: str = Field(default="", description="Исходный текст символа")


class EvaluationResult(BaseModel):
    """Результат оценки качества кода агентом."""

    syntax_valid: bool = Field(default=False, description="Синтаксическая корректность")
    style_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Оценка стиля (ruff)")
    type_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Оценка типизации (mypy)")
    test_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Оценка тестов (pytest)")
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Итоговая оценка")
    details: dict[str, Any] = Field(default_factory=dict, description="Детали проверок")


class FeedbackResult(BaseModel):
    """Результат работы FeedbackLoop."""

    evaluation: EvaluationResult = Field(..., description="Оценка выполнения")
    suggestions: list[str] = Field(default_factory=list, description="Рекомендации")
    new_rules: list[RuleSuggestion] = Field(
        default_factory=list, description="Новые предложенные правила"
    )
    golden_match: SearchResult | None = Field(
        default=None, description="Найденный эталон из GoldenDataset"
    )


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
    micro_phase: str | None = None
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
    source_event_id: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    def hash(self) -> str:
        """SHA256 хеш для deduplication."""
        import hashlib
        return hashlib.sha256(f"{self.pattern}:{self.rule_text}".encode()).hexdigest()[:16]
