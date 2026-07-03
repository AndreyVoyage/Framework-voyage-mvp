"""Integration tests for the `voyage report-state` CLI command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CLI = [sys.executable, "-m", "voyage_framework.cli"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

_GIT_LOCAL_ENV_VARS: frozenset[str] = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_DIR",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)


def _clean_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
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


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True)
    _git(path, "init", "--initial-branch=main")
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(
        path,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    )
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "update-ref", "refs/remotes/origin/main", "HEAD")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        env=_clean_env(),
    ).strip()


class TestReportStateCLIHelp:
    def test_report_state_help_mentions_observed_state(self) -> None:
        result = _run(["report-state", "--help"])
        assert result.returncode == 0
        assert "--repo" in result.stdout
        help_text = result.stdout.lower()
        assert "observed" in help_text or "canonical" in help_text


class TestReportStateCLIClean:
    def test_clean_repo_reports_ok_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        head = _init_repo(repo)

        result = _run(["report-state", "--repo", str(repo)])
        payload = json.loads(result.stdout)

        assert result.returncode == 0
        assert payload["command"] == "report-state"
        assert payload["ok"] is True
        assert payload["branch"] == "main"
        assert payload["head"] == head
        assert payload["worktree_clean"] is True
        assert payload["changed_files"] == []
        assert payload["staged_files"] == []
        assert payload["untracked_files"] == []


class TestReportStateCLIDirty:
    def test_dirty_repo_reports_worktree_clean_false(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
        _git(repo, "add", "staged.txt")

        result = _run(["report-state", "--repo", str(repo)])
        payload = json.loads(result.stdout)

        assert result.returncode == 0
        assert payload["ok"] is True
        assert payload["worktree_clean"] is False
        assert "dirty.txt" in payload["changed_files"]
        assert "staged.txt" in payload["staged_files"]
        assert "dirty.txt" in payload["untracked_files"] or "dirty.txt" in payload["changed_files"]


class TestReportStateCLINonGit:
    def test_non_git_repo_reports_ok_false(self, tmp_path: Path) -> None:
        not_repo = tmp_path / "not-a-repo"
        not_repo.mkdir()

        result = _run(["report-state", "--repo", str(not_repo)])
        payload = json.loads(result.stdout)

        assert result.returncode == 1
        assert payload["command"] == "report-state"
        assert payload["ok"] is False
        assert any("not a git repository" in error for error in payload["errors"])


class TestReportStateCLIDefaultRepo:
    def test_defaults_to_current_working_directory(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = _run(["report-state"], cwd=repo)
        payload = json.loads(result.stdout)

        assert result.returncode == 0
        assert payload["command"] == "report-state"
        assert payload["ok"] is True
        assert payload["repo_path"] == str(repo.resolve())
