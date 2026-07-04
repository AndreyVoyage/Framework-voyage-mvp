"""Unit tests for the read-only Narrative spec-plan helper."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from voyage_framework.core.auto_loop import AutoLoopError
from voyage_framework.core.narrative_adapter import narrative_spec_plan


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    result = _git(path, "init", "--initial-branch=main")
    assert result.returncode == 0, result.stderr
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    commit = _git(
        path,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test User",
        "commit",
        "-m",
        "init",
    )
    assert commit.returncode == 0, commit.stderr


def _scene(scene_id: str, version: str = "1.0") -> dict[str, Any]:
    return {
        "id": scene_id,
        "version": version,
        "location": "home",
        "time": "evening",
        "archetype": "none",
        "intensity": 5,
        "risk": 3,
        "duration_minutes": 20,
        "prerequisites": [],
        "flags_required": [],
        "flags_set": [f"{scene_id.lower()}_complete"],
        "choice_points": [],
        "content_rating": "PG-13",
        "safety_notes": "No issues.",
    }


def _write_scenario(repo: Path, scene_id: str, version: str = "1.0") -> Path:
    scenarios_dir = repo / "scenarios"
    scenarios_dir.mkdir(exist_ok=True)
    path = scenarios_dir / f"SCENARIO_{scene_id[-3:]}_TEST.json"
    path.write_text(json.dumps(_scene(scene_id, version)), encoding="utf-8")
    return path


def _write_library(repo: Path, entries: list[dict[str, Any]], total: int | None = None) -> None:
    library = {
        "version": "1.0",
        "last_updated": "2026-07-04",
        "total_scenarios": total if total is not None else len(entries),
        "scenarios": entries,
    }
    (repo / "scenarios" / "SCENARIO_LIBRARY.json").write_text(json.dumps(library), encoding="utf-8")


def _write_matrix(repo: Path, rows: list[dict[str, Any]]) -> None:
    matrix = {
        "parameters": {},
        "rules": [],
        "scenarios": rows,
    }
    (repo / "scenarios" / "SCENARIO_MATRIX.json").write_text(json.dumps(matrix), encoding="utf-8")


class TestNarrativeSpecPlanValid:
    def test_consistent_repo_is_ready(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_scenario(repo, "SC_002")
        _write_library(
            repo,
            [
                {"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json", "name": "One"},
                {"id": "SC_002", "file": "scenarios/SCENARIO_002_TEST.json", "name": "Two"},
            ],
        )
        _write_matrix(
            repo,
            [
                {"id": "SC_001", "title": "One"},
                {"id": "SC_002", "title": "Two"},
            ],
        )

        result = narrative_spec_plan(repo)

        assert result["command"] == "narrative.spec_plan"
        assert result["ok"] is True
        assert result["read_only"] is True
        assert result["apply_supported"] is False
        assert result["inventory"]["scenario_count"] == 2
        assert result["inventory"]["library_present"] is True
        assert result["inventory"]["matrix_present"] is True
        assert result["readiness"] == "ready"
        assert result["findings"] == []
        assert result["proposed_actions"] == []
        assert result["errors"] == []

    def test_result_is_json_serializable(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)
        text = json.dumps(result, indent=2)
        round_tripped = json.loads(text)

        assert round_tripped["command"] == "narrative.spec_plan"


class TestNarrativeSpecPlanLibrary:
    def test_stale_library_entry(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(
            repo,
            [
                {"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"},
                {"id": "SC_999", "file": "scenarios/SCENARIO_999_MISSING.json"},
            ],
        )
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)

        assert result["ok"] is True
        assert result["readiness"] == "warnings"
        finding = next(
            f for f in result["findings"] if f["code"] == "library_entry_missing_scenario"
        )
        assert finding["severity"] == "warning"
        assert "SC_999" in finding["message"]
        action = next(
            a
            for a in result["proposed_actions"]
            if a["action_type"] == "review_remove_stale_library_entry"
        )
        assert action["safe_to_apply_automatically"] is False

    def test_scenario_missing_library_entry(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_scenario(repo, "SC_002")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}, {"id": "SC_002"}])

        result = narrative_spec_plan(repo)

        finding = next(
            f for f in result["findings"] if f["code"] == "scenario_missing_library_entry"
        )
        assert finding["severity"] == "warning"
        assert "SC_002" in finding["message"]
        action = next(
            a for a in result["proposed_actions"] if a["action_type"] == "review_add_library_entry"
        )
        assert action["target_file"] == "scenarios/SCENARIO_LIBRARY.json"
        assert action["safe_to_apply_automatically"] is False

    def test_library_count_drift(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_scenario(repo, "SC_002")
        _write_library(
            repo,
            [
                {"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"},
                {"id": "SC_002", "file": "scenarios/SCENARIO_002_TEST.json"},
            ],
            total=1,
        )
        _write_matrix(repo, [{"id": "SC_001"}, {"id": "SC_002"}])

        result = narrative_spec_plan(repo)

        finding = next(f for f in result["findings"] if f["code"] == "library_count_drift")
        assert finding["severity"] == "warning"
        assert "declares 1" in finding["message"]

    def test_library_missing(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)

        finding = next(f for f in result["findings"] if f["code"] == "library_missing")
        assert finding["severity"] == "warning"


class TestNarrativeSpecPlanMatrix:
    def test_matrix_reference_unknown_scenario(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}, {"id": "SC_999"}])

        result = narrative_spec_plan(repo)

        finding = next(
            f for f in result["findings"] if f["code"] == "matrix_reference_unknown_scenario"
        )
        assert finding["severity"] == "warning"
        assert "SC_999" in finding["message"]

    def test_scenario_missing_matrix_reference(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_scenario(repo, "SC_002")
        _write_library(
            repo,
            [
                {"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"},
                {"id": "SC_002", "file": "scenarios/SCENARIO_002_TEST.json"},
            ],
        )
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)

        finding = next(
            f for f in result["findings"] if f["code"] == "scenario_missing_matrix_reference"
        )
        assert finding["severity"] == "info"
        assert "SC_002" in finding["message"]

    def test_matrix_missing(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])

        result = narrative_spec_plan(repo)

        finding = next(f for f in result["findings"] if f["code"] == "matrix_missing")
        assert finding["severity"] == "warning"


class TestNarrativeSpecPlanScenarioIssues:
    def test_mixed_schema_versions(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001", version="1.0")
        _write_scenario(repo, "SC_002", version="2.0")
        _write_library(
            repo,
            [
                {"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"},
                {"id": "SC_002", "file": "scenarios/SCENARIO_002_TEST.json"},
            ],
        )
        _write_matrix(repo, [{"id": "SC_001"}, {"id": "SC_002"}])

        result = narrative_spec_plan(repo)

        finding = next(f for f in result["findings"] if f["code"] == "schema_version_mixed")
        assert finding["severity"] == "warning"
        assert "1.0" in finding["message"]
        assert "2.0" in finding["message"]

    def test_duplicate_scenario_id(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        (repo / "scenarios" / "SCENARIO_001_DUPLICATE.json").write_text(
            json.dumps(_scene("SC_001")), encoding="utf-8"
        )
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)

        finding = next(f for f in result["findings"] if f["code"] == "duplicate_scenario_id")
        assert finding["severity"] == "warning"
        assert "SC_001" in finding["message"]

    def test_scenario_json_parse_error(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        (repo / "scenarios" / "SCENARIO_002_BROKEN.json").write_text(
            "{ not valid json", encoding="utf-8"
        )
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = narrative_spec_plan(repo)

        assert result["ok"] is True
        finding = next(f for f in result["findings"] if f["code"] == "scenario_json_parse_error")
        assert finding["severity"] == "warning"


class TestNarrativeSpecPlanErrors:
    def test_invalid_repo_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"

        with pytest.raises(AutoLoopError):
            narrative_spec_plan(missing)

    def test_read_only_no_changes(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        before = sorted((repo / "scenarios").rglob("*"))
        narrative_spec_plan(repo)
        after = sorted((repo / "scenarios").rglob("*"))

        assert before == after
