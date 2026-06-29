"""Source-only autoloop planning scaffold.

This module is intentionally read-only. It parses a JSON spec, evaluates git
state through read-only commands, and builds dry-run command plans. It never
executes planned commands and never mutates repositories.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Git local-env vars set by the pre-commit hook when running inside a worktree.
# Must be cleared before invoking git against any target repo so that hook env
# does not override the target's git configuration (which causes pollution of
# the Framework index when tests create temp repos under the hook).
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

SUPPORTED_SCHEMA = "voyage.auto.spec.v1"
SUPPORTED_MODE = "source_only"


class AutoLoopError(Exception):
    """Raised when an autoloop spec or guard is invalid."""


@dataclass(frozen=True)
class AutoLoopSpec:
    """Validated source-only autoloop specification."""

    schema: str
    id: str
    mode: str
    target_repo: Path
    expected_branch: str | None
    expected_head: str | None
    expected_origin_main: str | None
    require_clean_worktree: bool
    allowed_paths: list[str]
    forbidden_paths: list[str]
    max_files_changed: int | None
    allow_execution: bool
    allow_commit: bool
    allow_push: bool
    allow_merge: bool
    allow_bridge: bool
    allow_auto_launch: bool

    @classmethod
    def from_file(cls, path: Path) -> AutoLoopSpec:
        """Load and validate an autoloop spec from JSON."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise AutoLoopError(f"spec file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise AutoLoopError(f"spec file is not valid JSON: {exc}") from exc

        if not isinstance(raw, dict):
            raise AutoLoopError("spec root must be a JSON object")

        required = {
            "schema",
            "id",
            "mode",
            "target_repo",
            "require_clean_worktree",
            "allowed_paths",
            "forbidden_paths",
            "allow_execution",
            "allow_commit",
            "allow_push",
            "allow_merge",
            "allow_bridge",
            "allow_auto_launch",
        }
        missing = sorted(required - raw.keys())
        if missing:
            raise AutoLoopError(f"spec missing required fields: {missing}")

        allowed_paths = _string_list(raw.get("allowed_paths"), "allowed_paths")
        forbidden_paths = _string_list(raw.get("forbidden_paths"), "forbidden_paths")

        spec = cls(
            schema=str(raw["schema"]),
            id=str(raw["id"]),
            mode=str(raw["mode"]),
            target_repo=Path(str(raw["target_repo"])),
            expected_branch=_optional_str(raw.get("expected_branch")),
            expected_head=_optional_str(raw.get("expected_head")),
            expected_origin_main=_optional_str(raw.get("expected_origin_main")),
            require_clean_worktree=bool(raw["require_clean_worktree"]),
            allowed_paths=allowed_paths,
            forbidden_paths=forbidden_paths,
            max_files_changed=_optional_int(raw.get("max_files_changed")),
            allow_execution=bool(raw["allow_execution"]),
            allow_commit=bool(raw["allow_commit"]),
            allow_push=bool(raw["allow_push"]),
            allow_merge=bool(raw["allow_merge"]),
            allow_bridge=bool(raw["allow_bridge"]),
            allow_auto_launch=bool(raw["allow_auto_launch"]),
        )
        spec._validate_static()
        return spec

    def _validate_static(self) -> None:
        """Validate fields that do not require repository inspection."""
        if self.schema != SUPPORTED_SCHEMA:
            raise AutoLoopError(f"unsupported schema: {self.schema!r}")
        if self.mode != SUPPORTED_MODE:
            raise AutoLoopError(f"unsupported mode: {self.mode!r}")
        if not self.allowed_paths:
            raise AutoLoopError("allowed_paths must not be empty")
        if self.max_files_changed is not None and self.max_files_changed < 0:
            raise AutoLoopError("max_files_changed must be >= 0")

        enabled = [
            name
            for name, value in (
                ("allow_execution", self.allow_execution),
                ("allow_commit", self.allow_commit),
                ("allow_push", self.allow_push),
                ("allow_merge", self.allow_merge),
                ("allow_bridge", self.allow_bridge),
                ("allow_auto_launch", self.allow_auto_launch),
            )
            if value
        ]
        if enabled:
            raise AutoLoopError(f"execution flags must be false: {enabled}")

        for path in [*self.allowed_paths, *self.forbidden_paths]:
            normalized = _normalize_repo_path(path)
            if normalized in {"", ".", "/"}:
                raise AutoLoopError(f"path pattern is too broad: {path!r}")
            if normalized.startswith("../") or "/../" in normalized:
                raise AutoLoopError(f"path pattern must stay inside repo: {path!r}")

        conflicts = [
            allowed
            for allowed in self.allowed_paths
            if _matches_any(allowed, self.forbidden_paths)
            or any(_patterns_overlap(allowed, forbidden) for forbidden in self.forbidden_paths)
        ]
        if conflicts:
            raise AutoLoopError(f"allowed paths overlap forbidden paths: {conflicts}")


