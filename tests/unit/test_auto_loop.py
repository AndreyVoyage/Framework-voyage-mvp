"""Unit tests for the source-only autoloop scaffold."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

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
    return {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS}


from voyage_framework.core.auto_loop import (
    AutoLoopError,
    AutoLoopSpec,
    CommandPlan,
    GuardResult,
    build_command_plan,
    run_preflight,
    run_validate,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_git_env(),
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
        env=_clean_git_env(),
    ).strip()


def _spec_dict(repo: Path, head: str, **overrides: Any) -> dict[str, Any]:
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
        "forbidden_paths": [
            ".env",
            ".voyage/**",
            "tools/**",
            "personas/**",
            "game/script.rpy",
            "game/screens.rpy",
            "script.rpy",
            "screens.rpy",
        ],
        "max_files_changed": 1,
        "allow_execution": False,
        "allow_commit": False,
        "allow_push": False,
        "allow_merge": False,
        "allow_bridge": False,
        "allow_auto_launch": False,
    }
    spec.update(overrides)
    return spec


def _write_spec(path: Path, repo: Path, head: str, **overrides: Any) -> Path:
    path.write_text(json.dumps(_spec_dict(repo, head, **overrides)), encoding="utf-8")
    return path


def test_valid_spec_parse(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)

    spec = AutoLoopSpec.from_file(spec_path)

    assert spec.id == "D0B-SOURCE-ONLY"
    assert spec.mode == "source_only"
    assert spec.allow_execution is False
    assert ".env" in spec.forbidden_paths
    assert ".voyage/**" in spec.forbidden_paths


def test_missing_required_fields(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text('{"schema": "voyage.auto.spec.v1"}', encoding="utf-8")

    with pytest.raises(AutoLoopError, match="missing required"):
        AutoLoopSpec.from_file(spec_path)


def test_forbidden_path_rejection(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(
        tmp_path / "spec.json",
        repo,
        head,
        allowed_paths=[".voyage/**"],
    )

    with pytest.raises(AutoLoopError, match="overlap forbidden"):
        AutoLoopSpec.from_file(spec_path)


def test_preflight_clean_worktree_passes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)

    ok, report = run_preflight(spec_path)

    assert ok is True
    assert report["ok"] is True


def test_preflight_clean_worktree_requirement_fails_when_dirty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)
    (repo / "novel").mkdir()
    (repo / "novel" / "sources").mkdir()
    (repo / "novel" / "sources" / "SC_020.json").write_text("{}", encoding="utf-8")

    ok, report = run_preflight(spec_path)

    assert ok is False
    assert any(gate["name"] == "worktree_clean" for gate in report["gates"])


def test_validate_accepts_allowed_source_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)
    source_dir = repo / "novel" / "sources"
    source_dir.mkdir(parents=True)
    (source_dir / "SC_020.json").write_text("{}", encoding="utf-8")

    ok, report = run_validate(spec_path)

    assert ok is True
    assert report["changed_files"] == ["novel/sources/SC_020.json"]


def test_validate_rejects_forbidden_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)
    (repo / "tools").mkdir()
    (repo / "tools" / "bad.py").write_text("print('bad')\n", encoding="utf-8")

    ok, report = run_validate(spec_path)

    assert ok is False
    forbidden_gate = next(
        gate for gate in report["gates"] if gate["name"] == "forbidden_path_check"
    )
    assert "tools/bad.py" in forbidden_gate["detail"]


def test_validate_rejects_dot_prefixed_forbidden_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)
    (repo / ".env").write_text("SECRET=not-read\n", encoding="utf-8")

    ok, report = run_validate(spec_path)

    assert ok is False
    forbidden_gate = next(
        gate for gate in report["gates"] if gate["name"] == "forbidden_path_check"
    )
    assert ".env" in forbidden_gate["detail"]


def test_command_plan_marks_commands_non_executed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    spec_path = _write_spec(tmp_path / "spec.json", repo, head)
    spec = AutoLoopSpec.from_file(spec_path)

    plan = build_command_plan(spec, [GuardResult("example", True, "ok")])

    assert isinstance(plan, CommandPlan)
    assert plan.to_dict()["plan_only"] is True
    assert all(command.executed is False for command in plan.commands)
