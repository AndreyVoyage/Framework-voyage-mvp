"""Task Models — Pydantic models для task.yaml и TaskParser.

TaskYamlSpec — описание задачи из YAML (source of truth).
TaskFiles — список файлов для чтения/модификации.

Важно: это НЕ runtime-модели. Нет created_at, updated_at и т.д.
Runtime модели будут в Phase 2 (TaskRecord).
"""

from __future__ import annotations

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
