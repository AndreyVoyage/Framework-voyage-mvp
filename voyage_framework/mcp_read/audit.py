"""External append-only operational audit writer.

Writes JSONL outside the repository and .voyage.  Fail-closed on any write error.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditError(Exception):
    """Raised when audit writing fails."""


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Single MCP audit event (voyage.mcp-audit.v1).

    Contains only metadata and classifications — never raw secrets,
    raw request bodies, raw report content, or raw task data.
    """

    event_schema: str = "voyage.mcp-audit.v1"
    event_id: str = ""
    timestamp: str = ""
    session_id: str = ""
    request_id: str = ""
    operator: str = ""
    client_id: str = ""
    tool: str = ""
    project_scope: str = ""
    report_scope: str = ""
    input_classification: dict[str, Any] = field(default_factory=dict)
    sources_accessed: list[str] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    result_kind: str = ""
    decision: str = "denied"
    duration_ms: float = 0.0
    output_size_bytes: int = 0
    warnings: list[str] = field(default_factory=list)
    error_class: str | None = None


class AuditWriter:
    """Append-only JSONL audit writer for an external audit directory.

    Creates the directory on first use.  Fails closed on any I/O error.
    Single-process writer only — no locking.
    """

    def __init__(self, audit_dir: str | Path, *, max_event_bytes: int = 64 * 1024) -> None:
        self._dir = Path(audit_dir).resolve()
        self._max_event_bytes = max_event_bytes
        self._file: Path | None = None
        self._validate_outside_project()

    # ── public API ──────────────────────────────────────────────────────

    def write_event(self, event: AuditEvent) -> None:
        """Append one event to the audit log.  Fails closed."""
        line = json.dumps(asdict(event), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if len(line.encode("utf-8")) > self._max_event_bytes:
            raise AuditError(f"Audit event exceeds max size ({self._max_event_bytes} bytes)")
        path = self._ensure_file()
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as exc:
            raise AuditError(f"Audit write failed: {exc}") from exc

    # ── internal ─────────────────────────────────────────────────────────

    def _ensure_file(self) -> Path:
        if self._file is not None:
            return self._file
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / "mcp_audit.jsonl"
        # Probe append
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except OSError as exc:
            raise AuditError(f"Cannot open audit file for append: {exc}") from exc
        self._file = path
        return path

    def _validate_outside_project(self) -> None:
        # The caller must supply an external path; we cannot enumerate all projects.
        # Reject any path under .voyage as a safety net.
        if ".voyage" in self._dir.parts:
            raise AuditError(f"audit_dir must not be under .voyage: {self._dir}")


# ── factory helpers ──────────────────────────────────────────────────────


def write_startup_event(
    writer: AuditWriter,
    *,
    session_id: str,
    operator: str,
    client_id: str,
    project_scope: str,
    report_scope: str,
) -> None:
    """Write a session_started event at server startup."""
    writer.write_event(
        AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            session_id=session_id,
            operator=operator,
            client_id=client_id,
            tool="__startup__",
            project_scope=project_scope,
            report_scope=report_scope,
            decision="session_started",
        )
    )
