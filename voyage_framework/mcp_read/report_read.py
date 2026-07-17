"""Confined JSON report validation using only the hardened local Git reader."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.confinement import (
    check_root_containment,
    classify_sensitive_filename,
    redact_recursive,
    validate_report_id,
)
from voyage_framework.mcp_read.git_read import git_read_report_context


class ReportReadError(Exception):
    """Safe report validation failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def report_read_and_validate(
    report_id: str,
    project_root: Path,
    report_root: Path,
    limits: Limits | None = None,
) -> dict[str, object]:
    effective = limits or Limits()
    if not isinstance(report_id, str) or not validate_report_id(report_id):
        raise ReportReadError("invalid_report_id")
    if not report_id.lower().endswith(".json"):
        raise ReportReadError("report_format_not_supported")
    if classify_sensitive_filename(report_id) is not None:
        raise ReportReadError("secret_report_id_denied")
    project = _root(project_root, "project_root")
    reports = _root(report_root, "report_root")
    candidate = reports / report_id
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return {"status": "not_found", "report_id": report_id, "denied": False, "findings": []}
    except (OSError, RuntimeError) as exc:
        raise ReportReadError("report_path_error") from exc
    if not check_root_containment(resolved, reports) or not resolved.is_file():
        raise ReportReadError("report_path_denied")
    try:
        size = resolved.stat().st_size
        if size > effective.max_report_bytes:
            raise ReportReadError("report_too_large")
        with resolved.open("rb") as stream:
            raw = stream.read(effective.max_report_bytes + 1)
        if len(raw) > effective.max_report_bytes:
            raise ReportReadError("report_too_large")
        text = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReportReadError("report_encoding_invalid") from exc
    except OSError as exc:
        raise ReportReadError("report_read_error") from exc
    if "\x00" in text:
        raise ReportReadError("report_binary_content")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReportReadError("report_json_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "voyage.report.v1":
        raise ReportReadError("report_schema_invalid")
    repos = payload.get("repos")
    if not isinstance(repos, list) or not repos:
        raise ReportReadError("report_repositories_invalid")
    for claim in repos:
        if not isinstance(claim, dict) or not isinstance(claim.get("path"), str):
            raise ReportReadError("report_repository_invalid")
        _validate_claim_shape(claim)
        claimed_path = claim["path"]
        assert isinstance(claimed_path, str)
        lexical = Path(claimed_path)
        normalized = os.path.normcase(os.path.normpath(claimed_path))
        if ".." in lexical.parts or normalized != os.path.normcase(str(project)):
            raise ReportReadError("report_repository_denied")
        try:
            claimed = lexical.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ReportReadError("report_repository_denied") from exc
        if claimed != project:
            raise ReportReadError("report_repository_denied")

    git = git_read_report_context(project, effective)
    findings: list[dict[str, object]] = []
    for index, claim in enumerate(repos):
        name = str(claim.get("name") or f"repo-{index}")
        checks = (
            ("expected_branch", "local_branch"),
            ("expected_head", "local_head"),
            ("expected_origin_main", "local_origin_main_ref"),
            ("claimed_clean", "worktree_clean"),
            ("claimed_changed_files", "changed_files"),
            ("claimed_staged_files", "staged_files"),
        )
        for report_field, git_field in checks:
            if report_field not in claim or claim[report_field] is None:
                continue
            expected = _normalized(claim[report_field])
            actual = _normalized(git.get(git_field))
            matches = expected == actual
            findings.append(_finding(name, report_field, expected, actual, matches))
        for field in ("auto_commit_before", "auto_commit_after"):
            if claim.get(field):
                findings.append(
                    {
                        "type": "claim_unverifiable",
                        "field": field,
                        "expected": "present",
                        "actual": None,
                        "severity": "warning",
                        "report_provenance": name,
                        "git_provenance": str(project),
                        "message": f"{field} is not verified in Slice 2",
                    }
                )
    has_error = any(item["severity"] == "error" for item in findings)
    has_warning = any(item["severity"] == "warning" for item in findings)
    verdict = "C" if has_error else ("B" if has_warning else "A")
    git_warnings = git.get("warnings")
    warnings = [str(item) for item in git_warnings] if isinstance(git_warnings, list) else []
    result: dict[str, Any] = {
        "status": "conflict" if has_error else "validated",
        "report_id": report_id,
        "report_path": str(resolved),
        "report_schema": "voyage.report.v1",
        "validation_ok": not has_error,
        "recommended_verdict": verdict,
        "findings": findings,
        "report_size_bytes": size,
        "sources": [
            {"source_type": "external_report", "source_path": str(resolved)},
            {"source_type": "git_repository", "source_path": str(project)},
        ],
        "redactions": [],
        "warnings": warnings,
        "errors": [],
    }
    redacted = _redact_sensitive(redact_recursive(result))
    if not isinstance(redacted, dict):
        raise ReportReadError("report_result_invalid")
    redacted["redactions"] = _redaction_metadata(result, redacted)
    return redacted


def _root(path: Path, label: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ReportReadError(f"{label}_unavailable") from exc
    if not resolved.is_dir():
        raise ReportReadError(f"{label}_invalid")
    return resolved


def _normalized(value: object) -> object:
    if isinstance(value, list):
        return sorted(str(item).replace("\\", "/") for item in value)
    return value


def _validate_claim_shape(claim: dict[object, object]) -> None:
    for field in (
        "name",
        "path",
        "expected_branch",
        "expected_head",
        "expected_origin_main",
        "auto_commit_before",
        "auto_commit_after",
    ):
        value = claim.get(field)
        if value is not None and not isinstance(value, str):
            raise ReportReadError("report_repository_invalid")
    claimed_clean = claim.get("claimed_clean")
    if claimed_clean is not None and not isinstance(claimed_clean, bool):
        raise ReportReadError("report_repository_invalid")
    for field in ("claimed_changed_files", "claimed_staged_files"):
        value = claim.get(field, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ReportReadError("report_repository_invalid")


def _finding(
    name: str,
    field: str,
    expected: object,
    actual: object,
    matches: bool,
) -> dict[str, object]:
    return {
        "type": "claim_verified" if matches else "conflict",
        "field": field,
        "expected": expected,
        "actual": actual,
        "severity": "info" if matches else "error",
        "report_provenance": name,
        "git_provenance": "approved_project_root",
        "message": f"{field} {'matches' if matches else 'does not match'} local Git state",
    }


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_sensitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    if isinstance(value, str) and classify_sensitive_filename(Path(value).name) is not None:
        return "[REDACTED]"
    return value


def _redaction_metadata(original: Any, redacted: Any, path: str = "result") -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    if isinstance(original, dict) and isinstance(redacted, dict):
        for key, value in original.items():
            if key == "redactions" or key not in redacted:
                continue
            records.extend(_redaction_metadata(value, redacted[key], f"{path}.{key}"))
        return records
    if isinstance(original, list) and isinstance(redacted, list):
        for index, (left, right) in enumerate(zip(original, redacted, strict=False)):
            records.extend(_redaction_metadata(left, right, f"{path}[{index}]"))
        return records
    if original != redacted:
        classification = "sensitive_field"
        if isinstance(original, str) and classify_sensitive_filename(Path(original).name):
            classification = "potentially_sensitive_filename"
        records.append({"field": path, "classification": classification})
    return records
