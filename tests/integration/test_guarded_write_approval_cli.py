"""Integration tests for the `voyage guarded-write verify-approval` CLI command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    assert _git(path, "init", "--initial-branch=main").returncode == 0
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    assert (
        _git(
            path,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "init",
        ).returncode
        == 0
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _repo_state(repo: Path) -> dict[str, Any]:
    return {
        "worktree_clean": True,
        "head": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "origin_main": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "branch": "main",
    }


def _valid_preview(repo: Path) -> dict[str, Any]:
    return {
        "command": "edit.preview",
        "ok": True,
        "read_only": True,
        "apply_supported": False,
        "repo_root": str(repo),
        "source_plan": "plan.json",
        "repo_role": "generic",
        "repo_state": _repo_state(repo),
        "plan_summary": {
            "affected_files_count": 1,
            "proposed_actions_count": 1,
            "source_readiness": "ready",
            "source_apply_supported": False,
        },
        "safety_findings": [],
        "allowed_files": ["src/main.py"],
        "blocked_files": [],
        "warnings": [],
        "errors": [],
        "readiness": "ready",
        "next_gate": "F7_guarded_write_required",
    }


def _valid_approval(preview: dict[str, Any]) -> dict[str, Any]:
    repo_state = preview.get("repo_state") or {}
    return {
        "schema_version": "voyage.guarded_write.approval.v1",
        "approved": True,
        "approved_by": "human@example.com",
        "approved_at": "2026-07-05T12:00:00Z",
        "reason": "approved for guarded write",
        "bound_repo": {
            "branch": repo_state.get("branch"),
            "head": repo_state.get("head"),
            "origin_main": repo_state.get("origin_main"),
        },
        "bound_preview": {
            "command": "edit.preview",
            "next_gate": "F7_guarded_write_required",
            "repo_role": preview.get("repo_role", "generic"),
            "source_plan": preview.get("source_plan"),
        },
        "bound_allowed_files": preview.get("allowed_files", []),
        "bound_blocked_files": [],
        "checkpoint": {
            "type": "git_clean_head",
            "head": repo_state.get("head"),
            "rollback_plan": "git checkout HEAD -- affected files",
        },
        "post_write_validation": [
            "report-state",
            "validate-report",
            "targeted tests",
            "git diff --check",
        ],
        "evidence_acknowledged": [
            "source edit-preview reviewed",
            "blocked files empty",
            "repo state matches preview",
            "clean worktree confirmed",
            "rollback plan present",
            "post-write validation plan present",
        ],
    }


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
            "-m",
            "voyage_framework.cli",
            "guarded-write",
            "verify-approval",
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class TestGuardedWriteApprovalCLI:
    def test_cli_success(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = _run_cli(
            "--preview",
            str(preview_path),
            "--approval",
            str(approval_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "guarded_write.approval_verify"
        assert data["ok"] is True
        assert data["approval_valid"] is True
        assert data["writes_supported"] is False
        assert data["readiness"] == "ready"

    def test_cli_blocked_approval(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["ok"] = False
        preview["readiness"] = "blocked"
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = _run_cli(
            "--preview",
            str(preview_path),
            "--approval",
            str(approval_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 1, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "guarded_write.approval_verify"
        assert data["ok"] is False
        assert data["readiness"] == "blocked"
        assert data["approval_valid"] is False

    def test_cli_invalid_approval_json(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        approval_path.write_text("not-json", encoding="utf-8")

        result = _run_cli(
            "--preview",
            str(preview_path),
            "--approval",
            str(approval_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 1, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "guarded_write.approval_verify"
        assert data["ok"] is False

    def test_cli_help(self) -> None:
        result = subprocess.run(
            [
                "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
                "-m",
                "voyage_framework.cli",
                "guarded-write",
                "verify-approval",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        text = result.stdout
        assert "--preview" in text
        assert "--approval" in text
        assert "--repo" in text
        assert "approval" in text.lower()

    def test_existing_commands_still_available(self) -> None:
        result = subprocess.run(
            [
                "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
                "-m",
                "voyage_framework.cli",
                "guarded-write",
                "plan",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "--preview" in result.stdout

        result2 = subprocess.run(
            [
                "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
                "-m",
                "voyage_framework.cli",
                "edit-preview",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        assert result2.returncode == 0, result2.stderr
        assert "--plan" in result2.stdout

        result3 = subprocess.run(
            [
                "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
                "-m",
                "voyage_framework.cli",
                "repo",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        assert result3.returncode == 0, result3.stderr
        assert "status" in result3.stdout
