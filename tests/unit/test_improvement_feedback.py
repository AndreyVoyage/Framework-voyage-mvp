"""Unit tests for FeedbackLoop."""

import pytest

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import (
    AgentState,
    EvaluationResult,
    NodeResult,
    ToolResult,
)
from voyage_framework.improvement.evaluator import Evaluator
from voyage_framework.improvement.feedback_loop import FeedbackLoop
from voyage_framework.improvement.golden_dataset import GoldenDataset, GoldenSolution
from voyage_framework.improvement.rule_engine import RuleEngine


class TestFeedbackLoop:
    @pytest.fixture
    def loop(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        evaluator = Evaluator(project_root=tmp_path)
        rule_engine = RuleEngine(engine=engine)
        golden = GoldenDataset(engine=engine)
        return FeedbackLoop(engine, evaluator, rule_engine, golden)

    @pytest.mark.asyncio
    async def test_process_successful_task(self, loop) -> None:
        state = AgentState(role="developer", task="test", plan=["echo hello"])
        state.results.append(ToolResult(success=True, stdout="x = 1"))
        node = NodeResult(node_name="agent", success=True, state=state)

        result = await loop.process(node)

        assert result.evaluation.syntax_valid is True
        assert 0.0 <= result.evaluation.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_process_generates_rule_on_failure(self, loop) -> None:
        state = AgentState(role="developer", task="test", plan=["bad command"])
        state.results.append(ToolResult(success=False, stderr="SyntaxError: invalid syntax"))
        node = NodeResult(node_name="agent", success=False, state=state)

        result = await loop.process(node)

        assert len(result.new_rules) > 0

    def test_should_retry_low_score(self, loop) -> None:
        fb = type("obj", (object,), {
            "evaluation": EvaluationResult(overall_score=0.3, syntax_valid=True),
        })()

        assert loop.should_retry(fb) is True

    def test_should_not_retry_high_score(self, loop) -> None:
        fb = type("obj", (object,), {
            "evaluation": EvaluationResult(overall_score=0.9, syntax_valid=True),
        })()

        assert loop.should_retry(fb) is False

    @pytest.mark.asyncio
    async def test_golden_match_found(self, loop) -> None:
        loop.golden_dataset.add_solution(GoldenSolution(
            task_pattern="login",
            reference_code="def login(): pass",
        ))
        state = AgentState(role="developer", task="login user", plan=["echo ok"])
        state.results.append(ToolResult(success=True, stdout="def login(): pass"))
        node = NodeResult(node_name="agent", success=True, state=state)

        result = await loop.process(node)

        assert result.golden_match is not None

    @pytest.mark.asyncio
    async def test_improvement_summary(self, loop) -> None:
        state = AgentState(role="developer", task="test", plan=["echo hello"])
        state.results.append(ToolResult(success=True, stdout="x = 1"))
        node = NodeResult(node_name="agent", success=True, state=state)

        await loop.process(node, project_id="proj")
        summary = loop.get_improvement_summary(project_id="proj")

        assert summary["evaluations_count"] == 1
