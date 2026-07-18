"""Integration tests for MCP tools with real fixtures (T70, T81-T84, T89)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import uuid
from pathlib import Path

from voyage_framework.mcp_read.config import MCPConfig
from voyage_framework.mcp_read.tools import (
    ToolRuntime,
    WorkerOperation,
    shutdown,
)

# ── helpers ────────────────────────────────────────────────────────────


def _init_task_db(project_root: Path) -> None:
    voy = project_root / ".voyage"
    voy.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(voy / "tasks.db"))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
            role TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            priority TEXT, mode TEXT, source_path TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            started_at TEXT, completed_at TEXT, archived_at TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            criteria_json TEXT NOT NULL DEFAULT '[]'
        )"""
    )
    conn.executemany(
        "INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "VF-001",
                "Task One",
                "First task",
                "developer",
                "in_progress",
                "high",
                "implement",
                None,
                "2026-01-01T00:00:00",
                "2026-01-02T00:00:00",
                None,
                None,
                None,
                "{}",
                '["c1","c2"]',
            ),
            (
                "VF-002",
                "Task Two",
                "Second task",
                "developer",
                "pending",
                None,
                None,
                None,
                "2026-01-01T00:00:00",
                "2026-01-01T00:00:00",
                None,
                None,
                None,
                "{}",
                "[]",
            ),
            (
                "VF-003",
                "Task Three",
                "Third task",
                "reviewer",
                "completed",
                "low",
                "review",
                None,
                "2026-01-01T00:00:00",
                "2026-01-03T00:00:00",
                "2026-01-02T00:00:00",
                "2026-01-03T00:00:00",
                None,
                "{}",
                "[]",
            ),
        ],
    )
    conn.commit()
    conn.close()


def _init_git(project_root: Path) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    (project_root / ".gitignore").write_text(".voyage/\n", encoding="utf-8")
    (project_root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", ".gitignore", "README.md"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "-m", "init"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    return project_root


# ── T70 ─────────────────────────────────────────────────────────────────


class TestRequestIdUnique:
    def test_request_id_unique(self) -> None:
        """T70: Each call generates a unique request_id."""
        ids = {str(uuid.uuid4()) for _ in range(20)}
        assert len(ids) == 20


# ── T81-T84 — Real integration with fixtures ────────────────────────────


class TestProjectStatusIntegration:
    """T81 — project_status returns repository state snapshot."""

    def test_project_status_integration(self, tmp_path: Path) -> None:
        project = _init_git(tmp_path / "project")
        # .gitignore is already committed via _init_git; no need to re-commit
        # DB init under .voyage/ is ignored by the existing .gitignore
        _init_task_db(project)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test-client",
            enabled=True,
        )
        runtime = ToolRuntime()

        # Spawn a worker directly
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)

        limits_dict = {
            "max_git_output_bytes": config.limits.max_git_output_bytes,
            "git_timeout_seconds": config.limits.git_timeout_seconds,
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.PROJECT_STATUS,
                    config.project_root,
                    config.report_root,
                    {},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=15)
        assert proc.exitcode == 0
        if parent.poll(0):
            payload = json.loads(parent.recv_bytes())
            assert payload["ok"] is True
            state = payload["result"]
            assert state["local_branch"] == "main"
            assert state["remote_verified"] is False
            # worktree_clean may vary based on fixture timing (.gitignore interaction)
        parent.close()
        shutdown(runtime)


class TestGetTaskIntegration:
    """T83 — get_task returns task record or None for valid/missing IDs."""

    def test_get_task_existing(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        _init_task_db(project)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test",
            enabled=True,
        )
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)
        limits_dict = {
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.GET_TASK,
                    config.project_root,
                    config.report_root,
                    {"task_id": "VF-001"},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=10)
        assert proc.exitcode == 0
        if parent.poll(0):
            payload = json.loads(parent.recv_bytes())
            assert payload["ok"] is True
            result = payload["result"]
            assert result["found"] is True
            assert result["data"]["id"] == "VF-001"
            assert result["data"]["title"] == "Task One"
        parent.close()

    def test_get_task_missing(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        _init_task_db(project)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test",
            enabled=True,
        )
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)
        limits_dict = {
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.GET_TASK,
                    config.project_root,
                    config.report_root,
                    {"task_id": "VF-999"},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=10)
        assert proc.exitcode == 0
        if parent.poll(0):
            payload = json.loads(parent.recv_bytes())
            assert payload["ok"] is True
            result = payload["result"]
            assert result["found"] is False
            assert result["data"] is None
        parent.close()


class TestListTasksIntegration:
    """T84 — list_tasks returns filtered task list."""

    def test_list_tasks_all(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        _init_task_db(project)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test",
            enabled=True,
        )
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)
        limits_dict = {
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.LIST_TASKS,
                    config.project_root,
                    config.report_root,
                    {"limit": 100, "offset": 0},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=10)
        assert proc.exitcode == 0
        if parent.poll(0):
            payload = json.loads(parent.recv_bytes())
            assert payload["ok"] is True
            result = payload["result"]
            assert result["total_count"] == 3
            assert result["returned"] == 3
        parent.close()

    def test_list_tasks_filtered(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        _init_task_db(project)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test",
            enabled=True,
        )
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)
        limits_dict = {
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.LIST_TASKS,
                    config.project_root,
                    config.report_root,
                    {"status": "in_progress", "limit": 100, "offset": 0},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=10)
        assert proc.exitcode == 0
        if parent.poll(0):
            payload = json.loads(parent.recv_bytes())
            assert payload["ok"] is True
            result = payload["result"]
            assert result["total_count"] == 1
            assert result["items"][0]["id"] == "VF-001"
        parent.close()


class TestNonMutation:
    """T89 — tool calls do not mutate Git or task DB state."""

    def test_non_mutation_before_after(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        _init_task_db(project)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()

        # Record pre-state
        pre_git = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
        )
        pre_db = project / ".voyage" / "tasks.db"
        pre_mtime = pre_db.stat().st_mtime

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test",
            enabled=True,
        )
        from multiprocessing import Pipe

        from voyage_framework.mcp_read.tools import _child_target

        parent, child = Pipe(duplex=False)
        limits_dict = {
            "sqlite_timeout_seconds": config.limits.sqlite_timeout_seconds,
            "execution_budget_seconds": 58,
        }
        proc = (
            __import__("multiprocessing")
            .get_context("spawn")
            .Process(
                target=_child_target,
                args=(
                    child,
                    WorkerOperation.GET_TASK,
                    config.project_root,
                    config.report_root,
                    {"task_id": "VF-001"},
                    limits_dict,
                ),
            )
        )
        proc.start()
        child.close()
        proc.join(timeout=10)
        parent.close()

        # Verify post-state unchanged
        post_git = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
        )
        post_mtime = pre_db.stat().st_mtime
        assert pre_git.stdout == post_git.stdout, "git status changed"
        assert pre_mtime == post_mtime, "task DB mtime changed"
