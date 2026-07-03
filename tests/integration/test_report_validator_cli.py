"""Integration tests for the validate-report CLI command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import _GIT_LOCAL_ENV_VARS


def _clean_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in _GIT_LOCAL_ENV_VARS}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )
    return result.stdout.strip()


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True)
    _git(path, "init", "--initial-branch=main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    hooks_dir = path / ".empty-hooks"
    hooks_dir.mkdir()
    _git(path, "config", "core.hooksPath", str(hooks_dir))
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "init")
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "fetch", "origin", "+main:refs/remotes/origin/main")
    return _git(path, "rev-parse", "HEAD")


def _report(repo: Path, head: str) -> dict[str, Any]:
    return {
        "schema": "voyage.report.v1",
        "task_id": "T-CLI",
        "timestamp": "2026-06-30T00:00:00Z",
        "repos": [
            {
                "name": "framework",
                "path": str(repo),
                "expected_branch": "main",
                "expected_head": head,
                "expected_origin_main": head,
                "claimed_clean": True,
                "claimed_changed_files": [],
                "claimed_staged_files": [],
                "repo_role": "framework",
            }
        ],
        "safety": {},
        "claimed_verdict": "A",
    }


def _run_cli(report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "voyage_framework.cli", "validate-report", "--report", str(report)],
        capture_output=True,
        text=True,
        env=_clean_env(),
        check=False,
    )


def test_validate_report_cli_outputs_machine_readable_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    report = tmp_path / "report.json"
    report.write_text(json.dumps(_report(repo, head)), encoding="utf-8")

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["command"] == "validate-report"
    assert payload["ok"] is True
    assert payload["task_id"] == "T-CLI"
    assert payload["repos_checked"] == ["framework"]
    assert payload["mismatches"] == []
    assert payload["warnings"] == []
    assert payload["unverifiable_safety_claims"] == []
    assert payload["verdict_recommendation"] == "A"


def test_validate_report_cli_invalid_json_returns_error_json(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("{", encoding="utf-8")

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["command"] == "validate-report"
    assert payload["ok"] is False
    assert "not valid JSON" in payload["error"]


def test_validate_report_cli_wrong_schema_returns_error_json(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"schema": "wrong", "repos": []}), encoding="utf-8")

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["command"] == "validate-report"
    assert payload["ok"] is False
    assert "unsupported schema" in payload["error"]


"""
Integration tests for auto_commit / commit-range validation via CLI.
"""


def _make_commit(repo: Path, filename: str, content: str) -> str:
    file_path = repo / filename
    file_path.write_text(content, encoding="utf-8")
    _git(repo, "add", filename)
    _git(repo, "commit", "-m", f"add {filename}")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/main", head)
    return head


def _auto_commit_report(
    repo: Path, before: str, after: str, claimed_files: list[str]
) -> dict[str, Any]:
    return {
        "schema": "voyage.report.v1",
        "task_id": "T-CLI-AUTO",
        "timestamp": "2026-06-30T00:00:00Z",
        "repos": [
            {
                "name": "framework",
                "path": str(repo),
                "expected_branch": "main",
                "expected_head": after,
                "expected_origin_main": after,
                "claimed_clean": True,
                "claimed_changed_files": claimed_files,
                "claimed_staged_files": [],
                "repo_role": "framework",
                "auto_commit_before": before,
                "auto_commit_after": after,
            }
        ],
        "safety": {},
        "claimed_verdict": "A",
    }


def test_validate_report_cli_auto_commit_range_passes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    before = _init_repo(repo)
    after = _make_commit(repo, "feature.txt", "feature\n")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(_auto_commit_report(repo, before, after, ["feature.txt"])),
        encoding="utf-8",
    )

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["command"] == "validate-report"
    assert payload["ok"] is True
    assert payload["verdict_recommendation"] == "A"
    assert payload["mismatches"] == []


def test_validate_report_cli_auto_commit_range_mismatch_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    before = _init_repo(repo)
    after = _make_commit(repo, "feature.txt", "feature\n")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(_auto_commit_report(repo, before, after, ["wrong.txt"])),
        encoding="utf-8",
    )

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert any(
        mismatch["check"] == "auto_commit_changed_files" for mismatch in payload["mismatches"]
    )


def test_validate_report_cli_auto_commit_invalid_hash_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    before = _init_repo(repo)
    _make_commit(repo, "feature.txt", "feature\n")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(_auto_commit_report(repo, before, "not-a-hash", ["feature.txt"])),
        encoding="utf-8",
    )

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert any(
        mismatch["check"] == "auto_commit_after_hash_format" for mismatch in payload["mismatches"]
    )


def test_validate_report_cli_narrative_forbidden_claimed_path_fails(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "schema": "voyage.report.v1",
                "task_id": "T-CLI-NARR-FORBIDDEN",
                "timestamp": "2026-06-30T00:00:00Z",
                "repos": [
                    {
                        "name": "narrative",
                        "path": str(repo),
                        "expected_branch": "main",
                        "expected_head": head,
                        "expected_origin_main": head,
                        "claimed_clean": True,
                        "claimed_changed_files": ["script.rpy"],
                        "claimed_staged_files": [],
                        "repo_role": "narrative",
                    }
                ],
                "safety": {},
                "claimed_verdict": "A",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli(report)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert any(
        mismatch["check"] == "forbidden_paths:claimed_changed_files"
        for mismatch in payload["mismatches"]
    )
