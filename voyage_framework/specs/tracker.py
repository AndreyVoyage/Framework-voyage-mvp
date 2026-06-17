"""Acceptance Tracker — отслеживание выполнения acceptance criteria.

Проверяет: criteria met? proof? Записывает результат в EventEngine.
"""

from __future__ import annotations

from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType


class AcceptanceTracker:
    """Трекер acceptance criteria для задач.

    Проверяет выполнение критериев и логирует результаты.
    """

    def __init__(self, engine: EventEngine) -> None:
        self.engine = engine

    def check_criteria(
        self,
        task_id: str,
        criteria: list[str],
        results: dict[str, Any],
        project_id: str = "default",
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Проверить выполнение criteria.

        Args:
            task_id: ID задачи
            criteria: Список критериев
            results: Результаты проверок {criterion: result}
            project_id: ID проекта
            correlation_id: ID сессии

        Returns:
            dict с summary: all_passed, passed_count, failed_count, details.
        """
        details = []
        passed = 0
        failed = 0

        for criterion in criteria:
            result = results.get(criterion, False)
            if result:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            details.append({
                "criterion": criterion,
                "status": status,
                "result": result,
            })

        all_passed = failed == 0

        summary = {
            "task_id": task_id,
            "all_passed": all_passed,
            "passed_count": passed,
            "failed_count": failed,
            "total_count": len(criteria),
            "details": details,
        }

        # Логировать
        self.engine.append(Event(
            event_type=EventType.TASK_COMPLETED if all_passed else EventType.ERROR_LOGGED,
            payload=summary,
            project_id=project_id,
            correlation_id=correlation_id,
        ))

        return summary

    def get_task_history(self, task_id: str, project_id: str = "default") -> list[dict[str, Any]]:
        """Получить историю проверок для задачи."""
        events = self.engine.get_events(
            project_id=project_id,
            event_type=EventType.TASK_COMPLETED,
            limit=100,
        )
        return [
            ev.payload for ev in events
            if ev.payload.get("task_id") == task_id
        ]
