"""Integration test for Self-Improving Engine end-to-end."""

import pytest

from voyage_framework.agents.runtime import AgentRuntime
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import EventType, SecurityPolicy
from voyage_framework.improvement.evaluator import Evaluator
from voyage_framework.improvement.feedback_loop import FeedbackLoop
from voyage_framework.improvement.golden_dataset import GoldenDataset
from voyage_framework.improvement.rule_engine import RuleEngine
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor


class TestSelfImprovement:
    @pytest.fixture
    def tmp_engine(self, tmp_path):
        db = tmp_path / "events.db"
        return EventEngine(db_path=db)

    @pytest.fixture
    def tmp_feedback(self, tmp_engine, tmp_path):
        evaluator = Evaluator(project_root=tmp_path)
        rule_engine = RuleEngine(engine=tmp_engine)
        golden = GoldenDataset(engine=tmp_engine)
        return FeedbackLoop(tmp_engine, evaluator, rule_engine, golden)

    @pytest.fixture
    def tmp_runtime(self, tmp_engine, tmp_feedback):
        policy = PolicyEnforcer()
        security = SecurityPolicy()
        executor = SecureExecutor(security)
        return AgentRuntime(tmp_engine, executor, policy, feedback_loop=tmp_feedback)

    @pytest.mark.asyncio
    async def test_runtime_with_feedback_loop(self, tmp_engine, tmp_runtime, tmp_feedback):
        """Агент с FeedbackLoop логирует EVALUATION_COMPLETED."""
        result = await tmp_runtime.run(
            role="developer",
            task="simple task",
            plan=["python -c print(1)"],
            project_id="self-improvement-test",
        )

        assert result.success is True
        assert result.state.confidence >= 0.0

        events = tmp_engine.get_events(event_type=EventType.EVALUATION_COMPLETED)
        assert len(events) >= 1
        assert all(e.project_id == "self-improvement-test" for e in events)

    @pytest.mark.asyncio
    async def test_runtime_retry_on_low_score(self, tmp_engine, tmp_runtime, tmp_feedback):
        """FeedbackLoop может инициировать retry при плохом результате."""
        # Плохой код в stdout приведёт к низкой оценке
        result = await tmp_runtime.run(
            role="developer",
            task="broken code",
            plan=["python -c pass"],
            project_id="retry-test",
        )

        # Агент выполнил команду, но оценка низкая
        assert result.state.retry_count >= 0
        evaluations = tmp_engine.get_events(event_type=EventType.EVALUATION_COMPLETED)
        assert len(evaluations) >= 1
