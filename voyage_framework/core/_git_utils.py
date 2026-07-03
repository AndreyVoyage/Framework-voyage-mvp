"""Read-only Git subprocess helpers shared by Voyage guard code."""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Git local-env vars set by hooks when running inside a worktree. Clear them
# before invoking git against a target repo so hook env does not pollute tests
# or cross-repo inspections.
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


def _clean_git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in _GIT_LOCAL_ENV_VARS}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=_clean_git_env(),
    )


def _git_stdout(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_status(repo: Path) -> list[str]:
    result = _git(repo, "status", "--porcelain=v1", "-uall")
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else line
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return _normalize_repo_path(path.strip().strip('"'))


def _git_name_only(repo: Path, *args: str) -> list[str]:
    result = _git(repo, *args)
    if result.returncode != 0:
        return []
    return sorted(_normalize_repo_path(line) for line in result.stdout.splitlines() if line.strip())


def _git_commit_object_exists(repo: Path, sha: str) -> bool:
    """Return True iff *sha* resolves to a commit object in *repo*."""
    result = _git(repo, "cat-file", "-t", sha)
    return result.returncode == 0 and result.stdout.strip() == "commit"


def _git_changed_files_in_commit(repo: Path, sha: str) -> list[str]:
    """Return normalized paths changed in a single commit (handles root commits)."""
    result = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha)
    if result.returncode != 0:
        return []
    return sorted(_normalize_repo_path(line) for line in result.stdout.splitlines() if line.strip())


def _git_changed_files_in_range(repo: Path, before: str, after: str) -> list[str]:
    """Return normalized paths changed between *before* and *after*."""
    result = _git(repo, "diff", "--name-only", f"{before}..{after}")
    if result.returncode != 0:
        return []
    return sorted(_normalize_repo_path(line) for line in result.stdout.splitlines() if line.strip())


def _git_parent_commits(repo: Path, sha: str) -> list[str]:
    """Return parent commit hashes for *sha* (empty for root commits)."""
    result = _git(repo, "rev-list", "--parents", "-n", "1", sha)
    if result.returncode != 0:
        return []
    parts = result.stdout.strip().split()
    # First token is the commit itself, remaining tokens are parents.
    return parts[1:] if len(parts) > 1 else []


def collect_repo_state(repo_path: str | Path) -> dict[str, Any]:
    """Return a JSON-serializable, read-only snapshot of a git repository state.

    The function never modifies the repository. It only runs read-only git
    commands and returns observed facts. A dirty worktree is reported as data,
    not as a policy failure.
    """
    path = Path(repo_path).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists() or not path.is_dir():
        errors.append(f"repo path does not exist or is not a directory: {path}")
        return {
            "command": "report-state",
            "ok": False,
            "repo_path": str(path),
            "branch": None,
            "head": None,
            "origin_main": None,
            "head_equals_origin_main": None,
            "worktree_clean": False,
            "changed_files": [],
            "staged_files": [],
            "untracked_files": [],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "git_status_short": [],
            "errors": errors,
            "warnings": warnings,
        }

    inside = _git(path, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        errors.append(f"not a git repository: {path}")
        return {
            "command": "report-state",
            "ok": False,
            "repo_path": str(path),
            "branch": None,
            "head": None,
            "origin_main": None,
            "head_equals_origin_main": None,
            "worktree_clean": False,
            "changed_files": [],
            "staged_files": [],
            "untracked_files": [],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "git_status_short": [],
            "errors": errors,
            "warnings": warnings,
        }

    branch = _git_stdout(path, "branch", "--show-current") or None
    head = _git_stdout(path, "rev-parse", "HEAD") or None
    origin_main = _git_stdout(path, "rev-parse", "origin/main") or None

    if origin_main is None:
        warnings.append("origin/main ref not found")

    head_equals_origin_main: bool | None = None
    if head and origin_main:
        head_equals_origin_main = head == origin_main

    status_lines = _git_status(path)
    worktree_clean = not status_lines

    untracked_files = sorted(_status_path(line) for line in status_lines if line.startswith("?? "))
    staged_files = _git_name_only(path, "diff", "--cached", "--name-only")
    unstaged_files = _git_name_only(path, "diff", "--name-only")
    changed_files = sorted(set(unstaged_files) | set(staged_files) | set(untracked_files))

    return {
        "command": "report-state",
        "ok": True,
        "repo_path": str(path),
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": head_equals_origin_main,
        "worktree_clean": worktree_clean,
        "changed_files": changed_files,
        "staged_files": staged_files,
        "untracked_files": untracked_files,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_status_short": status_lines,
        "errors": errors,
        "warnings": warnings,
    }
