"""Immutable startup configuration for the MCP read-only interface.

No server startup, no SDK import, no environment side effects at import time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


class MCPConfigError(Exception):
    """Configuration validation error."""


@dataclass(frozen=True, slots=True)
class Limits:
    """Frozen numeric limits for MCP-READ-01."""

    max_request_bytes: int = 64 * 1024
    max_response_bytes: int = 1 * 1024 * 1024
    max_report_bytes: int = 1 * 1024 * 1024
    max_git_output_bytes: int = 1 * 1024 * 1024
    max_task_rows: int = 100
    max_offset: int = 10_000
    git_timeout_seconds: float = 30.0
    sqlite_timeout_seconds: float = 5.0
    request_timeout_seconds: float = 60.0
    max_concurrent_requests: int = 1
    requests_per_minute: int = 60
    max_audit_event_bytes: int = 64 * 1024
    max_warnings_errors: int = 50
    max_task_id_length: int = 100

    def __post_init__(self) -> None:
        for f in __import__("dataclasses").fields(self):
            value = getattr(self, f.name)
            if isinstance(value, (int, float)) and value <= 0:
                raise MCPConfigError(f"{f.name} must be positive, got {value}")


@dataclass(frozen=True, slots=True)
class MCPConfig:
    """Immutable MCP server configuration.

    Constructed once at startup; all fields are immutable after construction.
    """

    project_root: Path
    report_root: Path
    audit_root: Path
    client_id: str
    enabled: bool = False
    schema_version: str = "voyage.mcp-read.v1"
    limits: Limits = field(default_factory=Limits)

    def __post_init__(self) -> None:
        if not isinstance(self.project_root, Path) or not self.project_root.is_dir():
            raise MCPConfigError(f"project_root must be an existing directory: {self.project_root}")
        if not isinstance(self.report_root, Path) or not self.report_root.is_dir():
            raise MCPConfigError(f"report_root must be an existing directory: {self.report_root}")
        if not isinstance(self.client_id, str) or not self.client_id.strip():
            raise MCPConfigError("client_id must be a non-empty string")
        if self.schema_version != "voyage.mcp-read.v1":
            raise MCPConfigError(f"Unsupported schema_version: {self.schema_version}")


def load_config(
    *,
    project_root: str | None = None,
    report_root: str | None = None,
    audit_root: str | None = None,
    client_id: str | None = None,
    enabled: bool | None = None,
) -> MCPConfig:
    """Build an immutable MCPConfig from explicit arguments and environment.

    Does NOT read .env files, start a server, or import the MCP SDK.
    """
    env_enabled = os.environ.get("VOYAGE_MCP_ENABLED", "").strip()
    effective_enabled = enabled if enabled is not None else (env_enabled == "1")

    effective_client_id = client_id or os.environ.get("VOYAGE_MCP_CLIENT_ID", "").strip()
    if not effective_client_id:
        raise MCPConfigError("client_id is required (set VOYAGE_MCP_CLIENT_ID or pass client_id=)")

    proj = _resolve_root(
        project_root or os.environ.get("VOYAGE_MCP_PROJECT_ROOT"),
        "project_root",
    )
    rep = _resolve_root(
        report_root or os.environ.get("VOYAGE_MCP_REPORT_ROOT"),
        "report_root",
    )
    audit = _resolve_audit_root(audit_root or os.environ.get("VOYAGE_MCP_AUDIT_ROOT"), rep, proj)

    return MCPConfig(
        project_root=proj,
        report_root=rep,
        audit_root=audit,
        client_id=effective_client_id,
        enabled=effective_enabled,
        limits=Limits(),
    )


def _resolve_root(raw: str | None, name: str) -> Path:
    if not raw:
        raise MCPConfigError(f"{name} is required")
    path = Path(raw).resolve()
    if not path.is_dir():
        raise MCPConfigError(f"{name} is not an existing directory: {path}")
    return path


def _resolve_audit_root(raw: str | None, report_root: Path, project_root: Path) -> Path:
    if raw:
        path = Path(raw).resolve()
    else:
        project_id = project_root.resolve().name.lower().replace(" ", "-")
        path = (report_root / "mcp-runtime" / project_id).resolve()
    # Must be outside project root and not under .voyage
    try:
        path.relative_to(project_root)
        raise MCPConfigError(f"audit_root must be outside project_root: {path}")
    except ValueError:
        pass  # Expected — path is outside project_root
    if ".voyage" in path.parts:
        raise MCPConfigError(f"audit_root must not be under .voyage: {path}")
    return path
