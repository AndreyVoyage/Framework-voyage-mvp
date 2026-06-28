"""Unit tests for the minimal controlled launcher core (CONTROL-LOOP-10D)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from voyage_framework.core.launcher import (
    HumanApproval,
    LauncherConfig,
    LauncherError,
    RuntimePackage,
    _extract_frontmatter,
    _is_full_hash,
    _parse_human_approval,
    _parse_next_action,
    _parse_runtime_package,
    run_dry_run,
)


def _hash(seed: int) -> str:
    """Return a deterministic 40-character hex hash string."""
    return f"{seed:040x}"


def _write_next_action(
    path: Path,
    baseline_commit: str,
    cycle: str = "CONTROL_LOOP_10D",
    task_id: str = "VF-913",
    turn: str = "code",
    risk_level: str = "report-only",
) -> None:
    content = f"""---
schema: voyage.next_action.v1
cycle: {cycle}
task_id: {task_id}
baseline_commit: "{baseline_commit}"
turn: {turn}
risk_level: {risk_level}
---

# NEXT_ACTION

Planned work for this cycle.
"""
    path.write_text(content, encoding="utf-8")


def _write_human_approval(
    path: Path,
    baseline_commit: str,
    package_path: str = "/auto/pkg",
) -> None:
    content = f"""---
approved_by: human
package_path: {package_path}
baseline_commit: "{baseline_commit}"
risk_level: report-only
allowed_files:
  - voyage_framework/core/launcher.py
forbidden_paths:
  - .env
  - .voyage
statement: I approve this launcher run
---

