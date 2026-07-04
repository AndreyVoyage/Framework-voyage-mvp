"""Integration tests for the generic `voyage repo` CLI commands."""

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
        "id": "TEST-REPO-CLI",
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


def _setup_clean(tmp_path: Path) -> Path:
    """Repo + spec only, worktree stays clean (for status/preview)."""
    repo = tmp_path / "narrative"
    head = _init_repo(repo)
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
    return spec_file


def _setup_scene(tmp_path: Path) -> Path:
    repo = tmp_path / "narrative"
    head = _init_repo(repo)
    (repo / "scenarios").mkdir()
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
    scene_file = repo / "scenarios" / "SCENARIO_025_TEST.json"
    scene_file.write_text(json.dumps(_valid_scene()), encoding="utf-8")
    return spec_file


def _setup_arc(tmp_path: Path) -> Path:
    repo = tmp_path / "narrative"
    head = _init_repo(repo)
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(_spec_dict(repo, head)), encoding="utf-8")
    # 6 scenes to match the CLI's default --count of 6 when --count is omitted.
    scenes = [_arc_scene(20 + i) for i in range(6)]
    _write_arc(repo, scenes, start_num=20)
    return spec_file


class TestRepoCLIHelp:
    def test_top_level_help_lists_repo(self) -> None:
        result = _run(["--help"])
        assert result.returncode == 0
        assert "repo" in result.stdout

    def test_repo_help_mentions_adapter_and_narrative(self) -> None:
        result = _run(["repo", "--help"])
        assert result.returncode == 0
        assert "RepoControlAdapter" in result.stdout
        assert "narrative" in result.stdout.lower()

    def test_repo_help_mentions_local_adapter(self) -> None:
        result = _run(["repo", "--help"])
        assert result.returncode == 0
        assert "local" in result.stdout.lower()

    def test_repo_status_help_mentions_adapter_and_spec(self) -> None:
        result = _run(["repo", "status", "--help"])
        assert result.returncode == 0
        assert "--adapter" in result.stdout
        assert "--spec" in result.stdout

    def test_repo_validate_help_mentions_target(self) -> None:
        result = _run(["repo", "validate", "--help"])
        assert result.returncode == 0
        assert "--target" in result.stdout

    def test_repo_audit_help_mentions_count(self) -> None:
        result = _run(["repo", "audit", "--help"])
        assert result.returncode == 0
        assert "--count" in result.stdout

    def test_narrative_help_mentions_compatibility(self) -> None:
        result = _run(["narrative", "--help"])
        assert result.returncode == 0
        assert "compatibility" in result.stdout.lower()
        assert "repo" in result.stdout.lower()


