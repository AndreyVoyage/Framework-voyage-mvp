"""Unit tests for LocalRepoControlAdapter.

Tests use synthetic git repositories only. They never touch the Framework or
Narrative product repos and never perform any writes outside the temporary
repository roots created by pytest.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from voyage_framework.core.local_repo_adapter import LocalRepoControlAdapter
from voyage_framework.core.repo_control_adapter import (
    RepoAuditResult,
    RepoControlAdapter,
    RepoPreviewResult,
    RepoStatusResult,
    RepoValidationResult,
)


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
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "update-ref", "refs/remotes/origin/main", "HEAD")


@pytest.fixture
def adapter() -> LocalRepoControlAdapter:
    return LocalRepoControlAdapter()


class TestLocalRepoControlAdapterContract:
    def test_is_repo_control_adapter(self, adapter: LocalRepoControlAdapter) -> None:
        assert isinstance(adapter, RepoControlAdapter)

    def test_methods_return_typed_results(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        assert isinstance(adapter.status(repo), RepoStatusResult)
        assert isinstance(adapter.validate(repo), RepoValidationResult)
        assert isinstance(adapter.audit(repo), RepoAuditResult)
        assert isinstance(adapter.preview(repo), RepoPreviewResult)


class TestLocalRepoControlAdapterStatus:
    def test_clean_repo_ok_true(self, adapter: LocalRepoControlAdapter, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.status(repo)

        assert result.command == "repo.status"
        assert result.ok is True
        assert result.adapter == "local"
        assert result.repo_path == str(repo.resolve())
        assert result.summary is not None
        assert "main" in result.summary
        assert "clean" in result.summary
        assert result.issues == ()

    def test_dirty_repo_reports_dirty(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "dirty.txt").write_text("x", encoding="utf-8")

        result = adapter.status(repo)

        assert result.ok is True
        assert result.summary is not None
        assert "dirty" in result.summary

    def test_non_git_repo_reports_error(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        not_repo = tmp_path / "not_a_repo"
        not_repo.mkdir()

        result = adapter.status(not_repo)

        assert result.ok is False
        assert any("not a git repository" in issue.lower() for issue in result.issues)


class TestLocalRepoControlAdapterValidate:
    def test_validate_without_target_ok(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.validate(repo)

        assert result.command == "repo.validate"
        assert result.ok is True
        assert result.adapter == "local"
        assert result.target is None
        assert result.issues == ()
        assert result.details["is_git_repo"] is True

    def test_validate_with_existing_target_ok(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / "file.txt").write_text("data", encoding="utf-8")

        result = adapter.validate(repo, target="file.txt")

        assert result.ok is True
        assert result.target == "file.txt"
        assert result.issues == ()

    def test_validate_missing_target(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.validate(repo, target="missing.txt")

        assert result.ok is False
        assert any("target not found" in issue for issue in result.issues)

    def test_validate_traversal_target(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (tmp_path / "outside.txt").write_text("x", encoding="utf-8")

        result = adapter.validate(repo, target="../outside.txt")

        assert result.ok is False
        assert any("resolves outside repo" in issue for issue in result.issues)


class TestLocalRepoControlAdapterAudit:
    def test_audit_clean_repo_ok(self, adapter: LocalRepoControlAdapter, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.audit(repo)

        assert result.command == "repo.audit"
        assert result.ok is True
        assert result.adapter == "local"
        assert result.details["tracked_file_count"] >= 1
        assert "README.md" in result.details["sample_tracked_files"]
        assert result.details["changed_file_count"] == 0
        assert result.details["untracked_file_count"] == 0

    def test_audit_options_preserved_in_details(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.audit(repo, target="README.md", count=3)

        assert result.details["target"] == "README.md"
        assert result.details["options"] == {"count": 3}

    def test_audit_warns_on_tracked_forbidden_file(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)
        (repo / ".env").write_text("secret\n", encoding="utf-8")
        _git(repo, "add", ".env")
        commit = _git(
            repo,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "add env",
        )
        assert commit.returncode == 0, commit.stderr

        result = adapter.audit(repo)

        assert result.ok is True
        assert ".env" in result.details["forbidden_matches"]
        assert any("forbidden patterns" in issue for issue in result.issues)


class TestLocalRepoControlAdapterPreview:
    def test_preview_returns_read_only_plan(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        result = adapter.preview(repo)

        assert result.command == "repo.preview"
        assert result.ok is True
        assert result.adapter == "local"
        assert result.summary == "read-only plan; no mutations"
        assert result.actions == (
            "repo.status",
            "repo.validate",
            "repo.audit",
            "repo.preview",
        )
        assert result.details["read_only"] is True


class TestLocalRepoControlAdapterSerialization:
    def test_results_are_json_serializable(
        self, adapter: LocalRepoControlAdapter, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        _init_repo(repo)

        payload = {
            "status": adapter.status(repo).to_dict(),
            "validate": adapter.validate(repo, target="README.md").to_dict(),
            "audit": adapter.audit(repo).to_dict(),
            "preview": adapter.preview(repo).to_dict(),
        }

        text = json.dumps(payload, indent=2)
        round_tripped = json.loads(text)

        assert round_tripped["status"]["adapter"] == "local"
        assert round_tripped["validate"]["adapter"] == "local"
        assert round_tripped["audit"]["adapter"] == "local"
        assert round_tripped["preview"]["adapter"] == "local"


class TestLocalRepoControlAdapterCoupling:
    def test_module_has_no_narrative_imports(self) -> None:
        import voyage_framework.core.local_repo_adapter as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "narrative" not in source.lower()
