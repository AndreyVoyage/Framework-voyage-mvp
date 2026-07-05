"""Unit tests for the generic read-only edit-preview / change-plan validator."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from voyage_framework.core.edit_preview import edit_preview


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
    commit = _git(
        path,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    )
    assert commit.returncode == 0, commit.stderr


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


class TestEditPreviewValid:
    def test_valid_plan_is_ready(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)

        assert result["command"] == "edit.preview"
        assert result["ok"] is True
        assert result["read_only"] is True
        assert result["apply_supported"] is False
        assert result["readiness"] == "ready"
        assert result["next_gate"] == "F7_guarded_write_required"
        assert "src/main.py" in result["allowed_files"]
        assert result["blocked_files"] == []
        assert result["errors"] == []

    def test_result_is_json_serializable(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)
        text = json.dumps(result, indent=2)
        round_tripped = json.loads(text)

        assert round_tripped["command"] == "edit.preview"

    def test_repo_role_defaults_to_generic(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)

        assert result["repo_role"] == "generic"


class TestEditPreviewPathGuards:
    def test_forbidden_env_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = [".env"]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert result["readiness"] == "blocked"
        assert ".env" in result["blocked_files"]
        assert any(f["code"] == "forbidden_path" for f in result["safety_findings"])

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = ["../outside.txt"]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert "../outside.txt" in result["blocked_files"]
        assert any(f["code"] == "path_traversal" for f in result["safety_findings"])

    def test_absolute_path_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = ["/etc/passwd"]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert "/etc/passwd" in result["blocked_files"]
        assert any(f["code"] == "absolute_path" for f in result["safety_findings"])

    def test_missing_file_not_error_if_allowed(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = ["future/file.py"]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is True
        assert "future/file.py" in result["allowed_files"]


class TestEditPreviewActionGuards:
    def test_apply_supported_true_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["apply_supported"] = True
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert any(f["code"] == "apply_not_supported" for f in result["safety_findings"])

    def test_non_proposal_action_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["proposed_actions"][0]["status"] = "apply"
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert any(f["code"] == "action_not_proposal_only" for f in result["safety_findings"])

    def test_unsafe_auto_apply_flag_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["proposed_actions"][0]["safe_to_apply_automatically"] = True
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert any(f["code"] == "unsafe_auto_apply_flag" for f in result["safety_findings"])

    def test_unsafe_target_file_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["proposed_actions"][0]["target_file"] = ".env"
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert ".env" in result["blocked_files"]


class TestEditPreviewRepoState:
    def test_missing_repo_blocked(self, tmp_path: Path) -> None:
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())
        missing_repo = tmp_path / "missing"

        result = edit_preview(plan_path, missing_repo)

        assert result["ok"] is False
        assert result["readiness"] == "blocked"
        assert any(f["code"] == "repo_missing" for f in result["safety_findings"])

    def test_non_git_repo_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "not-git"
        repo.mkdir()
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert any(f["code"] == "repo_not_git" for f in result["safety_findings"])

    def test_dirty_worktree_warns(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "dirty.txt").write_text("x", encoding="utf-8")
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)

        assert result["ok"] is True
        assert result["readiness"] == "warnings"
        assert any(f["code"] == "dirty_worktree" for f in result["safety_findings"])
        assert "dirty_worktree" in result["warnings"]

    def test_staged_files_warn(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "staged.txt").write_text("x", encoding="utf-8")
        _git(repo, "add", "staged.txt")
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, _valid_plan())

        result = edit_preview(plan_path, repo)

        assert result["ok"] is True
        assert any(f["code"] == "staged_files_present" for f in result["safety_findings"])


class TestEditPreviewPlanErrors:
    def test_missing_plan_file_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        missing_plan = tmp_path / "missing.json"

        result = edit_preview(missing_plan, repo)

        assert result["ok"] is False
        assert any(f["code"] == "plan_missing" for f in result["safety_findings"])

    def test_invalid_json_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text("not-json", encoding="utf-8")

        result = edit_preview(plan_path, repo)

        assert result["ok"] is False
        assert any(f["code"] == "invalid_plan_json" for f in result["safety_findings"])


class TestEditPreviewNarrativeRole:
    def test_narrative_role_blocks_library_and_matrix(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        plan = _valid_plan()
        plan["affected_files"] = [
            "scenarios/SCENARIO_001.json",
            "scenarios/SCENARIO_LIBRARY.json",
            "scenarios/SCENARIO_MATRIX.json",
        ]
        plan_path = tmp_path / "plan.json"
        _write_plan(plan_path, plan)

        result = edit_preview(plan_path, repo, repo_role="narrative")

        assert result["ok"] is False
        assert "scenarios/SCENARIO_LIBRARY.json" in result["blocked_files"]
        assert "scenarios/SCENARIO_MATRIX.json" in result["blocked_files"]
        assert "scenarios/SCENARIO_001.json" in result["allowed_files"]
