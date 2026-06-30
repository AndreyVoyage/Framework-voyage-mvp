"""Read-only Git subprocess helpers shared by Voyage guard code."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

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
