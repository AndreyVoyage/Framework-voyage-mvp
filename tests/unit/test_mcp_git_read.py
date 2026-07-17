"""T35-T46: fixed-command, bounded local Git reader tests."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from voyage_framework.mcp_read import git_read
from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.git_read import (
    GIT_COMMANDS,
    GitReadError,
    _git_env,
    _parse_status,
    _run_fixed,
    git_read_state,
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env={
            **_git_env(),
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        },
    )


def _repo(tmp_path: Path, *, origin_ref: bool = True) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "fixture")
    if origin_ref:
        _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _git_snapshot(repo: Path) -> tuple[str, str, tuple[int, str] | None]:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    index = repo / ".git" / "index"
    index_state = (
        (index.stat().st_mtime_ns, hashlib.sha256(index.read_bytes()).hexdigest())
        if index.exists()
        else None
    )
    return head, status, index_state


def test_t35_exact_fixed_command_allowlist() -> None:
    assert GIT_COMMANDS == (
        ("rev-parse", "--show-toplevel"),
        ("branch", "--show-current"),
        ("rev-parse", "HEAD"),
        ("rev-parse", "--verify", "--quiet", "refs/remotes/origin/main"),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
    )


def test_t36_mutation_network_and_caller_commands_are_impossible(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for denied in (("push",), ("commit",), ("fetch",), ("status",)):
        with pytest.raises(GitReadError, match="git_command_denied"):
            _run_fixed(repo, denied, Limits())


def test_t37_environment_is_hardened(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_DIR", "unsafe")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "unsafe")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "unsafe")
    env = _git_env()
    assert "GIT_DIR" not in env and "GIT_CONFIG_KEY_0" not in env
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GCM_INTERACTIVE"] == "Never"
    assert env["GIT_CONFIG_GLOBAL"] and env["GIT_CONFIG_SYSTEM"]
    for key in ("GIT_EXTERNAL_DIFF", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND", "LESS"):
        assert env[key] == ""


def test_t38_state_read_performs_no_implicit_network(tmp_path: Path) -> None:
    repo = _repo(tmp_path, origin_ref=False)
    forbidden = {"fetch", "pull", "push", "ls-remote", "remote"}
    assert not any(forbidden & set(command) for command in GIT_COMMANDS)
    state = git_read_state(repo)
    assert state["remote_verified"] is False
    assert state["remote_verification_method"] == "none"


def test_t39_timeout_terminates_reaps_and_joins_readers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    before = {thread.ident for thread in threading.enumerate()}
    monkeypatch.setattr(
        git_read,
        "_PREFIX",
        (sys.executable, "-c", "import time; time.sleep(10)"),
    )
    started = time.monotonic()
    with pytest.raises(GitReadError, match="git_timeout"):
        _run_fixed(repo, GIT_COMMANDS[0], Limits(git_timeout_seconds=0.05))
    assert time.monotonic() - started < 2
    assert {thread.ident for thread in threading.enumerate()} == before


def test_t40_output_is_bounded_while_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    before = {thread.ident for thread in threading.enumerate()}
    monkeypatch.setattr(
        git_read,
        "_PREFIX",
        (sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'x'*1000000)"),
    )
    with pytest.raises(GitReadError, match="git_output_limit_exceeded"):
        _run_fixed(repo, GIT_COMMANDS[0], Limits(max_git_output_bytes=128))
    assert {thread.ident for thread in threading.enumerate()} == before


def test_t41_remote_is_explicitly_unverified(tmp_path: Path) -> None:
    state = git_read_state(_repo(tmp_path))
    assert state["remote_verified"] is False
    assert state["remote_checked_at"] is None
    assert state["remote_verification_method"] == "none"


def test_t42_local_tracking_ref_and_rename_semantics(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    state = git_read_state(repo)
    assert state["local_head"] == state["local_origin_main_ref"]
    assert state["local_head_matches_origin_ref"] is True
    parsed = _parse_status(b"R  renamed.txt\0original.txt\0")
    assert parsed["changed_files"] == ["renamed.txt"]
    assert parsed["staged_files"] == ["renamed.txt"]


def test_t43_detached_head_is_null_with_warning(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "--detach")
    state = git_read_state(repo)
    assert state["local_branch"] is None
    assert "HEAD is detached" in state["warnings"]


def test_t44_missing_origin_main_is_a_local_warning(tmp_path: Path) -> None:
    state = git_read_state(_repo(tmp_path, origin_ref=False))
    assert state["local_origin_main_ref"] is None
    assert state["local_head_matches_origin_ref"] is None
    assert "local origin/main tracking ref not found" in state["warnings"]


def test_t45_sensitive_filename_is_classified_without_content_read(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / ".env").write_text("synthetic=true\n", encoding="utf-8")
    state = git_read_state(repo)
    assert state["sensitive_files"] == [{"path": ".env", "classification": "potentially_sensitive"}]
    assert "synthetic=true" not in repr(state)


def test_t46_repository_state_is_unchanged(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "untracked.txt").write_text("fixture\n", encoding="utf-8")
    before = _git_snapshot(repo)
    state = git_read_state(repo)
    after = _git_snapshot(repo)
    assert state["untracked_files"] == ["untracked.txt"]
    assert after == before
