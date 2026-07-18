"""Unit tests for MCP tool schemas, handler dispatch, and prompt-injection guards (T78-T88)."""

from __future__ import annotations

import pytest

from voyage_framework.mcp_read.tools import (
    _TOOL_DEFS,
    _TOOL_NAMES,
    WorkerOperation,
    _validate_tool_arguments,
)


class TestToolSchemas:
    """T78, T79, T80 — schema shape constraints."""

    def test_exactly_four_tools(self) -> None:
        assert len(_TOOL_DEFS) == 4
        assert {"project_status", "validate_report", "get_task", "list_tasks"} == _TOOL_NAMES

    def test_tool_schema_no_path(self) -> None:
        """T78: No tool schema accepts an arbitrary 'path' parameter."""
        for tool in _TOOL_DEFS:
            props = tool["inputSchema"]["properties"]
            assert "path" not in props, f"{tool['name']} has 'path'"
            assert tool["inputSchema"]["additionalProperties"] is False

    def test_tool_schema_no_command(self) -> None:
        """T79: No tool schema accepts a 'command' parameter."""
        for tool in _TOOL_DEFS:
            props = tool["inputSchema"]["properties"]
            assert "command" not in props, f"{tool['name']} has 'command'"
            assert "args" not in props, f"{tool['name']} has 'args'"
            assert "exec" not in props, f"{tool['name']} has 'exec'"

    def test_tool_schema_enum_only(self) -> None:
        """T80: list_tasks status/role are strictly enums."""
        lt = _TOOL_DEFS[3]
        assert lt["name"] == "list_tasks"
        assert "enum" in lt["inputSchema"]["properties"]["status"]
        assert "enum" in lt["inputSchema"]["properties"]["role"]

    def test_frozen_worker_operations(self) -> None:
        """Exactly four fixed WorkerOperation values."""
        assert set(WorkerOperation) == {
            WorkerOperation.PROJECT_STATUS,
            WorkerOperation.VALIDATE_REPORT,
            WorkerOperation.GET_TASK,
            WorkerOperation.LIST_TASKS,
        }


class TestArgumentValidation:
    def test_project_status_accepts_empty_dict(self) -> None:
        result = _validate_tool_arguments("project_status", {})
        assert result == {}

    def test_project_status_accepts_none(self) -> None:
        result = _validate_tool_arguments("project_status", None)
        assert result == {}

    def test_project_status_rejects_extra(self) -> None:
        with pytest.raises(ValueError, match="Unknown arguments"):
            _validate_tool_arguments("project_status", {"unknown": "value"})

    def test_validate_report_valid(self) -> None:
        result = _validate_tool_arguments(
            "validate_report", {"report_id": "MCP-READ-01-REPORT.json"}
        )
        assert result == {"report_id": "MCP-READ-01-REPORT.json"}

    def test_validate_report_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError, match="report_id contains invalid"):
            _validate_tool_arguments("validate_report", {"report_id": "../../etc/passwd"})

    def test_validate_report_must_end_with_json(self) -> None:
        with pytest.raises(ValueError, match="must end with .json"):
            _validate_tool_arguments("validate_report", {"report_id": "report.md"})

    def test_validate_report_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _validate_tool_arguments("validate_report", {"report_id": ""})

    def test_get_task_valid(self) -> None:
        result = _validate_tool_arguments("get_task", {"task_id": "VF-001"})
        assert result == {"task_id": "VF-001"}

    def test_get_task_rejects_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="must match"):
            _validate_tool_arguments("get_task", {"task_id": "XX-001"})

    def test_get_task_rejects_short_suffix(self) -> None:
        with pytest.raises(ValueError, match="must match"):
            _validate_tool_arguments("get_task", {"task_id": "VF-1"})

    def test_get_task_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _validate_tool_arguments("get_task", {"task_id": ""})

    def test_list_tasks_defaults(self) -> None:
        result = _validate_tool_arguments("list_tasks", {})
        assert result == {"limit": 50, "offset": 0}

    def test_list_tasks_valid_filters(self) -> None:
        result = _validate_tool_arguments(
            "list_tasks", {"status": "in_progress", "role": "developer"}
        )
        assert result["status"] == "in_progress"
        assert result["role"] == "developer"

    def test_list_tasks_rejects_invalid_status(self) -> None:
        with pytest.raises(ValueError, match="status must be one of"):
            _validate_tool_arguments("list_tasks", {"status": "invalid"})

    def test_list_tasks_rejects_invalid_role(self) -> None:
        with pytest.raises(ValueError, match="role must be one of"):
            _validate_tool_arguments("list_tasks", {"role": "admin"})

    def test_unknown_tool_denied(self) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            _validate_tool_arguments("unknown_tool", {})

    def test_arguments_must_be_dict(self) -> None:
        with pytest.raises(ValueError, match="arguments must be a JSON object"):
            _validate_tool_arguments("project_status", "not a dict")  # type: ignore[arg-type]


class TestPromptInjection:
    """T85, T86, T87 — prompt injection can't change tool behavior."""

    def test_markdown_in_task_id_rejected(self) -> None:
        """T85: Markdown/injection in task_id is rejected by validation, not executed."""
        with pytest.raises(ValueError, match="must match"):
            _validate_tool_arguments("get_task", {"task_id": "# VF-001\n<script>"})

    def test_report_id_no_path_injection(self) -> None:
        """T86: Report content injection cannot propagate through report_id."""
        with pytest.raises(ValueError, match="contains invalid"):
            _validate_tool_arguments("validate_report", {"report_id": "report.json%0A%0DInjected"})

    def test_oversized_report_id_rejected(self) -> None:
        """T87: Very long report_id is rejected at validation."""
        long_id = "R" * 300 + ".json"
        with pytest.raises(ValueError, match="exceeds max length"):
            _validate_tool_arguments("validate_report", {"report_id": long_id})


class TestCrossProjectIsolation:
    """T88 — cross-project isolation at argument validation."""

    def test_no_arbitrary_path_param(self) -> None:
        """No tool accepts a path/project_root/report_root from caller."""
        for tool in _TOOL_DEFS:
            props = tool["inputSchema"]["properties"]
            for forbidden in ("path", "project_root", "report_root", "repo", "dir", "file"):
                assert forbidden not in props, f"{tool['name']} has {forbidden}"
