"""Unit tests for the generic guarded-write approval plan generator."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from voyage_framework.core.guarded_write import guarded_write_plan


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
    result = _git(path, "init", "--initial-branch=main")
    assert result.returncode == 0, result.stderr
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


def _write_preview(path: Path, preview: dict[str, Any]) -> None:
    path.write_text(json.dumps(preview), encoding="utf-8")


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


class TestGuardedWritePlanValid:
    def test_valid_preview_is_ready(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, _valid_preview(repo))

        result = guarded_write_plan(preview_path, repo)

        assert result["command"] == "guarded_write.plan"
        assert result["ok"] is True
        assert result["read_only"] is True
        assert result["writes_supported"] is False
        assert result["approval_required"] is True
        assert result["approval_status"] == "required"
        assert result["readiness"] == "ready"
        assert result["next_gate"] == "human_approval_required"
        assert result["required_evidence"]
        assert result["required_checks"]
        assert result["blocked_reasons"] == []

    def test_result_is_json_serializable(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, _valid_preview(repo))

        result = guarded_write_plan(preview_path, repo)
        text = json.dumps(result, indent=2)
        round_tripped = json.loads(text)

        assert round_tripped["command"] == "guarded_write.plan"


class TestGuardedWritePlanPreviewBlockers:
    def test_blocked_preview_is_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["ok"] = False
        preview["readiness"] = "blocked"
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert result["readiness"] == "blocked"
        assert result["approval_status"] == "blocked_before_approval"
        assert "source_preview_blocked" in result["blocked_reasons"]

    def test_blocked_files_present(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["blocked_files"] = ["scenarios/SCENARIO_LIBRARY.json"]
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "blocked_files_present" in result["blocked_reasons"]

    def test_error_safety_findings_present(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["safety_findings"] = [
            {
                "severity": "error",
                "code": "forbidden_path",
                "message": "blocked",
                "file": ".env",
            }
        ]
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "error_safety_findings_present" in result["blocked_reasons"]

    def test_invalid_preview_command(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["command"] = "edit.apply"
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "invalid_preview_command" in result["blocked_reasons"]

    def test_preview_apply_supported_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["apply_supported"] = True
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "preview_apply_supported" in result["blocked_reasons"]

    def test_preview_wrong_next_gate(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["next_gate"] = "apply_now"
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "preview_wrong_next_gate" in result["blocked_reasons"]


class TestGuardedWritePlanRepoState:
    def test_repo_head_drift(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["repo_state"]["head"] = "0" * 40
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "repo_head_drift" in result["blocked_reasons"]

    def test_repo_branch_drift(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["repo_state"]["branch"] = "other-branch"
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "repo_branch_drift" in result["blocked_reasons"]

    def test_dirty_worktree_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)
        (repo / "dirty.txt").write_text("x", encoding="utf-8")

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "dirty_worktree" in result["blocked_reasons"]

    def test_missing_repo(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        _write_preview(preview_path, preview)

        result = guarded_write_plan(preview_path, tmp_path / "missing")

        assert result["ok"] is False
        assert "repo_missing" in result["blocked_reasons"]

    def test_invalid_preview_json(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview_path = tmp_path / "preview.json"
        preview_path.write_text("not-json", encoding="utf-8")

        result = guarded_write_plan(preview_path, repo)

        assert result["ok"] is False
        assert "invalid_preview_json" in result["blocked_reasons"]
