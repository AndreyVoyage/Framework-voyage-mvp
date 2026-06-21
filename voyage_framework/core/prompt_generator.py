"""Детерминированная подготовка prompt packages без выполнения агентов."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .agent_registry import AgentRegistry, RoleProfile, default_agent_registry
from .prompt_modes import ModeProfile, ModeRegistry, default_mode_registry
from .task_models import TaskYamlSpec


class PromptGenerationError(ValueError):
    """Prompt package невозможно сформировать из переданных данных."""


class PromptPackage(BaseModel):
    """Неизменяемый пакет prompt-текста для внешнего AI-инструмента."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: str
    mode_id: str
    task_id: str
    title: str
    system_prompt: str
    user_prompt: str
    checklist: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    def as_messages(self) -> list[dict[str, str]]:
        """Вернуть стандартное system/user представление без runtime-вызова."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]


class PromptGenerator:
    """Read-only генератор deterministic prompt packages."""

    def __init__(
        self,
        *,
        agent_registry: AgentRegistry | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._agent_registry = agent_registry or default_agent_registry()
        self._mode_registry = mode_registry or default_mode_registry()

    def generate(
        self,
        *,
        task: TaskYamlSpec,
        role_id: str,
        mode_id: str,
        project_context: Mapping[str, Any] | None = None,
    ) -> PromptPackage:
        """Сформировать пакет, не изменяя task, registries или внешнее состояние."""
        try:
            role = self._agent_registry.require(role_id)
        except KeyError as exc:
            raise PromptGenerationError(f"Unknown role: {role_id}") from exc
        mode = self._mode_registry.require(mode_id)
        context = self._normalize_context(project_context)

        return PromptPackage(
            role_id=role_id,
            mode_id=mode_id,
            task_id=task.id,
            title=task.title,
            system_prompt=self._system_prompt(role, mode),
            user_prompt=self._user_prompt(task, context),
            checklist=tuple(mode.checklist) + tuple(task.acceptance_criteria),
            metadata={
                "priority": task.priority,
                "source_role": task.role,
                "source_mode": task.mode,
                "project_context": context,
            },
        )

    @staticmethod
    def _normalize_context(project_context: Mapping[str, Any] | None) -> dict[str, Any]:
        if project_context is None:
            return {}
        try:
            encoded = json.dumps(dict(project_context), sort_keys=True, ensure_ascii=False)
            normalized: dict[str, Any] = json.loads(encoded)
        except (TypeError, ValueError) as exc:
            raise PromptGenerationError("Project context must be JSON-serializable") from exc
        return normalized

    @classmethod
    def _system_prompt(cls, role: RoleProfile, mode: ModeProfile) -> str:
        sections = [
            f"Role: {role.display_name} ({role.role_id})\nPurpose: {role.purpose}",
            cls._section("Role responsibilities", role.responsibilities),
            cls._section(
                "Role capabilities",
                tuple(f"{item.id}: {item.description}" for item in role.capabilities),
            ),
            cls._section(
                "Role boundaries",
                tuple(f"{item.id}: {item.description}" for item in role.boundaries),
            ),
            f"Mode: {mode.display_name} ({mode.id})\nPurpose: {mode.purpose}",
            cls._section("Mode instructions", mode.instructions),
            cls._section("Mode constraints", mode.constraints),
            cls._section(
                "Output expectations", role.output_expectations + mode.output_expectations
            ),
            cls._section(
                "Global constraints",
                (
                    "Do not commit / do not push unless instructed.",
                    "Do not modify files outside task scope.",
                    "Report deviations instead of guessing.",
                ),
            ),
        ]
        return "\n\n".join(sections)

    @classmethod
    def _user_prompt(cls, task: TaskYamlSpec, context: dict[str, Any]) -> str:
        sections = [
            f"Task ID: {task.id}\nTitle: {task.title}\nDescription: {task.description}",
            cls._section("Acceptance criteria", task.acceptance_criteria),
        ]
        if task.files is not None:
            sections.extend(
                (
                    cls._section("Allowed files to read", task.files.read),
                    cls._section("Allowed files to modify", task.files.modify),
                )
            )
        if task.tests:
            sections.append(cls._section("Tests", task.tests))
        if context:
            sections.append(
                "Project context (reference only):\n"
                + json.dumps(context, sort_keys=True, ensure_ascii=False, indent=2)
            )
        return "\n\n".join(sections)

    @staticmethod
    def _section(title: str, items: Sequence[str]) -> str:
        lines = "\n".join(f"- {item}" for item in items) if items else "- None"
        return f"{title}:\n{lines}"


def default_prompt_generator() -> PromptGenerator:
    """Создать генератор со стандартными role и mode registries."""
    return PromptGenerator()
