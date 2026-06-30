"""Integration tests for the `voyage narrative` CLI commands."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

CLI = [sys.executable, "-m", "voyage_framework.cli"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

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


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*CLI, *args],
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=_clean_env(),
    )


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


class TestNarrativeCLIHelp:
    def test_narrative_help(self) -> None:
        result = _run(["narrative", "--help"])
        assert result.returncode == 0
        assert "narrative" in result.stdout.lower() or "scene-validate" in result.stdout

    def test_narrative_no_subcommand(self) -> None:
        result = _run(["narrative"])
        assert result.returncode == 1
        assert "scene-validate" in result.stdout

    def test_scene_validate_help(self) -> None:
        result = _run(["narrative", "scene-validate", "--help"])
        assert result.returncode == 0
        assert "--spec" in result.stdout
        assert "--file" in result.stdout

    def test_voyage_help_lists_narrative(self) -> None:
        result = _run(["--help"])
        assert result.returncode == 0
        assert "narrative" in result.stdout


class TestNarrativeSceneValidateCLI:
    def _setup(self, tmp_path: Path) -> tuple[Path, Path]:
        repo = tmp_path / "narrative"
        head = _init_repo(repo)
        (repo / "scenarios").mkdir()
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
        return repo, spec_file

    def test_valid_scene_returns_ok_true(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["json_parse_ok"] is True
        assert data["required_fields_present"] is True
        assert data["voyage_validate_ok"] is True
        assert data["issues"] == []
        assert data["command"] == "scene-validate"

    def test_invalid_json_returns_ok_false(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text("{ bad json }", encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert data["json_parse_ok"] is False

    def test_wrong_path_returns_ok_false(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        (repo / "other").mkdir()
        bad_file = repo / "other" / "file.json"
        bad_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "other/file.json",
            ]
        )

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert data["voyage_validate_ok"] is False

    def test_missing_required_field_returns_ok_false(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scene = _valid_scene()
        del scene["safety_notes"]
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(scene), encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert data["required_fields_present"] is False

    def test_spec_not_found_returns_error_json(self, tmp_path: Path) -> None:
        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(tmp_path / "nonexistent.json"),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert "error" in data

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_output_contains_all_required_keys(self, tmp_path: Path) -> None:
        repo, spec_file = self._setup(tmp_path)
        scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
        scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")

        result = _run(
            [
                "narrative",
                "scene-validate",
                "--spec",
                str(spec_file),
                "--file",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        data = json.loads(result.stdout)
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
        assert required_keys <= set(data.keys())
