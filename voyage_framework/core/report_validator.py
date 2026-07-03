"""Structured report trust validation against live Git state."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import (
    _git,
    _git_changed_files_in_commit,
    _git_changed_files_in_range,
    _git_commit_object_exists,
    _git_parent_commits,
    _git_status,
    _git_stdout,
)
from voyage_framework.core.forbidden_paths import (
    _matches_any,
    forbidden_patterns_for_role,
)

SUPPORTED_SCHEMA = "voyage.report.v1"
FULL_HASH_RE = re.compile(r"^[0-9a-f]{40}$")

UNVERIFIABLE_SAFETY_KEYS: frozenset[str] = frozenset(
    {
        "env_file_read",
        "claude_memory_modified",
        "claude_temp_tool_output_read",
        "bridge_executed",
        "auto_launch_executed",
        "controlled_launcher_executed",
        "secrets_printed",
        "no_verify_used",
        "git_reset_used",
        "git_clean_used",
    }
)


class ReportValidatorError(Exception):
    """Raised when a report cannot be loaded as a supported structured report."""


@dataclass(frozen=True)
class RepoClaim:
    name: str
    path: str
    expected_branch: str | None
    expected_head: str | None
    expected_origin_main: str | None
    claimed_clean: bool | None
    claimed_changed_files: list[str]
    claimed_staged_files: list[str]
    repo_role: str
    auto_commit_after: str | None
    auto_commit_before: str | None


@dataclass(frozen=True)
class ReportClaim:
    schema: str
    task_id: str
    timestamp: str | None
    repos: list[RepoClaim]
    safety: dict[str, bool]
    claimed_verdict: str

    @classmethod
    def from_file(cls, path: Path | str) -> ReportClaim:
        report_path = Path(path)
        try:
            raw = json.loads(report_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            raise ReportValidatorError(f"report file not found: {report_path}") from exc
        except json.JSONDecodeError as exc:
            raise ReportValidatorError(f"report file is not valid JSON: {exc}") from exc

        if not isinstance(raw, dict):
            raise ReportValidatorError("report root must be a JSON object")
        if raw.get("schema") != SUPPORTED_SCHEMA:
            raise ReportValidatorError(f"unsupported schema: {raw.get('schema')!r}")

        repos_raw = raw.get("repos")
        if not isinstance(repos_raw, list) or not repos_raw:
            raise ReportValidatorError("repos must be a non-empty list")

        repos = [_repo_claim(item, index) for index, item in enumerate(repos_raw)]
        safety_raw = raw.get("safety", {})
        if not isinstance(safety_raw, dict):
            raise ReportValidatorError("safety must be a JSON object")
        safety = {str(key): value for key, value in safety_raw.items() if isinstance(value, bool)}

        return cls(
            schema=str(raw["schema"]),
            task_id=str(raw.get("task_id", "")),
            timestamp=_optional_str(raw.get("timestamp")),
            repos=repos,
            safety=safety,
            claimed_verdict=str(raw.get("claimed_verdict", "")),
        )


@dataclass(frozen=True)
class ValidationMismatch:
    repo: str
    check: str
    claimed: str
    actual: str
    severity: str


@dataclass(frozen=True)
class ReportValidationResult:
    ok: bool
    task_id: str
    repos_checked: list[str]
    mismatches: list[ValidationMismatch]
    warnings: list[str]
    unverifiable_safety_claims: list[str]
    verdict_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "task_id": self.task_id,
            "repos_checked": self.repos_checked,
            "mismatches": [mismatch.__dict__ for mismatch in self.mismatches],
            "warnings": self.warnings,
            "unverifiable_safety_claims": self.unverifiable_safety_claims,
            "verdict_recommendation": self.verdict_recommendation,
        }


def validate_report(report_path: Path | str) -> ReportValidationResult:
    claim = ReportClaim.from_file(report_path)
    mismatches: list[ValidationMismatch] = []
    warnings: list[str] = []
    repos_checked: list[str] = []

    for repo in claim.repos:
        repos_checked.append(repo.name)
        _validate_repo(repo, mismatches, warnings)

    unverifiable = sorted(key for key in claim.safety if key in UNVERIFIABLE_SAFETY_KEYS)
    verdict = _recommend_verdict(mismatches, warnings)
    if claim.claimed_verdict and claim.claimed_verdict != verdict:
        warnings.append(
            f"claimed verdict {claim.claimed_verdict!r} differs from recommendation {verdict!r}"
        )
        verdict = _recommend_verdict(mismatches, warnings)

    return ReportValidationResult(
        ok=not any(mismatch.severity == "error" for mismatch in mismatches),
        task_id=claim.task_id,
        repos_checked=repos_checked,
        mismatches=mismatches,
        warnings=warnings,
        unverifiable_safety_claims=unverifiable,
        verdict_recommendation=verdict,
    )


def _validate_repo(
    repo: RepoClaim,
    mismatches: list[ValidationMismatch],
    warnings: list[str],
) -> None:
    path = Path(repo.path)
    if not path.exists() or not path.is_dir():
        mismatches.append(
            ValidationMismatch(repo.name, "repo_exists", repo.path, "missing", "error")
        )
        return

    branch = _git_stdout(path, "branch", "--show-current")
    head = _git_stdout(path, "rev-parse", "HEAD")
    origin_main = _git_stdout(path, "rev-parse", "origin/main")
    status_lines = _git_status(path)
    actual_dirty = sorted({_status_path(line) for line in status_lines})
    actual_changed = sorted(
        {
            *_git_name_only(path, "diff", "--name-only"),
            *_untracked_files(status_lines),
        }
    )
    actual_staged = sorted(_git_name_only(path, "diff", "--cached", "--name-only"))

    if repo.expected_branch is not None and repo.expected_branch != branch:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "branch",
                repo.expected_branch,
                branch,
                "error",
            )
        )

    _validate_hash_claim(repo, "head", repo.expected_head, head, path, mismatches)
    _validate_hash_claim(
        repo,
        "origin_main",
        repo.expected_origin_main,
        origin_main,
        path,
        mismatches,
    )

    if repo.claimed_clean is True and status_lines:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "clean",
                "true",
                f"{len(status_lines)} dirty path(s)",
                "error",
            )
        )
    elif repo.claimed_clean is False and not status_lines:
        warnings.append(f"{repo.name}: claimed clean=false but actual worktree is clean")
    elif repo.claimed_clean is None:
        warnings.append(f"{repo.name}: missing clean claim")

    auto_commit_enabled = repo.auto_commit_after is not None and repo.auto_commit_after != ""

    if auto_commit_enabled:
        _validate_auto_commit(
            repo,
            path,
            head,
            actual_dirty,
            actual_staged,
            mismatches,
            warnings,
        )
    else:
        _compare_file_sets(
            repo,
            "changed_files",
            repo.claimed_changed_files,
            actual_changed,
            mismatches,
            warnings,
        )

    _compare_file_sets(
        repo,
        "staged_files",
        repo.claimed_staged_files,
        actual_staged,
        mismatches,
        warnings,
    )

    if repo.claimed_clean is True and actual_staged:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "staged_when_clean_claimed",
                "none",
                ", ".join(actual_staged),
                "error",
            )
        )

    forbidden = forbidden_patterns_for_role(repo.repo_role)
    forbidden_sources = [
        ("claimed_changed_files", repo.claimed_changed_files),
        ("actual_dirty_files", actual_dirty),
    ]
    if auto_commit_enabled:
        actual_auto_commit_files = _auto_commit_changed_files(repo, path)
        forbidden_sources.append(("auto_commit_changed_files", actual_auto_commit_files))

    for source, paths in forbidden_sources:
        hits = sorted(path for path in paths if _matches_any(path, forbidden))
        if hits:
            mismatches.append(
                ValidationMismatch(
                    repo.name,
                    f"forbidden_paths:{source}",
                    "none",
                    ", ".join(hits),
                    "error",
                )
            )


def _validate_hash_claim(
    repo: RepoClaim,
    check: str,
    claimed: str | None,
    actual: str,
    path: Path,
    mismatches: list[ValidationMismatch],
) -> None:
    if claimed is None:
        return
    if not FULL_HASH_RE.fullmatch(claimed):
        mismatches.append(
            ValidationMismatch(repo.name, f"{check}_hash_format", claimed, actual, "error")
        )
        return
    object_type = _git(path, "cat-file", "-t", claimed)
    if object_type.returncode != 0:
        mismatches.append(
            ValidationMismatch(repo.name, f"{check}_object_exists", claimed, "unknown", "error")
        )
        return
    if actual != claimed:
        mismatches.append(ValidationMismatch(repo.name, check, claimed, actual, "error"))


def _auto_commit_changed_files(repo: RepoClaim, path: Path) -> list[str]:
    """Return actual changed files for the configured auto_commit range/commit."""
    if repo.auto_commit_before is not None and repo.auto_commit_before != "":
        return _git_changed_files_in_range(
            path, repo.auto_commit_before, repo.auto_commit_after or ""
        )
    return _git_changed_files_in_commit(path, repo.auto_commit_after or "")


def _validate_auto_commit(
    repo: RepoClaim,
    path: Path,
    head: str,
    actual_dirty: list[str],
    actual_staged: list[str],
    mismatches: list[ValidationMismatch],
    warnings: list[str],
) -> None:
    """Validate post-commit auto_commit claims.

    Assumes repo.auto_commit_after is present and non-empty.
    """
    after = repo.auto_commit_after or ""
    before = repo.auto_commit_before or None

    if not FULL_HASH_RE.fullmatch(after):
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_after_hash_format",
                after,
                head,
                "error",
            )
        )
        return

    if before is not None and not FULL_HASH_RE.fullmatch(before):
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_before_hash_format",
                before,
                head,
                "error",
            )
        )
        return

    if not _git_commit_object_exists(path, after):
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_after_object_exists",
                after,
                "unknown",
                "error",
            )
        )
        return

    if before is not None and not _git_commit_object_exists(path, before):
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_before_object_exists",
                before,
                "unknown",
                "error",
            )
        )
        return

    if after != head:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_after_equals_head",
                after,
                head,
                "error",
            )
        )

    if before is None:
        parents = _git_parent_commits(path, after)
        if len(parents) > 1:
            warnings.append(
                f"{repo.name}: auto_commit_after is a merge commit without explicit "
                "auto_commit_before; using single-commit diff-tree against first parent"
            )

    actual_auto_commit_files = _auto_commit_changed_files(repo, path)

    _compare_file_sets(
        repo,
        "auto_commit_changed_files",
        repo.claimed_changed_files,
        actual_auto_commit_files,
        mismatches,
        warnings,
    )

    if actual_staged:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                "auto_commit_staged_files",
                "none",
                ", ".join(actual_staged),
                "error",
            )
        )

    if repo.claimed_clean is False and actual_dirty:
        warnings.append(f"{repo.name}: post-commit report claims clean=false with dirty worktree")
    elif repo.claimed_clean is False and not actual_dirty:
        warnings.append(f"{repo.name}: post-commit report claims clean=false but worktree is clean")


def _compare_file_sets(
    repo: RepoClaim,
    check: str,
    claimed: list[str],
    actual: list[str],
    mismatches: list[ValidationMismatch],
    warnings: list[str],
) -> None:
    claimed_set = set(claimed)
    actual_set = set(actual)
    missing_claims = sorted(actual_set - claimed_set)
    stale_claims = sorted(claimed_set - actual_set)
    if missing_claims:
        mismatches.append(
            ValidationMismatch(
                repo.name,
                check,
                ", ".join(claimed),
                ", ".join(actual),
                "error",
            )
        )
    for path in stale_claims:
        warnings.append(f"{repo.name}: claimed {check} entry is not currently dirty: {path}")


def _repo_claim(raw: object, index: int) -> RepoClaim:
    if not isinstance(raw, dict):
        raise ReportValidatorError(f"repos[{index}] must be a JSON object")
    name = str(raw.get("name") or f"repo-{index}")
    repo_path = raw.get("path")
    if not isinstance(repo_path, str) or not repo_path:
        raise ReportValidatorError(f"{name}: path must be a non-empty string")
    return RepoClaim(
        name=name,
        path=repo_path,
        expected_branch=_optional_str(raw.get("expected_branch")),
        expected_head=_optional_str(raw.get("expected_head")),
        expected_origin_main=_optional_str(raw.get("expected_origin_main")),
        claimed_clean=_optional_bool(raw.get("claimed_clean")),
        claimed_changed_files=_string_list(raw.get("claimed_changed_files", []), name),
        claimed_staged_files=_string_list(raw.get("claimed_staged_files", []), name),
        repo_role=str(raw.get("repo_role", "generic")),
        auto_commit_after=_optional_str(raw.get("auto_commit_after")),
        auto_commit_before=_optional_str(raw.get("auto_commit_before")),
    )


def _string_list(value: object, repo_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ReportValidatorError(f"{repo_name}: file claims must be string lists")
    return sorted({_normalize_repo_path(item) for item in value})


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ReportValidatorError("claimed_clean must be a boolean or null")
    return value


def _git_name_only(repo: Path, *args: str) -> list[str]:
    result = _git(repo, *args)
    if result.returncode != 0:
        return []
    return sorted(_normalize_repo_path(line) for line in result.stdout.splitlines() if line.strip())


def _untracked_files(status_lines: list[str]) -> list[str]:
    return [_status_path(line) for line in status_lines if line.startswith("?? ")]


def _status_path(line: str) -> str:
    path = line[3:] if len(line) > 3 else line
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return _normalize_repo_path(path.strip().strip('"'))


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _recommend_verdict(
    mismatches: list[ValidationMismatch],
    warnings: list[str],
) -> str:
    if any(mismatch.severity == "error" for mismatch in mismatches):
        return "C"
    if warnings:
        return "B"
    return "A"
