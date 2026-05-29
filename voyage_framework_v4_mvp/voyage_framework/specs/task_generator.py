"""Task Generator — генерация TASK.md + CONTEXT.json для Kimi Code.

Генерирует спецификацию задачи на основе роли, контекста проекта и ADR.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from voyage_framework.core.models import EventEngine, Event, EventType, TaskSpec, ProjectContext
from voyage_framework.core.storage import atomic_write


class TaskGenerator:
    """Генератор TASK.md + CONTEXT.json для Kimi Code.

    Читает контекст из EventEngine, компилирует relevant files,
    rules, ADR references и генерирует готовые файлы.
    """

    DEFAULT_RULES = [
        "Все async функции должны иметь type hints",
        "Используй async_sessionmaker и AsyncSession для async SQLAlchemy",
        "Не используй eval(), exec(), compile() с user input",
        "Все секреты через pydantic-settings + .env файл",
        "Каждая новая функция >10 строк обязана иметь >=1 тест",
    ]

    def __init__(self, engine: EventEngine) -> None:
        self.engine = engine

    def generate(
        self,
        role: str,
        task: str,
        micro_phase: Optional[str] = None,
        project_id: str = "default",
        relevant_files: Optional[list[str]] = None,
        adrs: Optional[list[str]] = None,
        criteria: Optional[list[str]] = None,
        instructions: Optional[list[str]] = None,
    ) -> TaskSpec:
        """Сгенерировать TaskSpec с TASK.md и CONTEXT.json.

        Args:
            role: Роль, которая выполняет задачу (developer, architect, etc.)
            task: Описание задачи
            micro_phase: Микро-фаза (M1, M2, ...)
            project_id: ID проекта
            relevant_files: Список релевантных файлов
            adrs: Список ADR
            criteria: Acceptance criteria
            instructions: Дополнительные инструкции

        Returns:
            TaskSpec с готовыми task_markdown и context_json.
        """
        # Собрать контекст проекта
        project_context = self.engine.get_project_context(project_id)

        # Собрать правила
        rules = self.DEFAULT_RULES.copy()
        rules.extend(project_context.get("rules_added", []))

        # Собрать ADR
        all_adrs = adrs or []
        if not all_adrs:
            # По умолчанию ссылаемся на ADR-001 (PostgreSQL)
            all_adrs = ["ADR-001"]

        # Собрать criteria
        default_criteria = [
            f"Код реализует: {task}",
            "mypy проходит без ошибок",
            "pytest проходит без ошибок",
            "ruff check проходит без ошибок",
        ]
        all_criteria = criteria or default_criteria

        # Собрать instructions
        default_instructions = [
            "Напиши код согласно критериям.",
            "Запусти mypy и pytest перед финализацией.
            "Не меняй файлы вне указанных relevant_files.",
        ]
        all_instructions = instructions or default_instructions

        # Собрать relevant files
        all_files = relevant_files or []

        # Сгенерировать TASK.md
        task_md = self._generate_task_md(
            role=role,
            task=task,
            micro_phase=micro_phase,
            project_id=project_id,
            context_summary=project_context,
            relevant_files=all_files,
            rules=rules,
            adrs=all_adrs,
            criteria=all_criteria,
            instructions=all_instructions,
        )

        # Сгенерировать CONTEXT.json
        context_json = {
            "role": role,
            "task": task,
            "micro_phase": micro_phase,
            "project_id": project_id,
            "context_summary": f"Project {project_id}: {project_context.get('total_events', 0)} events",
            "relevant_files": all_files,
            "rules": rules,
            "adrs": all_adrs,
            "criteria": all_criteria,
            "instructions": all_instructions,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "framework_version": "4.0.0",
        }

        spec = TaskSpec(
            role=role,
            task=task,
            micro_phase=micro_phase,
            project_id=project_id,
            context_summary=context_json["context_summary"],
            relevant_files=all_files,
            rules=rules,
            adrs=all_adrs,
            criteria=all_criteria,
            instructions=all_instructions,
            task_markdown=task_md,
            context_json=context_json,
        )

        # Логировать событие
        self.engine.append(Event(
            event_type=EventType.PLAN_CREATED,
            payload={
                "task_id": spec.task_id,
                "role": role,
                "task": task,
                "micro_phase": micro_phase,
            },
            project_id=project_id,
            micro_phase=micro_phase,
        ))

        return spec

    def _generate_task_md(
        self,
        role: str,
        task: str,
        micro_phase: Optional[str],
        project_id: str,
        context_summary: dict[str, Any],
        relevant_files: list[str],
        rules: list[str],
        adrs: list[str],
        criteria: list[str],
        instructions: list[str],
    ) -> str:
        """Сгенерировать markdown TASK.md."""
        files_section = "\n".join(f"- `{f}`" for f in relevant_files) if relevant_files else "- Определи самостоятельно"
        rules_section = "\n".join(f"- {r}" for r in rules)
        adrs_section = "\n".join(f"- [{a}](ADR/{a}.md)" for a in adrs)
        criteria_section = "\n".join(f"- [ ] {c}" for c in criteria)
        instructions_section = "\n".join(f"{i+1}. {inst}" for i, inst in enumerate(instructions))

        return f"""# TASK: {task}

## Context
**Project:** {project_id}
**Events:** {context_summary.get('total_events', 0)} total
**Role:** {role}
**Phase:** Phase 1 | Micro-Phase: {micro_phase or 'N/A'}

## Relevant Files
{files_section}

## Acceptance Criteria
{criteria_section}

## Rules (from RULES.md)
{rules_section}

## ADR References
{adrs_section}

## Instructions
{instructions_section}

---
Generated by Voyage Framework v4.0 | Task ID: will-be-set | Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""

    def write_task_files(
        self,
        spec: TaskSpec,
        task_path: Path | str = "TASK.md",
        context_path: Path | str = "CONTEXT.json",
    ) -> tuple[Path, Path]:
        """Записать TASK.md и CONTEXT.json на диск.

        Returns:
            tuple: (task_path, context_path)
        """
        task_path = Path(task_path)
        context_path = Path(context_path)

        atomic_write(task_path, spec.task_markdown)
        atomic_write(context_path, json.dumps(spec.context_json, indent=2, ensure_ascii=False))

        return task_path, context_path
