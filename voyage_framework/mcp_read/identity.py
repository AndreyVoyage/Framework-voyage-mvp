"""Local weak identity and session primitives.

Provides operator, client label, session/request correlation IDs.
No cryptographic authentication. No remote identity.
"""

from __future__ import annotations

__all__ = [
    "MCPIdentity",
    "generate_session_id",
    "generate_request_id",
]

import getpass
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

_OS_LEVEL_AUTH_STRENGTH: str = "os_level_same_user"


def _safe_os_user() -> str:
    """Return the OS username, falling back safely."""
    try:
        return getpass.getuser()
    except (ImportError, OSError):
        pass
    try:
        return os.getlogin()
    except OSError:
        pass
    # Last resort — environment-based, but NOT a secret
    for var in ("USERNAME", "USER", "LOGNAME"):
        value = os.environ.get(var, "").strip()
        if value:
            return value
    return "unknown_operator"


def generate_session_id() -> str:
    """Return a UUID v4 session identifier."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Return a UUID v4 request identifier."""
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class MCPIdentity:
    """Local weak identity for a single MCP session.

    Every field is correlation metadata — none are cryptographic credentials.
    """

    operator: str
    client_id: str
    client_auth_strength: str = _OS_LEVEL_AUTH_STRENGTH
    session_id: str = ""
    request_id: str = ""
    project_scope: str = ""
    report_scope: str = ""

    def __post_init__(self) -> None:
        if not self.operator.strip():
            object.__setattr__(self, "operator", _safe_os_user())
        if not self.client_id.strip():
            raise ValueError("client_id must be a non-empty label")

    @classmethod
    def create(
        cls,
        *,
        client_id: str,
        project_root: str | Path,
        report_root: str | Path,
    ) -> MCPIdentity:
        """Factory: populate operator, session id, and scopes."""
        return cls(
            operator=_safe_os_user(),
            client_id=client_id,
            session_id=generate_session_id(),
            project_scope=str(Path(project_root).resolve()),
            report_scope=str(Path(report_root).resolve()),
        )

    def with_request_id(self) -> MCPIdentity:
        """Return a copy with a fresh request_id for each call."""
        return MCPIdentity(
            operator=self.operator,
            client_id=self.client_id,
            client_auth_strength=self.client_auth_strength,
            session_id=self.session_id,
            request_id=generate_request_id(),
            project_scope=self.project_scope,
            report_scope=self.report_scope,
        )
