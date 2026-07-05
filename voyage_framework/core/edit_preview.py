"""Generic read-only edit-preview / change-plan validator.

Validates a proposal JSON plan against a target repository state and the
role-based forbidden-path policy. Produces a JSON-serializable safety preview
with no writes, no patch generation, and no apply.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import collect_repo_state
from voyage_framework.core.forbidden_paths import (
    _matches_any,
    forbidden_patterns_for_role,
)

_COMMAND = "edit.preview"
_READ_ONLY = True
_APPLY_SUPPORTED = False
_NEXT_GATE = "F7_guarded_write_required"


def edit_preview(
    plan_path: str | Path,
    repo_path: str | Path,
    repo_role: str = "generic",
) -> dict[str, Any]:
    """Return a read-only safety preview for a proposed change plan.

    The function never modifies the repository. It validates the plan file,
    repository state, affected file paths, and proposed actions against the
    forbidden-path policy for ``repo_role``.

    Args:
        plan_path: Path to a JSON proposal plan (e.g. spec-plan output).
        repo_path: Path to the target repository root.
        repo_role: Role name used to select forbidden-path policy. Defaults to
            ``generic``.

    Returns:
        A JSON-serializable dictionary describing the safety preview.
    """
    repo_role = (repo_role or "generic").lower()
    plan_path_obj = Path(plan_path)
    repo_path_obj = Path(repo_path).resolve()

    findings: list[dict[str, Any]] = []
    findings_seen: set[tuple[str, str | None]] = set()
    warnings: set[str] = set()
    errors: set[str] = set()

    # ------------------------------------------------------------------
    # Load plan
    # ------------------------------------------------------------------
    plan: dict[str, Any] = {}
    if not plan_path_obj.exists() or not plan_path_obj.is_file():
        _add_finding(
            findings,
            findings_seen,
            "error",
            "plan_missing",
            f"plan file not found: {plan_path_obj}",
            None,
        )
        errors.add("plan_missing")
    else:
        try:
            raw = json.loads(plan_path_obj.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("plan root must be a JSON object")
            plan = raw
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            _add_finding(
                findings,
                findings_seen,
                "error",
                "invalid_plan_json",
                f"plan file is not valid JSON: {exc}",
                str(plan_path_obj),
            )
            errors.add("invalid_plan_json")

    # ------------------------------------------------------------------
    # Collect repo state
    # ------------------------------------------------------------------
    repo_state: dict[str, Any]
    repo_ok = False
    if not repo_path_obj.exists() or not repo_path_obj.is_dir():
        _add_finding(
            findings,
            findings_seen,
            "error",
            "repo_missing",
            f"repo path does not exist or is not a directory: {repo_path_obj}",
            None,
        )
        errors.add("repo_missing")
        repo_state = _empty_repo_state()
    else:
        state = collect_repo_state(repo_path_obj)
        repo_state = {
            "worktree_clean": state.get("worktree_clean"),
            "head": state.get("head"),
            "origin_main": state.get("origin_main"),
            "branch": state.get("branch"),
        }
        if state.get("ok") is not True:
            _add_finding(
                findings,
                findings_seen,
                "error",
                "repo_not_git",
                f"repo path is not a readable git repository: {repo_path_obj}",
                None,
            )
            errors.add("repo_not_git")
        else:
            repo_ok = True
            if not state.get("worktree_clean", True):
                _add_finding(
                    findings,
                    findings_seen,
                    "warning",
                    "dirty_worktree",
                    "target repo worktree is dirty",
                    None,
                )
                warnings.add("dirty_worktree")
            if state.get("staged_files"):
                _add_finding(
                    findings,
                    findings_seen,
                    "warning",
                    "staged_files_present",
                    f"staged files present: {len(state['staged_files'])}",
                    None,
                )
                warnings.add("staged_files_present")
            if state.get("untracked_files"):
                _add_finding(
                    findings,
                    findings_seen,
                    "warning",
                    "untracked_files_present",
                    f"untracked files present: {len(state['untracked_files'])}",
                    None,
                )
                warnings.add("untracked_files_present")

    # ------------------------------------------------------------------
    # Validate plan apply semantics
    # ------------------------------------------------------------------
    source_apply_supported = plan.get("apply_supported", "unknown")
    if source_apply_supported is True:
        _add_finding(
            findings,
            findings_seen,
            "error",
            "apply_not_supported",
            "input plan claims apply_supported=true; F6 preview does not allow apply",
            None,
        )
        errors.add("apply_not_supported")

    if plan.get("read_only") is False:
        _add_finding(
            findings,
            findings_seen,
            "error",
            "plan_not_read_only",
            "input plan is not marked read_only; only read-only plans are accepted",
            None,
        )
        errors.add("plan_not_read_only")

    # ------------------------------------------------------------------
    # Validate affected files and proposed action target files
    # ------------------------------------------------------------------
    forbidden_patterns = forbidden_patterns_for_role(repo_role)
    allowed_files: set[str] = set()
    blocked_files: set[str] = set()

    affected_files = _as_string_list(plan.get("affected_files"))
    for raw_path in affected_files:
        _classify_file(
            raw_path,
            repo_path_obj,
            forbidden_patterns,
            allowed_files,
            blocked_files,
            findings,
            findings_seen,
            errors,
        )

    proposed_actions = _as_dict_list(plan.get("proposed_actions"))
    for index, action in enumerate(proposed_actions):
        status = action.get("status") if isinstance(action, dict) else None
        if status != "proposal_only":
            _add_finding(
                findings,
                findings_seen,
                "error",
                "action_not_proposal_only",
                (f"proposed action at index {index} has status={status!r}; must be proposal_only"),
                None,
            )
            errors.add("action_not_proposal_only")

        safe_auto = action.get("safe_to_apply_automatically")
        if safe_auto is True:
            _add_finding(
                findings,
                findings_seen,
                "error",
                "unsafe_auto_apply_flag",
                f"proposed action at index {index} claims safe_to_apply_automatically=true",
                None,
            )
            errors.add("unsafe_auto_apply_flag")

        target_file = action.get("target_file") if isinstance(action, dict) else None
        if isinstance(target_file, str):
            _classify_file(
                target_file,
                repo_path_obj,
                forbidden_patterns,
                allowed_files,
                blocked_files,
                findings,
                findings_seen,
                errors,
            )

    # ------------------------------------------------------------------
    # Determine readiness and ok
    # ------------------------------------------------------------------
    has_errors = bool(errors)
    has_warnings = bool(warnings) or bool(findings and not has_errors)
    if has_errors or not repo_ok:
        readiness = "blocked"
        ok = False
    elif has_warnings:
        readiness = "warnings"
        ok = True
    else:
        readiness = "ready"
        ok = True

    return {
        "command": _COMMAND,
        "ok": ok,
        "read_only": _READ_ONLY,
        "apply_supported": _APPLY_SUPPORTED,
        "repo_root": str(repo_path_obj),
        "source_plan": str(plan_path_obj.resolve()),
        "repo_role": repo_role,
        "repo_state": repo_state,
        "plan_summary": {
            "affected_files_count": len(affected_files),
            "proposed_actions_count": len(proposed_actions),
            "source_readiness": str(plan.get("readiness", "unknown")),
            "source_apply_supported": source_apply_supported,
        },
        "safety_findings": sorted(findings, key=_finding_sort_key),
        "allowed_files": sorted(allowed_files - blocked_files),
        "blocked_files": sorted(blocked_files),
        "warnings": sorted(warnings),
        "errors": sorted(errors),
        "readiness": readiness,
        "next_gate": _NEXT_GATE,
    }


def _empty_repo_state() -> dict[str, Any]:
    return {
        "worktree_clean": None,
        "head": None,
        "origin_main": None,
        "branch": None,
    }


def _finding(
    severity: str,
    code: str,
    message: str,
    file: str | None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "file": file,
    }


def _finding_sort_key(finding: dict[str, Any]) -> tuple[str, str, str | None]:
    return (finding["severity"], finding["code"], finding.get("file") or "")


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _add_finding(
    findings: list[dict[str, Any]],
    seen: set[tuple[str, str | None]],
    severity: str,
    code: str,
    message: str,
    file: str | None,
) -> None:
    """Append a finding unless an identical (code, file) finding already exists."""
    key = (code, file)
    if key in seen:
        return
    seen.add(key)
    findings.append(_finding(severity, code, message, file))


def _classify_file(
    raw_path: str,
    repo_path: Path,
    forbidden_patterns: tuple[str, ...],
    allowed_files: set[str],
    blocked_files: set[str],
    findings: list[dict[str, Any]],
    findings_seen: set[tuple[str, str | None]],
    errors: set[str],
) -> None:
    """Classify a repo-relative path as allowed or blocked."""
    normalized = raw_path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]

    if not normalized:
        return

    # Absolute paths are not allowed.
    if Path(normalized).is_absolute() or normalized.startswith("/"):
        blocked_files.add(normalized)
        _add_finding(
            findings,
            findings_seen,
            "error",
            "absolute_path",
            f"affected file path is absolute: {raw_path}",
            normalized,
        )
        errors.add("absolute_path")
        return

    # Path traversal / outside repo check.
    candidate = (repo_path / normalized).resolve()
    try:
        candidate.relative_to(repo_path.resolve())
    except ValueError:
        blocked_files.add(normalized)
        _add_finding(
            findings,
            findings_seen,
            "error",
            "path_traversal",
            f"affected file path resolves outside repo: {raw_path}",
            normalized,
        )
        errors.add("path_traversal")
        return

    # Forbidden path policy.
    if _matches_any(normalized, forbidden_patterns):
        blocked_files.add(normalized)
        _add_finding(
            findings,
            findings_seen,
            "error",
            "forbidden_path",
            f"affected file path matches forbidden policy for role: {normalized}",
            normalized,
        )
        errors.add("forbidden_path")
        return

    allowed_files.add(normalized)
