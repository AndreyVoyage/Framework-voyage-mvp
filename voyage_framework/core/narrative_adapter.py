"""Narrative source-only scenario validation adapter.

Read-only. No repository mutations, no git writes, no staging, no commits.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voyage_framework.core.auto_loop import (
    AutoLoopError,
    AutoLoopSpec,
    run_plan,
    run_preflight,
    run_validate,
)
from voyage_framework.core.repo_control_adapter import (
    RepoAuditResult,
    RepoControlAdapter,
    RepoPreviewResult,
    RepoStatusResult,
    RepoValidationResult,
)

_CARRY_FLAGS: frozenset[str] = frozenset({"choice_still_open"})
_SC_NUM_RE = re.compile(r"^SC_(\d{3,})$")

_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "version",
        "location",
        "time",
        "intensity",
        "risk",
        "duration_minutes",
        "prerequisites",
        "flags_required",
        "flags_set",
        "choice_points",
        "content_rating",
        "safety_notes",
    }
)

_ID_RE = re.compile(r"^SC_\d{3,}$")


@dataclass(frozen=True)
class SceneValidationResult:
    """Result of a read-only scenario file structural and path-guard check."""

    spec_id: str
    target_repo: str
    file: str
    json_parse_ok: bool
    required_fields_present: bool
    schema_fields_valid: bool
    flags_required_non_empty: bool
    flags_set_non_empty: bool
    choice_points_valid: bool
    content_rating_present: bool
    safety_notes_present: bool
    voyage_validate_ok: bool
    changed_files: list[str]
    issues: list[str]
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": "scene-validate",
            "ok": self.ok,
            "spec_id": self.spec_id,
            "target_repo": self.target_repo,
            "file": self.file,
            "json_parse_ok": self.json_parse_ok,
            "required_fields_present": self.required_fields_present,
            "schema_fields_valid": self.schema_fields_valid,
            "flags_required_non_empty": self.flags_required_non_empty,
            "flags_set_non_empty": self.flags_set_non_empty,
            "choice_points_valid": self.choice_points_valid,
            "content_rating_present": self.content_rating_present,
            "safety_notes_present": self.safety_notes_present,
            "voyage_validate_ok": self.voyage_validate_ok,
            "changed_files": self.changed_files,
            "issues": self.issues,
        }


def validate_scene(spec_path: Path, file_rel: str) -> SceneValidationResult:
    """Validate a scenario JSON file against structural rules and path guards.

    Loads the autoloop spec, reads the scenario file from the target repo,
    runs structural checks, then calls run_validate() for the path-guard report.
    Never writes, stages, commits, or pushes.

    Raises AutoLoopError if the spec file cannot be loaded.
    """
    spec = AutoLoopSpec.from_file(spec_path)

    issues: list[str] = []
    scenario_path = spec.target_repo / file_rel

    # JSON parse
    json_parse_ok = False
    scene: dict[str, Any] = {}
    try:
        raw = scenario_path.read_text(encoding="utf-8")
        scene = json.loads(raw)
        json_parse_ok = True
    except OSError as exc:
        issues.append(f"cannot read file: {exc}")
    except json.JSONDecodeError as exc:
        issues.append(f"JSON parse error: {exc}")

    if not json_parse_ok:
        return _fail_result(spec, file_rel, issues)

    # Required fields
    missing = sorted(_REQUIRED_FIELDS - scene.keys())
    required_fields_present = not missing
    if not required_fields_present:
        issues.append(f"missing required fields: {missing}")

    # id format
    scene_id = scene.get("id", "")
    schema_fields_valid = bool(_ID_RE.match(str(scene_id)))
    if not schema_fields_valid:
        issues.append(f"id must match SC_NNN pattern, got: {scene_id!r}")

    # flags_required
    flags_req = scene.get("flags_required")
    flags_required_non_empty = isinstance(flags_req, list) and len(flags_req) > 0
    if not flags_required_non_empty:
        issues.append("flags_required must be a non-empty list")

    # flags_set
    flags_set_val = scene.get("flags_set")
    flags_set_non_empty = isinstance(flags_set_val, list) and len(flags_set_val) > 0
    if not flags_set_non_empty:
        issues.append("flags_set must be a non-empty list")

    # choice_points and branches
    cps = scene.get("choice_points")
    choice_points_valid = True
    if not isinstance(cps, list) or len(cps) == 0:
        choice_points_valid = False
        issues.append("choice_points must be a non-empty list")
    else:
        for cp in cps:
            if not isinstance(cp, dict):
                choice_points_valid = False
                issues.append("each choice_point must be an object")
                continue
            branches = cp.get("branches", [])
            if not isinstance(branches, list) or len(branches) < 2:
                choice_points_valid = False
                issues.append(f"choice_point {cp.get('id', '?')} must have at least 2 branches")
                continue
            for b in branches:
                if not isinstance(b, dict) or "id" not in b or "flags" not in b:
                    choice_points_valid = False
                    issues.append(
                        f"branch in choice_point {cp.get('id', '?')} missing 'id' or 'flags'"
                    )

    # content_rating
    content_rating_present = bool(scene.get("content_rating"))
    if not content_rating_present:
        issues.append("content_rating is missing or empty")

    # safety_notes
    safety_notes_present = bool(scene.get("safety_notes"))
    if not safety_notes_present:
        issues.append("safety_notes is missing or empty")

    # Path guard check: does the given file path satisfy allowed/forbidden patterns?
    # Uses inline logic mirroring auto_loop._match_pattern to avoid importing private symbols.
    file_normalized = _normalize_path(file_rel)
    path_allowed = _matches_any(file_normalized, spec.allowed_paths)
    path_not_forbidden = not _matches_any(file_normalized, spec.forbidden_paths)
    path_ok = path_allowed and path_not_forbidden
    if not path_ok:
        issues.append(
            f"path {file_rel!r} fails path guards "
            f"(allowed={path_allowed}, not_forbidden={path_not_forbidden})"
        )

    # Run voyage auto validate for changed-files report and full gate state
    validate_ok = False
    validate_report: dict[str, Any] = {"changed_files": []}
    try:
        validate_ok, validate_report = run_validate(spec_path)
    except AutoLoopError as exc:
        issues.append(f"voyage auto validate error: {exc}")

    changed_files: list[str] = validate_report.get("changed_files", [])
    voyage_validate_ok = validate_ok and path_ok

    ok = (
        json_parse_ok
        and required_fields_present
        and schema_fields_valid
        and flags_required_non_empty
        and flags_set_non_empty
        and choice_points_valid
        and content_rating_present
        and safety_notes_present
        and voyage_validate_ok
    )

    return SceneValidationResult(
        spec_id=spec.id,
        target_repo=str(spec.target_repo),
        file=file_rel,
        json_parse_ok=json_parse_ok,
        required_fields_present=required_fields_present,
        schema_fields_valid=schema_fields_valid,
        flags_required_non_empty=flags_required_non_empty,
        flags_set_non_empty=flags_set_non_empty,
        choice_points_valid=choice_points_valid,
        content_rating_present=content_rating_present,
        safety_notes_present=safety_notes_present,
        voyage_validate_ok=voyage_validate_ok,
        changed_files=changed_files,
        issues=issues,
        ok=ok,
    )


def _fail_result(spec: AutoLoopSpec, file_rel: str, issues: list[str]) -> SceneValidationResult:
    return SceneValidationResult(
        spec_id=spec.id,
        target_repo=str(spec.target_repo),
        file=file_rel,
        json_parse_ok=False,
        required_fields_present=False,
        schema_fields_valid=False,
        flags_required_non_empty=False,
        flags_set_non_empty=False,
        choice_points_valid=False,
        content_rating_present=False,
        safety_notes_present=False,
        voyage_validate_ok=False,
        changed_files=[],
        issues=issues,
        ok=False,
    )


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(_match_pattern(path, p) for p in patterns)


def _match_pattern(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    return path == pattern or fnmatch.fnmatch(path, pattern)


# ── Inventory / readiness ─────────────────────────────────────────────────────


def _resolve_inventory_source(
    path: Path,
) -> tuple[str, Path, Path, Path | None]:
    """Classify an inventory input path and return canonical source locations.

    Returns ``(source_type, repo_root, scenarios_dir, spec_path)``.
    ``spec_path`` is set only for autoloop-spec input. Raises ``AutoLoopError``
    if the path does not exist or cannot be classified.
    """
    if not path.exists():
        raise AutoLoopError(f"inventory source not found: {path}")

    if path.is_file():
        name = path.name
        if name == "SCENARIO_LIBRARY.json":
            scenarios_dir = path.parent
            repo_root = scenarios_dir.parent if scenarios_dir.name == "scenarios" else scenarios_dir
            return "library_file", repo_root, scenarios_dir, None
        if name == "SCENARIO_MATRIX.json":
            scenarios_dir = path.parent
            repo_root = scenarios_dir.parent if scenarios_dir.name == "scenarios" else scenarios_dir
            return "matrix_file", repo_root, scenarios_dir, None
        spec = AutoLoopSpec.from_file(path)
        repo_root = Path(spec.target_repo)
        return "autoloop_spec", repo_root, repo_root / "scenarios", path

    if path.is_dir():
        if path.name == "scenarios":
            scenarios_dir = path
            repo_root = path.parent
            return "scenarios_dir", repo_root, scenarios_dir, None
        repo_root = path
        return "repo_root", repo_root, repo_root / "scenarios", None

    raise AutoLoopError(f"cannot classify inventory source: {path}")


def _relative_to_repo(path: Path, repo_root: Path) -> str:
    """Return a POSIX relative path from repo_root to path."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return path.as_posix()
    return rel.as_posix()


