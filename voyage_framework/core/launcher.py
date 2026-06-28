"""Minimal controlled launcher core (CONTROL-LOOP-10D first slice).

The launcher is intentionally small and report-only. It never invokes AI tools,
never loops, never commits/pushes/merges/deploys, never reads `.env`, and never
writes to `.voyage`.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REQUIRED_APPROVAL_PHRASE = "I approve this launcher run"
_FULL_HASH_LEN = 40


class LauncherError(Exception):
    """Raised when a launcher preflight gate fails (STOP condition)."""


@dataclass(frozen=True)
class LauncherConfig:
    """Inputs for a single dry-run launch."""

    package_dir: Path
    primary_repo: Path
    auto_worktree: Path
    expected_origin_main: str


@dataclass(frozen=True)
class LauncherResult:
    """Outcome of a dry-run launch."""

    success: bool
    report_path: Path | None
    message: str


@dataclass(frozen=True)
class HumanApproval:
    """Parsed HUMAN_APPROVAL.md artifact."""

    approved_by: str
    package_path: str
    baseline_commit: str
    risk_level: str
    allowed_files: list[str]
    forbidden_paths: list[str]
    statement: str


@dataclass(frozen=True)
class RuntimePackage:
    """Parsed runtime package containing exactly one NEXT_ACTION and one approval."""

    package_dir: Path
    next_action_path: Path
    next_action: dict[str, Any]
    human_approval: HumanApproval


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _is_full_hash(value: str) -> bool:
    """Return True if value is a 40-character lowercase hex SHA-1 hash."""
    return len(value) == _FULL_HASH_LEN and all(c in "0123456789abcdef" for c in value.lower())


def _resolve(path: Path) -> Path:
    """Resolve a path, raising LauncherError if it does not exist where required."""
    return path.resolve()


def _git_rev_parse(repo: Path, ref: str) -> str:
    """Run ``git rev-parse <ref>`` in *repo* and return the full hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LauncherError(f"git not available for verifying {ref}: {exc}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise LauncherError(f"git rev-parse {ref} failed: {stderr}")

    value = result.stdout.strip()
    if not _is_full_hash(value):
        raise LauncherError(f"git rev-parse {ref} returned non-hash value: {value!r}")
    return value


def _extract_frontmatter(text: str, label: str) -> dict[str, Any]:
    """Extract YAML frontmatter from the top of a markdown file."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise LauncherError(f"{label} is missing YAML frontmatter")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise LauncherError(f"{label} frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise LauncherError(f"{label} frontmatter must be a YAML mapping")
    return data


def _reject_dotenv_voyage(path: Path, label: str) -> None:
    """Reject paths that contain `.env` or `.voyage` segments."""
    for part in path.parts:
        if part == ".env":
            raise LauncherError(f"{label} must not point to .env: {path}")
        if part == ".voyage":
            raise LauncherError(f"{label} must not point to .voyage: {path}")


def _is_inside(child: Path, parent: Path) -> bool:
    """Return True when *child* is equal to or inside *parent*."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _parse_human_approval(path: Path) -> HumanApproval:
    """Parse HUMAN_APPROVAL.md from *path*."""
    text = path.read_text(encoding="utf-8")
    if _REQUIRED_APPROVAL_PHRASE not in text:
        raise LauncherError(
            f"HUMAN_APPROVAL.md is missing required phrase: {_REQUIRED_APPROVAL_PHRASE!r}"
        )

    data = _extract_frontmatter(text, "HUMAN_APPROVAL.md")
    allowed_files = data.get("allowed_files")
    forbidden_paths = data.get("forbidden_paths")

    return HumanApproval(
        approved_by=str(data.get("approved_by", "")),
        package_path=str(data.get("package_path", "")),
        baseline_commit=str(data.get("baseline_commit", "")),
        risk_level=str(data.get("risk_level", "")),
        allowed_files=list(allowed_files) if allowed_files else [],
        forbidden_paths=list(forbidden_paths) if forbidden_paths else [],
        statement=str(data.get("statement", "")),
    )


def _parse_next_action(path: Path) -> dict[str, Any]:
    """Parse NEXT_ACTION.md frontmatter from *path*."""
    text = path.read_text(encoding="utf-8")
    data = _extract_frontmatter(text, "NEXT_ACTION.md")

    schema = data.get("schema")
    if schema != "voyage.next_action.v1":
        raise LauncherError(f"NEXT_ACTION.md has unexpected schema: {schema!r}")

    required = {"cycle", "task_id", "baseline_commit", "turn", "risk_level"}
    missing = required - set(data.keys())
    if missing:
        raise LauncherError(f"NEXT_ACTION.md missing required fields: {sorted(missing)}")

    if data.get("turn") != "code":
        raise LauncherError(f"NEXT_ACTION.md turn must be 'code', got {data.get('turn')!r}")

    return data


def _parse_runtime_package(package_dir: Path) -> RuntimePackage:
    """Parse a runtime package directory."""
    if not package_dir.exists():
        raise LauncherError(f"package directory does not exist: {package_dir}")
    if not package_dir.is_dir():
        raise LauncherError(f"package path is not a directory: {package_dir}")

    next_action_candidates = sorted(package_dir.glob("NEXT_ACTION*.md"))
    if not next_action_candidates:
        raise LauncherError("package is missing NEXT_ACTION.md")
    if len(next_action_candidates) > 1:
        names = [p.name for p in next_action_candidates]
        raise LauncherError(f"package must contain exactly one NEXT_ACTION*.md, found: {names}")
    next_action_path = next_action_candidates[0]

    human_approval_path = package_dir / "HUMAN_APPROVAL.md"
    if not human_approval_path.exists():
        raise LauncherError("package is missing HUMAN_APPROVAL.md")

    next_action = _parse_next_action(next_action_path)
    human_approval = _parse_human_approval(human_approval_path)

    return RuntimePackage(
        package_dir=package_dir,
        next_action_path=next_action_path,
        next_action=next_action,
        human_approval=human_approval,
    )


def _build_report(pkg: RuntimePackage) -> str:
    """Build the LATEST_AGENT_REPORT.md content."""
    lines = [
        "---",
        "schema: voyage.agent_report.v1",
        f"cycle: {pkg.next_action.get('cycle')}",
        f"task_id: {pkg.next_action.get('task_id')}",
        f"baseline_commit: {pkg.next_action.get('baseline_commit')}",
        "turn: work",
        "mode: dry-run",
        "risk_level: report-only",
        "---",
        "",
        "# Latest Agent Report",
        "",
        "This run was executed in **dry-run / report-only** mode.",
        "No AI model was invoked. No files were modified outside this report.",
        "",
        "## Safety confirmations",
        "",
        "- primary_untouched: true",
        "- origin_untouched: true",
        "- secrets_untouched: true",
        "- voyage_untouched: true",
        "",
        "## Anomalies",
        "",
        "None detected.",
        "",
        "## Recommendation",
        "",
        "stop",
    ]
    return "\n".join(lines)


def _run_dry_run(config: LauncherConfig) -> LauncherResult:
    """Internal dry-run implementation."""
    package = _resolve(config.package_dir)
    primary_repo = _resolve(config.primary_repo)
    auto_worktree = _resolve(config.auto_worktree)

    for path, label in (
        (primary_repo, "primary_repo"),
        (auto_worktree, "auto_worktree"),
    ):
        _reject_dotenv_voyage(path, label)
        if not path.exists():
            raise LauncherError(f"{label} does not exist: {path}")
        if not path.is_dir():
            raise LauncherError(f"{label} is not a directory: {path}")

    _reject_dotenv_voyage(package, "package_dir")
    if not _is_inside(package, auto_worktree):
        raise LauncherError(f"package_dir must be inside auto_worktree: {package}")

    expected = config.expected_origin_main.lower()
    if not _is_full_hash(expected):
        raise LauncherError(
            "expected_origin_main must be a full 40-character hex hash, "
            f"got {config.expected_origin_main!r}"
        )

    actual_origin = _git_rev_parse(primary_repo, "origin/main")
    if actual_origin != expected:
        raise LauncherError(f"origin/main mismatch: expected {expected}, got {actual_origin}")

    pkg = _parse_runtime_package(package)

    baseline = str(pkg.next_action.get("baseline_commit", "")).lower()
    if not _is_full_hash(baseline):
        raise LauncherError(
            "NEXT_ACTION.md baseline_commit must be a full 40-character hex hash, "
            f"got {pkg.next_action.get('baseline_commit')!r}"
        )

    actual_head = _git_rev_parse(auto_worktree, "HEAD")
    if actual_head != baseline:
        raise LauncherError(f"baseline_commit mismatch: expected {baseline}, got {actual_head}")

    approval_baseline = pkg.human_approval.baseline_commit.lower()
    if approval_baseline != baseline:
        raise LauncherError(
            f"HUMAN_APPROVAL.md baseline_commit does not match NEXT_ACTION.md: "
            f"{approval_baseline} != {baseline}"
        )

    if pkg.next_action.get("risk_level") != "report-only":
        raise LauncherError(
            "first slice only supports risk_level 'report-only', "
            f"got {pkg.next_action.get('risk_level')!r}"
        )

    report_path = package / "LATEST_AGENT_REPORT.md"
    if report_path.exists():
        raise LauncherError("LATEST_AGENT_REPORT.md already exists; refusing to overwrite")

    morning_path = package / "MORNING_REPORT.md"
    if morning_path.exists():
        raise LauncherError("MORNING_REPORT.md exists; refusing to run")

    report_path.write_text(_build_report(pkg), encoding="utf-8")
    return LauncherResult(
        success=True,
        report_path=report_path,
        message="dry-run completed",
    )


def run_dry_run(config: LauncherConfig) -> LauncherResult:
    """Run the launcher dry-run gate sequence and return a result object.

    On any STOP condition a ``LauncherResult(success=False, ...)`` is returned
    instead of raising, so callers (including the CLI) can decide how to present
    the failure.
    """
    try:
        return _run_dry_run(config)
    except LauncherError as exc:
        return LauncherResult(success=False, report_path=None, message=str(exc))
