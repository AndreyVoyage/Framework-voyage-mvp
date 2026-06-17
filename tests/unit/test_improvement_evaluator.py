"""Unit tests for Evaluator."""

import pytest

from voyage_framework.core.models import AgentState, NodeResult, ToolResult
from voyage_framework.improvement.evaluator import Evaluator
from voyage_framework.improvement.golden_dataset import GoldenDataset, GoldenSolution


class TestEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_valid_code(self, tmp_path) -> None:
        evaluator = Evaluator(project_root=tmp_path)
        code = "def hello() -> str:\n    return 'world'\n"

        result = await evaluator.evaluate_code(code)

        assert result.syntax_valid is True
        assert result.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_evaluate_invalid_syntax(self, tmp_path) -> None:
        evaluator = Evaluator(project_root=tmp_path)
        code = "def hello(\n    return 'world'\n"

        result = await evaluator.evaluate_code(code)

        assert result.syntax_valid is False

    @pytest.mark.asyncio
    async def test_evaluate_task(self, tmp_path) -> None:
        evaluator = Evaluator(project_root=tmp_path)
        state = AgentState(role="developer", task="test", plan=["echo hello"])
        state.results.append(ToolResult(success=True, stdout="def foo(): pass"))
        node = NodeResult(node_name="agent", success=True, state=state)

        result = await evaluator.evaluate_task(node)

        assert result.syntax_valid is True
        assert 0.0 <= result.overall_score <= 1.0

    def test_compare_with_golden(self) -> None:
        golden = GoldenDataset()
        evaluator = Evaluator(golden_dataset=golden)
        solution = GoldenSolution(
            task_pattern="auth",
            reference_code="def login(): pass",
        )

        score = evaluator.compare_with_golden("def login(): pass", solution)

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_overall_score_computed(self, tmp_path) -> None:
        evaluator = Evaluator(project_root=tmp_path)
        code = "x = 1\n"

        result = await evaluator.evaluate_code(code)

        assert result.overall_score == pytest.approx(
            0.2 * 1.0 + 0.3 * result.style_score + 0.3 * result.type_score + 0.2 * 1.0,
            abs=0.01,
        )