def narrative_inventory(source_path: str | Path) -> dict[str, Any]:
    """Read-only inventory/readiness summary of a Narrative target repo.

    Accepts an autoloop spec path, a repo root, a ``scenarios/`` directory,
    ``SCENARIO_LIBRARY.json``, or ``SCENARIO_MATRIX.json``. Discovers scenario
    files, checks for expected catalog files, and reports a coarse schema-version
    mix.

    Never writes, stages, commits, or pushes. Does not execute RenPy or any
    product runtime.
    """
    path = Path(source_path).resolve()
    source_type, repo_root, scenarios_dir, spec_path = _resolve_inventory_source(path)

    source_path_str = str(path)
    spec_path_str = str(spec_path.resolve()) if spec_path else None
    repo_root_str = str(repo_root)

    errors: list[str] = []
    warnings: list[str] = []
    missing: list[str] = []

    scenario_files: list[str] = []
    if scenarios_dir.is_dir():
        for scenario_path in sorted(scenarios_dir.glob("SCENARIO_*.json")):
            if scenario_path.name in ("SCENARIO_LIBRARY.json", "SCENARIO_MATRIX.json"):
                continue
            scenario_files.append(_relative_to_repo(scenario_path, repo_root))
    else:
        errors.append(f"scenarios directory not found: {scenarios_dir}")

    if not scenario_files and not errors:
        errors.append(f"no scenario files found in {scenarios_dir}")

    library_path = scenarios_dir / "SCENARIO_LIBRARY.json"
    matrix_path = scenarios_dir / "SCENARIO_MATRIX.json"
    library_present = library_path.is_file()
    matrix_present = matrix_path.is_file()
    if not library_present:
        missing.append(_relative_to_repo(library_path, repo_root))
    if not matrix_present:
        missing.append(_relative_to_repo(matrix_path, repo_root))

    schema_versions: dict[str, int] = {}
    parse_failures: list[str] = []
    for rel in scenario_files:
        scene_path = repo_root / rel
        try:
            raw = json.loads(scene_path.read_text(encoding="utf-8"))
        except OSError as exc:
            parse_failures.append(f"{rel}: cannot read scenario: {exc}")
            schema_versions["unknown"] = schema_versions.get("unknown", 0) + 1
            continue
        except json.JSONDecodeError as exc:
            parse_failures.append(f"{rel}: JSON parse error: {exc}")
            schema_versions["unknown"] = schema_versions.get("unknown", 0) + 1
            continue

        if isinstance(raw, dict):
            version = raw.get("schema_version") or raw.get("version") or "unknown"
            version_key = str(version)
        else:
            version_key = "unknown"
        schema_versions[version_key] = schema_versions.get(version_key, 0) + 1

    if parse_failures:
        if len(parse_failures) < len(scenario_files):
            warnings.extend(parse_failures)
        else:
            errors.extend(parse_failures)

    if errors:
        readiness = "blocked"
        ok = False
    elif missing or warnings:
        readiness = "warnings"
        ok = True
    else:
        readiness = "ready"
        ok = True

    return {
        "command": "narrative.inventory",
        "ok": ok,
        "source_type": source_type,
        "source_path": source_path_str,
        "spec_path": spec_path_str,
        "repo_root": repo_root_str,
        "scenario_files": scenario_files,
        "scenario_count": len(scenario_files),
        "library": {
            "present": library_present,
            "path": _relative_to_repo(library_path, repo_root),
        },
        "matrix": {
            "present": matrix_present,
            "path": _relative_to_repo(matrix_path, repo_root),
        },
        "schema_versions": schema_versions,
        "missing_expected_files": sorted(missing),
        "warnings": warnings,
        "errors": errors,
        "readiness": readiness,
    }


