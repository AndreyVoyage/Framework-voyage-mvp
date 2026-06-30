"""Unit tests for structured report trust validation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import voyage_framework.core.report_validator as rv
from voyage_framework.core.report_validator import ReportValidatorError, validate_report

HEAD = "1" * 40
ORIGIN = "2" * 40


def _write_report(path: Path, report: dict[str, Any]) -> Path:
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _report(repo: Path, **overrides: Any) -> dict[str, Any]:
    repo_claim: dict[str, Any] = {
        "name": "framework",
        "path": str(repo),
        "expected_branch": "main",
        "expected_head": HEAD,
        "expected_origin_main": ORIGIN,
        "claimed_clean": True,
        "claimed_changed_files": [],
        "claimed_staged_files": [],
        "repo_role": "framework",
    }
    repo_claim.update(overrides.pop("repo_overrides", {}))
    report: dict[str, Any] = {
        "schema": "voyage.report.v1",
        "task_id": "T-REPORT",
        "timestamp": "2026-06-30T00:00:00Z",
        "repos": [repo_claim],
        "safety": {},
        "claimed_verdict": "A",
    }
    report.update(overrides)
    return report


def _patch_git(
    monkeypatch: pytest.MonkeyPatch,
    *,
    branch: str = "main",
    head: str = HEAD,
    origin: str = ORIGIN,
    status: list[str] | None = None,
    changed: list[str] | None = None,
    staged: list[str] | None = None,
    known_hashes: set[str] | None = None,
) -> None:
    status = status or []
    changed = changed or []
    staged = staged or []
    known_hashes = known_hashes or {HEAD, ORIGIN, head, origin}

    def fake_stdout(_repo: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return branch
        if args == ("rev-parse", "HEAD"):
            return head
        if args == ("rev-parse", "origin/main"):
            return origin
        return ""

    def fake_name_only(_repo: Path, *args: str) -> list[str]:
        if args == ("diff", "--name-only"):
            return changed
        if args == ("diff", "--cached", "--name-only"):
            return staged
        return []

    def fake_git(_repo: Path, *args: str) -> SimpleNamespace:
        if args[:2] == ("cat-file", "-t") and args[2] in known_hashes:
            return SimpleNamespace(returncode=0, stdout="commit\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="missing")

    monkeypatch.setattr(rv, "_git_stdout", fake_stdout)
    monkeypatch.setattr(rv, "_git_status", lambda _repo: status)
    monkeypatch.setattr(rv, "_git_name_only", fake_name_only)
    monkeypatch.setattr(rv, "_git", fake_git)


def test_valid_report_matches_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_path = _write_report(tmp_path / "report.json", _report(repo))

    result = validate_report(report_path)

    assert result.ok is True
    assert result.verdict_recommendation == "A"
    assert result.repos_checked == ["framework"]
    assert result.mismatches == []


def test_wrong_schema_raises(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path / "report.json", {"schema": "wrong", "repos": []})

    with pytest.raises(ReportValidatorError, match="unsupported schema"):
        validate_report(report_path)


def test_invalid_json_raises(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text("{", encoding="utf-8")

    with pytest.raises(ReportValidatorError, match="not valid JSON"):
        validate_report(report_path)


def test_wrong_head_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, head="3" * 40, known_hashes={HEAD, ORIGIN, "3" * 40})
    report_path = _write_report(tmp_path / "report.json", _report(repo))

    result = validate_report(report_path)

    assert result.ok is False
    assert result.verdict_recommendation == "C"
    assert any(mismatch.check == "head" for mismatch in result.mismatches)


def test_short_head_hash_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_path = _write_report(
        tmp_path / "report.json",
        _report(repo, repo_overrides={"expected_head": HEAD[:7]}),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "head_hash_format" for mismatch in result.mismatches)


def test_non_hex_head_hash_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_path = _write_report(
        tmp_path / "report.json",
        _report(repo, repo_overrides={"expected_head": "z" * 40}),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "head_hash_format" for mismatch in result.mismatches)


def test_unknown_head_object_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, known_hashes={ORIGIN})
    report_path = _write_report(tmp_path / "report.json", _report(repo))

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "head_object_exists" for mismatch in result.mismatches)


def test_claimed_clean_true_with_dirty_file_is_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, status=[" M README.md"], changed=["README.md"])
    report_path = _write_report(tmp_path / "report.json", _report(repo))

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "clean" for mismatch in result.mismatches)
    assert any(mismatch.check == "changed_files" for mismatch in result.mismatches)


def test_untracked_file_not_claimed_is_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, status=["?? new.txt"])
    report_path = _write_report(
        tmp_path / "report.json",
        _report(repo, repo_overrides={"claimed_clean": False}),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "changed_files" for mismatch in result.mismatches)


def test_staged_file_not_claimed_is_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, status=["A  staged.txt"], staged=["staged.txt"])
    report_path = _write_report(
        tmp_path / "report.json",
        _report(
            repo,
            repo_overrides={
                "claimed_clean": False,
                "claimed_changed_files": ["staged.txt"],
            },
        ),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert any(mismatch.check == "staged_files" for mismatch in result.mismatches)


def test_forbidden_claimed_path_is_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_path = _write_report(
        tmp_path / "report.json",
        _report(
            repo,
            repo_overrides={
                "claimed_clean": False,
                "claimed_changed_files": [".env"],
            },
        ),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert any("forbidden_paths" in mismatch.check for mismatch in result.mismatches)


def test_unverifiable_safety_claims_are_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_path = _write_report(
        tmp_path / "report.json",
        _report(
            repo,
            safety={"env_file_read": False, "bridge_executed": False, "other": False},
        ),
    )

    result = validate_report(report_path)

    assert result.ok is True
    assert result.unverifiable_safety_claims == ["bridge_executed", "env_file_read"]


def test_verdict_mismatch_adds_warning_but_keeps_error_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch, status=["?? dirty.txt"])
    report_path = _write_report(
        tmp_path / "report.json",
        _report(repo, claimed_verdict="A"),
    )

    result = validate_report(report_path)

    assert result.ok is False
    assert result.verdict_recommendation == "C"
    assert any("claimed verdict" in warning for warning in result.warnings)


def test_utf8_bom_report_loads_and_validates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _patch_git(monkeypatch)
    report_bytes = ("﻿" + json.dumps(_report(repo))).encode("utf-8")
    report_path = tmp_path / "report_bom.json"
    report_path.write_bytes(report_bytes)

    result = validate_report(report_path)

    assert result.ok is True
    assert result.verdict_recommendation == "A"
    assert result.mismatches == []


def test_multi_repo_mismatch_is_scoped_to_repo_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_one = tmp_path / "repo-one"
    repo_two = tmp_path / "repo-two"
    repo_one.mkdir()
    repo_two.mkdir()
    _patch_git(monkeypatch)
    report = _report(repo_one)
    report["repos"].append(
        {
            "name": "narrative",
            "path": str(repo_two),
            "expected_branch": "wrong",
            "expected_head": HEAD,
            "expected_origin_main": ORIGIN,
            "claimed_clean": True,
            "claimed_changed_files": [],
            "claimed_staged_files": [],
            "repo_role": "narrative",
        }
    )
    report_path = _write_report(tmp_path / "report.json", report)

    result = validate_report(report_path)

    assert result.ok is False
    assert result.repos_checked == ["framework", "narrative"]
    assert any(mismatch.repo == "narrative" for mismatch in result.mismatches)
