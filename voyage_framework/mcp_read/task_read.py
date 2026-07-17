"""Physically read-only access to the canonical Voyage task database."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.confinement import redact_recursive

TASK_COLUMNS: tuple[str, ...] = (
    "id",
    "title",
    "description",
    "role",
    "status",
    "priority",
    "mode",
    "source_path",
    "created_at",
    "updated_at",
    "started_at",
    "completed_at",
    "archived_at",
    "metadata_json",
    "criteria_json",
)
_COLUMN_SQL = ", ".join(TASK_COLUMNS)
_TASK_ID_RE = re.compile(r"^(?:VF|ST)-\d{3,}$")


class TaskReadError(Exception):
    """Safe task-read failure without task content or SQL values."""


class TaskInputError(TaskReadError, ValueError):
    """Invalid caller input."""


class TaskDataError(TaskReadError):
    """Invalid database schema or row data."""


class TaskReadFacade:
    """Read canonical tasks through SQLite URI ``mode=ro`` only."""

    def __init__(self, project_root: Path, limits: Limits | None = None) -> None:
        self.limits = limits or Limits()
        try:
            root = Path(project_root).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise TaskReadError("project_root is unavailable") from exc
        if not root.is_dir():
            raise TaskReadError("project_root is not a directory")
        candidate = root / ".voyage" / "tasks.db"
        try:
            resolved_db = candidate.resolve(strict=True)
        except (FileNotFoundError, OSError, RuntimeError) as exc:
            raise TaskReadError("task database not found") from exc
        if not resolved_db.is_file():
            raise TaskReadError("task database is not a regular file")
        try:
            resolved_db.relative_to(root)
        except ValueError as exc:
            raise TaskReadError("task database escapes project_root") from exc
        self.project_root = root
        self.db_path = resolved_db
        self.uri = f"{resolved_db.as_uri()}?mode=ro"
        self.journal_mode: str | None = None

    def _connect(self) -> sqlite3.Connection:
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(
                self.uri,
                uri=True,
                timeout=self.limits.sqlite_timeout_seconds,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only = ON")
            query_only = conn.execute("PRAGMA query_only").fetchone()
            if query_only is None or query_only[0] != 1:
                conn.close()
                raise TaskReadError("SQLite query_only could not be verified")
            journal = conn.execute("PRAGMA journal_mode").fetchone()
            self.journal_mode = str(journal[0]) if journal else None
            columns = tuple(row[1] for row in conn.execute("PRAGMA table_info(tasks)"))
            if columns != TASK_COLUMNS:
                conn.close()
                raise TaskDataError("task database schema does not match the canonical schema")
            return conn
        except sqlite3.Error as exc:
            if conn is not None:
                conn.close()
            raise TaskReadError("task database could not be opened read-only") from exc

    def get(self, task_id: str) -> dict[str, object] | None:
        self._validate_task_id(task_id)
        try:
            with closing(self._connect()) as conn:
                row = conn.execute(
                    f"SELECT {_COLUMN_SQL} FROM tasks WHERE id = ?",  # noqa: S608
                    (task_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise TaskReadError("task lookup failed") from exc
        return None if row is None else self._row_to_dict(row)

    def list(
        self,
        *,
        status: str | None = None,
        role: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, object]], int]:
        self._validate_filter("status", status)
        self._validate_filter("role", role)
        max_rows = min(100, self.limits.max_task_rows)
        max_offset = min(10_000, self.limits.max_offset)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= max_rows:
            raise TaskInputError("limit must be an integer from 1 to 100")
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= max_offset:
            raise TaskInputError("offset must be an integer from 0 to 10000")

        clauses: list[str] = []
        params: list[object] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if role is not None:
            clauses.append("role = ?")
            params.append(role)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        try:
            with closing(self._connect()) as conn:
                count_row = conn.execute(f"SELECT COUNT(*) FROM tasks{where}", params).fetchone()
                total = int(count_row[0])
                rows = conn.execute(
                    f"SELECT {_COLUMN_SQL} FROM tasks{where} "  # noqa: S608
                    "ORDER BY updated_at DESC, id ASC LIMIT ? OFFSET ?",
                    [*params, limit, offset],
                ).fetchall()
        except sqlite3.Error as exc:
            raise TaskReadError("task listing failed") from exc
        return [self._row_to_dict(row) for row in rows], total

    def _validate_task_id(self, task_id: str) -> None:
        invalid_type_or_size = (
            not isinstance(task_id, str)
            or not task_id
            or len(task_id) > self.limits.max_task_id_length
        )
        if invalid_type_or_size:
            raise TaskInputError("invalid task_id")
        if _has_control(task_id) or _TASK_ID_RE.fullmatch(task_id) is None:
            raise TaskInputError("invalid task_id")

    @staticmethod
    def _validate_filter(name: str, value: str | None) -> None:
        if value is None:
            return
        if not isinstance(value, str) or not value or len(value) > 200 or _has_control(value):
            raise TaskInputError(f"invalid {name} filter")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, object]:
        raw: dict[str, Any] = dict(row)
        try:
            metadata = json.loads(raw.pop("metadata_json"))
            criteria = json.loads(raw.pop("criteria_json"))
        except (json.JSONDecodeError, TypeError) as exc:
            raise TaskDataError("task row contains malformed JSON") from exc
        if (
            not isinstance(metadata, dict)
            or not isinstance(criteria, list)
            or not all(isinstance(item, str) for item in criteria)
        ):
            raise TaskDataError("task row contains invalid structured data")
        raw["metadata"] = metadata
        raw["acceptance_criteria"] = criteria
        redacted = redact_recursive(raw)
        if not isinstance(redacted, dict):
            raise TaskDataError("task row could not be mapped")
        return redacted


def _has_control(value: str) -> bool:
    return any(ord(char) < 32 or ord(char) == 127 for char in value)
