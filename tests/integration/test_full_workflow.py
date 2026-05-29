"""Integration test: full agent workflow.

End-to-end: EventEngine → TaskGenerator → AgentRuntime → SecureExecutor.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import SecurityPolicy
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.agents.runtime import AgentRuntime
from voyage_framework.specs.task_generator import TaskGenerator


class TestFullWorkflow:
    @pytest.fixture
    def tmp_engine(self, tmp_path):
        db = tmp_path / "events.db"
        return EventEngine(db_path=db)

    @pytest.fixture
    def tmp_executor(self, tmp_path):
        policy = SecurityPolicy()
        return SecureExecutor(policy, project_root=tmp_path)

    @pytest.fixture
    def tmp_runtime(self, tmp_engine, tmp_executor):
        policy = PolicyEnforcer()
        return AgentRuntime(tmp_engine, tmp_executor, policy)

    @pytest.mark.asyncio
    async def test_task_generation_and_execution(self, tmp_engine, tmp_executor, tmp_runtime, tmp_path):
        """Полный цикл: генерация задачи → выполнение агентом."""
        # 1. Генерация задачи
        generator = TaskGenerator(tmp_engine)
        spec = generator.generate(
            role="developer",
            task="Run echo command",
            project_id="integration-test",
        )
        assert spec.task_id is not None

        # 2. Выполнение агентом
        result = await tmp_runtime.run(
            role="developer",
            task="Run echo command",
            plan=["echo hello from voyage"],
            project_id="integration-test",
        )

        assert result.success is True
        assert result.state.status.value == "completed"
        assert result.state.confidence > 0.0

        # 3. Проверка событий
        events = tmp_engine.get_events(project_id="integration-test")
        assert len(events) >= 3  # PLAN_CREATED + AGENT_STARTED + TOOL_EXECUTED + AGENT_COMPLETED

    @pytest.mark.asyncio
    async def test_agent_retry_on_failure(self, tmp_engine, tmp_executor, tmp_runtime):
        """Агент retry при ошибке."""
        result = await tmp_runtime.run(
            role="developer",
            task="Run failing command",
            plan=["nonexistent_command_xyz"],
            project_id="retry-test",
        )

        # Команда не найдена, но агент попробует retry
        assert result.state.retry_count > 0

    @pytest.mark.asyncio
    async def test_dangerous_command_blocked(self, tmp_engine, tmp_executor, tmp_runtime):
        """Опасная команда блокируется."""
        result = await tmp_runtime.run(
            role="devops",
            task="Restart nginx",
            plan=["systemctl restart nginx"],
            project_id="security-test",
        )

        # Dangerous tier требует approval
        assert any(r.blocked for r in result.state.results)

    def test_project_context_accumulation(self, tmp_engine):
        """Контекст проекта накапливается."""
        for i in range(5):
            tmp_engine.append(
                type("Event", (), {
                    "event_type": type("ET", (), {"value": "plan_created"})(),
                    "payload": {"n": i},
                    "project_id": "ctx-test",
                    "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                    "event_id": str(i),
                    "micro_phase": None,
                    "correlation_id": None,
                    "causation_id": None,
                    "agent_id": None,
                    "role": None,
                })()
            )

        ctx = tmp_engine.get_project_context("ctx-test")
        assert ctx["total_events"] == 5