This human approval authorizes a single report-only launcher run.
"""
    path.write_text(content, encoding="utf-8")


def _write_valid_package(package_dir: Path, baseline_commit: str) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_next_action(package_dir / "NEXT_ACTION.md", baseline_commit)
    _write_human_approval(package_dir / "HUMAN_APPROVAL.md", baseline_commit)


def _patch_git(
    monkeypatch: Any,
    primary: Path,
    auto: Path,
    origin_hash: str,
    head_hash: str,
) -> None:
    def _git_rev_parse(repo: Path, ref: str) -> str:
        if repo.resolve() == primary.resolve() and ref == "origin/main":
            return origin_hash
        if repo.resolve() == auto.resolve() and ref == "HEAD":
            return head_hash
        raise RuntimeError(f"unexpected git call: {repo!r} {ref!r}")

    monkeypatch.setattr(
        "voyage_framework.core.launcher._git_rev_parse",
        _git_rev_parse,
    )


# ───────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────


class TestHashHelper:
    def test_is_full_hash_accepts_lowercase_hex(self) -> None:
        assert _is_full_hash("a" * 40) is True
        assert _is_full_hash("0" * 40) is True
        assert _is_full_hash("9" * 40) is True

    def test_is_full_hash_rejects_short(self) -> None:
        assert _is_full_hash("a" * 39) is False
        assert _is_full_hash("abc123") is False

    def test_is_full_hash_rejects_non_hex(self) -> None:
        assert _is_full_hash("g" * 40) is False


class TestFrontmatterExtraction:
    def test_extracts_valid_frontmatter(self) -> None:
        text = "---\nkey: value\n---\nbody\n"
        data = _extract_frontmatter(text, "file.md")
        assert data == {"key": "value"}

    def test_missing_frontmatter_raises(self) -> None:
        with pytest.raises(LauncherError):
            _extract_frontmatter("no frontmatter", "file.md")

    def test_invalid_yaml_raises(self) -> None:
        with pytest.raises(LauncherError):
            _extract_frontmatter("---\n[ invalid\n---\n", "file.md")


class TestNextActionParsing:
    def test_valid_next_action(self, tmp_path: Path) -> None:
        path = tmp_path / "NEXT_ACTION.md"
        _write_next_action(path, _hash(1))
        data = _parse_next_action(path)
        assert data["schema"] == "voyage.next_action.v1"
        assert data["turn"] == "code"
        assert data["baseline_commit"] == _hash(1)

    def test_wrong_schema_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "NEXT_ACTION.md"
        path.write_text(
            "---\nschema: wrong\ncycle: c\ntask_id: id\nbaseline_commit: "
            + _hash(1)
            + "\nturn: code\nrisk_level: report-only\n---\n",
            encoding="utf-8",
        )
        with pytest.raises(LauncherError):
            _parse_next_action(path)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "NEXT_ACTION.md"
        path.write_text(
            "---\nschema: voyage.next_action.v1\ncycle: c\n---\n",
            encoding="utf-8",
        )
        with pytest.raises(LauncherError):
            _parse_next_action(path)

    def test_turn_not_code_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "NEXT_ACTION.md"
        _write_next_action(path, _hash(1), turn="review")
        with pytest.raises(LauncherError):
            _parse_next_action(path)


class TestHumanApprovalParsing:
    def test_valid_approval(self, tmp_path: Path) -> None:
        path = tmp_path / "HUMAN_APPROVAL.md"
        _write_human_approval(path, _hash(1))
        approval = _parse_human_approval(path)
        assert isinstance(approval, HumanApproval)
        assert approval.baseline_commit == _hash(1)

    def test_missing_phrase_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "HUMAN_APPROVAL.md"
        path.write_text(
            "---\napproved_by: human\n---\n\nApproval without exact phrase.\n",
            encoding="utf-8",
        )
        with pytest.raises(LauncherError):
            _parse_human_approval(path)


class TestRuntimePackageParsing:
    def test_valid_package(self, tmp_path: Path) -> None:
        _write_valid_package(tmp_path, _hash(1))
        pkg = _parse_runtime_package(tmp_path)
        assert isinstance(pkg, RuntimePackage)
        assert pkg.next_action["baseline_commit"] == _hash(1)

    def test_missing_next_action_raises(self, tmp_path: Path) -> None:
        _write_human_approval(tmp_path / "HUMAN_APPROVAL.md", _hash(1))
        with pytest.raises(LauncherError):
            _parse_runtime_package(tmp_path)

    def test_missing_human_approval_raises(self, tmp_path: Path) -> None:
        _write_next_action(tmp_path / "NEXT_ACTION.md", _hash(1))
        with pytest.raises(LauncherError):
            _parse_runtime_package(tmp_path)

    def test_multiple_next_action_files_raises(self, tmp_path: Path) -> None:
        _write_valid_package(tmp_path, _hash(1))
        _write_next_action(tmp_path / "NEXT_ACTION_2.md", _hash(1))
        with pytest.raises(LauncherError):
            _parse_runtime_package(tmp_path)


# ───────────────────────────────────────────────────────────────
# Dry-run gates
# ───────────────────────────────────────────────────────────────


class TestDryRunSuccess:
    def test_valid_package_creates_report(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        _write_valid_package(package, baseline)
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)

        assert result.success is True
        assert result.report_path is not None
        assert result.report_path.exists()
        report_text = result.report_path.read_text(encoding="utf-8")
        assert "voyage.agent_report.v1" in report_text
        assert "dry-run" in report_text.lower()
        assert "stop" in report_text.lower()


class TestDryRunFailures:
    def test_short_expected_hash_rejected(self, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        _write_valid_package(package, _hash(2))

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main="abc123",
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "40-character" in result.message

    def test_missing_human_approval_rejected(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        package.mkdir(parents=True)
        _write_next_action(package / "NEXT_ACTION.md", baseline)
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "HUMAN_APPROVAL.md" in result.message

    def test_missing_next_action_rejected(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        package.mkdir(parents=True)
        _write_human_approval(package / "HUMAN_APPROVAL.md", baseline)
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "NEXT_ACTION.md" in result.message

    def test_existing_latest_report_rejected(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        _write_valid_package(package, baseline)
        (package / "LATEST_AGENT_REPORT.md").write_text("existing", encoding="utf-8")
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "LATEST_AGENT_REPORT.md" in result.message

    def test_existing_morning_report_rejected(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        _write_valid_package(package, baseline)
        (package / "MORNING_REPORT.md").write_text("existing", encoding="utf-8")
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "MORNING_REPORT.md" in result.message

    def test_dotenv_package_path_rejected(self, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / ".env"
        package.mkdir()

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=_hash(1),
        )
        result = run_dry_run(config)
        assert result.success is False
        assert ".env" in result.message

    def test_dotvoyage_package_path_rejected(self, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        primary.mkdir()
        auto.mkdir()
        package = auto / ".voyage"
        package.mkdir()

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=_hash(1),
        )
        result = run_dry_run(config)
        assert result.success is False
        assert ".voyage" in result.message

    def test_dotenv_primary_repo_rejected(self, tmp_path: Path) -> None:
        primary = tmp_path / ".env"
        primary.mkdir()
        auto = tmp_path / "auto"
        auto.mkdir()
        package = auto / "pkg"
        package.mkdir()

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=_hash(1),
        )
        result = run_dry_run(config)
        assert result.success is False
        assert ".env" in result.message

    def test_dotvoyage_auto_worktree_rejected(self, tmp_path: Path) -> None:
        primary = tmp_path / "primary"
        primary.mkdir()
        auto = tmp_path / ".voyage"
        auto.mkdir()
        package = auto / "pkg"
        package.mkdir()

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=_hash(1),
        )
        result = run_dry_run(config)
        assert result.success is False
        assert ".voyage" in result.message

    def test_package_outside_auto_rejected(self, tmp_path: Path, monkeypatch: Any) -> None:
        primary = tmp_path / "primary"
        auto = tmp_path / "auto"
        other = tmp_path / "other"
        primary.mkdir()
        auto.mkdir()
        other.mkdir()
        package = other / "pkg"
        baseline = _hash(2)
        origin = _hash(1)
        _write_valid_package(package, baseline)
        _patch_git(monkeypatch, primary, auto, origin, baseline)

        config = LauncherConfig(
            package_dir=package,
            primary_repo=primary,
            auto_worktree=auto,
            expected_origin_main=origin,
        )
        result = run_dry_run(config)
        assert result.success is False
        assert "inside auto_worktree" in result.message