# ── Spec-update proposal ──────────────────────────────────────────────────────


def _extract_id(raw: object, filename: str) -> str:
    """Return a scenario id from parsed JSON or the filename stem."""
    if isinstance(raw, dict):
        for key in ("scenario_id", "id"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        metadata = raw.get("metadata")
        if isinstance(metadata, dict):
            for key in ("scenario_id", "id"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return Path(filename).stem


def _extract_version(raw: object) -> str:
    """Return a schema version string from parsed JSON."""
    if isinstance(raw, dict):
        for key in ("schema_version", "version"):
            value = raw.get(key)
            if isinstance(value, (str, int, float)):
                return str(value).strip() or "unknown"
        metadata = raw.get("metadata")
        if isinstance(metadata, dict):
            for key in ("schema_version", "version"):
                value = metadata.get(key)
                if isinstance(value, (str, int, float)):
                    return str(value).strip() or "unknown"
    return "unknown"


def _extract_entries(catalog: object) -> list[dict[str, Any]]:
    """Tolerantly extract a list of entry dicts from a catalog object."""
    if isinstance(catalog, list):
        return [item for item in catalog if isinstance(item, dict)]
    if isinstance(catalog, dict):
        for key in ("scenarios", "entries", "items", "library"):
            value = catalog.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [item for item in catalog.values() if isinstance(item, dict)]
    return []


def _entry_id(entry: dict[str, Any]) -> str | None:
    for key in ("scenario_id", "id", "scenarioId"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _entry_file(entry: dict[str, Any]) -> str | None:
    for key in ("file", "filename", "path"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_rows(matrix: object) -> list[dict[str, Any]]:
    """Tolerantly extract a list of row dicts from a matrix object."""
    if isinstance(matrix, list):
        return [item for item in matrix if isinstance(item, dict)]
    if isinstance(matrix, dict):
        for key in ("rows", "matrix", "entries", "items", "scenarios"):
            value = matrix.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [item for item in matrix.values() if isinstance(item, dict)]
    return []


def _row_id(row: dict[str, Any]) -> str | None:
    for key in (
        "scenario_id",
        "id",
        "source",
        "target",
        "from",
        "to",
        "scenario",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _row_file(row: dict[str, Any]) -> str | None:
    for key in ("file", "filename", "path"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _library_count_field(catalog: dict[str, Any]) -> int | None:
    for key in ("total_scenarios", "count", "total", "length"):
        value = catalog.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
    return None


def narrative_spec_plan(repo_path: str | Path) -> dict[str, Any]:
    """Read-only spec-update proposal plan for a Narrative target repo.

    Discovers scenario files, reads ``SCENARIO_LIBRARY.json`` and
    ``SCENARIO_MATRIX.json``, and reports inconsistencies as findings with
    proposal-only actions. Never writes, stages, commits, or pushes. Does not
    run RenPy or any product runtime.
    """
    path = Path(repo_path).resolve()
    source_type, repo_root, scenarios_dir, _spec_path = _resolve_inventory_source(path)

    repo_root_str = str(repo_root)
    library_path = scenarios_dir / "SCENARIO_LIBRARY.json"
    matrix_path = scenarios_dir / "SCENARIO_MATRIX.json"
    library_rel = _relative_to_repo(library_path, repo_root)
    matrix_rel = _relative_to_repo(matrix_path, repo_root)

    findings: list[dict[str, Any]] = []
    proposed_actions: list[dict[str, Any]] = []
    affected_files: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    scenario_files: list[str] = []
    scenario_ids: dict[str, str] = {}
    schema_versions: dict[str, int] = {}
    parse_failures: list[str] = []

    if scenarios_dir.is_dir():
        for scenario_path in sorted(scenarios_dir.glob("SCENARIO_*.json")):
            name = scenario_path.name
            if name in ("SCENARIO_LIBRARY.json", "SCENARIO_MATRIX.json"):
                continue
            rel = _relative_to_repo(scenario_path, repo_root)
            scenario_files.append(rel)
            try:
                raw = json.loads(scenario_path.read_text(encoding="utf-8"))
            except OSError as exc:
                parse_failures.append(f"{rel}: cannot read scenario: {exc}")
                schema_versions["unknown"] = schema_versions.get("unknown", 0) + 1
                continue
            except json.JSONDecodeError as exc:
                parse_failures.append(f"{rel}: JSON parse error: {exc}")
                schema_versions["unknown"] = schema_versions.get("unknown", 0) + 1
                continue

            scenario_id = _extract_id(raw, name)
            if scenario_id in scenario_ids:
                findings.append(
                    {
                        "severity": "warning",
                        "code": "duplicate_scenario_id",
                        "message": (
                            f"scenario id {scenario_id!r} appears in multiple files: "
                            f"{scenario_ids[scenario_id]} and {rel}"
                        ),
                        "file": rel,
                        "related": sorted({scenario_ids[scenario_id], rel}),
                    }
                )
                proposed_actions.append(
                    {
                        "action_type": "review_duplicate_scenario_id",
                        "status": "proposal_only",
                        "target_file": rel,
                        "reason": (
                            f"scenario id {scenario_id!r} is duplicated; "
                            "review and rename or merge files"
                        ),
                        "safe_to_apply_automatically": False,
                    }
                )
            else:
                scenario_ids[scenario_id] = rel

            version = _extract_version(raw)
            schema_versions[version] = schema_versions.get(version, 0) + 1

    if parse_failures:
        warnings.extend(parse_failures)
        for failure in parse_failures:
            findings.append(
                {
                    "severity": "warning",
                    "code": "scenario_json_parse_error",
                    "message": failure,
                    "file": None,
                    "related": [],
                }
            )

    if len(schema_versions) > 1:
        findings.append(
            {
                "severity": "warning",
                "code": "schema_version_mixed",
                "message": (
                    "scenario files use multiple schema versions: "
                    f"{dict(sorted(schema_versions.items()))}"
                ),
                "file": None,
                "related": sorted(scenario_files),
            }
        )
        proposed_actions.append(
            {
                "action_type": "review_schema_version_mix",
                "status": "proposal_only",
                "target_file": None,
                "reason": (
                    "schema versions are mixed; review whether to normalize to a single version"
                ),
                "safe_to_apply_automatically": False,
            }
        )

    # Library analysis
    library_present = library_path.is_file()
    library_entries: list[dict[str, Any]] = []
    library_entry_ids: set[str] = set()
    library_entry_files: set[str] = set()
    library_raw: object = None

    if not library_present:
        findings.append(
            {
                "severity": "warning",
                "code": "library_missing",
                "message": f"SCENARIO_LIBRARY.json not found at {library_rel}",
                "file": library_rel,
                "related": [],
            }
        )
        proposed_actions.append(
            {
                "action_type": "review_library_missing",
                "status": "proposal_only",
                "target_file": library_rel,
                "reason": "library is missing; consider creating it from scenario files",
                "safe_to_apply_automatically": False,
            }
        )
        affected_files.append(library_rel)
    else:
        try:
            library_raw = json.loads(library_path.read_text(encoding="utf-8"))
        except OSError as exc:
            warnings.append(f"cannot read library: {exc}")
            findings.append(
                {
                    "severity": "warning",
                    "code": "library_json_parse_error",
                    "message": f"cannot read {library_rel}: {exc}",
                    "file": library_rel,
                    "related": [],
                }
            )
        except json.JSONDecodeError as exc:
            warnings.append(f"library JSON parse error: {exc}")
            findings.append(
                {
                    "severity": "warning",
                    "code": "library_json_parse_error",
                    "message": f"{library_rel}: JSON parse error: {exc}",
                    "file": library_rel,
                    "related": [],
                }
            )
        else:
            if isinstance(library_raw, dict):
                declared_count = _library_count_field(library_raw)
                if declared_count is not None and declared_count != len(
                    _extract_entries(library_raw)
                ):
                    findings.append(
                        {
                            "severity": "warning",
                            "code": "library_count_drift",
                            "message": (
                                f"library declares {declared_count} scenarios but "
                                f"contains {len(_extract_entries(library_raw))} entries"
                            ),
                            "file": library_rel,
                            "related": [],
                        }
                    )
                    proposed_actions.append(
                        {
                            "action_type": "review_library_count",
                            "status": "proposal_only",
                            "target_file": library_rel,
                            "reason": "library total_scenarios/count does not match entry count",
                            "safe_to_apply_automatically": False,
                        }
                    )
                    affected_files.append(library_rel)

            library_entries = _extract_entries(library_raw)
            if not library_entries and library_raw is not None:
                findings.append(
                    {
                        "severity": "warning",
                        "code": "library_unrecognized_shape",
                        "message": (
                            f"{library_rel} has a recognized shape but no extractable entries"
                        ),
                        "file": library_rel,
                        "related": [],
                    }
                )
                proposed_actions.append(
                    {
                        "action_type": "review_library_shape",
                        "status": "proposal_only",
                        "target_file": library_rel,
                        "reason": "library structure could not be parsed; review schema",
                        "safe_to_apply_automatically": False,
                    }
                )
                affected_files.append(library_rel)

            for entry in library_entries:
                entry_id = _entry_id(entry)
                entry_file = _entry_file(entry)
                if entry_id:
                    library_entry_ids.add(entry_id)
                if entry_file:
                    library_entry_files.add(entry_file)

                referenced_ids = {i for i in (entry_id,) if i}
                if entry_file:
                    file_stem = Path(entry_file).stem
                    referenced_ids.add(file_stem)

                missing_refs = sorted(
                    ref
                    for ref in referenced_ids
                    if ref not in scenario_ids
                    and ref not in {Path(f).stem for f in scenario_files}
                    and ref not in scenario_files
                )
                if missing_refs:
                    msg_parts: list[str] = []
                    if entry_id:
                        msg_parts.append(f"id={entry_id!r}")
                    if entry_file:
                        msg_parts.append(f"file={entry_file!r}")
                    findings.append(
                        {
                            "severity": "warning",
                            "code": "library_entry_missing_scenario",
                            "message": (
                                "library entry references missing scenario(s): "
                                f"{', '.join(missing_refs)} "
                                f"({', '.join(msg_parts)})"
                            ),
                            "file": library_rel,
                            "related": sorted(missing_refs),
                        }
                    )
                    proposed_actions.append(
                        {
                            "action_type": "review_remove_stale_library_entry",
                            "status": "proposal_only",
                            "target_file": library_rel,
                            "reason": (
                                "library entry points to scenario(s) that do not exist; "
                                "review for removal or correction"
                            ),
                            "safe_to_apply_automatically": False,
                        }
                    )
                    affected_files.append(library_rel)

            for scenario_id, rel in sorted(scenario_ids.items()):
                if scenario_id not in library_entry_ids and rel not in library_entry_files:
                    findings.append(
                        {
                            "severity": "warning",
                            "code": "scenario_missing_library_entry",
                            "message": (
                                f"scenario {scenario_id!r} ({rel}) is not referenced by the library"
                            ),
                            "file": rel,
                            "related": [library_rel],
                        }
                    )
                    proposed_actions.append(
                        {
                            "action_type": "review_add_library_entry",
                            "status": "proposal_only",
                            "target_file": library_rel,
                            "reason": f"scenario {scenario_id!r} exists but has no library entry",
                            "safe_to_apply_automatically": False,
                        }
                    )
                    affected_files.extend([rel, library_rel])

    # Matrix analysis
    matrix_present = matrix_path.is_file()
    matrix_row_ids: set[str] = set()
    matrix_row_files: set[str] = set()

    if not matrix_present:
        findings.append(
            {
                "severity": "warning",
                "code": "matrix_missing",
                "message": f"SCENARIO_MATRIX.json not found at {matrix_rel}",
                "file": matrix_rel,
                "related": [],
            }
        )
        proposed_actions.append(
            {
                "action_type": "review_matrix_missing",
                "status": "proposal_only",
                "target_file": matrix_rel,
                "reason": "matrix is missing; consider creating it from scenario files",
                "safe_to_apply_automatically": False,
            }
        )
        affected_files.append(matrix_rel)
    else:
        try:
            matrix_raw = json.loads(matrix_path.read_text(encoding="utf-8"))
        except OSError as exc:
            warnings.append(f"cannot read matrix: {exc}")
            findings.append(
                {
                    "severity": "warning",
                    "code": "matrix_json_parse_error",
                    "message": f"cannot read {matrix_rel}: {exc}",
                    "file": matrix_rel,
                    "related": [],
                }
            )
        except json.JSONDecodeError as exc:
            warnings.append(f"matrix JSON parse error: {exc}")
            findings.append(
                {
                    "severity": "warning",
                    "code": "matrix_json_parse_error",
                    "message": f"{matrix_rel}: JSON parse error: {exc}",
                    "file": matrix_rel,
                    "related": [],
                }
            )
        else:
            matrix_rows = _extract_rows(matrix_raw)
            if not matrix_rows and matrix_raw is not None:
                findings.append(
                    {
                        "severity": "warning",
                        "code": "matrix_unrecognized_shape",
                        "message": (f"{matrix_rel} has a recognized shape but no extractable rows"),
                        "file": matrix_rel,
                        "related": [],
                    }
                )
                proposed_actions.append(
                    {
                        "action_type": "review_matrix_shape",
                        "status": "proposal_only",
                        "target_file": matrix_rel,
                        "reason": "matrix structure could not be parsed; review schema",
                        "safe_to_apply_automatically": False,
                    }
                )
                affected_files.append(matrix_rel)

            for row in matrix_rows:
                row_id = _row_id(row)
                row_file = _row_file(row)
                if row_id:
                    matrix_row_ids.add(row_id)
                if row_file:
                    matrix_row_files.add(row_file)

                referenced_ids = {i for i in (row_id,) if i}
                if row_file:
                    referenced_ids.add(Path(row_file).stem)

                unknown = sorted(
                    ref
                    for ref in referenced_ids
                    if ref not in scenario_ids
                    and ref not in {Path(f).stem for f in scenario_files}
                    and ref not in scenario_files
                )
                if unknown:
                    findings.append(
                        {
                            "severity": "warning",
                            "code": "matrix_reference_unknown_scenario",
                            "message": (
                                f"matrix row references unknown scenario(s): {', '.join(unknown)}"
                            ),
                            "file": matrix_rel,
                            "related": sorted(unknown),
                        }
                    )
                    proposed_actions.append(
                        {
                            "action_type": "review_matrix_reference",
                            "status": "proposal_only",
                            "target_file": matrix_rel,
                            "reason": (
                                "matrix references scenario(s) that do not exist; "
                                "review for removal or correction"
                            ),
                            "safe_to_apply_automatically": False,
                        }
                    )
                    affected_files.append(matrix_rel)

            for scenario_id, rel in sorted(scenario_ids.items()):
                if scenario_id not in matrix_row_ids and rel not in matrix_row_files:
                    findings.append(
                        {
                            "severity": "info",
                            "code": "scenario_missing_matrix_reference",
                            "message": (
                                f"scenario {scenario_id!r} ({rel}) is not referenced by the matrix"
                            ),
                            "file": rel,
                            "related": [matrix_rel],
                        }
                    )
                    proposed_actions.append(
                        {
                            "action_type": "review_matrix_coverage",
                            "status": "proposal_only",
                            "target_file": matrix_rel,
                            "reason": f"scenario {scenario_id!r} exists but has no matrix row",
                            "safe_to_apply_automatically": False,
                        }
                    )
                    affected_files.extend([rel, matrix_rel])

    # Determine readiness
    error_findings = [f for f in findings if f.get("severity") == "error"]
    warning_findings = [f for f in findings if f.get("severity") in ("warning", "info")]

    if errors or error_findings:
        readiness = "blocked"
        ok = False
    elif warning_findings:
        readiness = "warnings"
        ok = True
    else:
        readiness = "ready"
        ok = True

    return {
        "command": "narrative.spec_plan",
        "ok": ok,
        "repo_root": repo_root_str,
        "read_only": True,
        "apply_supported": False,
        "inventory": {
            "scenario_count": len(scenario_files),
            "library_present": library_present,
            "matrix_present": matrix_present,
            "schema_versions": dict(sorted(schema_versions.items())),
        },
        "findings": sorted(findings, key=lambda f: (f["severity"], f["code"], f["message"])),
        "proposed_actions": sorted(
            proposed_actions,
            key=lambda a: (a["action_type"], a.get("target_file") or "", a["reason"]),
        ),
        "affected_files": sorted(set(affected_files)),
        "warnings": sorted(warnings),
        "errors": sorted(errors),
        "readiness": readiness,
    }


# ── Arc checkpoint ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ArcCheckpoint:
    """Result of a read-only continuity check across a Narrative scenario arc."""

    spec_id: str
    target_repo: str
    from_id: str
    count: int
    scenarios_checked: list[str]
    files_checked: list[str]
    predecessor_chain_valid: bool
    choice_still_open_consistent: bool
    flag_duplicates: list[str]
    schema_stable: bool
    branch_pattern_valid: bool
    intensity_curve: list[dict[str, object]]
    arc_flags_progression: list[dict[str, object]]
    recommended_next_id: str
    recommended_next_filename_pattern: str
    recommended_flags_required: list[str]
    issues: list[str]
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": "arc-check",
            "ok": self.ok,
            "spec_id": self.spec_id,
            "target_repo": self.target_repo,
            "from_id": self.from_id,
            "count": self.count,
            "scenarios_checked": self.scenarios_checked,
            "files_checked": self.files_checked,
            "predecessor_chain_valid": self.predecessor_chain_valid,
            "choice_still_open_consistent": self.choice_still_open_consistent,
            "flag_duplicates": self.flag_duplicates,
            "schema_stable": self.schema_stable,
            "branch_pattern_valid": self.branch_pattern_valid,
            "intensity_curve": self.intensity_curve,
            "arc_flags_progression": self.arc_flags_progression,
            "recommended_next_id": self.recommended_next_id,
            "recommended_next_filename_pattern": self.recommended_next_filename_pattern,
            "recommended_flags_required": self.recommended_flags_required,
            "issues": self.issues,
        }


def run_arc_check(spec_path: Path | str, from_id: str, count: int = 6) -> ArcCheckpoint:
    """Check continuity across a Narrative scenario arc.

    Reads scenario JSON files from the target repo, checks predecessor chain,
    flag consistency, schema stability, and branch patterns.
    Never writes, stages, commits, or pushes.

    Raises AutoLoopError if the spec file cannot be loaded.
    """
    spec = AutoLoopSpec.from_file(Path(spec_path))
    issues: list[str] = []

    # Parse from_id
    m = _SC_NUM_RE.match(from_id)
    if m is None:
        issues.append(f"from_id must match SC_NNN pattern, got: {from_id!r}")
        return _fail_arc(spec, from_id, count, issues)
    start_num = int(m.group(1))

    scenarios_dir = spec.target_repo / "scenarios"
    scenario_ids: list[str] = []
    file_paths: list[str] = []
    scenes: list[dict[str, Any]] = []

    # Discover and parse files
    for i in range(count):
        num = start_num + i
        sc_id = f"SC_{num:03d}"
        matches = sorted(scenarios_dir.glob(f"SCENARIO_{num:03d}_*.json"))
        if len(matches) != 1:
            issues.append(
                f"expected exactly one file for {sc_id}, found {len(matches)} in {scenarios_dir}"
            )
            return _fail_arc(spec, from_id, count, issues)
        rel = f"scenarios/{matches[0].name}"
        try:
            scene = json.loads(matches[0].read_text(encoding="utf-8"))
        except OSError as exc:
            issues.append(f"cannot read {rel}: {exc}")
            return _fail_arc(spec, from_id, count, issues)
        except json.JSONDecodeError as exc:
            issues.append(f"JSON parse error in {rel}: {exc}")
            return _fail_arc(spec, from_id, count, issues)

        file_id = scene.get("id", "")
        if file_id != sc_id:
            issues.append(f"{rel}: expected id={sc_id!r}, got {file_id!r}")

        scenario_ids.append(sc_id)
        file_paths.append(rel)
        scenes.append(scene)

    # Schema stability
    field_sets = [frozenset(s.keys()) for s in scenes]
    schema_stable = all(fs == field_sets[0] for fs in field_sets)
    if not schema_stable:
        for i, fs in enumerate(field_sets):
            diff = fs.symmetric_difference(field_sets[0])
            if diff:
                issues.append(f"{scenario_ids[i]}: schema differs from first: {sorted(diff)}")

    # choice_still_open consistency
    cso_present = any(
        "choice_still_open" in s.get("flags_required", [])
        or "choice_still_open" in s.get("flags_set", [])
        for s in scenes
    )
    choice_still_open_consistent = True
    if cso_present:
        for i, s in enumerate(scenes):
            if "choice_still_open" not in s.get("flags_required", []):
                choice_still_open_consistent = False
                issues.append(f"{scenario_ids[i]}: choice_still_open missing from flags_required")
            if "choice_still_open" not in s.get("flags_set", []):
                choice_still_open_consistent = False
                issues.append(f"{scenario_ids[i]}: choice_still_open missing from flags_set")

    # Predecessor chain: sc_NNN_complete in curr.flags_set and next.flags_required
    predecessor_chain_valid = True
    for i in range(len(scenes) - 1):
        complete_flag = f"{scenario_ids[i].lower()}_complete"
        if complete_flag not in scenes[i].get("flags_set", []):
            predecessor_chain_valid = False
            issues.append(f"{scenario_ids[i]}: {complete_flag!r} not in flags_set")
        if complete_flag not in scenes[i + 1].get("flags_required", []):
            predecessor_chain_valid = False
            issues.append(f"{scenario_ids[i + 1]}: {complete_flag!r} not in flags_required")

    # Duplicate flag detection across arc (excluding carry flags)
    seen: dict[str, list[str]] = {}
    for i, s in enumerate(scenes):
        for flag in s.get("flags_set", []):
            if flag in _CARRY_FLAGS:
                continue
            seen.setdefault(flag, []).append(scenario_ids[i])
    flag_duplicates = sorted(f for f, ids in seen.items() if len(ids) > 1)
    for flag in flag_duplicates:
        issues.append(f"duplicate flag {flag!r} in flags_set: {seen[flag]}")

    # Branch pattern
    branch_pattern_valid = True
    for i, s in enumerate(scenes):
        cps = s.get("choice_points")
        if not isinstance(cps, list) or len(cps) == 0:
            branch_pattern_valid = False
            issues.append(f"{scenario_ids[i]}: choice_points must be a non-empty list")
            continue
        for cp in cps:
            branches = cp.get("branches", [])
            if not isinstance(branches, list) or len(branches) < 2:
                branch_pattern_valid = False
                issues.append(f"{scenario_ids[i]} {cp.get('id', '?')}: needs at least 2 branches")
                continue
            for b in branches:
                if not isinstance(b, dict) or "id" not in b or "flags" not in b:
                    branch_pattern_valid = False
                    issues.append(
                        f"{scenario_ids[i]} {cp.get('id', '?')}: branch missing 'id' or 'flags'"
                    )

    # Intensity/risk/time curve
    intensity_curve: list[dict[str, object]] = [
        {
            "id": scenario_ids[i],
            "intensity": scenes[i].get("intensity"),
            "risk": scenes[i].get("risk"),
            "time": scenes[i].get("time"),
            "location": scenes[i].get("location"),
        }
        for i in range(len(scenes))
    ]

    # Arc flags progression
    arc_flags_progression: list[dict[str, object]] = [
        {
            "id": scenario_ids[i],
            "flags_required": scenes[i].get("flags_required", []),
            "flags_set": scenes[i].get("flags_set", []),
        }
        for i in range(len(scenes))
    ]

    # Recommend next
    next_num = start_num + count
    recommended_next_id = f"SC_{next_num:03d}"
    recommended_next_filename_pattern = f"SCENARIO_{next_num:03d}_*.json"

    last_flags_set: set[str] = set(scenes[-1].get("flags_set", []))
    branch_flags: set[str] = set()
    for cp in scenes[-1].get("choice_points", []):
        for b in cp.get("branches", []):
            branch_flags.update(b.get("flags", []))
    last_complete = f"{scenario_ids[-1].lower()}_complete"
    key_flags = sorted(last_flags_set - _CARRY_FLAGS - branch_flags - {last_complete})
    recommended_flags_required: list[str] = [last_complete, *key_flags]
    if choice_still_open_consistent:
        recommended_flags_required.append("choice_still_open")

    ok = (
        predecessor_chain_valid
        and choice_still_open_consistent
        and not flag_duplicates
        and schema_stable
        and branch_pattern_valid
        and not issues
    )

    return ArcCheckpoint(
        spec_id=spec.id,
        target_repo=str(spec.target_repo),
        from_id=from_id,
        count=count,
        scenarios_checked=scenario_ids,
        files_checked=file_paths,
        predecessor_chain_valid=predecessor_chain_valid,
        choice_still_open_consistent=choice_still_open_consistent,
        flag_duplicates=flag_duplicates,
        schema_stable=schema_stable,
        branch_pattern_valid=branch_pattern_valid,
        intensity_curve=intensity_curve,
        arc_flags_progression=arc_flags_progression,
        recommended_next_id=recommended_next_id,
        recommended_next_filename_pattern=recommended_next_filename_pattern,
        recommended_flags_required=recommended_flags_required,
        issues=issues,
        ok=ok,
    )


def _fail_arc(spec: AutoLoopSpec, from_id: str, count: int, issues: list[str]) -> ArcCheckpoint:
    return ArcCheckpoint(
        spec_id=spec.id,
        target_repo=str(spec.target_repo),
        from_id=from_id,
        count=count,
        scenarios_checked=[],
        files_checked=[],
        predecessor_chain_valid=False,
        choice_still_open_consistent=False,
        flag_duplicates=[],
        schema_stable=False,
        branch_pattern_valid=False,
        intensity_curve=[],
        arc_flags_progression=[],
        recommended_next_id="",
        recommended_next_filename_pattern="",
        recommended_flags_required=[],
        issues=issues,
        ok=False,
    )


class NarrativeRepoControlAdapter(RepoControlAdapter):
    """First concrete RepoControlAdapter implementation, wrapping the
    existing read-only Narrative source-only validation functions.

    Wraps validate_scene/run_arc_check/run_preflight/run_plan unchanged;
    does not alter their public behavior.
    """

    def status(self, spec_path: str | Path) -> RepoStatusResult:
        spec = Path(spec_path)
        ok, report = run_preflight(spec)
        gates: list[dict[str, Any]] = report.get("gates", [])
        issues = tuple(str(gate["detail"]) for gate in gates if not gate["passed"])
        passed_count = sum(1 for gate in gates if gate["passed"])
        summary = f"{passed_count}/{len(gates)} guards passed"
        repo_path = report.get("target_repo")
        return RepoStatusResult(
            command="repo.status",
            ok=ok,
            adapter="narrative",
            repo_path=str(repo_path) if repo_path is not None else None,
            summary=summary,
            issues=issues,
            details=report,
        )

    def validate(self, spec_path: str | Path, target: str | None = None) -> RepoValidationResult:
        if target is None:
            return RepoValidationResult(
                command="repo.validate",
                ok=False,
                adapter="narrative",
                target=None,
                issues=("target (scene/file relative path) is required for narrative validate",),
                details={},
            )
        spec = Path(spec_path)
        result = validate_scene(spec, target)
        return RepoValidationResult(
            command="repo.validate",
            ok=result.ok,
            adapter="narrative",
            target=target,
            issues=tuple(result.issues),
            details=result.to_dict(),
        )

    def audit(
        self,
        spec_path: str | Path,
        target: str | None = None,
        **options: object,
    ) -> RepoAuditResult:
        from_id = target
        if from_id is None:
            options_from_id = options.get("from_id")
            if isinstance(options_from_id, str):
                from_id = options_from_id
        if from_id is None:
            return RepoAuditResult(
                command="repo.audit",
                ok=False,
                adapter="narrative",
                target=None,
                issues=("target (from_id) is required for narrative audit",),
                details={},
            )
        count = 6
        options_count = options.get("count")
        if isinstance(options_count, int):
            count = options_count
        spec = Path(spec_path)
        result = run_arc_check(spec, from_id, count=count)
        return RepoAuditResult(
            command="repo.audit",
            ok=result.ok,
            adapter="narrative",
            target=from_id,
            issues=tuple(result.issues),
            details=result.to_dict(),
        )

    def preview(self, spec_path: str | Path) -> RepoPreviewResult:
        spec = Path(spec_path)
        ok, report = run_plan(spec)
        plan: dict[str, Any] = report.get("plan", {})
        gates: list[dict[str, Any]] = plan.get("gates", [])
        issues = tuple(str(gate["detail"]) for gate in gates if not gate["passed"])
        return RepoPreviewResult(
            command="repo.preview",
            ok=ok,
            adapter="narrative",
            summary="plan generated; commands not executed",
            actions=("repo.status", "repo.validate", "repo.audit", "repo.preview"),
            issues=issues,
            details=report,
        )
