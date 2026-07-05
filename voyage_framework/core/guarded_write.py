"""Generic guarded-write approval plan generator.

Consumes an F6 ``edit-preview`` JSON output and produces a read-only
approval/preflight plan. The module never writes files, generates patches,
applies changes, stages files, or commits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import collect_repo_state

_COMMAND = "guarded_write.plan"
_READ_ONLY = True
_WRITES_SUPPORTED = False
_APPROVAL_REQUIRED = True
_NEXT_GATE = "human_approval_required"

_REQUIRED_EVIDENCE = (
    "source edit-preview JSON file",
    "repo_state snapshot matching current target repo",
    "human approval with identity, reason, and timestamp",
    "allowed file list confirmed",
    "blocked file list empty",
    "clean worktree (no unstaged/staged/untracked changes)",
    "rollback/checkpoint plan",
    "post-write validation plan",
    "validate-report plan for after writes",
)

_REQUIRED_CHECKS = (
    "verify edit-preview ok=true",
    "verify edit-preview readiness is ready or warnings",
    "verify no blocked files",
    "verify no error safety_findings",
    "verify repo state unchanged from preview snapshot",
    "verify no forbidden paths in allowed files",
    "verify human approval recorded",
    "verify rollback checkpoint exists",
    "run targeted tests after write",
    "run validate-report after write",
    "run report-state after write",
)


# Blocked reason codes returned in the ``blocked_reasons`` list.
class _Reason:
    PREVIEW_MISSING = "preview_missing"
    INVALID_PREVIEW_JSON = "invalid_preview_json"
    REPO_MISSING = "repo_missing"
    REPO_NOT_GIT = "repo_not_git"
    INVALID_PREVIEW_COMMAND = "invalid_preview_command"
    PREVIEW_NOT_READ_ONLY = "preview_not_read_only"
    PREVIEW_APPLY_SUPPORTED = "preview_apply_supported"
    PREVIEW_WRONG_NEXT_GATE = "preview_wrong_next_gate"
    SOURCE_PREVIEW_BLOCKED = "source_preview_blocked"
    BLOCKED_FILES_PRESENT = "blocked_files_present"
    ERROR_SAFETY_FINDINGS_PRESENT = "error_safety_findings_present"
    REPO_HEAD_DRIFT = "repo_head_drift"
    REPO_BRANCH_DRIFT = "repo_branch_drift"
    DIRTY_WORKTREE = "dirty_worktree"
    STAGED_FILES_PRESENT = "staged_files_present"


def guarded_write_plan(
    preview_path: str | Path,
    repo_path: str | Path,
) -> dict[str, Any]:
    """Return a read-only approval plan for a previously emitted edit-preview.

    The function validates that the supplied preview JSON is a suitable
    pre-write evidence artifact, compares the current target repo state against
    the snapshot stored in the preview, and emits the evidence/checklist that
    a human (or future F7-C write layer) would need before any file mutation.

    Args:
        preview_path: Path to an ``edit-preview`` JSON output file.
        repo_path: Path to the target repository root.

    Returns:
        A JSON-serializable approval plan. ``ok`` is ``True`` only when the
        plan can be presented for human approval; it is ``False`` when any
        blocker prevents safe approval.
    """
    preview_path_obj = Path(preview_path)
    repo_path_obj = Path(repo_path).resolve()

    warnings: set[str] = set()
    errors: set[str] = set()
    blocked_reasons: list[str] = []

    # ------------------------------------------------------------------
    # Load preview
    # ------------------------------------------------------------------
    preview: dict[str, Any] = {}
    if not preview_path_obj.exists() or not preview_path_obj.is_file():
        errors.add(_Reason.PREVIEW_MISSING)
        blocked_reasons.append(_Reason.PREVIEW_MISSING)
    else:
        try:
            raw = json.loads(preview_path_obj.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("preview root must be a JSON object")
            preview = raw
        except (json.JSONDecodeError, ValueError, OSError):
            errors.add(_Reason.INVALID_PREVIEW_JSON)
            blocked_reasons.append(_Reason.INVALID_PREVIEW_JSON)

    # ------------------------------------------------------------------
    # Collect current repo state
    # ------------------------------------------------------------------
    repo_state: dict[str, Any]
    state: dict[str, Any] = {}
    repo_ok = False
    if not repo_path_obj.exists() or not repo_path_obj.is_dir():
        errors.add(_Reason.REPO_MISSING)
        blocked_reasons.append(_Reason.REPO_MISSING)
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
            errors.add(_Reason.REPO_NOT_GIT)
            blocked_reasons.append(_Reason.REPO_NOT_GIT)
        else:
            repo_ok = True

    preview_command = str(preview.get("command", ""))
    if preview and preview_command != "edit.preview":
        errors.add(_Reason.INVALID_PREVIEW_COMMAND)
        blocked_reasons.append(_Reason.INVALID_PREVIEW_COMMAND)

    if (
        preview.get("read_only") is not True
        and _Reason.PREVIEW_NOT_READ_ONLY not in blocked_reasons
    ):
        errors.add(_Reason.PREVIEW_NOT_READ_ONLY)
        blocked_reasons.append(_Reason.PREVIEW_NOT_READ_ONLY)

    if preview.get("apply_supported") is True:
        errors.add(_Reason.PREVIEW_APPLY_SUPPORTED)
        blocked_reasons.append(_Reason.PREVIEW_APPLY_SUPPORTED)

    preview_next_gate = str(preview.get("next_gate", ""))
    if preview and preview_next_gate != "F7_guarded_write_required":
        errors.add(_Reason.PREVIEW_WRONG_NEXT_GATE)
        blocked_reasons.append(_Reason.PREVIEW_WRONG_NEXT_GATE)

    preview_ok = bool(preview.get("ok", False))
    preview_readiness = str(preview.get("readiness", "unknown"))
    if not preview_ok or preview_readiness == "blocked":
        errors.add(_Reason.SOURCE_PREVIEW_BLOCKED)
        blocked_reasons.append(_Reason.SOURCE_PREVIEW_BLOCKED)

    blocked_files = _as_string_list(preview.get("blocked_files"))
    if blocked_files:
        errors.add(_Reason.BLOCKED_FILES_PRESENT)
        blocked_reasons.append(_Reason.BLOCKED_FILES_PRESENT)

    if _has_error_finding(preview.get("safety_findings")):
        errors.add(_Reason.ERROR_SAFETY_FINDINGS_PRESENT)
        blocked_reasons.append(_Reason.ERROR_SAFETY_FINDINGS_PRESENT)

    # ------------------------------------------------------------------
    # Repo drift / cleanliness
    # ------------------------------------------------------------------
    preview_repo_state = preview.get("repo_state") or {}
    preview_head = preview_repo_state.get("head")
    preview_branch = preview_repo_state.get("branch")
    current_head = repo_state.get("head")
    current_branch = repo_state.get("branch")

    if (
        repo_ok
        and preview_head is not None
        and current_head is not None
        and preview_head != current_head
    ):
        errors.add(_Reason.REPO_HEAD_DRIFT)
        blocked_reasons.append(_Reason.REPO_HEAD_DRIFT)

    if (
        repo_ok
        and preview_branch is not None
        and current_branch is not None
        and preview_branch != current_branch
    ):
        errors.add(_Reason.REPO_BRANCH_DRIFT)
        blocked_reasons.append(_Reason.REPO_BRANCH_DRIFT)

    if repo_ok and not repo_state.get("worktree_clean", True):
        errors.add(_Reason.DIRTY_WORKTREE)
        blocked_reasons.append(_Reason.DIRTY_WORKTREE)

    if repo_ok and state.get("staged_files"):
        errors.add(_Reason.STAGED_FILES_PRESENT)
        blocked_reasons.append(_Reason.STAGED_FILES_PRESENT)

    # origin/main drift is a warning, not a hard blocker: the local HEAD may
    # still be the same snapshot the preview was generated against.
    preview_origin_main = preview_repo_state.get("origin_main")
    current_origin_main = repo_state.get("origin_main")
    if (
        repo_ok
        and preview_origin_main is not None
        and current_origin_main is not None
        and preview_origin_main != current_origin_main
    ):
        warnings.add("origin_main drift observed since preview snapshot")

    allowed_files = sorted(_as_string_list(preview.get("allowed_files")))

    has_errors = bool(errors)
    has_warnings = bool(warnings)
    if has_errors or not repo_ok:
        readiness = "blocked"
        ok = False
        approval_status = "blocked_before_approval"
    elif has_warnings:
        readiness = "warnings"
        ok = True
        approval_status = "required"
    else:
        readiness = "ready"
        ok = True
        approval_status = "required"

    return {
        "command": _COMMAND,
        "ok": ok,
        "read_only": _READ_ONLY,
        "writes_supported": _WRITES_SUPPORTED,
        "approval_required": _APPROVAL_REQUIRED,
        "approval_status": approval_status,
        "repo_root": str(repo_path_obj),
        "source_preview": str(preview_path_obj.resolve()),
        "repo_state": repo_state,
        "preview_summary": {
            "source_ok": preview_ok,
            "source_readiness": preview_readiness,
            "allowed_files_count": len(allowed_files),
            "blocked_files_count": len(blocked_files),
            "safety_findings_count": len(_as_dict_list(preview.get("safety_findings"))),
        },
        "required_evidence": sorted(_REQUIRED_EVIDENCE),
        "required_checks": sorted(_REQUIRED_CHECKS),
        "blocked_reasons": sorted(set(blocked_reasons)),
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


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _has_error_finding(findings: Any) -> bool:
    for finding in _as_dict_list(findings):
        if str(finding.get("severity", "")).lower() == "error":
            return True
    return False
