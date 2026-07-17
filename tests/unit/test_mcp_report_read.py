"""T47-T56: confined JSON report validation tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.report_read import ReportReadError, report_read_and_validate


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    reports = tmp_path / "reports"
    project.mkdir()
    reports.mkdir()
    return project.resolve(), reports.resolve()


def _context(project: Path, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "repo_path": str(project),
        "local_branch": "feature/read",
        "local_head": "a" * 40,
        "local_origin_main_ref": "b" * 40,
        "worktree_clean": True,
        "changed_files": [],
        "staged_files": [],
        "untracked_files": [],
        "remote_verified": False,
        "warnings": [],
        "errors": [],
    }
    base.update(overrides)
    return base


def _payload(project: Path, **claim_overrides: object) -> dict[str, object]:
    claim: dict[str, object] = {
        "name": "framework",
        "path": str(project),
        "expected_branch": "feature/read",
        "expected_head": "a" * 40,
        "expected_origin_main": "b" * 40,
        "claimed_clean": True,
        "claimed_changed_files": [],
        "claimed_staged_files": [],
    }
    claim.update(claim_overrides)
    return {
        "schema": "voyage.report.v1",
        "task_id": "VF-047",
        "repos": [claim],
        "claimed_verdict": "A",
    }


def _write(reports: Path, name: str, payload: object) -> Path:
    path = reports / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _no_hash_keys(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if "hash" in str(key).lower() or not _no_hash_keys(item):
                return False
    elif isinstance(value, list):
        return all(_no_hash_keys(item) for item in value)
    return True


def _init_git_repo(project: Path) -> None:
    env = {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(
        ["git", "init", "--initial-branch=main"], cwd=project, check=True, capture_output=True
    )
    (project / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=project, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=project,
        check=True,
        capture_output=True,
    )


def test_t47_valid_json_basename_is_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, reports = _roots(tmp_path)
    _write(reports, "valid-report.json", _payload(project))
    calls: list[Path] = []

    def fake_git(root: Path, _limits: Limits) -> dict[str, object]:
        calls.append(root)
        return _context(project)

    monkeypatch.setattr("voyage_framework.mcp_read.report_read.git_read_report_context", fake_git)
    result = report_read_and_validate("valid-report.json", project, reports)
    assert result["status"] == "validated" and result["recommended_verdict"] == "A"
    assert result["validation_ok"] is True and calls == [project]


def test_t48_subdirectory_traversal_absolute_and_markdown_are_denied(tmp_path: Path) -> None:
    project, reports = _roots(tmp_path)
    for report_id in ("nested/report.json", "../report.json", "C:\\report.json", "report.md"):
        with pytest.raises(ReportReadError):
            report_read_and_validate(report_id, project, reports)


def test_t49_secret_name_is_denied_before_any_path_read(tmp_path: Path) -> None:
    with pytest.raises(ReportReadError, match="secret_report_id_denied"):
        report_read_and_validate(
            "credentials.json",
            tmp_path / "missing-project",
            tmp_path / "missing-reports",
        )


def test_t50_size_encoding_and_binary_limits(tmp_path: Path) -> None:
    project, reports = _roots(tmp_path)
    (reports / "oversize.json").write_bytes(b"x" * 21)
    with pytest.raises(ReportReadError, match="report_too_large"):
        report_read_and_validate("oversize.json", project, reports, Limits(max_report_bytes=20))
    (reports / "encoding.json").write_bytes(b"\xff\xfe")
    with pytest.raises(ReportReadError, match="report_encoding_invalid"):
        report_read_and_validate("encoding.json", project, reports)
    (reports / "binary.json").write_bytes(b'{"schema":"voyage.report.v1"}\x00')
    with pytest.raises(ReportReadError, match="report_binary_content"):
        report_read_and_validate("binary.json", project, reports)


def test_t51_missing_allowed_report_is_structured_not_found(tmp_path: Path) -> None:
    project, reports = _roots(tmp_path)
    result = report_read_and_validate("missing.json", project, reports)
    assert result == {
        "status": "not_found",
        "report_id": "missing.json",
        "denied": False,
        "findings": [],
    }


def test_t52_json_schema_and_repository_shape_errors(tmp_path: Path) -> None:
    project, reports = _roots(tmp_path)
    (reports / "invalid.json").write_text("{", encoding="utf-8")
    with pytest.raises(ReportReadError, match="report_json_invalid"):
        report_read_and_validate("invalid.json", project, reports)
    for name, payload, error in (
        ("array.json", [], "report_schema_invalid"),
        ("schema.json", {"schema": "wrong", "repos": []}, "report_schema_invalid"),
        ("repos.json", {"schema": "voyage.report.v1", "repos": []}, "report_repositories_invalid"),
        (
            "types.json",
            {
                "schema": "voyage.report.v1",
                "repos": [{"path": str(project), "claimed_changed_files": "not-a-list"}],
            },
            "report_repository_invalid",
        ),
    ):
        _write(reports, name, payload)
        with pytest.raises(ReportReadError, match=error):
            report_read_and_validate(name, project, reports)


def test_t53_claim_mismatch_is_a_structured_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, reports = _roots(tmp_path)
    _write(reports, "mismatch.json", _payload(project, expected_head="c" * 40))
    monkeypatch.setattr(
        "voyage_framework.mcp_read.report_read.git_read_report_context",
        lambda _root, _limits: _context(project),
    )
    result = report_read_and_validate("mismatch.json", project, reports)
    finding = next(item for item in result["findings"] if item["field"] == "expected_head")
    assert finding["type"] == "conflict" and finding["severity"] == "error"
    assert finding["expected"] == "c" * 40 and finding["actual"] == "a" * 40
    assert result["recommended_verdict"] == "C" and result["validation_ok"] is False


def test_t54_findings_have_dual_provenance_and_unverifiable_is_b(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, reports = _roots(tmp_path)
    _write(reports, "provenance.json", _payload(project, auto_commit_after="a" * 40))
    monkeypatch.setattr(
        "voyage_framework.mcp_read.report_read.git_read_report_context",
        lambda _root, _limits: _context(project),
    )
    result = report_read_and_validate("provenance.json", project, reports)
    assert result["recommended_verdict"] == "B"
    for finding in result["findings"]:
        assert finding["report_provenance"]
        assert finding["git_provenance"]
    assert any(item["type"] == "claim_unverifiable" for item in result["findings"])


def test_t55_recursive_redaction_has_metadata_and_no_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, reports = _roots(tmp_path)
    _write(
        reports,
        "redaction.json",
        _payload(project, claimed_clean=False, claimed_changed_files=[".env"]),
    )
    monkeypatch.setattr(
        "voyage_framework.mcp_read.report_read.git_read_report_context",
        lambda _root, _limits: _context(project, worktree_clean=False, changed_files=[".env"]),
    )
    result = report_read_and_validate("redaction.json", project, reports)
    representation = repr(result)
    assert ".env" not in representation and "[REDACTED]" in representation
    assert result["redactions"]
    assert all(set(item) == {"field", "classification"} for item in result["redactions"])
    assert _no_hash_keys(result)


def test_t56_no_raw_content_foreign_repo_following_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, reports = _roots(tmp_path)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    _write(reports, "foreign.json", _payload(foreign))

    def git_must_not_run(_root: Path, _limits: Limits) -> dict[str, object]:
        raise AssertionError("Git must not run for a foreign repository claim")

    monkeypatch.setattr(
        "voyage_framework.mcp_read.report_read.git_read_report_context", git_must_not_run
    )
    with pytest.raises(ReportReadError, match="report_repository_denied"):
        report_read_and_validate("foreign.json", project, reports)

    monkeypatch.undo()
    _init_git_repo(project)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, check=True, capture_output=True, text=True
    ).stdout.strip()
    payload = _payload(
        project,
        expected_branch="main",
        expected_head=head,
        expected_origin_main=head,
        narrative="UNIQUE_RAW_SENTINEL",
    )
    report = _write(reports, "bounded.json", payload)
    before = hashlib.sha256(report.read_bytes()).hexdigest()
    result = report_read_and_validate("bounded.json", project, reports)
    after = hashlib.sha256(report.read_bytes()).hexdigest()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=project, check=True, capture_output=True, text=True
    ).stdout
    assert before == after and status == ""
    assert "UNIQUE_RAW_SENTINEL" not in repr(result)
    assert not {"raw_content", "content", "payload"} & set(result)