@dataclass(frozen=True)
class GuardResult:
    """Single guard outcome."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class PlannedCommand:
    """A command that is planned but explicitly not executed."""

    command: list[str]
    executed: bool
    reason: str


@dataclass(frozen=True)
class CommandPlan:
    """Dry-run command plan for a source-only autoloop."""

    spec_id: str
    target_repo: str
    mode: str
    risk: str
    allowed_paths: list[str]
    forbidden_paths: list[str]
    gates: list[GuardResult]
    commands: list[PlannedCommand]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable command plan."""
        return {
            "spec_id": self.spec_id,
            "target_repo": self.target_repo,
            "mode": self.mode,
            "risk": self.risk,
            "plan_only": True,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "gates": [guard.__dict__ for guard in self.gates],
            "commands": [
                {
                    "command": command.command,
                    "executed": command.executed,
                    "reason": command.reason,
                }
                for command in self.commands
            ],
        }


def run_preflight(spec_path: Path) -> tuple[bool, dict[str, Any]]:
    """Load *spec_path*, evaluate guards, and return a structured report."""
    spec = AutoLoopSpec.from_file(spec_path)
    guards = evaluate_guards(spec, require_clean=spec.require_clean_worktree)
    return _all_passed(guards), _report("preflight", spec, guards)


def run_plan(spec_path: Path) -> tuple[bool, dict[str, Any]]:
    """Load *spec_path*, evaluate guards, and build a non-executed plan."""
    spec = AutoLoopSpec.from_file(spec_path)
    guards = evaluate_guards(spec, require_clean=spec.require_clean_worktree)
    plan = build_command_plan(spec, guards)
    return _all_passed(guards), {
        "command": "plan",
        "ok": _all_passed(guards),
        "plan": plan.to_dict(),
    }


def run_validate(spec_path: Path) -> tuple[bool, dict[str, Any]]:
    """Load *spec_path* and validate current changed files against path guards."""
    spec = AutoLoopSpec.from_file(spec_path)
    guards = evaluate_guards(spec, require_clean=False)
    changed_files = _changed_files(spec.target_repo)
    guards.extend(_changed_file_guards(spec, changed_files))
    return _all_passed(guards), {
        "command": "validate",
        "ok": _all_passed(guards),
        "spec_id": spec.id,
        "target_repo": str(spec.target_repo),
        "changed_files": changed_files,
        "gates": [guard.__dict__ for guard in guards],
    }


def evaluate_guards(spec: AutoLoopSpec, *, require_clean: bool) -> list[GuardResult]:
    """Evaluate read-only repository guards for *spec*."""
    guards: list[GuardResult] = []
    repo = spec.target_repo

    guards.append(
        GuardResult(
            "target_repo_exists",
            repo.exists() and repo.is_dir(),
            f"target repo path: {repo}",
        )
    )
    if not repo.exists() or not repo.is_dir():
        return guards

    inside_worktree = _git(repo, "rev-parse", "--is-inside-work-tree")
    guards.append(
        GuardResult(
            "target_repo_is_worktree",
            inside_worktree.returncode == 0 and inside_worktree.stdout.strip() == "true",
            inside_worktree.stdout.strip() or inside_worktree.stderr.strip(),
        )
    )

    branch = _git_stdout(repo, "branch", "--show-current")
    if spec.expected_branch:
        guards.append(
            GuardResult(
                "branch_matches",
                branch == spec.expected_branch,
                f"expected {spec.expected_branch}, got {branch}",
            )
        )

    head = _git_stdout(repo, "rev-parse", "HEAD")
    if spec.expected_head:
        guards.append(
            GuardResult(
                "head_matches",
                head == spec.expected_head,
                f"expected {spec.expected_head}, got {head}",
            )
        )

    origin_main = _git_stdout(repo, "rev-parse", "origin/main")
    if spec.expected_origin_main:
        guards.append(
            GuardResult(
                "origin_main_matches",
                origin_main == spec.expected_origin_main,
                f"expected {spec.expected_origin_main}, got {origin_main}",
            )
        )

    status = _git_status(repo)
    if require_clean:
        guards.append(
            GuardResult(
                "worktree_clean",
                not status,
                "clean" if not status else f"{len(status)} changed path(s)",
            )
        )

    guards.append(
        GuardResult(
            "source_only_mode",
            spec.mode == SUPPORTED_MODE,
            f"mode={spec.mode}",
        )
    )
    guards.append(
        GuardResult(
            "no_execution_flags",
            not any(
                (
                    spec.allow_execution,
                    spec.allow_commit,
                    spec.allow_push,
                    spec.allow_merge,
                    spec.allow_bridge,
                    spec.allow_auto_launch,
                )
            ),
            "all execution flags are false",
        )
    )
    return guards


