"""Integration tests for the `voyage launcher` CLI (CONTROL-LOOP-10D)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

CLI = [sys.executable, "-m", "voyage_framework.cli"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _clean_env() -> dict[str, str]:
    """Return an environment dict safe for nested git subprocesses."""
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    return env


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*CLI, *args],
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=_clean_env(),
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )


def _setup_git_repos(tmp_path: Path) -> tuple[Path, Path, Path, str, str]:
    """Create primary repo, auto worktree, and package with real git hashes."""
    primary = tmp_path / "primary"
    auto = tmp_path / "auto"
    package = auto / "CONTROL_LOOP_10D"
    primary.mkdir(parents=True)
    auto.mkdir(parents=True)
    package.mkdir(parents=True)

    # Primary repo with origin/main tracking ref
    _git(primary, "init", "--initial-branch=main")
    _git(primary, "config", "user.email", "test@example.com")
    _git(primary, "config", "user.name", "Test User")
    (primary / "README.md").write_text("primary repo\n", encoding="utf-8")
    _git(primary, "add", ".")
    _git(primary, "commit", "-m", "init primary")
    _git(primary, "remote", "add", "origin", str(primary))
    _git(primary, "fetch", "origin", "+main:refs/remotes/origin/main")

    # Auto worktree with HEAD
    _git(auto, "init", "--initial-branch=main")
    _git(auto, "config", "user.email", "test@example.com")
    _git(auto, "config", "user.name", "Test User")
    (auto / "README.md").write_text("auto worktree\n", encoding="utf-8")
    _git(auto, "add", ".")
    _git(auto, "commit", "-m", "init auto")

    origin_hash = subprocess.check_output(
        ["git", "rev-parse", "origin/main"],
        cwd=primary,
        text=True,
        env=_clean_env(),
    ).strip()
    head_hash = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=auto,
        text=True,
        env=_clean_env(),
    ).strip()

    # Runtime package files
    next_action = package / "NEXT_ACTION.md"
    next_action.write_text(
        f"""---
schema: voyage.next_action.v1
cycle: CONTROL_LOOP_10D
task_id: VF-913
baseline_commit: {head_hash}
turn: code
risk_level: report-only
---

Planned work.
""",
        encoding="utf-8",
    )

    human_approval = package / "HUMAN_APPROVAL.md"
    human_approval.write_text(
        f"""---
approved_by: human
package_path: {package}
baseline_commit: {head_hash}
risk_level: report-only
allowed_files:
  - voyage_framework/core/launcher.py
  - voyage_framework/cli.py
forbidden_paths:
  - .env
  - .voyage
statement: I approve this launcher run
---

Human approval for a single report-only launcher run.
""",
        encoding="utf-8",
    )

    return primary, auto, package, origin_hash, head_hash


def test_launcher_dry_run_success(tmp_path: Path) -> None:
    primary, auto, package, origin_hash, _head_hash = _setup_git_repos(tmp_path)
    result = _run(
        [
            "launcher",
            "dry-run",
            "--package",
            str(package),
            "--primary-repo",
            str(primary),
            "--auto-worktree",
            str(auto),
            "--expected-origin-main",
            origin_hash,
        ],
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, combined
    assert (package / "LATEST_AGENT_REPORT.md").exists()
    assert "dry-run completed" in combined


def test_launcher_dry_run_rejects_short_hash(tmp_path: Path) -> None:
    primary, auto, package, _origin_hash, _head_hash = _setup_git_repos(tmp_path)
    result = _run(
        [
            "launcher",
            "dry-run",
            "--package",
            str(package),
            "--primary-repo",
            str(primary),
            "--auto-worktree",
            str(auto),
            "--expected-origin-main",
            "abc123",
        ],
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 1, combined
    assert "40-character" in combined


def test_launcher_dry_run_rejects_missing_package(tmp_path: Path) -> None:
    primary, auto, _package, origin_hash, _head_hash = _setup_git_repos(tmp_path)
    missing = tmp_path / "missing_package"
    result = _run(
        [
            "launcher",
            "dry-run",
            "--package",
            str(missing),
            "--primary-repo",
            str(primary),
            "--auto-worktree",
            str(auto),
            "--expected-origin-main",
            origin_hash,
        ],
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 1, combined
