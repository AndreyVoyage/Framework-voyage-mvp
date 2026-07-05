"""Unit tests for the guarded-write approval artifact verifier."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from voyage_framework.core.guarded_write_approval import guarded_write_approval_verify


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
            "rollback_plan": "git checkout HEAD -- affected files or reset via backup branch",
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


class TestGuardedWriteApprovalVerifyValid:
    def test_valid_approval_is_ready(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["command"] == "guarded_write.approval_verify"
        assert result["ok"] is True
        assert result["read_only"] is True
        assert result["writes_supported"] is False
        assert result["approval_required"] is True
        assert result["approval_valid"] is True
        assert result["readiness"] == "ready"
        assert result["next_gate"] == "F7_structured_write_required"
        assert result["required_evidence"]
        assert result["required_checks"]
        assert result["blocked_reasons"] == []

    def test_result_is_json_serializable(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)
        text = json.dumps(result, indent=2)
        round_tripped = json.loads(text)

        assert round_tripped["command"] == "guarded_write.approval_verify"


class TestGuardedWriteApprovalVerifyInputs:
    def test_missing_approval_file(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        _write_json(preview_path, preview)

        result = guarded_write_approval_verify(preview_path, tmp_path / "missing.json", repo)

        assert result["ok"] is False
        assert "approval_missing" in result["blocked_reasons"]
        assert result["approval_valid"] is False

    def test_invalid_approval_json(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        approval_path.write_text("not-json", encoding="utf-8")

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "invalid_approval_json" in result["blocked_reasons"]

    def test_invalid_preview_json(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        preview_path.write_text("not-json", encoding="utf-8")
        _write_json(approval_path, _valid_approval(_valid_preview(repo)))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "invalid_preview_json" in result["blocked_reasons"]


class TestGuardedWriteApprovalVerifyPreviewBlockers:
    def test_blocked_preview(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["ok"] = False
        preview["readiness"] = "blocked"
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "source_preview_blocked" in result["blocked_reasons"]

    def test_blocked_files_present(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        preview["blocked_files"] = ["scenarios/SCENARIO_LIBRARY.json"]
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

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
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, _valid_approval(preview))

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "error_safety_findings_present" in result["blocked_reasons"]


class TestGuardedWriteApprovalVerifyApprovalFields:
    def test_approved_false(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["approved"] = False
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_not_true" in result["blocked_reasons"]

    def test_missing_approved_by(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["approved_by"] = ""
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_identity_missing" in result["blocked_reasons"]

    def test_missing_approved_at(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["approved_at"] = ""
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_timestamp_missing" in result["blocked_reasons"]

    def test_missing_reason(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["reason"] = ""
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_reason_missing" in result["blocked_reasons"]


class TestGuardedWriteApprovalVerifyBindings:
    def test_repo_head_mismatch(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["bound_repo"]["head"] = "0" * 40
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_head_mismatch" in result["blocked_reasons"]

    def test_repo_branch_mismatch(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["bound_repo"]["branch"] = "other-branch"
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_branch_mismatch" in result["blocked_reasons"]

    def test_allowed_files_mismatch(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["bound_allowed_files"] = ["src/other.py"]
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_allowed_files_mismatch" in result["blocked_reasons"]

    def test_bound_blocked_files_not_empty(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["bound_blocked_files"] = [".env"]
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "approval_blocked_files_not_empty" in result["blocked_reasons"]

    def test_missing_rollback_plan(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["checkpoint"]["rollback_plan"] = ""
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "rollback_plan_missing" in result["blocked_reasons"]

    def test_missing_post_write_validation(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        approval["post_write_validation"] = []
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "post_write_validation_missing" in result["blocked_reasons"]


class TestGuardedWriteApprovalVerifyRepoState:
    def test_dirty_worktree_blocked(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        preview = _valid_preview(repo)
        approval = _valid_approval(preview)
        preview_path = tmp_path / "preview.json"
        approval_path = tmp_path / "approval.json"
        _write_json(preview_path, preview)
        _write_json(approval_path, approval)
        (repo / "dirty.txt").write_text("x", encoding="utf-8")

        result = guarded_write_approval_verify(preview_path, approval_path, repo)

        assert result["ok"] is False
        assert "dirty_worktree" in result["blocked_reasons"]