class TestRepoStatusCLI:
    def test_status_returns_ok_true(self, tmp_path: Path) -> None:
        spec_file = _setup_clean(tmp_path)

        result = _run(["repo", "status", "--adapter", "narrative", "--spec", str(spec_file)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.status"
        assert data["ok"] is True
        assert data["adapter"] == "narrative"


class TestRepoPreviewCLI:
    def test_preview_returns_ok_true_with_actions(self, tmp_path: Path) -> None:
        spec_file = _setup_clean(tmp_path)

        result = _run(["repo", "preview", "--adapter", "narrative", "--spec", str(spec_file)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.preview"
        assert data["ok"] is True
        assert data["adapter"] == "narrative"
        assert set(data["actions"]) == {
            "repo.status",
            "repo.validate",
            "repo.audit",
            "repo.preview",
        }


class TestRepoValidateCLI:
    def test_validate_with_target_returns_ok_true(self, tmp_path: Path) -> None:
        spec_file = _setup_scene(tmp_path)

        result = _run(
            [
                "repo",
                "validate",
                "--adapter",
                "narrative",
                "--spec",
                str(spec_file),
                "--target",
                "scenarios/SCENARIO_025_TEST.json",
            ]
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.validate"
        assert data["ok"] is True
        assert data["adapter"] == "narrative"
        assert data["target"] == "scenarios/SCENARIO_025_TEST.json"

    def test_validate_without_target_fails_cleanly(self, tmp_path: Path) -> None:
        spec_file = _setup_scene(tmp_path)

        result = _run(["repo", "validate", "--adapter", "narrative", "--spec", str(spec_file)])

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["command"] == "repo.validate"
        assert data["ok"] is False
        assert len(data["issues"]) > 0


class TestRepoAuditCLI:
    def test_audit_with_target_returns_ok_true(self, tmp_path: Path) -> None:
        spec_file = _setup_arc(tmp_path)

        result = _run(
            [
                "repo",
                "audit",
                "--adapter",
                "narrative",
                "--spec",
                str(spec_file),
                "--target",
                "SC_020",
            ]
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.audit"
        assert data["ok"] is True
        assert data["adapter"] == "narrative"
        assert data["target"] == "SC_020"

    def test_audit_without_target_fails_cleanly(self, tmp_path: Path) -> None:
        spec_file = _setup_arc(tmp_path)

        result = _run(["repo", "audit", "--adapter", "narrative", "--spec", str(spec_file)])

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["command"] == "repo.audit"
        assert data["ok"] is False
        assert len(data["issues"]) > 0

    def test_audit_accepts_count_option(self, tmp_path: Path) -> None:
        spec_file = _setup_arc(tmp_path)

        result = _run(
            [
                "repo",
                "audit",
                "--adapter",
                "narrative",
                "--spec",
                str(spec_file),
                "--target",
                "SC_020",
                "--count",
                "2",
            ]
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True


class TestRepoLocalAdapterCLI:
    def test_local_status_returns_ok_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "local_repo"
        _init_repo(repo)

        result = _run(["repo", "status", "--adapter", "local", "--spec", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.status"
        assert data["ok"] is True
        assert data["adapter"] == "local"

    def test_local_validate_with_target_returns_ok_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "local_repo"
        _init_repo(repo)
        (repo / "file.txt").write_text("data", encoding="utf-8")

        result = _run(
            [
                "repo",
                "validate",
                "--adapter",
                "local",
                "--spec",
                str(repo),
                "--target",
                "file.txt",
            ]
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.validate"
        assert data["ok"] is True
        assert data["adapter"] == "local"
        assert data["target"] == "file.txt"

    def test_local_validate_missing_target_fails_cleanly(self, tmp_path: Path) -> None:
        repo = tmp_path / "local_repo"
        _init_repo(repo)

        result = _run(
            [
                "repo",
                "validate",
                "--adapter",
                "local",
                "--spec",
                str(repo),
                "--target",
                "missing.txt",
            ]
        )

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["command"] == "repo.validate"
        assert data["ok"] is False
        assert len(data["issues"]) > 0

    def test_local_audit_returns_ok_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "local_repo"
        _init_repo(repo)

        result = _run(["repo", "audit", "--adapter", "local", "--spec", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.audit"
        assert data["ok"] is True
        assert data["adapter"] == "local"
        assert data["details"]["tracked_file_count"] >= 1

    def test_local_preview_returns_ok_true(self, tmp_path: Path) -> None:
        repo = tmp_path / "local_repo"
        _init_repo(repo)

        result = _run(["repo", "preview", "--adapter", "local", "--spec", str(repo)])

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["command"] == "repo.preview"
        assert data["ok"] is True
        assert data["adapter"] == "local"
        assert data["details"]["read_only"] is True


class TestRepoUnknownAdapterCLI:
    def test_unknown_adapter_fails_cleanly(self, tmp_path: Path) -> None:
        spec_file = _setup_scene(tmp_path)

        result = _run(["repo", "status", "--adapter", "unknown", "--spec", str(spec_file)])

        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert "unknown" in data["error"].lower()
