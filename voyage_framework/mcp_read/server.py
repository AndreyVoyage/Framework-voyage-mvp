"""Slice 3: Low-level MCP stdio server entrypoint.

Usage:
    python -m voyage_framework.mcp_read.server \
        --project-root <dir> --report-root <dir> [--audit-root <dir>]
"""

from __future__ import annotations

import asyncio
import sys

# ── SDK imports (parent process only) ──────────────────────────────────
import mcp.server.stdio  # noqa: E402
from mcp.server.lowlevel import Server  # noqa: E402

# ── Voyage imports ─────────────────────────────────────────────────────
from voyage_framework.mcp_read.config import MCPConfig, MCPConfigError, load_config
from voyage_framework.mcp_read.tools import ToolRuntime, register_tools, shutdown


def create_server(config: MCPConfig) -> tuple[Server, ToolRuntime]:
    """Build the MCP low-level Server, register tools, and return it.

    Does NOT start the transport.
    """
    if not config.enabled:
        raise RuntimeError("Voyage MCP server is disabled. Set VOYAGE_MCP_ENABLED=1 to enable.")

    # Verify project root and task DB
    project_root = config.project_root.resolve()
    if not project_root.is_dir():
        raise MCPConfigError(f"project_root not found: {project_root}")
    task_db = project_root / ".voyage" / "tasks.db"
    if not task_db.is_file():
        raise MCPConfigError(f"Task database not found: {task_db}")

    # Verify report root
    report_root = config.report_root.resolve()
    if not report_root.is_dir():
        raise MCPConfigError(f"report_root not found: {report_root}")

    # Create audit root (auto-create)
    audit_root = config.audit_root.resolve()
    audit_root.mkdir(parents=True, exist_ok=True)

    # Build server
    server = Server(
        name="voyage-mcp-read",
        version="4.3.0",
    )

    # Register tools
    runtime = ToolRuntime()
    register_tools(server, runtime, config)

    return server, runtime


def main() -> int:
    """Parse args, build config, create server, and enter stdio loop."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="voyage-mcp-read",
        description="Voyage Framework MCP-READ-01 read-only tool server",
    )
    parser.add_argument("--project-root", help="Path to Voyage project worktree")
    parser.add_argument("--report-root", help="Path to external report directory")
    parser.add_argument("--audit-root", help="Path to external audit directory")
    args = parser.parse_args()

    try:
        config = load_config(
            project_root=args.project_root,
            report_root=args.report_root,
            audit_root=args.audit_root,
        )
    except MCPConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    server, runtime = create_server(config)

    # SIGINT / CTRL_BREAK handling for graceful stdio shutdown
    async def _serve() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        pass
    finally:
        shutdown(runtime)

    return 0


if __name__ == "__main__":
    sys.exit(main())
