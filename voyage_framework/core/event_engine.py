"""Event Engine — сердце Voyage Framework.

Append-only event store с SQLite primary и JSONL backup.
Все изменения состояния логируются как Event.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from voyage_framework.core.models import Event, EventType
from voyage_framework.core.storage import append_jsonl, journal_rotate


class EventEngine:
    """Event Store: append-only, replayable, project-scoped.

    Primary: SQLite ( durability, query by project_id/correlation_id).
    Backup: JSONL (human-readable, git-friendly).

    ADR-001: PostgreSQL primary + SQLite fallback.
    MVP использует SQLite (zero-config).
    """

    def __init__(
        self,
        db_path: Path | str = ".voyage/events.db",
        jsonl_path: Path | str = ".voyage/events.jsonl",
    ) -> None:
        self.db_path = Path(db_path)
        self.jsonl_path = Path(jsonl_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Создать таблицы если не существуют."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    project_id TEXT NOT NULL DEFAULT 'default',
                    micro_phase TEXT,
                    correlation_id TEXT,
                    causation_id TEXT,
                    agent_id TEXT,
                    role TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_project
                ON events(project_id, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_correlation
                ON events(correlation_id, timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type
                ON events(event_type, timestamp)
            """)
            conn.commit()

    def append(self, event: Event) -> Event:
        """Добавить событие в store.

        Атомарно: SQLite + JSONL backup.
        """
        # SQLite
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, event_type, payload, timestamp, project_id,
                    micro_phase, correlation_id, causation_id, agent_id, role
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type.value,
                    json.dumps(event.payload, ensure_ascii=False),
                    event.timestamp.isoformat(),
                    event.project_id,
                    event.micro_phase,
                    event.correlation_id,
                    event.causation_id,
                    event.agent_id,
                    event.role,
                ),
            )
            conn.commit()

        # JSONL backup
        append_jsonl(self.jsonl_path, event.model_dump())
        journal_rotate(self.jsonl_path, max_size_bytes=50 * 1024 * 1024)

        return event

    def get_events(
        self,
        project_id: str | None = None,
        event_type: EventType | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Event]:
        """Получить события с фильтрацией."""
        query = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []

        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type.value)
        if correlation_id is not None:
            query += " AND correlation_id = ?"
            params.append(correlation_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        events = []
        for row in rows:
            data = dict(row)
            data["event_type"] = EventType(data["event_type"])
            data["payload"] = json.loads(data["payload"])
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            events.append(Event(**data))

        return events

    def get_events_by_type(
        self,
        event_type: EventType,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Получить события конкретного типа."""
        return self.get_events(
            project_id=project_id,
            event_type=event_type,
            limit=limit,
        )

    def replay(
        self,
        project_id: str | None = None,
        correlation_id: str | None = None,
    ) -> list[Event]:
        """Replay событий в хронологическом порядке.

        Возвращает все события, отсортированные по времени (ASC).
        """
        events = self.get_events(
            project_id=project_id,
            correlation_id=correlation_id,
            limit=10000,
        )
        return sorted(events, key=lambda e: e.timestamp)

    def get_project_context(self, project_id: str) -> dict[str, Any]:
        """Собрать контекст проекта из событий."""
        events = self.get_events(project_id=project_id, limit=1000)

        context: dict[str, Any] = {
            "project_id": project_id,
            "total_events": len(events),
            "event_types": {},
            "latest_events": [],
            "errors": [],
            "rules_added": [],
        }

        for ev in events:
            # Счётчики по типам
            et = ev.event_type.value
            context["event_types"][et] = context["event_types"].get(et, 0) + 1

            # Последние 10 событий
            if len(context["latest_events"]) < 10:
                context["latest_events"].append(
                    {
                        "event_id": ev.event_id,
                        "type": et,
                        "timestamp": ev.timestamp.isoformat(),
                        "payload_keys": list(ev.payload.keys()),
                    }
                )

            # Ошибки
            if ev.event_type == EventType.ERROR_LOGGED:
                context["errors"].append(ev.payload)

            # Добавленные правила
            if ev.event_type == EventType.RULE_ADDED:
                context["rules_added"].append(ev.payload.get("rule_text", ""))

        return context

    def count(self, project_id: str | None = None) -> int:
        """Количество событий."""
        query = "SELECT COUNT(*) FROM events WHERE 1=1"
        params: list[Any] = []

        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0

    def close(self) -> None:
        """Закрыть соединения (SQLite автоматически закрывается)."""
        pass
