"""T22-T34: physically read-only task service tests."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from voyage_framework.mcp_read.task_read import (
    TASK_COLUMNS,
    TaskDataError,
    TaskInputError,
    TaskReadError,
    TaskReadFacade,
)

_SCHEMA = """
CREATE TABLE tasks (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
    role TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', priority TEXT,
    mode TEXT, source_path TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    started_at TEXT, completed_at TEXT, archived_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}', criteria_json TEXT NOT NULL DEFAULT '[]'
)
"""


def _insert(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    role: str = "developer",
    status: str = "pending",
    updated: str = "2026-01-02T00:00:00+00:00",
    metadata: str | None = None,
    criteria: str | None = None,
) -> None:
    values = (
        task_id,
        f"Title {task_id}",
        "Synthetic description",
        role,
        status,
        "high",
        "code",
        f"tasks/{task_id}/task.yaml",
        "2026-01-01T00:00:00+00:00",
        updated,
        None,
        None,
        None,
        metadata if metadata is not None else json.dumps({"owner": "test"}),
        criteria if criteria is not None else json.dumps(["passes"]),
    )
    conn.execute(
        f"INSERT INTO tasks ({', '.join(TASK_COLUMNS)}) VALUES ({', '.join('?' * 15)})", values
    )


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    voyage = root / ".voyage"
    voyage.mkdir(parents=True)
    with sqlite3.connect(voyage / "tasks.db") as conn:
        conn.execute(_SCHEMA)
        _insert(conn, "VF-001")
        _insert(conn, "ST-002", role="reviewer", status="done")
        _insert(conn, "VF-003", updated="2026-01-02T00:00:00+00:00")
    return root


def _snapshot(root: Path) -> dict[str, object]:
    database = root / ".voyage" / "tasks.db"
    data = database.read_bytes()
    result: dict[str, object] = {
        "size": len(data),
        "hash": hashlib.sha256(data).hexdigest(),
        "mtime_ns": database.stat().st_mtime_ns,
    }
    for suffix in ("-journal", "-wal", "-shm"):
        sidecar = Path(f"{database}{suffix}")
        result[suffix] = (
            (sidecar.stat().st_size, hashlib.sha256(sidecar.read_bytes()).hexdigest())
            if sidecar.exists()
            else None
        )
    return result


def test_t22_no_mutable_core_or_model_imports() -> None:
    source_path = Path(__file__).parents[2] / "voyage_framework" / "mcp_read" / "task_read.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(module.startswith("voyage_framework.core") for module in imported)
    assert "TaskRecord" not in source_path.read_text(encoding="utf-8")


def test_t23_uri_mode_ro_is_derived_from_project_root(tmp_path: Path) -> None:
    facade = TaskReadFacade(_project(tmp_path))
    assert facade.db_path == (facade.project_root / ".voyage" / "tasks.db").resolve()
    assert facade.uri == f"{facade.db_path.as_uri()}?mode=ro"


def test_t24_query_only_is_set_and_verified(tmp_path: Path) -> None:
    facade = TaskReadFacade(_project(tmp_path))
    with closing(facade._connect()) as conn:
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
    assert facade.journal_mode is not None


def test_t25_insert_update_delete_denied_without_mutation(tmp_path: Path) -> None:
    root = _project(tmp_path)
    facade = TaskReadFacade(root)
    before = _snapshot(root)
    with closing(facade._connect()) as conn:
        for statement in (
            "INSERT INTO tasks (id) VALUES ('VF-999')",
            "UPDATE tasks SET title = 'changed' WHERE id = 'VF-001'",
            "DELETE FROM tasks WHERE id = 'VF-001'",
        ):
            with pytest.raises(sqlite3.OperationalError):
                conn.execute(statement)
    assert _snapshot(root) == before


def test_t26_create_table_and_write_pragma_denied(tmp_path: Path) -> None:
    root = _project(tmp_path)
    facade = TaskReadFacade(root)
    before = _snapshot(root)
    with closing(facade._connect()) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE forbidden (id INTEGER)")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("PRAGMA user_version = 1")
    assert _snapshot(root) == before


def test_t27_reads_leave_database_schema_and_sidecars_unchanged(tmp_path: Path) -> None:
    root = _project(tmp_path)
    facade = TaskReadFacade(root)
    before = _snapshot(root)
    assert facade.get("VF-001") is not None
    assert facade.list(limit=2, offset=1)[1] == 3
    assert _snapshot(root) == before


def test_t28_missing_nonfile_and_escape_paths_fail_without_creation(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    missing.mkdir()
    with pytest.raises(TaskReadError):
        TaskReadFacade(missing)
    assert not (missing / ".voyage").exists()

    nonfile = tmp_path / "nonfile"
    (nonfile / ".voyage" / "tasks.db").mkdir(parents=True)
    with pytest.raises(TaskReadError):
        TaskReadFacade(nonfile)

    escape = tmp_path / "escape"
    escape.mkdir()
    outside_voyage = _project(tmp_path / "outside") / ".voyage"
    link = escape / ".voyage"
    try:
        os.symlink(outside_voyage, link, target_is_directory=True)
    except OSError:
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside_voyage)],
            check=False,
            capture_output=True,
        )
        assert junction.returncode == 0, junction.stderr.decode(errors="replace")
    with pytest.raises(TaskReadError, match="escapes"):
        TaskReadFacade(escape)


def test_t29_select_uses_exact_explicit_fifteen_columns() -> None:
    assert len(TASK_COLUMNS) == 15
    assert TASK_COLUMNS == (
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
    source = (Path(__file__).parents[2] / "voyage_framework/mcp_read/task_read.py").read_text()
    assert "SELECT *" not in source.upper()


def test_t30_get_existing_returns_structured_redacted_row(tmp_path: Path) -> None:
    root = _project(tmp_path)
    with sqlite3.connect(root / ".voyage" / "tasks.db") as conn:
        conn.execute(
            "UPDATE tasks SET metadata_json = ? WHERE id = ?",
            (json.dumps({"api_key": "never-return", "safe": "yes"}), "VF-001"),
        )
    row = TaskReadFacade(root).get("VF-001")
    assert row is not None
    assert row["metadata"] == {"api_key": "[REDACTED]", "safe": "yes"}
    assert row["acceptance_criteria"] == ["passes"]
    assert "metadata_json" not in row and "criteria_json" not in row


def test_t31_get_missing_returns_none(tmp_path: Path) -> None:
    assert TaskReadFacade(_project(tmp_path)).get("VF-404") is None


def test_t32_filters_count_and_stable_order(tmp_path: Path) -> None:
    facade = TaskReadFacade(_project(tmp_path))
    rows, total = facade.list(status="pending", role="developer")
    assert total == 2
    assert [row["id"] for row in rows] == ["VF-001", "VF-003"]
    page, page_total = facade.list(limit=1, offset=1)
    assert page_total == 3 and [row["id"] for row in page] == ["VF-001"]


def test_t33_invalid_task_filter_and_pagination_inputs_rejected(tmp_path: Path) -> None:
    facade = TaskReadFacade(_project(tmp_path))
    invalid_ids: tuple[object, ...] = (None, "", "VF-1", "XX-001", "VF-001\x00")
    for value in invalid_ids:
        with pytest.raises(TaskInputError):
            facade.get(value)  # type: ignore[arg-type]
    for kwargs in (
        {"status": ""},
        {"role": "bad\nrole"},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": 10_001},
    ):
        with pytest.raises(TaskInputError):
            facade.list(**kwargs)  # type: ignore[arg-type]


def test_t34_malformed_json_fails_closed_and_metadata_is_redacted(tmp_path: Path) -> None:
    root = _project(tmp_path)
    with sqlite3.connect(root / ".voyage" / "tasks.db") as conn:
        _insert(conn, "VF-034", metadata="{not-json")
    facade = TaskReadFacade(root)
    with pytest.raises(TaskDataError, match="malformed JSON") as caught:
        facade.get("VF-034")
    assert "not-json" not in str(caught.value)
    original = {"password": "secret", "nested": {"token": "secret"}}
    with sqlite3.connect(root / ".voyage" / "tasks.db") as conn:
        conn.execute(
            "UPDATE tasks SET metadata_json = ? WHERE id = 'VF-001'", (json.dumps(original),)
        )
    row = facade.get("VF-001")
    assert row is not None and row["metadata"] != original
    assert original == {"password": "secret", "nested": {"token": "secret"}}
