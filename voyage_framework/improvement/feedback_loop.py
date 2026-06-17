"""Feedback Loop — цикл обратной связи: execute → evaluate → improve."""

from __future__ import annotations

from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType, FeedbackResult, NodeResult
from voyage_framework.improvement.evaluator import Evaluator
from voyage_framework.improvement.golden_dataset import GoldenDataset
from voyage_framework.improvement.rule_engine import RuleEngine


class FeedbackLoop:
    """Связывает Evaluator, RuleEngine и GoldenDataset в цикл улучшения."""

    def __init__(
        self,
        engine: EventEngine,
        evaluator: Evaluator,
        rule_engine: RuleEngine,
        golden_dataset: GoldenDataset,
    ) -> None:
        self.engine = engine
        self.evaluator = evaluator
        self.rule_engine = rule_engine
        self.golden_dataset = golden_dataset

    async def process(
        self,
        node_result: NodeResult,
        project_id: str = "default",
    ) -> FeedbackResult:
        """Обработать результат агента и сгенерировать feedback.

        Args:
            node_result: Результат выполнения задачи агентом.
            project_id: ID проекта.

        Returns:
            FeedbackResult с оценкой, рекомендациями и новыми правилами.
        """
        evaluation = await self.evaluator.evaluate_task(node_result)

        new_rules: list[Any] = []
        suggestions: list[str] = []

        # Генерация правил при низкой оценке
        if evaluation.overall_score < 0.7:
            failed_results = [
                r for r in node_result.state.results if not r.success
            ]
            for failed in failed_results:
                rule = self.rule_engine.analyze_error(failed, project_id=project_id)
                if rule:
                    new_rules.append(rule)
                    suggestions.append(f"New rule: {rule.rule_text}")

            # Если нет failed ToolResult, анализируем сам NodeResult
            if not new_rules and not node_result.success:
                rule = self.rule_engine.analyze_error(node_result, project_id=project_id)
                if rule:
                    new_rules.append(rule)
                    suggestions.append(f"New rule: {rule.rule_text}")

        # Поиск эталона
        golden_match = None
        golden = self.golden_dataset.find_match(node_result.state.task)
        if golden:
            similarity = self.golden_dataset.compare(
                node_result.state.task,
                golden.reference_code,
            )
            from voyage_framework.core.models import SearchResult
            golden_match = SearchResult(
                id=golden.id,
                text=golden.reference_code,
                score=similarity,
                metadata={
                    "task_pattern": golden.task_pattern,
                    "language": golden.language,
                    "explanation": golden.explanation,
                },
            )
            suggestions.append(
                f"Golden match found: {golden.task_pattern} "
                f"(similarity {similarity:.2f})"
            )
            self.engine.append(Event(
                event_type=EventType.GOLDEN_MATCH_FOUND,
                payload={
                    "solution_id": golden.id,
                    "task": node_result.state.task,
                    "score": similarity,
                    "project_id": project_id,
                },
                project_id=project_id,
                agent_id=node_result.state.agent_id,
            ))

        # Логирование оценки
        self.engine.append(Event(
            event_type=EventType.EVALUATION_COMPLETED,
            payload={
                "agent_id": node_result.state.agent_id,
                "task": node_result.state.task,
                "overall_score": evaluation.overall_score,
                "syntax_valid": evaluation.syntax_valid,
                "style_score": evaluation.style_score,
                "type_score": evaluation.type_score,
                "test_score": evaluation.test_score,
                "new_rules_count": len(new_rules),
                "project_id": project_id,
            },
            project_id=project_id,
            agent_id=node_result.state.agent_id,
            role=node_result.state.role,
        ))

        return FeedbackResult(
            evaluation=evaluation,
            suggestions=suggestions,
            new_rules=new_rules,
            golden_match=golden_match,
        )

    def should_retry(self, result: FeedbackResult) -> bool:
        """Определить, стоит ли перезапускать задачу."""
        if result.evaluation.overall_score < 0.5:
            return True
        return not result.evaluation.syntax_valid

    def get_improvement_summary(self, project_id: str = "default") -> dict[str, Any]:
        """Агрегированный отчёт по улучшениям проекта."""
        evaluations = self.engine.get_events(
            project_id=project_id,
            event_type=EventType.EVALUATION_COMPLETED,
        )
        rules = self.engine.get_events(
            project_id=project_id,
            event_type=EventType.RULE_SUGGESTED,
        )
        golden = self.engine.get_events(
            project_id=project_id,
            event_type=EventType.GOLDEN_MATCH_FOUND,
        )

        scores = [
            ev.payload.get("overall_score", 0.0)
            for ev in evaluations
            if "overall_score" in ev.payload
        ]

        return {
            "project_id": project_id,
            "evaluations_count": len(evaluations),
            "rules_suggested_count": len(rules),
            "golden_matches_count": len(golden),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "last_score": scores[-1] if scores else None,
            "stored_rules_count": len(self.rule_engine.get_rules()),
            "golden_solutions_count": self.golden_dataset.count(),
        }
