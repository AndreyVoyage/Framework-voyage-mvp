"""Task Models — Pydantic models для task.yaml и TaskParser.

TaskYamlSpec — описание задачи из YAML (source of truth).
TaskFiles — список файлов для чтения/модификации.

Важно: это НЕ runtime-модели. Нет created_at, updated_at и т.д.
Runtime модели будут в Phase 2 (TaskRecord).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskFiles(BaseModel):
    """Файлы, связанные с задачей."""

    read: list[str] = Field(default_factory=list, description="Файлы для чтения")
    modify: list[str] = Field(default_factory=list, description="Файлы для изменения")


class TaskYamlSpec(BaseModel):
    """Спецификация задачи из task.yaml — source of truth.

    Не содержит runtime-полей (created_at, updated_at и т.д.).
    Генерируется из task.yaml через TaskParser.
    """

    id: str = Field(..., description="Уникальный ID задачи (VF-001, ST-001)")
    title: str = Field(..., min_length=1, max_length=200, description="Краткое название задачи")
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Подробное описание задачи",
    )
    role: str = Field(..., description="Роль исполнителя (developer, architect, devops...)")
    mode: str | None = Field(
        default="solution",
        description="Режим: discover, design, solution, plan, implement",
    )
    priority: str | None = Field(
        default="medium",
        description="Приоритет: high, medium, low",
    )
    status: str = Field(
        default="pending",
        description="Статус задачи (для новых задач только 'pending')",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Критерии приёмки (минимум 1)",
    )
    files: TaskFiles | None = Field(
        default=None,
        description="Файлы для чтения/модификации",
    )
    tests: list[str] | None = Field(
        default=None,
        description="Команды тестирования",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метаданные",
    )

    model_config = ConfigDict(frozen=True)

    @field_validator("id")
    @classmethod
    def _validate_id_format(cls, value: str) -> str:
        import re

        if re.fullmatch(r"(?:VF|ST)-\d{3,}", value) is None:
            raise ValueError("id must match ^(VF|ST)-\\d{3,}$")
        return value

    @field_validator("acceptance_criteria")
    @classmethod
    def _validate_criteria_not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("acceptance_criteria must contain at least one item")
        return value

    @field_validator("status")
    @classmethod
    def _validate_status_allowed(cls, value: str) -> str:
        allowed = {"pending", "in_progress", "blocked", "completed", "failed", "archived"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}, got '{value}'")
        return value

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"high", "medium", "low"}
        if value not in allowed:
            raise ValueError(f"priority must be one of {allowed}, got '{value}'")
        return value

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"discover", "design", "solution", "plan", "implement"}
        if value not in allowed:
            raise ValueError(f"mode must be one of {allowed}, got '{value}'")
        return value

    @field_validator("role")
    @classmethod
    def _validate_role_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("role must not be empty")
        return value


class TaskRecord:
    """Runtime-запись задачи в SQLite.

    Mutable. Хранит текущее состояние задачи: статус, timestamps и т.д.
    Создаётся TaskEngine из TaskYamlSpec. Не содержит Pydantic-валидации
    (валидация уже пройдена на этапе TaskParser → TaskYamlSpec).

    Разделение:
        TaskYamlSpec = immutable description from task.yaml
        TaskRecord = mutable runtime state from SQLite
    """

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        role: str,
        status: str = "pending",
        priority: str | None = None,
        mode: str | None = None,
        source_path: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        archived_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.role = role
        self.status = status
        self.priority = priority
        self.mode = mode
        self.source_path = source_path
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or self.created_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.archived_at = archived_at
        self.metadata = metadata or {}
        self.acceptance_criteria = acceptance_criteria or []

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в dict (для EventEngine payload)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "role": self.role,
            "status": self.status,
            "priority": self.priority,
            "mode": self.mode,
            "source_path": self.source_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "metadata": self.metadata,
            "acceptance_criteria": self.acceptance_criteria,
        }

    def __repr__(self) -> str:
        return f"<TaskRecord {self.id[:8]} {self.status} '{self.title[:40]}'>"
