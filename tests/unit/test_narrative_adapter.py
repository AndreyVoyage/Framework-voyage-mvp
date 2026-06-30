"""Unit tests for the Narrative source-only scene validation adapter."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from voyage_framework.core.auto_loop import AutoLoopError
from voyage_framework.core.narrative_adapter import validate_scene

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
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "init")
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "fetch", "origin", "+main:refs/remotes/origin/main")
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
