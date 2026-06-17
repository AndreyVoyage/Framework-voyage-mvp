"""Адаптер checkpoint LangGraph → EventEngine."""

from __future__ import annotations

from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType
from voyage_framework.langgraph_tools.state import VoyageState


class EventEngineCheckpoint:
    """Сохраняет node transitions в EventEngine для восстановления state."""

    def __init__(self, engine: EventEngine, project_id: str = "default") -> None:
        self.engine = engine
        self.project_id = project_id

    def on_node_start(self, node_name: str, state: VoyageState) -> None:
        """Залогировать начало ноды."""
        self._append(
            EventType.NODE_STARTED,
            {
                "node_name": node_name,
                "state": state.model_dump(mode="json"),
                "correlation_id": state.correlation_id,
            },
            state,
        )

    def on_node_end(self, node_name: str, state: VoyageState) -> None:
        """Залогировать завершение ноды."""
        self._append(
            EventType.NODE_COMPLETED,
            {
                "node_name": node_name,
                "state": state.model_dump(mode="json"),
                "correlation_id": state.correlation_id,
            },
            state,
        )

    def on_edge_taken(
        self,
        from_node: str,
        to_node: str,
        condition: Any | None = None,
    ) -> None:
        """Залогировать переход по ребру."""
        self.engine.append(
            Event(
                event_type=EventType.EDGE_TAKEN,
                payload={
                    "from_node": from_node,
                    "to_node": to_node,
                    "condition": condition,
                    "project_id": self.project_id,
                },
                project_id=self.project_id,
            )
        )

    def get_state(self, correlation_id: str) -> VoyageState | None:
        """Восстановить последнее состояние по correlation_id."""
        events = self.engine.get_events(
            event_type=EventType.NODE_COMPLETED,
            correlation_id=correlation_id,
            limit=1,
        )
        if not events:
            return None
        data = events[0].payload.get("state")
        return VoyageState(**data) if data else None

    def _append(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        state: VoyageState,
    ) -> None:
        self.engine.append(
            Event(
                event_type=event_type,
                payload=payload,
                project_id=self.project_id,
                correlation_id=state.correlation_id,
                agent_id=state.agent_id,
                role=state.role,
            )
        )
