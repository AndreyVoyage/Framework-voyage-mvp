"""Unit tests for server startup, shutdown, and transport constraints (T90-T97)."""

from __future__ import annotations

from pathlib import Path

import pytest

from voyage_framework.mcp_read.config import MCPConfig, MCPConfigError
from voyage_framework.mcp_read.server import create_server


class TestServerDisabled:
    """T90 — server refuses to start when disabled."""

    def test_disabled_by_default_raises(self, tmp_path: Path) -> None:
        config = MCPConfig(
            project_root=tmp_path,
            report_root=tmp_path,
            audit_root=tmp_path / "audit",
            client_id="test-client",
            enabled=False,
        )
        with pytest.raises(RuntimeError, match="disabled"):
            create_server(config)


class TestServerEnabled:
    """T91 — server starts when enabled with valid configuration."""

    def test_enabled_creates_server(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".voyage").mkdir()
        (project / ".voyage" / "tasks.db").write_bytes(b"SQLite format 3\0" + b"\0" * 100)
        report = tmp_path / "reports"
        report.mkdir()

        config = MCPConfig(
            project_root=project,
            report_root=report,
            audit_root=tmp_path / "audit",
            client_id="test-client",
            enabled=True,
        )
        server, runtime = create_server(config)
        assert server is not None
        assert runtime is not None


class TestRefuseMissingRoots:
    """T92, T93 — server refuses missing project/report root."""

    def test_refuse_missing_project_root(self, tmp_path: Path) -> None:
        with pytest.raises(MCPConfigError, match="project_root must be an existing directory"):
            MCPConfig(
                project_root=tmp_path / "nonexistent",
                report_root=tmp_path,
                audit_root=tmp_path / "audit",
                client_id="test-client",
                enabled=True,
            )

    def test_refuse_missing_report_root(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".voyage").mkdir()
        (project / ".voyage" / "tasks.db").write_bytes(b"SQLite format 3\0" + b"\0" * 100)
        with pytest.raises(MCPConfigError, match="report_root must be an existing directory"):
            MCPConfig(
                project_root=project,
                report_root=tmp_path / "nonexistent_reports",
                audit_root=tmp_path / "audit",
                client_id="test-client",
                enabled=True,
            )


class TestNoNetworkListener:
    """T94 — server does not open a network listener."""

    def test_no_network_socket_in_server_code(self) -> None:
        """AST / code inspection: no socket/HTTP imports."""
        import ast

        src = Path(__file__).parents[2] / "voyage_framework" / "mcp_read" / "server.py"
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("socket", "http", "urllib", "aiohttp"), (
                        f"forbidden import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in ("socket", "http", "urllib", "aiohttp"), (
                    f"forbidden import: {node.module}"
                )


class TestStdioOnly:
    """T95 — only stdio transport is used."""

    def test_stdio_only_import(self) -> None:
        import ast

        src = Path(__file__).parents[2] / "voyage_framework" / "mcp_read" / "server.py"
        tree = ast.parse(src.read_text())
        has_stdio = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "mcp.server.stdio":
                has_stdio = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "mcp.server.stdio":
                        has_stdio = True
        assert has_stdio, "no stdio import found — server must use stdio"


class TestServerImportSideEffects:
    """Server import must not start the server or open stdio."""

    def test_import_does_not_start(self) -> None:
        """Module-level import is safe."""
        from voyage_framework.mcp_read import server as _server

        assert _server.create_server is not None
        assert _server.main is not None
