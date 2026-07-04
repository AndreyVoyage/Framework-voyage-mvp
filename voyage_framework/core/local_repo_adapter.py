"""Generic local Git repo adapter implementing RepoControlAdapter.

Read-only. Works against any local Git repository. Does not depend on any
product-specific schema or runtime. Uses existing generic git-state helpers
and the forbidden-path policy registry.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from voyage_framework.core._git_utils import collect_repo_state
from voyage_framework.core.forbidden_paths import (
    _matches_any,
    forbidden_patterns_for_role,
)
from voyage_framework.core.repo_control_adapter import (
    RepoAuditResult,
    RepoControlAdapter,
    RepoPreviewResult,
    RepoStatusResult,
    RepoValidationResult,
)

_SAMPLE_SIZE = 20


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _tracked_files(repo: Path) -> list[str]:
    """Return normalized tracked file paths using a read-only git command."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return []
    return sorted(_normalize_path(line) for line in result.stdout.splitlines() if line.strip())


class LocalRepoControlAdapter(RepoControlAdapter):
    """Second concrete RepoControlAdapter: generic local Git repo.

    Treats ``spec_path`` as the local repository root. All operations are
    read-only and use existing generic helpers.
    """

    def status(self, spec_path: str | Path) -> RepoStatusResult:
        repo = Path(spec_path).resolve()
        state = collect_repo_state(repo)

        issues: list[str] = []
        issues.extend(str(w) for w in state.get("warnings", []))
        issues.extend(str(e) for e in state.get("errors", []))

        branch = state.get("branch")
        worktree_clean = state.get("worktree_clean")
        summary_parts: list[str] = []
        if branch:
            summary_parts.append(f"branch {branch}")
        if worktree_clean is not None:
            summary_parts.append("clean" if worktree_clean else "dirty")
        summary = ", ".join(summary_parts) if summary_parts else None

        return RepoStatusResult(
            command="repo.status",
            ok=bool(state.get("ok")),
            adapter="local",
            repo_path=str(repo),
            summary=summary,
            issues=tuple(issues),
            details=state,
        )

    def validate(self, spec_path: str | Path, target: str | None = None) -> RepoValidationResult:
        repo = Path(spec_path).resolve()
        state = collect_repo_state(repo)
        issues: list[str] = []
        issues.extend(str(e) for e in state.get("errors", []))

        if target is not None:
            target_path = (repo / target).resolve()
            try:
                target_path.relative_to(repo)
            except ValueError:
                issues.append(f"target resolves outside repo: {target}")
            else:
                if not target_path.exists():
                    issues.append(f"target not found: {target}")

        ok = bool(state.get("ok")) and not issues
        details: dict[str, Any] = {
            "repo_path": str(repo),
            "is_git_repo": state.get("ok") is True,
        }
        if target is not None:
            details["target"] = target

        return RepoValidationResult(
            command="repo.validate",
            ok=ok,
            adapter="local",
            target=target,
            issues=tuple(issues),
            details=details,
        )

    def audit(
        self,
        spec_path: str | Path,
        target: str | None = None,
        **options: object,
    ) -> RepoAuditResult:
        repo = Path(spec_path).resolve()
        state = collect_repo_state(repo)
        issues: list[str] = []
        warnings: list[str] = []
        issues.extend(str(e) for e in state.get("errors", []))
        warnings.extend(str(w) for w in state.get("warnings", []))

        tracked = _tracked_files(repo) if state.get("ok") else []
        tracked_sample = tracked[:_SAMPLE_SIZE]

        forbidden_patterns = forbidden_patterns_for_role("generic")
        forbidden_matches: list[str] = []
        for rel_path in tracked:
            if _matches_any(rel_path, forbidden_patterns):
                forbidden_matches.append(rel_path)
        if forbidden_matches:
            warnings.append(f"tracked files match generic forbidden patterns: {forbidden_matches}")

        details: dict[str, Any] = {
            "repo_path": str(repo),
            "tracked_file_count": len(tracked),
            "sample_tracked_files": tracked_sample,
            "changed_file_count": len(state.get("changed_files", [])),
            "staged_file_count": len(state.get("staged_files", [])),
            "untracked_file_count": len(state.get("untracked_files", [])),
            "forbidden_matches": forbidden_matches,
        }
        if target is not None:
            details["target"] = target
        if options:
            details["options"] = dict(options)

        ok = bool(state.get("ok"))
        return RepoAuditResult(
            command="repo.audit",
            ok=ok,
            adapter="local",
            target=target,
            issues=tuple(issues) if issues else tuple(warnings),
            details=details,
        )

    def preview(self, spec_path: str | Path) -> RepoPreviewResult:
        repo = Path(spec_path).resolve()
        state = collect_repo_state(repo)
        issues: list[str] = []
        issues.extend(str(e) for e in state.get("errors", []))

        return RepoPreviewResult(
            command="repo.preview",
            ok=bool(state.get("ok")),
            adapter="local",
            summary="read-only plan; no mutations",
            actions=(
                "repo.status",
                "repo.validate",
                "repo.audit",
                "repo.preview",
            ),
            issues=tuple(issues),
            details={
                "repo_path": str(repo),
                "read_only": True,
            },
        )
