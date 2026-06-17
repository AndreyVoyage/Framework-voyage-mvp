"""DecisionLog — хранение решений и их обоснований."""

from __future__ import annotations

from datetime import UTC, datetime

from ulid import ULID

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType


class DecisionLog:
    """Лог архитектурных и процессных решений."""

    def __init__(self, engine: EventEngine) -> None:
        self.engine = engine

    def record_decision(
        self,
        context: str,
        question: str,
        options: list[str],
        chosen: str,
        rationale: str,
        adrs: list[str] | None = None,
        project_id: str = "default",
    ) -> Event:
        """Записать одно решение."""
        payload = {
            "ulid": str(ULID()),
            "timestamp": datetime.now(UTC).isoformat(),
            "context": context,
            "question": question,
            "options": options,
            "chosen": chosen,
            "rationale": rationale,
            "adrs": adrs or [],
            "project_id": project_id,
        }

        event = Event(
            event_type=EventType.DECISION_RECORDED,
            payload=payload,
            project_id=project_id,
        )
        return self.engine.append(event)

    def get_decisions(
        self,
        project_id: str | None = None,
        adr: str | None = None,
    ) -> list[Event]:
        """Получить решения с фильтрацией."""
        events = self.engine.get_events(
            event_type=EventType.DECISION_RECORDED,
            project_id=project_id,
            limit=10000,
        )
        if adr:
            events = [e for e in events if adr in (e.payload.get("adrs") or [])]
        return events

    def get_rationale_for(self, adr: str) -> list[str]:
        """Получить обоснования для ADR."""
        decisions = self.get_decisions(adr=adr)
        return [e.payload.get("rationale", "") for e in decisions if e.payload.get("rationale")]

    def generate_adr_update_draft(self, adr: str) -> str:
        """Сгенерировать markdown-черновик для обновления ADR."""
        decisions = self.get_decisions(adr=adr)
        lines = [f"# ADR Update Draft: {adr}", ""]

        for event in decisions:
            payload = event.payload
            lines.append(f"## {payload.get('context', 'Decision')}")
            lines.append("")
            lines.append(f"**Question:** {payload.get('question', '')}")
            lines.append("")
            lines.append(f"**Chosen:** {payload.get('chosen', '')}")
            lines.append("")
            lines.append(f"**Rationale:** {payload.get('rationale', '')}")
            lines.append("")
            options = payload.get("options", [])
            if options:
                lines.append("**Options considered:**")
                for option in options:
                    marker = "✅" if option == payload.get("chosen") else "❌"
                    lines.append(f"- {marker} {option}")
                lines.append("")

        return "\n".join(lines)
