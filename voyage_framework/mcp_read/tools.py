"""Slice 3: Four non-authoritative read-only MCP tools with spawn-worker isolation.

Imported by the parent server process (imports MCP types) and by the child
worker (must NOT import MCP SDK — imports only service modules via local imports
in the child entrypoint).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from multiprocessing import Pipe, Process, get_context
from pathlib import Path
from typing import Any

# ── lightweight top-level imports (safe for child import) ────────────
from voyage_framework.mcp_read.config import Limits, MCPConfig
from voyage_framework.mcp_read.confinement import validate_report_id

# ═══════════════════════════════════════════════════════════════════════
# Worker operation enum
# ═══════════════════════════════════════════════════════════════════════


class WorkerOperation(StrEnum):
    PROJECT_STATUS = "project_status"
    VALIDATE_REPORT = "validate_report"
    GET_TASK = "get_task"
    LIST_TASKS = "list_tasks"


# ═══════════════════════════════════════════════════════════════════════
# Tool schemas
# ═══════════════════════════════════════════════════════════════════════

_VALID_STATUSES = frozenset(
    {"pending", "in_progress", "blocked", "completed", "failed", "archived"}
)
_VALID_ROLES = frozenset(
    {
        "developer",
        "architect",
        "reviewer",
        "devops",
        "qa",
        "security",
        "data",
        "designer",
        "writer",
        "pm",
        "product",
        "researcher",
        "analyst",
        "tester",
        "maintainer",
        "contributor",
        "operator",
        "auditor",
        "observer",
        "mentor",
    }
)

_TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "project_status",
        "description": (
            "Return a read-only repository state snapshot from the local Git "
            "worktree. No network verification is performed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "validate_report",
        "description": (
            "Validate a structured Voyage report (voyage.report.v1) against "
            "current local Git facts. Accepts a report basename only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "report_id": {
                    "type": "string",
                    "description": "Report basename ending in .json",
                    "maxLength": 200,
                },
            },
            "required": ["report_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_task",
        "description": "Look up a single task by its canonical ID (VF-… or ST-…).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Canonical task ID (VF-### or ST-###)",
                    "maxLength": 100,
                    "pattern": "^(?:VF|ST)-\\d{3,}$",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks with optional status/role filters and pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": sorted(_VALID_STATUSES),
                    "description": "Filter by task status",
                },
                "role": {
                    "type": "string",
                    "enum": sorted(_VALID_ROLES),
                    "description": "Filter by task role",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 50,
                    "description": "Maximum items to return (1-100)",
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10000,
                    "default": 0,
                    "description": "Number of items to skip",
                },
            },
            "additionalProperties": False,
        },
    },
]

_TOOL_NAMES = frozenset(t["name"] for t in _TOOL_DEFS)


# ═══════════════════════════════════════════════════════════════════════
# Child-worker contract (worker runs this function)
# ═══════════════════════════════════════════════════════════════════════


def _child_target(
    conn: Any,
    operation: WorkerOperation,
    project_root: Path,
    report_root: Path,
    arguments: dict[str, object],
    limits_dict: dict[str, Any],
) -> None:
    """Spawned child entrypoint — imports service modules locally only."""
    import io
    import traceback

    # Redirect stdio to devnull
    try:
        null_fd = os.open(os.devnull, os.O_RDWR)
        os.dup2(null_fd, 0)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
        os.close(null_fd)
    except OSError:
        pass

    limits = Limits()
    for key in (
        "max_git_output_bytes",
        "git_timeout_seconds",
        "sqlite_timeout_seconds",
        "max_task_rows",
        "max_offset",
        "max_task_id_length",
    ):
        if key in limits_dict:
            object.__setattr__(limits, key, limits_dict[key])

    parent_deadline = float(limits_dict.get("execution_budget_seconds", 58))
    deadline = time.monotonic() + min(parent_deadline, 55)

    # Adjust Git/SQLite timeouts under the remaining budget
    remaining = max(deadline - time.monotonic(), 0.1)
    object.__setattr__(
        limits, "git_timeout_seconds", min(limits.git_timeout_seconds, remaining / 5)
    )
    object.__setattr__(
        limits, "sqlite_timeout_seconds", min(limits.sqlite_timeout_seconds, remaining)
    )

    child_result: dict[str, Any] = {}
    try:
        if operation == WorkerOperation.PROJECT_STATUS:
            from voyage_framework.mcp_read.git_read import git_read_state  # noqa: E402

            child_result = dict(git_read_state(project_root, limits))
        elif operation == WorkerOperation.VALIDATE_REPORT:
            from voyage_framework.mcp_read.report_read import report_read_and_validate  # noqa: E402

            report_id = str(arguments.get("report_id", ""))
            child_result = dict(
                report_read_and_validate(report_id, project_root, report_root, limits)
            )
        elif operation == WorkerOperation.GET_TASK:
            from voyage_framework.mcp_read.task_read import TaskReadFacade  # noqa: E402

            facade = TaskReadFacade(project_root, limits)
            task_id = str(arguments.get("task_id", ""))
            row = facade.get(task_id)
            child_result = {"found": row is not None, "data": row}
        elif operation == WorkerOperation.LIST_TASKS:
            from voyage_framework.mcp_read.task_read import TaskReadFacade  # noqa: E402

            facade = TaskReadFacade(project_root, limits)
            filt_status: str | None = arguments.get("status")  # type: ignore[assignment]
            filt_role: str | None = arguments.get("role")  # type: ignore[assignment]
            raw_limit = arguments.get("limit", 50)
            raw_offset = arguments.get("offset", 0)
            task_limit = int(raw_limit) if isinstance(raw_limit, (int, float)) else 50
            task_offset = int(raw_offset) if isinstance(raw_offset, (int, float)) else 0
            rows, total = facade.list(
                status=filt_status, role=filt_role, limit=task_limit, offset=task_offset
            )
            child_result = {
                "items": rows,
                "total_count": total,
                "limit": task_limit,
                "offset": task_offset,
                "returned": len(rows),
                "truncated": len(rows) < total,
            }
        else:
            child_result = {"error": "unknown_operation"}

        # Serialize bounded canonical JSON
        payload = json.dumps(
            {"ok": True, "result": child_result}, ensure_ascii=False, separators=(",", ":")
        )
        payload_bytes = payload.encode("utf-8")
        if len(payload_bytes) > 1_048_576:
            payload_bytes = json.dumps(
                {"ok": True, "result": {"error": "child_oversized_response"}},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        conn.send_bytes(payload_bytes)
    except Exception:
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        error_payload = json.dumps(
            {
                "ok": False,
                "error_code": "child_execution_failed",
                "error_detail": buf.getvalue()[:1024],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        with contextlib.suppress(Exception):
            conn.send_bytes(error_payload.encode("utf-8"))
    finally:
        with contextlib.suppress(Exception):
            conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Parent runtime
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ToolRuntime:
    """Mutable per-request orchestration state."""

    _active_child: Process | None = None
    _active_pipe: Any = None
    _active_deadline: float = 0.0
    _job_handle: object | None = None  # Windows Job Object handle


def _validate_tool_arguments(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, object]:
    """Validate tool arguments against the frozen schema. Returns normalized dict."""
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be a JSON object")

    # Reject additional properties for all tools
    expected = set(_TOOL_DEFS[0]["inputSchema"]["properties"])
    for td in _TOOL_DEFS:
        if td["name"] == tool_name:
            expected = set(td["inputSchema"]["properties"])
            break
    extra = set(arguments.keys()) - expected
    if extra:
        raise ValueError(f"Unknown arguments: {sorted(extra)}")

    if tool_name == "project_status":
        return {}

    if tool_name == "validate_report":
        report_id = arguments.get("report_id")
        if not isinstance(report_id, str) or not report_id:
            raise ValueError("report_id must be a non-empty string")
        if len(report_id) > 200:
            raise ValueError("report_id exceeds max length")
        if not validate_report_id(report_id):
            raise ValueError("report_id contains invalid characters")
        if not report_id.lower().endswith(".json"):
            raise ValueError("report_id must end with .json")
        return {"report_id": report_id}

    if tool_name == "get_task":
        task_id = arguments.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")
        if len(task_id) > 100:
            raise ValueError("task_id exceeds max length")
        import re

        if not re.fullmatch(r"^(?:VF|ST)-\d{3,}$", task_id):
            raise ValueError("task_id must match VF-### or ST-###")
        if any(ord(c) < 32 or ord(c) == 127 for c in task_id):
            raise ValueError("task_id contains control characters")
        return {"task_id": task_id}

    if tool_name == "list_tasks":
        normalized: dict[str, Any] = {}
        if "status" in arguments:
            status = arguments["status"]
            if not isinstance(status, str) or status not in _VALID_STATUSES:
                raise ValueError(f"status must be one of: {sorted(_VALID_STATUSES)}")
            normalized["status"] = status
        if "role" in arguments:
            role = arguments["role"]
            if not isinstance(role, str) or role not in _VALID_ROLES:
                raise ValueError(f"role must be one of: {sorted(_VALID_ROLES)}")
            normalized["role"] = role
        limit = arguments.get("limit", 50)
        if isinstance(limit, (int, float)) and not isinstance(limit, bool):
            normalized["limit"] = int(min(max(int(limit), 1), 100))
        else:
            normalized["limit"] = 50
        offset = arguments.get("offset", 0)
        if isinstance(offset, (int, float)) and not isinstance(offset, bool):
            normalized["offset"] = int(min(max(int(offset), 0), 10000))
        else:
            normalized["offset"] = 0
        return normalized

    raise ValueError(f"Unknown tool: {tool_name}")


def register_tools(server: Any, runtime: ToolRuntime, config: MCPConfig) -> None:
    """Register the four tools on a low-level MCP Server instance.

    Uses ``@server.list_tools()`` and ``@server.call_tool()`` decorators.
    Applies rate-limit, schema validation, worker supervision, redaction,
    hash, audit, and response-size enforcement.
    """
    import mcp.types as types  # noqa: E402

    from voyage_framework.mcp_read.audit import AuditWriter  # noqa: E402
    from voyage_framework.mcp_read.identity import MCPIdentity, generate_request_id  # noqa: E402

    # Create runtime components (once per server, not per request)
    identity = MCPIdentity.create(
        client_id=config.client_id,
        project_root=config.project_root,
        report_root=config.report_root,
    )
    audit = AuditWriter(config.audit_root, max_event_bytes=config.limits.max_audit_event_bytes)
    from voyage_framework.mcp_read.audit import write_startup_event  # noqa: E402

    write_startup_event(
        audit,
        session_id=identity.session_id,
        operator=identity.operator,
        client_id=identity.client_id,
        project_scope=identity.project_scope,
        report_scope=identity.report_scope,
    )

    # Token bucket rate limiter
    rate_state = {"last_time": time.monotonic(), "tokens": float(config.limits.requests_per_minute)}
    rate_lock = asyncio.Lock()
    concurrency_sem = asyncio.Semaphore(1)

    @server.list_tools()  # type: ignore[untyped-decorator]
    async def _list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in _TOOL_DEFS
        ]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def _call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        request_id = generate_request_id()
        call_identity = identity.with_request_id()
        start_time = time.monotonic()

        # Validate tool name
        if name not in _TOOL_NAMES:
            return _denied_response(f"Unknown tool: {name}", request_id, name, start_time)

        # Validate arguments
        try:
            normalized = _validate_tool_arguments(name, arguments)
        except ValueError as exc:
            return _denied_response(str(exc), request_id, name, start_time)

        # Rate limit
        async with rate_lock:
            now = time.monotonic()
            elapsed = now - rate_state["last_time"]
            rate_state["tokens"] = min(
                float(config.limits.requests_per_minute),
                rate_state["tokens"] + elapsed * (config.limits.requests_per_minute / 60.0),
            )
            rate_state["last_time"] = now
            if rate_state["tokens"] < 1.0:
                retry_sec = int(60.0 / config.limits.requests_per_minute)
                return _denied_response(
                    f"Rate limit exceeded, retry after {retry_sec}s",
                    request_id,
                    name,
                    start_time,
                )
            rate_state["tokens"] -= 1.0

        # Concurrency
        if concurrency_sem.locked():
            return _denied_response("Server busy", request_id, name, start_time)

        async with concurrency_sem:
            return await _execute_tool(
                name,
                normalized,
                request_id,
                call_identity,
                config,
                runtime,
                audit,
                start_time,
            )


async def _execute_tool(
    name: str,
    normalized: dict[str, object],
    request_id: str,
    identity: Any,
    config: MCPConfig,
    runtime: ToolRuntime,
    audit: Any,
    start_time: float,
) -> list[Any]:
    """Spawn one worker, supervise it, build the redacted/hashed/audited result."""
    import mcp.types as types  # noqa: E402

    from voyage_framework.mcp_read.result import (  # noqa: E402
        CallerInfo,
        ResultKind,
        SourceProvenance,
        tool_result,
    )

    result_kind = ResultKind.ERROR
    data: Any = None
    sources: list[SourceProvenance] = []
    warnings: list[str] = []
    errors: list[str] = []
    denials: list[dict[str, Any]] = []
    decision = "error"

    try:
        # Determine operation
        operation = WorkerOperation(name)

        # Build parent_conn, child_conn (duplex=False — one-way each direction)
        parent_conn, child_conn = Pipe(duplex=False)

        # Build canonical JSON request for the child
        child_request = json.dumps(
            {
                "operation": operation.value,
                "project_root": str(config.project_root),
                "report_root": str(config.report_root),
                "limits": {
                    k: getattr(config.limits, k)
                    for k in (
                        "max_git_output_bytes",
                        "git_timeout_seconds",
                        "sqlite_timeout_seconds",
                        "max_task_rows",
                        "max_offset",
                        "max_task_id_length",
                    )
                },
                "arguments": normalized,
                "execution_budget_seconds": 58,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(child_request) > 65536:
            raise RuntimeError("child_request_oversized")

        # Spawn worker
        ctx = get_context("spawn")
        proc = ctx.Process(
            target=_child_target,
            args=(
                child_conn,
                operation,
                config.project_root,
                config.report_root,
                normalized,
                {
                    k: getattr(config.limits, k)
                    for k in (
                        "max_git_output_bytes",
                        "git_timeout_seconds",
                        "sqlite_timeout_seconds",
                        "max_task_rows",
                        "max_offset",
                        "max_task_id_length",
                    )
                },
            ),
        )
        proc.start()
        child_conn.close()
        runtime._active_child = proc  # type: ignore[assignment]
        runtime._active_pipe = parent_conn
        runtime._active_deadline = time.monotonic() + 60.0

        # Send request to child
        parent_conn.send_bytes(child_request)

        # Poll for response with monotonic deadline
        deadline = runtime._active_deadline
        response_bytes: bytes | None = None
        while time.monotonic() < deadline:
            if parent_conn.poll(0):
                response_bytes = parent_conn.recv_bytes()
                break
            if proc.exitcode is not None:
                break
            await asyncio.sleep(0.01)

        if response_bytes is None:
            _cleanup_worker(runtime, "timeout")
            raise RuntimeError("timeout")

        # Parse child response
        try:
            child_result = json.loads(response_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            _cleanup_worker(runtime, "error")
            raise RuntimeError("child_malformed_response") from None

        if not child_result.get("ok"):
            _cleanup_worker(runtime, "child_execution_failed")
            raise RuntimeError(child_result.get("error_code", "child_execution_failed"))

        # Success — determine result kind from operation
        kind_map = {
            "project_status": ResultKind.REPOSITORY_STATE_SNAPSHOT,
            "validate_report": ResultKind.VALIDATION_FINDINGS,
            "get_task": ResultKind.TASK_RECORD,
            "list_tasks": ResultKind.TASK_LIST,
        }
        result_kind = kind_map.get(name, ResultKind.ERROR)
        data = child_result["result"]

        _cleanup_worker(runtime, "success")
        decision = "allowed"

    except Exception as exc:
        errors.append(str(exc))
        result_kind = ResultKind.ERROR
        decision = "error"

    finally:
        _cleanup_worker(runtime, "cleanup")

    # Redact data recursively, compute hash, build result
    from voyage_framework.mcp_read.confinement import redact_recursive  # noqa: E402

    redacted = redact_recursive(data) if data is not None else {}

    caller = CallerInfo(
        operator=identity.operator,
        client_id=identity.client_id,
        client_auth_strength=identity.client_auth_strength,
        session_id=identity.session_id,
        request_id=request_id,
        project_scope=str(config.project_root),
        report_scope=str(config.report_root),
    )

    result = tool_result(
        tool=name,
        request_id=request_id,
        result_kind=result_kind,
        data=redacted,
        sources=sources,
        warnings=warnings,
        errors=errors,
        denials=denials,
        caller=caller,
        generated_at=datetime.now(UTC).isoformat(),
        authorization="human_required" if decision == "allowed" else "not_applicable",
    )

    # Audit
    duration = (time.monotonic() - start_time) * 1000
    output_bytes = len(json.dumps(data or {}, ensure_ascii=False).encode("utf-8"))
    from voyage_framework.mcp_read.audit import AuditEvent  # noqa: E402

    try:
        audit.write_event(
            AuditEvent(
                event_id=request_id,
                timestamp=datetime.now(UTC).isoformat(),
                session_id=identity.session_id,
                request_id=request_id,
                operator=identity.operator,
                client_id=identity.client_id,
                tool=name,
                project_scope=str(config.project_root),
                report_scope=str(config.report_root),
                result_kind=result_kind.value,
                decision=decision,
                duration_ms=duration,
                output_size_bytes=output_bytes,
                error_class=errors[0] if errors else None,
            )
        )
    except Exception:
        result = tool_result(
            tool=name,
            request_id=request_id,
            result_kind=ResultKind.ERROR,
            data=None,
            errors=["audit_write_failed"],
            caller=caller,
            generated_at=datetime.now(UTC).isoformat(),
            authorization="not_applicable",
        )

    # Response-size enforcement
    serialized = json.dumps(
        result.data if result.data is not None else {}, ensure_ascii=False
    ).encode("utf-8")
    if len(serialized) > config.limits.max_response_bytes:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "response_too_large",
                        "output_size_bytes": len(serialized),
                        "limit_bytes": config.limits.max_response_bytes,
                    }
                ),
            )
        ]

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "schema_version": result.schema_version,
                    "tool": result.tool,
                    "request_id": result.request_id,
                    "result_kind": result.result_kind.value,
                    "authoritative": result.authoritative,
                    "authorization": result.authorization,
                    "data": result.data,
                    "content_hash": result.content_hash,
                    "warnings": result.warnings,
                    "errors": result.errors,
                    "denials": result.denials,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
    ]


def _denied_response(
    message: str,
    request_id: str,
    tool_name: str,
    start_time: float,
) -> list[Any]:
    """Build a minimal denied response."""
    import mcp.types as types  # noqa: E402

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "schema_version": "voyage.mcp-read.v1",
                    "tool": tool_name,
                    "request_id": request_id,
                    "result_kind": "denied",
                    "authoritative": False,
                    "authorization": "human_required",
                    "data": None,
                    "errors": [message],
                    "denials": [{"reason": message}],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
    ]


def _cleanup_worker(runtime: ToolRuntime, reason: str) -> None:
    """Terminate/kill/reap worker and close pipe handles."""
    proc = runtime._active_child
    pipe = runtime._active_pipe

    if (
        proc is not None
        and proc.is_alive()
        and reason
        in (
            "timeout",
            "cleanup",
            "error",
            "child_execution_failed",
        )
    ):
        with contextlib.suppress(Exception):
            proc.terminate()
        with contextlib.suppress(Exception):
            proc.join(timeout=0.25)
        if proc.is_alive():
            with contextlib.suppress(Exception):
                proc.kill()
            with contextlib.suppress(Exception):
                proc.join(timeout=1.0)

    if pipe is not None:
        with contextlib.suppress(Exception):
            pipe.close()

    if proc is not None:
        try:
            if proc.exitcode is None:
                proc.join(timeout=0.5)
        except Exception:
            pass
        if proc.is_alive():
            with contextlib.suppress(Exception):
                proc.kill()
            with contextlib.suppress(Exception):
                proc.join(timeout=1.0)

    runtime._active_child = None
    runtime._active_pipe = None
    runtime._active_deadline = 0.0


def shutdown(runtime: ToolRuntime) -> None:
    """Clean shutdown — reaps any active worker."""
    _cleanup_worker(runtime, "shutdown")
