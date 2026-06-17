"""Integration tests for LangGraph-based runtime."""

from __future__ import annotations

import pytest

from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
from voyage_framework.core.models import EventType, SecurityPolicy
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor


class TestLangGraphWorkflow:
    @pytest.fixture
    def runtime(self, tmp_engine, tmp_path):
        policy = PolicyEnforcer()
        executor = SecureExecutor(SecurityPolicy(), project_root=tmp_path)
        return LangGraphRuntime(tmp_engine, executor, policy)

    @pytest.mark.asyncio
    async def test_end_to_end_success(self, runtime, tmp_engine):
        result = await runtime.run(
            role="developer",
            task="hello",
            plan=["echo hello"],
            project_id="langgraph-test",
            correlation_id="corr-e2e",
        )

        assert result.success is True
        assert result.state.confidence >= 0.0

        node_completed = tmp_engine.get_events(event_type=EventType.NODE_COMPLETED)
        assert len(node_completed) >= 3  # plan, execute, complete

    @pytest.mark.asyncio
    async def test_graph_visualization(self, runtime):
        mermaid = runtime.visualize()
        assert "```mermaid" in mermaid
        assert "plan" in mermaid
        assert "execute" in mermaid

    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, runtime, tmp_engine):
        correlation_id = "corr-recover"
        await runtime.run(
            role="developer",
            task="checkpoint test",
            plan=["echo checkpoint"],
            project_id="langgraph-test",
            correlation_id=correlation_id,
        )

        state = runtime.get_state(correlation_id)
        assert state is not None
        assert state.task == "checkpoint test"
