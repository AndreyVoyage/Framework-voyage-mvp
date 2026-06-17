"""ProcessJournal — запись шагов процесса разработки в EventEngine."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from ulid import ULID

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType


class ProcessJournal:
    """Журнал шагов разработки, сохраняемый в EventEngine."""

    STEP_TYPES: set[str] = {
        "plan",
        "code",
        "test",
        "commit",
        "review",
        "deploy",
        "audit",
        "fix",
    }

    def __init__(
        self,
        engine: EventEngine,
        project_id: str = "default",
        correlation_id: str | None = None,
    ) -> None:
        self.engine = engine
        self.project_id = project_id
        self.correlation_id = correlation_id

    def record_step(
        self,
        step_type: str,
        description: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        decision: dict[str, Any] | None = None,
        command: str | None = None,
    ) -> Event:
        """Записать один шаг процесса разработки."""
        if step_type not in self.STEP_TYPES:
            raise ValueError(f"Unknown step_type: {step_type}. Use one of {self.STEP_TYPES}")

        payload = {
            "ulid": str(ULID()),
            "timestamp": datetime.now(UTC).isoformat(),
            "step_type": step_type,
            "description": description,
            "inputs": inputs or {},
            "outputs": outputs or {},
            "decision": decision,
            "command": command,
            "project_id": self.project_id,
            "correlation_id": self.correlation_id,
        }

        event = Event(
            event_type=EventType.PROCESS_STEP,
            payload=payload,
            project_id=self.project_id,
            correlation_id=self.correlation_id,
        )
        return self.engine.append(event)

    def get_steps(
        self,
        correlation_id: str | None = None,
        step_type: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Получить шаги процесса с фильтрацией."""
        events = self.engine.get_events(
            event_type=EventType.PROCESS_STEP,
            project_id=self.project_id,
            correlation_id=correlation_id or self.correlation_id,
            limit=limit,
        )
        if step_type:
            events = [e for e in events if e.payload.get("step_type") == step_type]
        return events

    def get_step_count(self, correlation_id: str | None = None) -> int:
        """Количество шагов для correlation_id."""
        return len(
            self.engine.get_events(
                event_type=EventType.PROCESS_STEP,
                project_id=self.project_id,
                correlation_id=correlation_id or self.correlation_id,
                limit=10000,
            )
        )

    def get_last_step(self, correlation_id: str | None = None) -> Event | None:
        """Последний шаг для correlation_id."""
        events = self.get_steps(correlation_id=correlation_id or self.correlation_id, limit=1)
        return events[0] if events else None

    @staticmethod
    def _sanitize(value: str) -> str:
        """Очистить строку для использования в имени файла."""
        return re.sub(r"[^\w\-_.]", "_", value)
