"""Integration tests for the `voyage edit-preview` CLI command."""

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


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    path.write_text(json.dumps(plan), encoding="utf-8")


def _valid_plan() -> dict[str, Any]:
    return {
        "command": "test.plan",
        "ok": True,
        "read_only": True,
        "apply_supported": False,
        "readiness": "ready",
        "affected_files": ["src/main.py"],
        "proposed_actions": [
            {
                "action_type": "review",
                "status": "proposal_only",
                "target_file": "src/main.py",
                "safe_to_apply_automatically": False,
                "reason": "review needed",
            }
        ],
        "findings": [],
        "warnings": [],
        "errors": [],
    }


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
            "-m",
            "voyage_framework.cli",
            "edit-preview",
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class TestEditPreviewCLI:
    def test_cli_success(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = _run_cli(
            "--plan",
            str(plan_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "edit.preview"
        assert data["ok"] is True
        assert data["readiness"] == "ready"
        assert "src/main.py" in data["allowed_files"]

    def test_cli_blocked_plan(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = [".env"]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = _run_cli(
            "--plan",
            str(plan_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 1, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "edit.preview"
        assert data["ok"] is False
        assert data["readiness"] == "blocked"
        assert ".env" in data["blocked_files"]

    def test_cli_invalid_plan(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text("not-json", encoding="utf-8")

        result = _run_cli(
            "--plan",
            str(plan_path),
            "--repo",
            str(repo),
        )

        assert result.returncode == 1, result.stderr
        data = json.loads(result.stdout)
        assert data["command"] == "edit.preview"
        assert data["ok"] is False

    def test_cli_help(self) -> None:
        result = subprocess.run(
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

        assert result.returncode == 0, result.stderr
        text = result.stdout
        assert "--plan" in text
        assert "--repo" in text
        assert "--repo-role" in text or "repo-role" in text

    def test_existing_commands_still_available(self) -> None:
        result = subprocess.run(
            [
                "C:/DEV/FRAMEWORK/Framework-voyage-mvp/.venv/Scripts/python.exe",
                "-m",
                "voyage_framework.cli",
                "narrative",
                "spec-plan",
                "--help",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "--repo" in result.stdout

        result2 = subprocess.run(
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

        assert result2.returncode == 0, result2.stderr
        assert "status" in result2.stdout
