"""Integration tests for the `voyage auto` CLI scaffold."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

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
    return {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS}


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
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "init")
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "fetch", "origin", "+main:refs/remotes/origin/main")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        env=_clean_env(),
    ).strip()


def _write_spec(path: Path, repo: Path, head: str, **overrides: Any) -> Path:
    spec: dict[str, Any] = {
        "schema": "voyage.auto.spec.v1",
        "id": "D0B-SOURCE-ONLY",
        "mode": "source_only",
        "target_repo": str(repo),
        "expected_branch": "main",
        "expected_head": head,
        "expected_origin_main": head,
        "require_clean_worktree": True,
        "allowed_paths": ["novel/sources/**"],
        "forbidden_paths": [".env", ".voyage/**", "tools/**", "game/script.rpy"],
        "max_files_changed": 1,
        "allow_execution": False,
        "allow_commit": False,
        "allow_push": False,
        "allow_merge": False,
        "allow_bridge": False,
        "allow_auto_launch": False,
    }
    spec.update(overrides)
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def test_cli_help_includes_auto() -> None:
    result = _run(["--help"])
    combined = (result.stdout or "") + (result.stderr or "")

    assert result.returncode == 0, combined
    assert "auto" in combined


def test_auto_subcommand_help() -> None:
    for args in (
        ["auto", "--help"],
        ["auto", "preflight", "--help"],
        ["auto", "plan", "--help"],
        ["auto", "validate", "--help"],
    ):
        result = _run(args)
        combined = (result.stdout or "") + (result.stderr or "")
        assert result.returncode == 0, combined


def test_auto_preflight_plan_validate_do_not_execute_commands(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec = _write_spec(tmp_path / "spec.json", repo, head)

    for command in ("preflight", "plan", "validate"):
        result = _run(["auto", command, "--spec", str(spec)])
        combined = (result.stdout or "") + (result.stderr or "")
        assert result.returncode == 0, combined
        payload = json.loads(result.stdout)
        assert payload["ok"] is True

    plan = json.loads(_run(["auto", "plan", "--spec", str(spec)]).stdout)
    commands = plan["plan"]["commands"]
    assert commands
    assert all(command["executed"] is False for command in commands)
    assert ".env" in plan["plan"]["forbidden_paths"]
    assert ".voyage/**" in plan["plan"]["forbidden_paths"]
