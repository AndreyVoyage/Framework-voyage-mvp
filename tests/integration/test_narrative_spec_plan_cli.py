"""Integration tests for the `voyage narrative spec-plan` CLI command."""

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


def _init_repo(path: Path) -> None:
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


def _write_scenario(repo: Path, scene_id: str, version: str = "1.0") -> None:
    scenarios_dir = repo / "scenarios"
    scenarios_dir.mkdir(exist_ok=True)
    (scenarios_dir / f"SCENARIO_{scene_id[-3:]}_TEST.json").write_text(
        json.dumps(_scene(scene_id, version)), encoding="utf-8"
    )


def _write_library(repo: Path, entries: list[dict[str, Any]]) -> None:
    library = {
        "version": "1.0",
        "last_updated": "2026-07-04",
        "total_scenarios": len(entries),
        "scenarios": entries,
    }
    (repo / "scenarios" / "SCENARIO_LIBRARY.json").write_text(json.dumps(library), encoding="utf-8")


def _write_matrix(repo: Path, rows: list[dict[str, Any]]) -> None:
    matrix = {"parameters": {}, "rules": [], "scenarios": rows}
    (repo / "scenarios" / "SCENARIO_MATRIX.json").write_text(json.dumps(matrix), encoding="utf-8")


class TestNarrativeSpecPlanCli:
    def test_spec_plan_success(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = _run(["narrative", "spec-plan", "--repo", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "narrative.spec_plan"
        assert data["ok"] is True
        assert data["read_only"] is True
        assert data["apply_supported"] is False
        assert data["readiness"] == "ready"

    def test_spec_plan_invalid_repo(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"

        result = _run(["narrative", "spec-plan", "--repo", str(missing)])

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["command"] == "narrative.spec_plan"
        assert data["ok"] is False
        assert data.get("error", "")

    def test_spec_plan_finds_inconsistencies(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_scenario(repo, "SC_002")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = _run(["narrative", "spec-plan", "--repo", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["readiness"] == "warnings"
        codes = {f["code"] for f in data["findings"]}
        assert "scenario_missing_library_entry" in codes
        assert "scenario_missing_matrix_reference" in codes
        assert all(a["status"] == "proposal_only" for a in data["proposed_actions"])
        assert all(a["safe_to_apply_automatically"] is False for a in data["proposed_actions"])

    def test_spec_plan_help_mentions_repo(self) -> None:
        result = _run(["narrative", "spec-plan", "--help"])

        assert result.returncode == 0
        assert "--repo" in result.stdout

    def test_existing_inventory_still_works(self, tmp_path: Path) -> None:
        repo = tmp_path / "narrative"
        _init_repo(repo)
        _write_scenario(repo, "SC_001")
        _write_library(repo, [{"id": "SC_001", "file": "scenarios/SCENARIO_001_TEST.json"}])
        _write_matrix(repo, [{"id": "SC_001"}])

        result = _run(["narrative", "inventory", "--repo", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "narrative.inventory"
        assert data["ok"] is True
