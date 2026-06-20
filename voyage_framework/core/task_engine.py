"""Task Engine — жизненный цикл задач с SQLite persistence и EventEngine logging.

TaskEngine управляет runtime-состоянием задач. Только он меняет статус TaskRecord.
EventEngine — append-only audit log, не управляет задачами.

Архитектура:
    TaskYamlSpec (immutable) → TaskEngine → TaskRecord (mutable in SQLite)
                                         ↓
                                    EventEngine (append-only log)

Использует sqlite3 sync (ADR-009).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType
from voyage_framework.core.task_models import TaskRecord, TaskYamlSpec


class TaskEngineError(Exception):
    """Базовая ошибка TaskEngine."""

    pass


class TaskNotFoundError(TaskEngineError):
    """Задача не найдена."""

    pass


class TaskAlreadyExistsError(TaskEngineError):
    """Задача с таким ID уже существует."""

    pass


class TaskTransitionError(TaskEngineError):
    """Невалидный переход статуса."""

    pass


class TaskEngine:
    """Управляет жизненным циклом задач: создание, переходы, запросы."""

    VALID_TRANSITIONS: dict[str, set[str]] = {
        "pending": {"in_progress", "blocked"},
        "in_progress": {"blocked", "completed", "failed", "archived"},
        "blocked": {"in_progress", "archived"},
        "failed": {"in_progress", "archived"},
        "completed": {"archived"},
        "archived": set(),
    }

    _EVENT_MAP: dict[str, EventType] = {
        "pending": EventType.TASK_CREATED,
        "in_progress": EventType.TASK_STARTED,
        "blocked": EventType.TASK_BLOCKED,
        "completed": EventType.TASK_COMPLETED,
        "failed": EventType.TASK_FAILED,
        "archived": EventType.TASK_ARCHIVED,
    }

    def __init__(
        self,
        db_path: Path | str = ".voyage/tasks.db",
        event_engine: EventEngine | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.event_engine = event_engine
        self._init_db()

    def _init_db(self) -> None:
        """Создать таблицу tasks и индексы."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT,
                    mode TEXT,
                    source_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    archived_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    criteria_json TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_status_role
                ON tasks(status, role)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_status_updated
                ON tasks(status, updated_at)
                """
            )
            conn.commit()

    def _now(self) -> datetime:
        """UTC-aware timestamp."""
        return datetime.now(UTC)

    def _log_event(
        self,
        event_type: EventType,
        task_id: str,
        old_status: str | None,
        new_status: str,
        actor: str,
        reason: str | None,
        source_path: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Записать событие в EventEngine, если доступно."""
        if self.event_engine is None:
            return

        event = Event(
            event_type=event_type,
            payload={
                "task_id": task_id,
                "actor": actor,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "source_path": source_path,
                "timestamp": self._now().isoformat(),
                "metadata": metadata or {},
            },
            correlation_id=task_id,
        )
        self.event_engine.append(event)

    # ───────────────────────────────────────────────────────────
    # CRUD
    # ───────────────────────────────────────────────────────────

    def create_from_spec(self, spec: TaskYamlSpec) -> TaskRecord:
        """Создать TaskRecord из TaskYamlSpec.

        Raises:
            TaskAlreadyExistsError: если задача с таким ID уже существует.
        """
        if self.get(spec.id) is not None:
            raise TaskAlreadyExistsError(f"Task {spec.id} already exists")

        now = self._now()
        record = TaskRecord(
            id=spec.id,
            title=spec.title,
            description=spec.description,
            role=spec.role,
            status=spec.status,
            priority=spec.priority,
            mode=spec.mode,
            source_path=spec.metadata.get("source_path"),
            created_at=now,
            updated_at=now,
            metadata={k: v for k, v in spec.metadata.items() if k != "source_path"},
            acceptance_criteria=list(spec.acceptance_criteria),
        )

        self._insert_record(record)
        self._log_event(
            EventType.TASK_CREATED,
            record.id,
            old_status=None,
            new_status=record.status,
            actor="cli",
            reason=None,
            source_path=record.source_path,
            metadata=record.metadata,
        )
        return record

    def _insert_record(self, record: TaskRecord) -> None:
        """INSERT TaskRecord в SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, title, description, role, status, priority, mode,
                    source_path, created_at, updated_at, started_at,
                    completed_at, archived_at, metadata_json, criteria_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.title,
                    record.description,
                    record.role,
                    record.status,
                    record.priority,
                    record.mode,
                    record.source_path,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    record.started_at.isoformat() if record.started_at else None,
                    record.completed_at.isoformat() if record.completed_at else None,
                    record.archived_at.isoformat() if record.archived_at else None,
                    json.dumps(record.metadata, ensure_ascii=False),
                    json.dumps(record.acceptance_criteria, ensure_ascii=False),
                ),
            )
            conn.commit()

    def get(self, task_id: str) -> TaskRecord | None:
        """Получить TaskRecord по ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._row_to_record(dict(row)) if row else None

    def list(
        self,
        status: str | None = None,
        role: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskRecord]:
        """Список задач с фильтрацией."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []

        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if role is not None:
            query += " AND role = ?"
            params.append(role)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_record(dict(row)) for row in rows]

    def delete(self, task_id: str) -> bool:
        """Удалить задачу."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ───────────────────────────────────────────────────────────
    # Transitions
    # ───────────────────────────────────────────────────────────

    def transition(
        self,
        task_id: str,
        new_status: str,
        reason: str | None = None,
        actor: str = "cli",
    ) -> TaskRecord:
        """Перевести задачу в новый статус с валидацией.

        Raises:
            TaskNotFoundError: задача не найдена.
            TaskTransitionError: невалидный переход.
        """
        record = self.get(task_id)
        if record is None:
            raise TaskNotFoundError(f"Task {task_id} not found")

        old_status = record.status

        if new_status not in self.VALID_TRANSITIONS[old_status]:
            allowed = sorted(self.VALID_TRANSITIONS[old_status])
            raise TaskTransitionError(
                f"Invalid transition: {old_status} → {new_status}. "
                f"Allowed: {allowed}"
            )

        now = self._now()
        updates: dict[str, Any] = {"status": new_status, "updated_at": now.isoformat()}

        # Timestamp rules
        if new_status == "in_progress" and record.started_at is None:
            updates["started_at"] = now.isoformat()
        if new_status in ("completed", "failed"):
            updates["completed_at"] = now.isoformat()
        if new_status == "archived":
            updates["archived_at"] = now.isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values,
            )
            conn.commit()

        # Обновить объект in-memory
        record.status = new_status
        record.updated_at = now
        if new_status == "in_progress" and record.started_at is None:
            record.started_at = now
        if new_status in ("completed", "failed"):
            record.completed_at = now
        if new_status == "archived":
            record.archived_at = now

        # Определить тип события
        if new_status == "in_progress" and old_status == "blocked":
            event_type = EventType.TASK_UNBLOCKED
        else:
            event_type = self._EVENT_MAP.get(new_status)

        if event_type is not None:
            self._log_event(
                event_type,
                task_id,
                old_status=old_status,
                new_status=new_status,
                actor=actor,
                reason=reason,
                source_path=record.source_path,
                metadata=record.metadata,
            )

        return record

    def start(self, task_id: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: pending/in_progress/failed → in_progress."""
        return self.transition(task_id, "in_progress", actor=actor)

    def block(self, task_id: str, reason: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: pending/in_progress → blocked."""
        return self.transition(task_id, "blocked", reason=reason, actor=actor)

    def unblock(self, task_id: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: blocked → in_progress."""
        return self.transition(task_id, "in_progress", actor=actor)

    def complete(self, task_id: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: in_progress → completed."""
        return self.transition(task_id, "completed", actor=actor)

    def fail(self, task_id: str, reason: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: in_progress → failed."""
        return self.transition(task_id, "failed", reason=reason, actor=actor)

    def archive(self, task_id: str, actor: str = "cli") -> TaskRecord:
        """Shorthand: any allowed → archived."""
        return self.transition(task_id, "archived", actor=actor)

    # ───────────────────────────────────────────────────────────
    # Internal helpers
    # ───────────────────────────────────────────────────────────

    def _row_to_record(self, row: dict[str, Any]) -> TaskRecord:
        """Преобразовать sqlite3.Row в TaskRecord."""
        return TaskRecord(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            role=row["role"],
            status=row["status"],
            priority=row["priority"],
            mode=row["mode"],
            source_path=row["source_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
            archived_at=datetime.fromisoformat(row["archived_at"]) if row.get("archived_at") else None,
            metadata=json.loads(row["metadata_json"]),
            acceptance_criteria=json.loads(row["criteria_json"]),
        )

    # ───────────────────────────────────────────────────────────
    # Resource management
    # ───────────────────────────────────────────────────────────

    def close(self) -> None:
        """Закрыть ресурсы (SQLite соединения автоматически закрываются)."""
        pass

    def __enter__(self) -> TaskEngine:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        self.close()
