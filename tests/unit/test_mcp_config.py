from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from voyage_framework.mcp_read.config import Limits, MCPConfig, MCPConfigError, load_config


def test_limits_defaults():
    limits = Limits()
    assert limits.max_task_rows == 100
    assert limits.requests_per_minute == 60
    assert limits.git_timeout_seconds == 30.0


def test_limits_rejects_nonpositive():
    with pytest.raises(MCPConfigError):
        Limits(max_request_bytes=0)


def test_config_immutable():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "proj").mkdir()
        (root / "reports").mkdir()
        cfg = MCPConfig(
            project_root=root / "proj",
            report_root=root / "reports",
            audit_root=root / "audit",
            client_id="test",
        )
        with pytest.raises(Exception):  # noqa: B017
            cfg.project_root = Path("/other")  # type: ignore[misc]


def test_config_rejects_missing_dirs():
    with pytest.raises(MCPConfigError):
        MCPConfig(
            project_root=Path("/nonexistent/proj"),
            report_root=Path("/nonexistent/reports"),
            audit_root=Path("/nonexistent/audit"),
            client_id="test",
        )


def test_config_rejects_empty_client_id():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "proj").mkdir()
        (root / "reports").mkdir()
        with pytest.raises(MCPConfigError):
            MCPConfig(
                project_root=root / "proj",
                report_root=root / "reports",
                audit_root=root / "audit",
                client_id="   ",
            )


def test_load_config_disabled_by_default(monkeypatch):
    monkeypatch.delenv("VOYAGE_MCP_ENABLED", raising=False)
    monkeypatch.setenv("VOYAGE_MCP_CLIENT_ID", "test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj = root / "proj"
        rep = root / "reports"
        proj.mkdir()
        rep.mkdir()
        monkeypatch.setenv("VOYAGE_MCP_PROJECT_ROOT", str(proj))
        monkeypatch.setenv("VOYAGE_MCP_REPORT_ROOT", str(rep))
        cfg = load_config()
        assert cfg.enabled is False


def test_load_config_audit_root_outside_project(monkeypatch):
    monkeypatch.setenv("VOYAGE_MCP_ENABLED", "1")
    monkeypatch.setenv("VOYAGE_MCP_CLIENT_ID", "test")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj = root / "proj"
        rep = root / "reports"
        proj.mkdir()
        rep.mkdir()
        monkeypatch.setenv("VOYAGE_MCP_PROJECT_ROOT", str(proj))
        monkeypatch.setenv("VOYAGE_MCP_REPORT_ROOT", str(rep))
        monkeypatch.setenv("VOYAGE_MCP_AUDIT_ROOT", str(rep / "mcp-runtime" / "test-proj"))
        cfg = load_config()
        # Audit root must be outside project root
        with pytest.raises(ValueError):
            cfg.audit_root.relative_to(proj)
