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

from voyage_framework.core.auto_loop import AutoLoopError, AutoLoopSpec, run_validate

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
