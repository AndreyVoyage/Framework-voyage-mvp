"""Frozen non-authoritative result contract (voyage.mcp-read.v1).

Public hash is computed over the redacted payload only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResultKind(StrEnum):
    """Outcome classification for an MCP tool call."""

    REPOSITORY_STATE_SNAPSHOT = "repository_state_snapshot"
    VALIDATION_FINDINGS = "validation_findings"
    TASK_RECORD = "task_record"
    TASK_LIST = "task_list"
    DENIED = "denied"
    ERROR = "error"
    CONFLICT = "conflict"


_AUTHORITATIVE = False
_AUTHORIZATION = "human_required"


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Traceability record for a single data source."""

    source_type: str  # "git_repository" | "task_database" | "external_report"
    source_path: str
    git_commit: str | None = None
    git_branch: str | None = None
    source_canonical: bool = False
    source_status: str = "unknown"  # "current" | "stale" | "draft" | "external_validated" | ...
    staleness_warning: str | None = None


@dataclass(frozen=True, slots=True)
class CallerInfo:
    """Weak caller identity and correlation metadata."""

    operator: str
    client_id: str
    client_auth_strength: str
    session_id: str
    request_id: str
    project_scope: str
    report_scope: str


@dataclass(frozen=True, slots=True)
class MCPResult:
    """Versioned non-authoritative result envelope.

    Fields:
        schema_version: always "voyage.mcp-read.v1"
        tool: tool name
        request_id: UUID v4
        result_kind: one of ResultKind
        authoritative: always False
        authorization: always "human_required" or "not_applicable"
        evidence_complete: whether all expected evidence was collected
        data: tool-specific payload (already redacted)
        sources: provenance list
        redactions: list of redacted field paths
        warnings: non-fatal messages
        errors: error messages (empty on success)
        denials: denial reasons (empty unless denied)
        caller: identity/session metadata
        generated_at: ISO-8601 UTC timestamp
        content_hash: SHA-256 of canonical serialized redacted data
    """

    schema_version: str = "voyage.mcp-read.v1"
    tool: str = ""
    request_id: str = ""
    result_kind: ResultKind = ResultKind.ERROR
    authoritative: bool = _AUTHORITATIVE
    authorization: str = _AUTHORIZATION
    evidence_complete: bool = True
    data: Any = None
    sources: list[SourceProvenance] = field(default_factory=list)
    redactions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    denials: list[dict[str, Any]] = field(default_factory=list)
    caller: CallerInfo | None = None
    generated_at: str = ""
    content_hash: str = ""

    def with_hash(self) -> MCPResult:
        """Return a new MCPResult with content_hash computed over redacted data."""
        raw = json.dumps(
            self.data if self.data is not None else {},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return MCPResult(
            schema_version=self.schema_version,
            tool=self.tool,
            request_id=self.request_id,
            result_kind=self.result_kind,
            authoritative=self.authoritative,
            authorization=self.authorization,
            evidence_complete=self.evidence_complete,
            data=self.data,
            sources=self.sources,
            redactions=self.redactions,
            warnings=self.warnings,
            errors=self.errors,
            denials=self.denials,
            caller=self.caller,
            generated_at=self.generated_at,
            content_hash=digest,
        )


def _validate_schema_version(version: str) -> None:
    if version != "voyage.mcp-read.v1":
        raise ValueError(f"Unsupported schema version: {version!r}; expected 'voyage.mcp-read.v1'")


def tool_result(
    *,
    tool: str,
    request_id: str,
    result_kind: ResultKind,
    data: Any = None,
    sources: list[SourceProvenance] | None = None,
    redactions: list[str] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    denials: list[dict[str, Any]] | None = None,
    caller: CallerInfo | None = None,
    generated_at: str = "",
    evidence_complete: bool = True,
    authorization: str = _AUTHORIZATION,
) -> MCPResult:
    """Factory: build an MCPResult with correct authority semantics."""
    result = MCPResult(
        tool=tool,
        request_id=request_id,
        result_kind=result_kind,
        authoritative=_AUTHORITATIVE,
        authorization=authorization,
        evidence_complete=evidence_complete,
        data=data,
        sources=sources or [],
        redactions=redactions or [],
        warnings=warnings or [],
        errors=errors or [],
        denials=denials or [],
        caller=caller,
        generated_at=generated_at,
    )
    return result.with_hash()
