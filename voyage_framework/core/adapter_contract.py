"""Immutable interface models for external Voyage adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .agent_registry import default_agent_registry
from .prompt_generator import PromptPackage
from .prompt_modes import default_mode_registry


class AdapterContract(BaseModel):
    """Defines the interface contract for external AI agents."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    version: str = "v4.1.0"
    supported_roles: tuple[str, ...]
    supported_modes: tuple[str, ...]
    required_context_fields: tuple[str, ...]
    optional_context_fields: tuple[str, ...]
    max_task_length: int = Field(gt=0)
    max_prompt_length: int = Field(gt=0)
    approval_required_for: tuple[str, ...]


class AgentRequest(BaseModel):
    """Request from external agent to Voyage."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    role_id: str
    mode_id: str
    task_hint: str | None = None
    project_context: Mapping[str, Any] | None = None

    @model_validator(mode="after")
    def validate_catalog_references(self) -> AgentRequest:
        if not default_agent_registry().has_role(self.role_id):
            raise ValueError(f"Unknown role: {self.role_id}")
        if not default_mode_registry().has_mode(self.mode_id):
            raise ValueError(f"Unknown mode: {self.mode_id}")
        return self


class AgentResponse(BaseModel):
    """Response from Voyage to external agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected", "completed"]
    task_id: str | None = None
    prompt_package: PromptPackage | None = None
    context_snapshot: Mapping[str, Any] | None = None
    next_steps: tuple[str, ...] = ()


class ValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_error_state(self) -> ValidationResult:
        if self.valid and self.errors:
            raise ValueError("A valid result cannot contain errors")
        if not self.valid and not self.errors:
            raise ValueError("An invalid result must contain errors")
        return self


class ApprovalFlow(BaseModel):
    """Defines when human approval is required."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    action: str = Field(min_length=1)
    required: bool
    reason: str | None = None
    timeout_hours: int = Field(gt=0)


def default_adapter_contract() -> AdapterContract:
    """Return the deterministic Phase 7 adapter contract."""
    return AdapterContract(
        supported_roles=tuple(default_agent_registry().list_roles()),
        supported_modes=default_mode_registry().list_modes(),
        required_context_fields=("task_id", "title", "description"),
        optional_context_fields=("acceptance_criteria", "files", "tests", "metadata"),
        max_task_length=10_000,
        max_prompt_length=15_000,
        approval_required_for=("mutate_task", "delete_task", "change_status", "deploy"),
    )
