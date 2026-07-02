"""Unit tests for the generic RepoControlAdapter contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from voyage_framework.core.repo_control_adapter import (
    RepoAuditResult,
    RepoControlAdapter,
    RepoPreviewResult,
    RepoStatusResult,
    RepoValidationResult,
)


class ExampleRepoAdapter(RepoControlAdapter):
    """Synthetic, test-only adapter used to exercise the abstract contract."""

    def status(self, spec_path: str | Path) -> RepoStatusResult:
        return RepoStatusResult(
            command="status",
            ok=True,
            adapter="example",
            repo_path=str(spec_path),
            summary="clean",
            issues=(),
            details={"branch": "main"},
        )

    def validate(self, spec_path: str | Path, target: str | None = None) -> RepoValidationResult:
        return RepoValidationResult(
            command="validate",
            ok=True,
            adapter="example",
            target=target,
            issues=(),
            details={"spec_path": str(spec_path)},
        )

    def audit(
        self,
        spec_path: str | Path,
        target: str | None = None,
        **options: object,
    ) -> RepoAuditResult:
        return RepoAuditResult(
            command="audit",
            ok=True,
            adapter="example",
            target=target,
            issues=(),
            details={"spec_path": str(spec_path), "options": dict(options)},
        )

    def preview(self, spec_path: str | Path) -> RepoPreviewResult:
        return RepoPreviewResult(
            command="preview",
            ok=True,
            adapter="example",
            summary="no-op",
            actions=("noop",),
            issues=(),
            details={"spec_path": str(spec_path)},
        )


class TestRepoStatusResult:
    def test_to_dict_shape(self) -> None:
        result = RepoStatusResult(
            command="status",
            ok=True,
            adapter="example",
            repo_path="/tmp/repo",
            summary="clean",
            issues=("warn",),
            details={"branch": "main"},
        )
        data = result.to_dict()
        assert data == {
            "command": "status",
            "ok": True,
            "adapter": "example",
            "repo_path": "/tmp/repo",
            "summary": "clean",
            "issues": ["warn"],
            "details": {"branch": "main"},
        }

    def test_to_dict_json_serializable(self) -> None:
        result = RepoStatusResult(command="status", ok=True, adapter="example")
        assert json.dumps(result.to_dict())


class TestRepoValidationResult:
    def test_to_dict_shape(self) -> None:
        result = RepoValidationResult(
            command="validate",
            ok=False,
            adapter="example",
            target="file.json",
            issues=("bad field",),
            details={"count": 1},
        )
        data = result.to_dict()
        assert data == {
            "command": "validate",
            "ok": False,
            "adapter": "example",
            "target": "file.json",
            "issues": ["bad field"],
            "details": {"count": 1},
        }

    def test_to_dict_json_serializable(self) -> None:
        result = RepoValidationResult(command="validate", ok=True, adapter="example")
        assert json.dumps(result.to_dict())


class TestRepoAuditResult:
    def test_to_dict_shape(self) -> None:
        result = RepoAuditResult(
            command="audit",
            ok=True,
            adapter="example",
            target="chain",
            issues=(),
            details={"checked": 3},
        )
        data = result.to_dict()
        assert data == {
            "command": "audit",
            "ok": True,
            "adapter": "example",
            "target": "chain",
            "issues": [],
            "details": {"checked": 3},
        }

    def test_to_dict_json_serializable(self) -> None:
        result = RepoAuditResult(command="audit", ok=True, adapter="example")
        assert json.dumps(result.to_dict())


class TestRepoPreviewResult:
    def test_to_dict_shape(self) -> None:
        result = RepoPreviewResult(
            command="preview",
            ok=True,
            adapter="example",
            summary="no-op",
            actions=("a", "b"),
            issues=(),
            details={},
        )
        data = result.to_dict()
        assert data == {
            "command": "preview",
            "ok": True,
            "adapter": "example",
            "summary": "no-op",
            "actions": ["a", "b"],
            "issues": [],
            "details": {},
        }

    def test_to_dict_json_serializable(self) -> None:
        result = RepoPreviewResult(command="preview", ok=True, adapter="example")
        assert json.dumps(result.to_dict())


class TestExampleRepoAdapter:
    def test_status_returns_status_result(self, tmp_path: Path) -> None:
        adapter = ExampleRepoAdapter()
        result = adapter.status(tmp_path / "spec.json")
        assert isinstance(result, RepoStatusResult)
        assert result.ok is True

    def test_validate_returns_validation_result(self, tmp_path: Path) -> None:
        adapter = ExampleRepoAdapter()
        result = adapter.validate(tmp_path / "spec.json", target="file.json")
        assert isinstance(result, RepoValidationResult)
        assert result.target == "file.json"

    def test_audit_returns_audit_result(self, tmp_path: Path) -> None:
        adapter = ExampleRepoAdapter()
        result = adapter.audit(tmp_path / "spec.json", target="chain", count=3)
        assert isinstance(result, RepoAuditResult)
        assert result.details["options"] == {"count": 3}

    def test_preview_returns_preview_result(self, tmp_path: Path) -> None:
        adapter = ExampleRepoAdapter()
        result = adapter.preview(tmp_path / "spec.json")
        assert isinstance(result, RepoPreviewResult)
        assert result.actions == ("noop",)


class TestAbstractEnforcement:
    def test_cannot_instantiate_abstract_adapter_directly(self) -> None:
        with pytest.raises(TypeError):
            RepoControlAdapter()  # type: ignore[abstract]
