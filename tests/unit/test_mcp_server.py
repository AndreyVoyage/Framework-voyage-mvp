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


class TestGracefulShutdownSigint:
    """T96 — graceful shutdown via CTRL_BREAK_EVENT (Windows) or SIGINT (POSIX)."""

    def test_graceful_shutdown_sigint(self, tmp_path: Path) -> None:
        import os
        import signal
        import subprocess
        import sys
        import time

        project = tmp_path / "project"
        project.mkdir()
        (project / ".voyage").mkdir()
        (project / ".voyage" / "tasks.db").write_bytes(b"SQLite format 3\0" + b"\0" * 100)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()
        audit = tmp_path / "audit"
        audit.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["VOYAGE_MCP_ENABLED"] = "1"
        env["VOYAGE_MCP_CLIENT_ID"] = "test-t96"

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "voyage_framework.mcp_read.server",
                "--project-root",
                str(project),
                "--report-root",
                str(report),
                "--audit-root",
                str(audit),
            ],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        try:
            # Wait for startup audit to appear or bounded timeout
            startup_deadline = time.monotonic() + 15
            audit_ready = False
            while time.monotonic() < startup_deadline:
                audit_file = audit / "mcp_audit.jsonl"
                if audit_file.exists() and audit_file.stat().st_size > 0:
                    audit_ready = True
                    break
                if server.poll() is not None:
                    break
                time.sleep(0.1)

            assert audit_ready, "Server did not produce startup audit within timeout"
            assert server.poll() is None, "Server exited prematurely"

            # Send shutdown signal
            if sys.platform == "win32":
                os.kill(server.pid, signal.CTRL_BREAK_EVENT)
            else:
                server.send_signal(signal.SIGINT)

            # Wait for graceful exit
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
                pytest.fail("Server did not exit within timeout after signal")

            # Audit should be flushed (file exists with content)
            assert audit_file.exists(), "Audit file should exist after shutdown"
        finally:
            if server.poll() is None:
                server.kill()
                server.wait(timeout=5)


class TestGracefulShutdownStdinClose:
    """T97 — graceful shutdown via stdin EOF/close."""

    def test_graceful_shutdown_stdin_close(self, tmp_path: Path) -> None:
        import os
        import subprocess
        import sys
        import time

        project = tmp_path / "project"
        project.mkdir()
        (project / ".voyage").mkdir()
        (project / ".voyage" / "tasks.db").write_bytes(b"SQLite format 3\0" + b"\0" * 100)
        _init_git(project)
        report = tmp_path / "reports"
        report.mkdir()
        audit = tmp_path / "audit"
        audit.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["VOYAGE_MCP_ENABLED"] = "1"
        env["VOYAGE_MCP_CLIENT_ID"] = "test-t97"

        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "voyage_framework.mcp_read.server",
                "--project-root",
                str(project),
                "--report-root",
                str(report),
                "--audit-root",
                str(audit),
            ],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            # Wait for startup audit
            startup_deadline = time.monotonic() + 15
            audit_ready = False
            while time.monotonic() < startup_deadline:
                audit_file = audit / "mcp_audit.jsonl"
                if audit_file.exists() and audit_file.stat().st_size > 0:
                    audit_ready = True
                    break
                if server.poll() is not None:
                    break
                time.sleep(0.1)

            assert audit_ready, "Server did not produce startup audit within timeout"
            assert server.poll() is None, "Server exited prematurely"

            # Close stdin to deliver EOF
            if server.stdin is not None:
                server.stdin.close()

            # Wait for graceful exit
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
                pytest.fail("Server did not exit within timeout after stdin close")

            assert audit_file.exists(), "Audit file should exist after shutdown"
        finally:
            if server.poll() is None:
                server.kill()
                server.wait(timeout=5)


def _init_git(project_root: Path) -> None:
    import subprocess

    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    (project_root / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "-m", "init"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
