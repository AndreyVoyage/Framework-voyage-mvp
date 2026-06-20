"""Task Engine — жизненный цикл задач для Voyage Framework.

SQLite-based, sync SQLAlchemy (согласно ADR-009).

Возможности:
- Создание задачи с критериями приёмки
- Переход статусов: pending → in_progress → completed | failed
- Список задач по проекту/роли/статусу
- События в EventEngine (task_created, task_started, task_completed, task_failed)
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from voyage_framework.core.models import Event, EventType
from voyage_framework.core.event_engine import EventEngine


class TaskStatus(StrEnum):
    """Статусы жизненного цикла задачи."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Задача в Voyage Framework.

    Не наследуем BaseModel, потому что хранится в SQLite напрямую
    (sync SQLAlchemy, ADR-009).
    """

    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        role: str,
        status: TaskStatus = TaskStatus.PENDING,
        project_id: str = "default",
        criteria: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        self.task_id = task_id
        self.title = title
        self.description = description
        self.role = role
        self.status = status
        self.project_id = project_id
        self.criteria = criteria or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(UTC)
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в dict."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "role": self.role,
            "status": self.status.value,
            "project_id": self.project_id,
            "criteria": self.criteria,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Десериализация из dict."""
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            role=data["role"],
            status=TaskStatus(data.get("status", "pending")),
            project_id=data.get("project_id", "default"),
            criteria=data.get("criteria", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )

    def __repr__(self) -> str:
        return f"<Task {self.task_id[:8]} {self.status.value} '{self.title[:40]}'>"


class TaskManager:
    """Менеджер задач: CRUD + жизненный цикл + интеграция с EventEngine."""

    VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
        TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: {TaskStatus.PENDING, TaskStatus.CANCELLED},
        TaskStatus.CANCELLED: set(),
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
        """Создать таблицу tasks если не существует."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    project_id TEXT NOT NULL DEFAULT 'default',
                    criteria TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_project
                ON tasks(project_id, status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_role
                ON tasks(role, status)
            """)
            conn.commit()

    def _log_event(self, event_type: EventType, payload: dict[str, Any]) -> None:
        """Записать событие в EventEngine, если доступно."""
        if self.event_engine is not None:
            event = Event(
                event_type=event_type,
                payload=payload,
                project_id=payload.get("project_id", "default"),
                correlation_id=payload.get("task_id"),
            )
            self.event_engine.append(event)

    def create(
        self,
        title: str,
        description: str,
        role: str,
        project_id: str = "default",
        criteria: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> Task:
        """Создать новую задачу."""
        from ulid import ULID

        task = Task(
            task_id=task_id or str(ULID()),
            title=title,
            description=description,
            role=role,
            status=TaskStatus.PENDING,
            project_id=project_id,
            criteria=criteria,
            metadata=metadata,
        )

        with sqlite3.connect(self.db_path) as conn:
            import json
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, title, description, role, status, project_id,
                    criteria, metadata, created_at, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.title,
                    task.description,
                    task.role,
                    task.status.value,
                    task.project_id,
                    json.dumps(task.criteria),
                    json.dumps(task.metadata),
                    task.created_at.isoformat(),
                    None,
                    None,
                ),
            )
            conn.commit()

        self._log_event(EventType.TASK_CREATED, task.to_dict())
        return task

    def get(self, task_id: str) -> Task | None:
        """Получить задачу по ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_task(dict(row))

    def list(
        self,
        project_id: str | None = None,
        role: str | None = None,
        status: TaskStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        """Список задач с фильтрацией."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []

        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if role is not None:
            query += " AND role = ?"
            params.append(role)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_task(dict(row)) for row in rows]

    def transition(self, task_id: str, new_status: TaskStatus) -> Task:
        """Перевести задачу в новый статус с валидацией."""
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if new_status not in self.VALID_TRANSITIONS[task.status]:
            raise ValueError(
                f"Invalid transition: {task.status.value} → {new_status.value}. "
                f"Allowed: {[s.value for s in self.VALID_TRANSITIONS[task.status]]}"
            )

        now = datetime.now(UTC)
        updates = {"status": new_status.value}

        if new_status == TaskStatus.IN_PROGRESS:
            updates["started_at"] = now.isoformat()
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            updates["completed_at"] = now.isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE task_id = ?",
                values,
            )
            conn.commit()

        # Обновить объект
        task.status = new_status
        if new_status == TaskStatus.IN_PROGRESS:
            task.started_at = now
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task.completed_at = now

        event_map = {
            TaskStatus.IN_PROGRESS: EventType.TASK_STARTED,
            TaskStatus.COMPLETED: EventType.TASK_COMPLETED,
            TaskStatus.FAILED: EventType.TASK_FAILED,
            TaskStatus.CANCELLED: EventType.TASK_CANCELLED,
        }
        event_type = event_map.get(new_status)
        if event_type:
            self._log_event(event_type, task.to_dict())

        return task

    def start(self, task_id: str) -> Task:
        """Shorthand: начать задачу."""
        return self.transition(task_id, TaskStatus.IN_PROGRESS)

    def complete(self, task_id: str) -> Task:
        """Shorthand: завершить задачу."""
        return self.transition(task_id, TaskStatus.COMPLETED)

    def fail(self, task_id: str) -> Task:
        """Shorthand: отметить задачу как failed."""
        return self.transition(task_id, TaskStatus.FAILED)

    def cancel(self, task_id: str) -> Task:
        """Shorthand: отменить задачу."""
        return self.transition(task_id, TaskStatus.CANCELLED)

    def delete(self, task_id: str) -> bool:
        """Удалить задачу."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count(self, project_id: str | None = None, status: TaskStatus | None = None) -> int:
        """Количество задач."""
        query = "SELECT COUNT(*) FROM tasks WHERE 1=1"
        params: list[Any] = []

        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0

    def _row_to_task(self, row: dict[str, Any]) -> Task:
        """Преобразовать sqlite row в Task."""
        import json
        return Task(
            task_id=row["task_id"],
            title=row["title"],
            description=row["description"],
            role=row["role"],
            status=TaskStatus(row["status"]),
            project_id=row["project_id"],
            criteria=json.loads(row["criteria"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
        )
