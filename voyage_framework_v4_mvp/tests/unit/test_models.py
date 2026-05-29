"""Unit tests for core models."""

import pytest
from datetime import datetime, timezone
from voyage_framework.core.models import (
    Event, EventType, AgentState, AgentStatus, ToolResult,
    SecurityPolicy, SecurityLevel, ApprovalRequest, ApprovalStatus,
    TaskSpec, ProjectContext,
)


class TestEvent:
    def test_event_creation(self):
        ev = Event(event_type=EventType.PLAN_CREATED, payload={"test": True})
        assert ev.event_type == EventType.PLAN_CREATED
        assert ev.payload == {"test": True}
        assert ev.project_id == "default"
        assert ev.timestamp is not None

    def test_event_jsonl_roundtrip(self):
        ev = Event(event_type=EventType.ERROR_LOGGED, payload={"error": "test"})
        jsonl = ev.to_jsonl()
        restored = Event.from_jsonl(jsonl)
        assert restored.event_type == ev.event_type
        assert restored.payload == ev.payload

    def test_event_ulid_unique(self):
        ev1 = Event(event_type=EventType.PLAN_CREATED)
        ev2 = Event(event_type=EventType.PLAN_CREATED)
        assert ev1.event_id != ev2.event_id


class TestAgentState:
    def test_default_state(self):
        state = AgentState(role="developer", task="test task")
        assert state.status == AgentStatus.IDLE
        assert state.retry_count == 0
        assert state.confidence == 0.0

    def test_state_with_plan(self):
        state = AgentState(
            role="developer",
            task="test",
            plan=["step1", "step2"],
        )
        assert len(state.plan) == 2
        assert state.current_step == 0


class TestToolResult:
    def test_success_result(self):
        result = ToolResult(success=True, stdout="output", exit_code=0)
        assert result.success is True
        assert result.blocked is False

    def test_blocked_result(self):
        result = ToolResult(
            success=False,
            blocked=True,
            approval_required=True,
            reason="Dangerous command",
        )
        assert result.blocked is True
        assert result.approval_required is True


class TestSecurityPolicy:
    def test_default_policy(self):
        policy = SecurityPolicy()
        assert "git" in policy.allowed_commands
        assert "rm" in policy.dangerous_commands
        assert policy.allow_network is False

    def test_custom_policy(self):
        policy = SecurityPolicy(
            allowed_commands={"python", "pytest"},
            allow_network=True,
        )
        assert "python" in policy.allowed_commands
        assert policy.allow_network is True


class TestApprovalRequest:
    def test_default_status(self):
        req = ApprovalRequest(command=["rm", "-rf", "/"], agent_id="test", role="devops")
        assert req.status == ApprovalStatus.PENDING
        assert req.approved_by is None


class TestTaskSpec:
    def test_task_spec_creation(self):
        spec = TaskSpec(
            role="developer",
            task="Implement feature",
            task_markdown="# TASK",
            context_json={"role": "developer"},
        )
        assert spec.role == "developer"
        assert spec.task == "Implement feature"


class TestProjectContext:
    def test_default_context(self):
        ctx = ProjectContext(project_id="test-project")
        assert ctx.project_id == "test-project"
        assert ctx.tech_stack == []
        assert ctx.max_tokens == 12000
