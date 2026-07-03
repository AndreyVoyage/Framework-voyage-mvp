"""Unit tests for the Narrative source-only scene validation adapter."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from voyage_framework.core.auto_loop import AutoLoopError
from voyage_framework.core.narrative_adapter import (
    NarrativeRepoControlAdapter,
    narrative_inventory,
    run_arc_check,
    validate_scene,
)
from voyage_framework.core.repo_control_adapter import (
    RepoAuditResult,
    RepoControlAdapter,
    RepoPreviewResult,
    RepoStatusResult,
    RepoValidationResult,
)

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


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_LOCAL_ENV_VARS}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True)
    _git(path, "init", "--initial-branch=main")
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(
        path,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    )
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "update-ref", "refs/remotes/origin/main", "HEAD")
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        text=True,
        env=_clean_env(),
    ).strip()


def _spec_dict(repo: Path, head: str, **overrides: Any) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "schema": "voyage.auto.spec.v1",
        "id": "TEST-NARRATIVE",
        "mode": "source_only",
        "target_repo": str(repo),
        "expected_branch": "main",
        "expected_head": head,
        "expected_origin_main": head,
        "require_clean_worktree": True,
        "allowed_paths": ["scenarios/SCENARIO_*.json"],
        "forbidden_paths": [".env", "scenarios/INDEX.json"],
        "max_files_changed": 1,
        "allow_execution": False,
        "allow_commit": False,
        "allow_push": False,
        "allow_merge": False,
        "allow_bridge": False,
        "allow_auto_launch": False,
    }
    spec.update(overrides)
    return spec


def _valid_scene(scene_id: str = "SC_025") -> dict[str, Any]:
    return {
        "id": scene_id,
        "version": "1.0",
        "location": "home",
        "time": "evening",
        "archetype": "none",
        "kira_level_start": "U5",
        "kira_level_end": "U5",
        "sergey_level_start": "S5",
        "sergey_level_end": "S5",
        "intensity": 7,
        "risk": 4,
        "duration_minutes": 30,
        "prerequisites": ["sc_024_complete"],
        "flags_required": ["choice_still_open"],
        "flags_set": ["sc_025_complete", "choice_still_open"],
        "emotional_anchors": [],
        "symbols": [],
        "choice_points": [
            {
                "id": "CP_1",
                "timing": "test_timing",
                "question": "Test question?",
                "branches": [
                    {
                        "id": "1A",
                        "action": "action a",
                        "kira_reaction": "kira a",
                        "yakov_reaction": "yakov a",
                        "next_level": "U5",
                        "flags": ["flag_a"],
                    },
                    {
                        "id": "1B",
                        "action": "action b",
                        "kira_reaction": "kira b",
                        "yakov_reaction": "yakov b",
                        "next_level": "U5",
                        "flags": ["flag_b"],
                    },
                ],
            }
        ],
        "visual_scene_id": "VS_025",
        "content_rating": "PG-13",
        "safety_notes": "No escalation, no coercion.",
    }


class TestValidateScene:
    def _setup(self, tmp_path: Path) -> tuple[Path, str, Path]:
        repo = tmp_path / "narrative"
        head = _init_repo(repo)
        (repo / "scenarios").mkdir()
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
        return repo, head, spec_file

    def test_valid_scene_passes(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is True
        assert result.json_parse_ok is True
        assert result.required_fields_present is True
        assert result.schema_fields_valid is True
        assert result.flags_required_non_empty is True
        assert result.flags_set_non_empty is True
        assert result.choice_points_valid is True
        assert result.content_rating_present is True
        assert result.safety_notes_present is True
        assert result.voyage_validate_ok is True
        assert result.issues == []

    def test_missing_required_field_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        del scene["content_rating"]
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.required_fields_present is False
        assert any("content_rating" in issue for issue in result.issues)

    def test_invalid_id_format_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        scene["id"] = "INVALID_ID"
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.schema_fields_valid is False
        assert any("SC_NNN" in issue for issue in result.issues)

    def test_empty_flags_required_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        scene["flags_required"] = []
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.flags_required_non_empty is False

    def test_empty_flags_set_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        scene["flags_set"] = []
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.flags_set_non_empty is False

    def test_too_few_branches_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        scene["choice_points"][0]["branches"] = [scene["choice_points"][0]["branches"][0]]
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.choice_points_valid is False
        assert any("2 branches" in issue for issue in result.issues)

    def test_empty_choice_points_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        scene["choice_points"] = []
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.choice_points_valid is False

    def test_branch_missing_flags_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        del scene["choice_points"][0]["branches"][0]["flags"]
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.choice_points_valid is False

    def test_path_not_in_allowlist_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        (repo / "other").mkdir()
        scene_file = repo / "other" / "file.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = validate_scene(spec_file, "other/file.json")

        assert result.ok is False
        assert result.voyage_validate_ok is False
        assert any("path guards" in issue for issue in result.issues)

    def test_forbidden_path_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "INDEX.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/INDEX.json")

        assert result.ok is False
        assert result.voyage_validate_ok is False
        assert any("path guards" in issue for issue in result.issues)

    def test_json_parse_error_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text("{ not valid json }", encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")

        assert result.ok is False
        assert result.json_parse_ok is False
        assert any("JSON parse error" in issue for issue in result.issues)

    def test_file_not_found_fails(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)

        result = validate_scene(spec_file, "scenarios/SCENARIO_NONEXISTENT.json")

        assert result.ok is False
        assert result.json_parse_ok is False
        assert any("cannot read file" in issue for issue in result.issues)

    def test_spec_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(AutoLoopError, match="spec file not found"):
            validate_scene(tmp_path / "nonexistent.json", "scenarios/SCENARIO_025.json")

    def test_result_to_dict_has_all_required_keys(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_025_TEST.json")
        d = result.to_dict()

        required_keys = {
            "command",
            "ok",
            "spec_id",
            "target_repo",
            "file",
            "json_parse_ok",
            "required_fields_present",
            "schema_fields_valid",
            "flags_required_non_empty",
            "flags_set_non_empty",
            "choice_points_valid",
            "content_rating_present",
            "safety_notes_present",
            "voyage_validate_ok",
            "changed_files",
            "issues",
        }
        assert required_keys <= set(d.keys())
        assert d["command"] == "scene-validate"

    def test_sc_id_pattern_accepts_three_digit(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_026_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene("SC_026")), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_026_TEST.json")

        assert result.schema_fields_valid is True

    def test_sc_id_pattern_accepts_longer(self, tmp_path: Path) -> None:
        repo, _, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_100_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene("SC_100")), encoding="utf-8")

        result = validate_scene(spec_file, "scenarios/SCENARIO_100_TEST.json")

        assert result.schema_fields_valid is True


def _arc_scene(num: int, has_cso: bool = True) -> dict[str, Any]:
    sc_id = f"SC_{num:03d}"
    prev_complete = f"sc_{num - 1:03d}_complete"
    return {
        "id": sc_id,
        "version": "1.0",
        "location": "home",
        "time": "evening",
        "archetype": "none",
        "kira_level_start": "U5",
        "kira_level_end": "U5",
        "sergey_level_start": "S5",
        "sergey_level_end": "S5",
        "intensity": 6,
        "risk": 3,
        "duration_minutes": 25,
        "prerequisites": [prev_complete],
        "flags_required": [prev_complete] + (["choice_still_open"] if has_cso else []),
        "flags_set": [f"sc_{num:03d}_complete"] + (["choice_still_open"] if has_cso else []),
        "emotional_anchors": [],
        "symbols": [],
        "choice_points": [
            {
                "id": "CP_1",
                "timing": "test",
                "question": "Test?",
                "branches": [
                    {"id": "1A", "action": "A", "flags": ["flag_a"]},
                    {"id": "1B", "action": "B", "flags": ["flag_b"]},
                ],
            }
        ],
        "visual_scene_id": f"VS_{num:03d}",
        "content_rating": "PG-13",
        "safety_notes": "No issues.",
    }


def _write_arc(repo: Path, scenes: list[dict[str, Any]], start_num: int = 20) -> None:
    d = repo / "scenarios"
    d.mkdir(exist_ok=True)
    for i, scene in enumerate(scenes):
        num = start_num + i
        (d / f"SCENARIO_{num:03d}_TEST.json").write_text(json.dumps(scene), encoding="utf-8")


def _write_catalog(repo: Path, name: str) -> None:
    (repo / "scenarios" / name).write_text("{}", encoding="utf-8")


def _inventory_setup(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "narrative"
    head = _init_repo(repo)
    (repo / "scenarios").mkdir()
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
    return repo, spec_file


class TestNarrativeInventory:
    def test_valid_inventory_ready(self, tmp_path: Path) -> None:
        repo, spec_file = _inventory_setup(tmp_path)
        (repo / "scenarios" / "SCENARIO_025_TEST.json").write_text(
            json.dumps(_valid_scene()), encoding="utf-8"
        )
        _write_catalog(repo, "SCENARIO_LIBRARY.json")
        _write_catalog(repo, "SCENARIO_MATRIX.json")

        before_files = sorted(p.name for p in repo.rglob("*") if p.is_file())

        result = narrative_inventory(spec_file)

        after_files = sorted(p.name for p in repo.rglob("*") if p.is_file())
        assert after_files == before_files

        assert result["command"] == "narrative.inventory"
        assert result["ok"] is True
        assert result["scenario_files"] == ["scenarios/SCENARIO_025_TEST.json"]
        assert result["scenario_count"] == 1
        assert result["library"]["present"] is True
        assert result["matrix"]["present"] is True
        assert result["missing_expected_files"] == []
        assert result["readiness"] == "ready"
        assert result["errors"] == []
        assert json.dumps(result)

    def test_missing_catalog_files_warn(self, tmp_path: Path) -> None:
        repo, spec_file = _inventory_setup(tmp_path)
        (repo / "scenarios" / "SCENARIO_025_TEST.json").write_text(
            json.dumps(_valid_scene()), encoding="utf-8"
        )

        result = narrative_inventory(spec_file)

        assert result["ok"] is True
        assert result["readiness"] == "warnings"
        assert result["missing_expected_files"] == [
            "scenarios/SCENARIO_LIBRARY.json",
            "scenarios/SCENARIO_MATRIX.json",
        ]

    def test_schema_version_mix(self, tmp_path: Path) -> None:
        repo, spec_file = _inventory_setup(tmp_path)
        v2_scene = {**_valid_scene(), "schema_version": "2.0"}
        v1_scene = {**_valid_scene("SC_026"), "version": "1.0"}
        v1_scene.pop("schema_version", None)
        unknown_scene = {**_valid_scene("SC_027")}
        unknown_scene.pop("schema_version", None)
        unknown_scene.pop("version", None)
        (repo / "scenarios" / "SCENARIO_025_TEST.json").write_text(
            json.dumps(v2_scene), encoding="utf-8"
        )
        (repo / "scenarios" / "SCENARIO_026_TEST.json").write_text(
            json.dumps(v1_scene), encoding="utf-8"
        )
        (repo / "scenarios" / "SCENARIO_027_TEST.json").write_text(
            json.dumps(unknown_scene), encoding="utf-8"
        )

        result = narrative_inventory(spec_file)

        assert result["ok"] is True
        assert result["schema_versions"].get("2.0") == 1
        assert result["schema_versions"].get("1.0") == 1
        assert result["schema_versions"].get("unknown") == 1
        assert result["scenario_count"] == 3

    def test_invalid_spec_raises_auto_loop_error(self, tmp_path: Path) -> None:
        spec_file = tmp_path / "spec.json"
        spec_file.write_text("{}", encoding="utf-8")

        with pytest.raises(AutoLoopError):
            narrative_inventory(spec_file)

    def test_broken_scenario_reported_as_error(self, tmp_path: Path) -> None:
        repo, spec_file = _inventory_setup(tmp_path)
        (repo / "scenarios" / "SCENARIO_025_TEST.json").write_text("not json", encoding="utf-8")

        result = narrative_inventory(spec_file)

        assert result["ok"] is False
        assert result["readiness"] == "blocked"
        assert any("JSON parse error" in error for error in result["errors"])
        assert result["schema_versions"].get("unknown") == 1


class TestRunArcCheck:
    def _setup(self, tmp_path: Path) -> tuple[Path, Path]:
        repo = tmp_path / "narrative"
        head = _init_repo(repo)
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
        return repo, spec_file

    def test_valid_arc_passes(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scenes = [_arc_scene(20 + i) for i in range(3)]
        _write_arc(repo, scenes, start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=3)

        assert result.ok is True
        assert result.scenarios_checked == ["SC_020", "SC_021", "SC_022"]
        assert result.predecessor_chain_valid is True
        assert result.choice_still_open_consistent is True
        assert result.flag_duplicates == []
        assert result.schema_stable is True
        assert result.branch_pattern_valid is True
        assert result.issues == []

    def test_recommended_next_id(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scenes = [_arc_scene(20 + i) for i in range(3)]
        _write_arc(repo, scenes, start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=3)

        assert result.recommended_next_id == "SC_023"
        assert result.recommended_next_filename_pattern == "SCENARIO_023_*.json"
        assert "sc_022_complete" in result.recommended_flags_required
        assert "choice_still_open" in result.recommended_flags_required

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        (repo / "scenarios").mkdir(exist_ok=True)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert result.ok is False
        assert any("SC_020" in issue for issue in result.issues)

    def test_invalid_from_id_fails(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)

        result = run_arc_check(spec_file, "INVALID", count=1)

        assert result.ok is False
        assert any("SC_NNN" in issue for issue in result.issues)

    def test_predecessor_chain_broken(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        s0 = _arc_scene(20)
        s1 = _arc_scene(21)
        s1["flags_required"] = ["choice_still_open"]  # remove sc_020_complete
        _write_arc(repo, [s0, s1], start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert result.predecessor_chain_valid is False
        assert result.ok is False

    def test_choice_still_open_missing(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        s0 = _arc_scene(20, has_cso=True)
        s1 = _arc_scene(21, has_cso=False)  # breaks consistency
        _write_arc(repo, [s0, s1], start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert result.choice_still_open_consistent is False
        assert result.ok is False

    def test_duplicate_flags_detected(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        s0 = _arc_scene(20)
        s1 = _arc_scene(21)
        s0["flags_set"] = ["sc_020_complete", "shared_flag", "choice_still_open"]
        s1["flags_set"] = ["sc_021_complete", "shared_flag", "choice_still_open"]
        _write_arc(repo, [s0, s1], start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert "shared_flag" in result.flag_duplicates
        assert result.ok is False

    def test_schema_unstable(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        s0 = _arc_scene(20)
        s1 = _arc_scene(21)
        s1["extra_field"] = "unexpected"
        _write_arc(repo, [s0, s1], start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert result.schema_stable is False
        assert result.ok is False

    def test_branch_pattern_too_few_branches(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        s0 = _arc_scene(20)
        s0["choice_points"][0]["branches"] = [{"id": "1A", "flags": ["f"]}]
        _write_arc(repo, [s0], start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=1)

        assert result.branch_pattern_valid is False
        assert result.ok is False

    def test_intensity_curve_populated(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scenes = [_arc_scene(20 + i) for i in range(2)]
        _write_arc(repo, scenes, start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)

        assert len(result.intensity_curve) == 2
        assert result.intensity_curve[0]["id"] == "SC_020"
        assert "intensity" in result.intensity_curve[0]
        assert "risk" in result.intensity_curve[0]

    def test_to_dict_has_all_required_keys(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scenes = [_arc_scene(20 + i) for i in range(2)]
        _write_arc(repo, scenes, start_num=20)

        result = run_arc_check(spec_file, "SC_020", count=2)
        d = result.to_dict()

        required = {
            "command",
            "ok",
            "spec_id",
            "target_repo",
            "from_id",
            "count",
            "scenarios_checked",
            "files_checked",
            "predecessor_chain_valid",
            "choice_still_open_consistent",
            "flag_duplicates",
            "schema_stable",
            "branch_pattern_valid",
            "intensity_curve",
            "arc_flags_progression",
            "recommended_next_id",
            "recommended_next_filename_pattern",
            "recommended_flags_required",
            "issues",
        }
        assert required <= set(d.keys())
        assert d["command"] == "arc-check"

    def test_spec_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(AutoLoopError, match="spec file not found"):
            run_arc_check(tmp_path / "nonexistent.json", "SC_020")


class TestNarrativeRepoControlAdapter:
    def _setup_scene(self, tmp_path: Path) -> tuple[Path, Path]:
        repo = tmp_path / "narrative"
        head = _init_repo(repo)
        (repo / "scenarios").mkdir()
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")
        return repo, spec_file

    def _setup_arc(self, tmp_path: Path) -> tuple[Path, Path]:
        repo = tmp_path / "narrative"
        head = _init_repo(repo)
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
        scenes = [_arc_scene(20 + i) for i in range(3)]
        _write_arc(repo, scenes, start_num=20)
        return repo, spec_file

    def test_is_repo_control_adapter(self) -> None:
        adapter = NarrativeRepoControlAdapter()
        assert isinstance(adapter, RepoControlAdapter)

    def test_status_returns_status_result(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_scene(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.status(spec_file)

        assert isinstance(result, RepoStatusResult)
        assert result.adapter == "narrative"
        assert json.dumps(result.to_dict())

    def test_validate_with_target_preserves_validate_scene_behavior(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_scene(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.validate(spec_file, target="scenarios/SCENARIO_025_TEST.json")

        assert isinstance(result, RepoValidationResult)
        assert result.ok is True
        assert result.target == "scenarios/SCENARIO_025_TEST.json"
        assert json.dumps(result.to_dict())

    def test_validate_without_target_fails(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_scene(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.validate(spec_file)

        assert result.ok is False
        assert result.target is None
        assert len(result.issues) > 0

    def test_audit_with_target_preserves_run_arc_check_behavior(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_arc(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.audit(spec_file, target="SC_020", count=3)

        assert isinstance(result, RepoAuditResult)
        assert result.ok is True
        assert result.target == "SC_020"
        assert json.dumps(result.to_dict())

    def test_audit_without_target_fails(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_arc(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.audit(spec_file)

        assert result.ok is False
        assert result.target is None
        assert len(result.issues) > 0

    def test_preview_returns_preview_result(self, tmp_path: Path) -> None:
        _, spec_file = self._setup_scene(tmp_path)
        adapter = NarrativeRepoControlAdapter()

        result = adapter.preview(spec_file)

        assert isinstance(result, RepoPreviewResult)
        assert result.actions == (
            "repo.status",
            "repo.validate",
            "repo.audit",
            "repo.preview",
        )
        assert json.dumps(result.to_dict())
