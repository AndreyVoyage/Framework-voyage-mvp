"""Generic guarded-write approval artifact verifier.

Consumes an F6 ``edit-preview`` JSON output and an external human approval
artifact JSON, then verifies that the approval is valid, bound to the preview,
and bound to the current target repository state.

This module never writes files, generates patches, applies changes, stages
files, or commits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import collect_repo_state

_COMMAND = "guarded_write.approval_verify"
_READ_ONLY = True
_WRITES_SUPPORTED = False
_APPROVAL_REQUIRED = True
_NEXT_GATE = "F7_structured_write_required"
_APPROVAL_SCHEMA_VERSION = "voyage.guarded_write.approval.v1"

_REQUIRED_EVIDENCE = (
    "source edit-preview JSON file",
    "source approval artifact JSON file",
    "approval identity (approved_by)",
    "approval reason",
    "approval timestamp (approved_at)",
    "repo_state snapshot matching approval.bound_repo",
    "allowed files bound to approval",
    "blocked file list empty",
    "clean worktree (no unstaged/staged/untracked changes)",
    "rollback/checkpoint plan",
    "post-write validation plan",
    "validate-report plan for after writes",
)

_REQUIRED_CHECKS = (
    "verify edit-preview ok=true",
    "verify edit-preview readiness is ready or warnings",
    "verify edit-preview command/read_only/apply_supported/next_gate",
    "verify no blocked files in preview",
    "verify no error safety_findings in preview",
    "verify approval schema_version",
    "verify approval.approved=true",
    "verify approved_by non-empty",
    "verify approved_at non-empty",
    "verify reason non-empty",
    "verify approval.bound_repo matches current repo",
    "verify approval.bound_repo matches preview.repo_state",
    "verify approval.bound_allowed_files match preview.allowed_files",
    "verify approval.bound_blocked_files empty",
    "verify checkpoint.rollback_plan present",
    "verify checkpoint.head matches approval.bound_repo.head",
    "verify post_write_validation non-empty",
    "verify evidence_acknowledged non-empty",
    "verify repo worktree clean and no staged files",
)


class _Reason:
    PREVIEW_MISSING = "preview_missing"
    INVALID_PREVIEW_JSON = "invalid_preview_json"
    APPROVAL_MISSING = "approval_missing"
    INVALID_APPROVAL_JSON = "invalid_approval_json"
    REPO_MISSING = "repo_missing"
    REPO_NOT_GIT = "repo_not_git"
    DIRTY_WORKTREE = "dirty_worktree"
    STAGED_FILES_PRESENT = "staged_files_present"
    INVALID_PREVIEW_COMMAND = "invalid_preview_command"
    PREVIEW_NOT_READ_ONLY = "preview_not_read_only"
    PREVIEW_APPLY_SUPPORTED = "preview_apply_supported"
    PREVIEW_WRONG_NEXT_GATE = "preview_wrong_next_gate"
    SOURCE_PREVIEW_BLOCKED = "source_preview_blocked"
    BLOCKED_FILES_PRESENT = "blocked_files_present"
    ERROR_SAFETY_FINDINGS_PRESENT = "error_safety_findings_present"
    APPROVAL_SCHEMA_INVALID = "approval_schema_invalid"
    APPROVAL_NOT_TRUE = "approval_not_true"
    APPROVAL_IDENTITY_MISSING = "approval_identity_missing"
    APPROVAL_TIMESTAMP_MISSING = "approval_timestamp_missing"
    APPROVAL_REASON_MISSING = "approval_reason_missing"
    APPROVAL_BOUND_REPO_MISSING = "approval_bound_repo_missing"
    APPROVAL_BOUND_PREVIEW_MISSING = "approval_bound_preview_missing"
    APPROVAL_HEAD_MISMATCH = "approval_head_mismatch"
    APPROVAL_BRANCH_MISMATCH = "approval_branch_mismatch"
    APPROVAL_PREVIEW_HEAD_MISMATCH = "approval_preview_head_mismatch"
    APPROVAL_PREVIEW_BRANCH_MISMATCH = "approval_preview_branch_mismatch"
    APPROVAL_ALLOWED_FILES_MISMATCH = "approval_allowed_files_mismatch"
    APPROVAL_BLOCKED_FILES_NOT_EMPTY = "approval_blocked_files_not_empty"
    CHECKPOINT_MISSING = "checkpoint_missing"
    ROLLBACK_PLAN_MISSING = "rollback_plan_missing"
    CHECKPOINT_HEAD_MISMATCH = "checkpoint_head_mismatch"
    POST_WRITE_VALIDATION_MISSING = "post_write_validation_missing"
    EVIDENCE_ACKNOWLEDGEMENT_MISSING = "evidence_acknowledgement_missing"


def guarded_write_approval_verify(
    preview_path: str | Path,
    approval_path: str | Path,
    repo_path: str | Path,
) -> dict[str, Any]:
    """Verify a human approval artifact against an edit-preview and repo state.

    The function validates that the supplied approval JSON is structurally
    valid, that it binds to the supplied preview, and that the current target
    repository state still matches the snapshot the human approved. It never
    modifies the repository.

    Args:
        preview_path: Path to an ``edit-preview`` JSON output file.
        approval_path: Path to an external approval artifact JSON file.
        repo_path: Path to the target repository root.

    Returns:
        A JSON-serializable verification report. ``ok`` is ``True`` only when
        the approval is valid and all bindings match.
    """
    preview_path_obj = Path(preview_path)
    approval_path_obj = Path(approval_path)
    repo_path_obj = Path(repo_path).resolve()

    warnings: set[str] = set()
    errors: set[str] = set()
    approval_errors: set[str] = set()
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
    # Load approval
    # ------------------------------------------------------------------
    approval: dict[str, Any] = {}
    if not approval_path_obj.exists() or not approval_path_obj.is_file():
        approval_errors.add(_Reason.APPROVAL_MISSING)
        errors.add(_Reason.APPROVAL_MISSING)
        blocked_reasons.append(_Reason.APPROVAL_MISSING)
    else:
        try:
            raw = json.loads(approval_path_obj.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("approval root must be a JSON object")
            approval = raw
        except (json.JSONDecodeError, ValueError, OSError):
            approval_errors.add(_Reason.INVALID_APPROVAL_JSON)
            errors.add(_Reason.INVALID_APPROVAL_JSON)
            blocked_reasons.append(_Reason.INVALID_APPROVAL_JSON)

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

    # ------------------------------------------------------------------
    # Validate preview semantics
    # ------------------------------------------------------------------
    preview_command = str(preview.get("command", ""))
    if preview and preview_command != "edit.preview":
        errors.add(_Reason.INVALID_PREVIEW_COMMAND)
        blocked_reasons.append(_Reason.INVALID_PREVIEW_COMMAND)

    if preview.get("read_only") is not True:
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

    preview_blocked_files = _as_string_list(preview.get("blocked_files"))
    if preview_blocked_files:
        errors.add(_Reason.BLOCKED_FILES_PRESENT)
        blocked_reasons.append(_Reason.BLOCKED_FILES_PRESENT)

    if _has_error_finding(preview.get("safety_findings")):
        errors.add(_Reason.ERROR_SAFETY_FINDINGS_PRESENT)
        blocked_reasons.append(_Reason.ERROR_SAFETY_FINDINGS_PRESENT)

    # ------------------------------------------------------------------
    # Validate approval artifact structure
    # ------------------------------------------------------------------
    if approval:
        if str(approval.get("schema_version", "")) != _APPROVAL_SCHEMA_VERSION:
            approval_errors.add(_Reason.APPROVAL_SCHEMA_INVALID)
            errors.add(_Reason.APPROVAL_SCHEMA_INVALID)
            blocked_reasons.append(_Reason.APPROVAL_SCHEMA_INVALID)

        if approval.get("approved") is not True:
            approval_errors.add(_Reason.APPROVAL_NOT_TRUE)
            errors.add(_Reason.APPROVAL_NOT_TRUE)
            blocked_reasons.append(_Reason.APPROVAL_NOT_TRUE)

        if not _non_empty_str(approval.get("approved_by")):
            approval_errors.add(_Reason.APPROVAL_IDENTITY_MISSING)
            errors.add(_Reason.APPROVAL_IDENTITY_MISSING)
            blocked_reasons.append(_Reason.APPROVAL_IDENTITY_MISSING)

        if not _non_empty_str(approval.get("approved_at")):
            approval_errors.add(_Reason.APPROVAL_TIMESTAMP_MISSING)
            errors.add(_Reason.APPROVAL_TIMESTAMP_MISSING)
            blocked_reasons.append(_Reason.APPROVAL_TIMESTAMP_MISSING)

        if not _non_empty_str(approval.get("reason")):
            approval_errors.add(_Reason.APPROVAL_REASON_MISSING)
            errors.add(_Reason.APPROVAL_REASON_MISSING)
            blocked_reasons.append(_Reason.APPROVAL_REASON_MISSING)

        bound_repo = approval.get("bound_repo")
        if not isinstance(bound_repo, dict):
            approval_errors.add(_Reason.APPROVAL_BOUND_REPO_MISSING)
            errors.add(_Reason.APPROVAL_BOUND_REPO_MISSING)
            blocked_reasons.append(_Reason.APPROVAL_BOUND_REPO_MISSING)
            bound_repo = {}

        bound_preview = approval.get("bound_preview")
        if not isinstance(bound_preview, dict):
            approval_errors.add(_Reason.APPROVAL_BOUND_PREVIEW_MISSING)
            errors.add(_Reason.APPROVAL_BOUND_PREVIEW_MISSING)
            blocked_reasons.append(_Reason.APPROVAL_BOUND_PREVIEW_MISSING)

        if not _non_empty_list(approval.get("post_write_validation")):
            approval_errors.add(_Reason.POST_WRITE_VALIDATION_MISSING)
            errors.add(_Reason.POST_WRITE_VALIDATION_MISSING)
            blocked_reasons.append(_Reason.POST_WRITE_VALIDATION_MISSING)

        if not _non_empty_list(approval.get("evidence_acknowledged")):
            approval_errors.add(_Reason.EVIDENCE_ACKNOWLEDGEMENT_MISSING)
            errors.add(_Reason.EVIDENCE_ACKNOWLEDGEMENT_MISSING)
            blocked_reasons.append(_Reason.EVIDENCE_ACKNOWLEDGEMENT_MISSING)

        # ------------------------------------------------------------------
        # Validate approval-to-current-repo binding
        # ------------------------------------------------------------------
        approval_head = bound_repo.get("head") if isinstance(bound_repo, dict) else None
        approval_branch = bound_repo.get("branch") if isinstance(bound_repo, dict) else None
        current_head = repo_state.get("head")
        current_branch = repo_state.get("branch")

        if (
            repo_ok
            and approval_head is not None
            and current_head is not None
            and approval_head != current_head
        ):
            approval_errors.add(_Reason.APPROVAL_HEAD_MISMATCH)
            errors.add(_Reason.APPROVAL_HEAD_MISMATCH)
            blocked_reasons.append(_Reason.APPROVAL_HEAD_MISMATCH)

        if (
            repo_ok
            and approval_branch is not None
            and current_branch is not None
            and approval_branch != current_branch
        ):
            approval_errors.add(_Reason.APPROVAL_BRANCH_MISMATCH)
            errors.add(_Reason.APPROVAL_BRANCH_MISMATCH)
            blocked_reasons.append(_Reason.APPROVAL_BRANCH_MISMATCH)

        # ------------------------------------------------------------------
        # Validate approval-to-preview binding
        # ------------------------------------------------------------------
        preview_repo_state = preview.get("repo_state") or {}
        preview_head = preview_repo_state.get("head")
        preview_branch = preview_repo_state.get("branch")

        if approval_head is not None and preview_head is not None and approval_head != preview_head:
            approval_errors.add(_Reason.APPROVAL_PREVIEW_HEAD_MISMATCH)
            errors.add(_Reason.APPROVAL_PREVIEW_HEAD_MISMATCH)
            blocked_reasons.append(_Reason.APPROVAL_PREVIEW_HEAD_MISMATCH)

        if (
            approval_branch is not None
            and preview_branch is not None
            and approval_branch != preview_branch
        ):
            approval_errors.add(_Reason.APPROVAL_PREVIEW_BRANCH_MISMATCH)
            errors.add(_Reason.APPROVAL_PREVIEW_BRANCH_MISMATCH)
            blocked_reasons.append(_Reason.APPROVAL_PREVIEW_BRANCH_MISMATCH)

        # ------------------------------------------------------------------
        # Validate allowed/blocked file binding
        # ------------------------------------------------------------------
        approval_allowed = sorted(
            {_normalize_path(p) for p in _as_string_list(approval.get("bound_allowed_files"))}
        )
        approval_blocked = _as_string_list(approval.get("bound_blocked_files"))
        preview_allowed = sorted(
            {_normalize_path(p) for p in _as_string_list(preview.get("allowed_files"))}
        )

        if approval_allowed != preview_allowed:
            approval_errors.add(_Reason.APPROVAL_ALLOWED_FILES_MISMATCH)
            errors.add(_Reason.APPROVAL_ALLOWED_FILES_MISMATCH)
            blocked_reasons.append(_Reason.APPROVAL_ALLOWED_FILES_MISMATCH)

        if approval_blocked:
            approval_errors.add(_Reason.APPROVAL_BLOCKED_FILES_NOT_EMPTY)
            errors.add(_Reason.APPROVAL_BLOCKED_FILES_NOT_EMPTY)
            blocked_reasons.append(_Reason.APPROVAL_BLOCKED_FILES_NOT_EMPTY)

        # ------------------------------------------------------------------
        # Validate checkpoint / rollback plan
        # ------------------------------------------------------------------
        checkpoint = approval.get("checkpoint")
        if not isinstance(checkpoint, dict):
            approval_errors.add(_Reason.CHECKPOINT_MISSING)
            errors.add(_Reason.CHECKPOINT_MISSING)
            blocked_reasons.append(_Reason.CHECKPOINT_MISSING)
        else:
            if not _non_empty_str(checkpoint.get("rollback_plan")):
                approval_errors.add(_Reason.ROLLBACK_PLAN_MISSING)
                errors.add(_Reason.ROLLBACK_PLAN_MISSING)
                blocked_reasons.append(_Reason.ROLLBACK_PLAN_MISSING)
            checkpoint_head = checkpoint.get("head")
            if (
                approval_head is not None
                and checkpoint_head is not None
                and checkpoint_head != approval_head
            ):
                approval_errors.add(_Reason.CHECKPOINT_HEAD_MISMATCH)
                errors.add(_Reason.CHECKPOINT_HEAD_MISMATCH)
                blocked_reasons.append(_Reason.CHECKPOINT_HEAD_MISMATCH)

    # ------------------------------------------------------------------
    # Repo cleanliness
    # ------------------------------------------------------------------
    if repo_ok and not repo_state.get("worktree_clean", True):
        errors.add(_Reason.DIRTY_WORKTREE)
        blocked_reasons.append(_Reason.DIRTY_WORKTREE)

    if repo_ok and state.get("staged_files"):
        errors.add(_Reason.STAGED_FILES_PRESENT)
        blocked_reasons.append(_Reason.STAGED_FILES_PRESENT)

    # origin/main drift is a warning, not a hard blocker.
    preview_origin_main = (preview.get("repo_state") or {}).get("origin_main")
    approval_origin_main = (approval.get("bound_repo") or {}).get("origin_main")
    current_origin_main = repo_state.get("origin_main")
    if repo_ok and current_origin_main is not None:
        if preview_origin_main is not None and preview_origin_main != current_origin_main:
            warnings.add("origin_main drift observed between preview and current repo")
        if approval_origin_main is not None and approval_origin_main != current_origin_main:
            warnings.add("origin_main drift observed between approval and current repo")

    allowed_files = sorted(
        {_normalize_path(p) for p in _as_string_list(preview.get("allowed_files"))}
    )

    has_errors = bool(errors)
    has_warnings = bool(warnings)
    if has_errors or not repo_ok:
        readiness = "blocked"
        ok = False
    elif has_warnings:
        readiness = "warnings"
        ok = True
    else:
        readiness = "ready"
        ok = True

    approval_valid = ok

    return {
        "command": _COMMAND,
        "ok": ok,
        "read_only": _READ_ONLY,
        "writes_supported": _WRITES_SUPPORTED,
        "approval_required": _APPROVAL_REQUIRED,
        "approval_valid": approval_valid,
        "repo_root": str(repo_path_obj),
        "source_preview": str(preview_path_obj.resolve()),
        "approval_artifact": str(approval_path_obj.resolve()),
        "repo_state": repo_state,
        "preview_summary": {
            "source_ok": preview_ok,
            "source_readiness": preview_readiness,
            "allowed_files_count": len(allowed_files),
            "blocked_files_count": len(preview_blocked_files),
            "safety_findings_count": len(_as_dict_list(preview.get("safety_findings"))),
        },
        "approval_summary": _approval_summary(approval),
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


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _has_error_finding(findings: Any) -> bool:
    for finding in _as_dict_list(findings):
        if str(finding.get("severity", "")).lower() == "error":
            return True
    return False


def _approval_summary(approval: dict[str, Any]) -> dict[str, Any]:
    if not approval:
        return {
            "schema_version": None,
            "approved": None,
            "approved_by": None,
            "approved_at": None,
            "reason_present": False,
            "bound_branch": None,
            "bound_head": None,
            "bound_allowed_files_count": 0,
            "rollback_plan_present": False,
            "post_write_validation_count": 0,
        }

    bound_repo = approval.get("bound_repo") or {}
    checkpoint = approval.get("checkpoint") or {}
    approved_value = approval.get("approved")
    approved_bool = bool(approved_value) if isinstance(approved_value, bool) else None
    approved_by = approval.get("approved_by")
    approved_at = approval.get("approved_at")
    bound_branch = bound_repo.get("branch") if isinstance(bound_repo, dict) else None
    bound_head = bound_repo.get("head") if isinstance(bound_repo, dict) else None
    rollback_present = (
        _non_empty_str(checkpoint.get("rollback_plan")) if isinstance(checkpoint, dict) else False
    )
    allowed_count = len(
        {_normalize_path(p) for p in _as_string_list(approval.get("bound_allowed_files"))}
    )
    return {
        "schema_version": str(approval.get("schema_version", "")),
        "approved": approved_bool,
        "approved_by": approved_by if _non_empty_str(approved_by) else None,
        "approved_at": approved_at if _non_empty_str(approved_at) else None,
        "reason_present": _non_empty_str(approval.get("reason")),
        "bound_branch": bound_branch,
        "bound_head": bound_head,
        "bound_allowed_files_count": allowed_count,
        "rollback_plan_present": rollback_present,
        "post_write_validation_count": len(_as_string_list(approval.get("post_write_validation"))),
    }
