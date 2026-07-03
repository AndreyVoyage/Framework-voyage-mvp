"""Unit tests for the read-only repo state collector."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import _GIT_LOCAL_ENV_VARS, collect_repo_state

_GIT_LOCAL_ENV_VARS_LOCAL: frozenset[str] = _GIT_LOCAL_ENV_VARS


def _clean_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS_LOCAL}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )


def _init_repo(path: Path, with_origin: bool = True) -> str:
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
    if with_origin:
        _git(path, "remote", "add", "origin", str(path))
        _git(path, "update-ref", "refs/remotes/origin/main", "HEAD")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        env=_clean_env(),
    ).strip()


def _assert_json_serializable(state: dict[str, Any]) -> None:
    json.dumps(state)


def test_clean_repo_with_origin_main_has_expected_fields(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["command"] == "report-state"
    assert state["ok"] is True
    assert state["repo_path"] == str(repo.resolve())
    assert state["branch"] == "main"
    assert state["head"] == head
    assert state["origin_main"] == head
    assert state["head_equals_origin_main"] is True
    assert state["worktree_clean"] is True
    assert state["changed_files"] == []
    assert state["staged_files"] == []
    assert state["untracked_files"] == []
    assert state["errors"] == []


def test_dirty_unstaged_file_reported_in_changed_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["ok"] is True
    assert state["worktree_clean"] is False
    assert "README.md" in state["changed_files"]
    assert "README.md" not in state["staged_files"]
    assert "README.md" not in state["untracked_files"]


def test_staged_file_reported_in_staged_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
    _git(repo, "add", "staged.txt")

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["ok"] is True
    assert state["worktree_clean"] is False
    assert "staged.txt" in state["staged_files"]
    assert "staged.txt" in state["changed_files"]
    assert "staged.txt" not in state["untracked_files"]


def test_untracked_file_reported_in_untracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["ok"] is True
    assert state["worktree_clean"] is False
    assert "untracked.txt" in state["untracked_files"]
    assert "untracked.txt" in state["changed_files"]
    assert "untracked.txt" not in state["staged_files"]


def test_repo_without_origin_main_does_not_crash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo, with_origin=False)

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["ok"] is True
    assert state["head"] == head
    assert state["origin_main"] is None
    assert state["head_equals_origin_main"] is None
    assert "origin/main ref not found" in state["warnings"]


def test_non_git_directory_returns_ok_false(tmp_path: Path) -> None:
    not_repo = tmp_path / "not-a-repo"
    not_repo.mkdir()

    state = collect_repo_state(not_repo)

    _assert_json_serializable(state)
    assert state["ok"] is False
    assert state["branch"] is None
    assert state["head"] is None
    assert state["origin_main"] is None
    assert state["head_equals_origin_main"] is None
    assert state["worktree_clean"] is False
    assert any("not a git repository" in error for error in state["errors"])


def test_missing_directory_returns_ok_false(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    state = collect_repo_state(missing)

    _assert_json_serializable(state)
    assert state["ok"] is False
    assert any("does not exist" in error for error in state["errors"])


def test_deleted_file_appears_in_changed_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "delete-me.txt").write_text("bye\n", encoding="utf-8")
    _git(repo, "add", "delete-me.txt")
    _git(
        repo,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "add file",
    )
    (repo / "delete-me.txt").unlink()

    state = collect_repo_state(repo)

    _assert_json_serializable(state)
    assert state["ok"] is True
    assert state["worktree_clean"] is False
    assert "delete-me.txt" in state["changed_files"]