def build_command_plan(spec: AutoLoopSpec, guards: list[GuardResult]) -> CommandPlan:
    """Build a dry-run command plan without executing the planned commands."""
    commands = [
        PlannedCommand(
            ["git", "status", "--porcelain=v1", "-uall"],
            executed=False,
            reason="plan only",
        ),
        PlannedCommand(
            ["git", "rev-parse", "HEAD"],
            executed=False,
            reason="plan only",
        ),
        PlannedCommand(
            ["git", "rev-parse", "origin/main"],
            executed=False,
            reason="plan only",
        ),
    ]
    return CommandPlan(
        spec_id=spec.id,
        target_repo=str(spec.target_repo),
        mode=spec.mode,
        risk="source-only dry-run planning",
        allowed_paths=spec.allowed_paths,
        forbidden_paths=spec.forbidden_paths,
        gates=guards,
        commands=commands,
    )


def _report(command: str, spec: AutoLoopSpec, guards: list[GuardResult]) -> dict[str, Any]:
    return {
        "command": command,
        "ok": _all_passed(guards),
        "spec_id": spec.id,
        "target_repo": str(spec.target_repo),
        "mode": spec.mode,
        "allowed_paths": spec.allowed_paths,
        "forbidden_paths": spec.forbidden_paths,
        "gates": [guard.__dict__ for guard in guards],
    }


def _changed_file_guards(spec: AutoLoopSpec, changed_files: list[str]) -> list[GuardResult]:
    guards: list[GuardResult] = []
    forbidden = [path for path in changed_files if _matches_any(path, spec.forbidden_paths)]
    outside_allowlist = [
        path for path in changed_files if not _matches_any(path, spec.allowed_paths)
    ]

    guards.append(
        GuardResult(
            "forbidden_path_check",
            not forbidden,
            "none" if not forbidden else ", ".join(forbidden),
        )
    )
    guards.append(
        GuardResult(
            "file_allowlist_check",
            not outside_allowlist,
            "all changed files allowed" if not outside_allowlist else ", ".join(outside_allowlist),
        )
    )
    if spec.max_files_changed is not None:
        guards.append(
            GuardResult(
                "max_files_changed",
                len(changed_files) <= spec.max_files_changed,
                f"{len(changed_files)} <= {spec.max_files_changed}",
            )
        )
    return guards


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AutoLoopError(f"{label} must be a list of strings")
    return [_normalize_repo_path(item) for item in value]


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise AutoLoopError("max_files_changed must be an integer")
    return value


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _patterns_overlap(left: str, right: str) -> bool:
    left = _normalize_repo_path(left).rstrip("/")
    right = _normalize_repo_path(right).rstrip("/")
    left_prefix = left.removesuffix("/**")
    right_prefix = right.removesuffix("/**")
    return left_prefix == right_prefix or left_prefix.startswith(f"{right_prefix}/")


def _matches_any(path: str, patterns: list[str]) -> bool:
    normalized = _normalize_repo_path(path)
    return any(_match_pattern(normalized, pattern) for pattern in patterns)


def _match_pattern(path: str, pattern: str) -> bool:
    normalized = _normalize_repo_path(pattern)
    if normalized.endswith("/**"):
        prefix = normalized[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    return path == normalized or fnmatch.fnmatch(path, normalized)


def _changed_files(repo: Path) -> list[str]:
    return [_status_path(line) for line in _git_status(repo)]


def _git_status(repo: Path) -> list[str]:
    result = _git(repo, "status", "--porcelain=v1", "-uall")
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else line
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return _normalize_repo_path(path.strip().strip('"'))


def _git_stdout(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    clean_env = {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS}
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=clean_env,
    )


def _all_passed(guards: list[GuardResult]) -> bool:
    return all(guard.passed for guard in guards)
