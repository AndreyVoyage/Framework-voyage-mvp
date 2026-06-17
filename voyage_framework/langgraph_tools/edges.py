"""Conditional edges для VoyageState."""

from __future__ import annotations

from voyage_framework.langgraph_tools.state import VoyageState


def route_after_plan(state: VoyageState) -> str:
    """После планирования всегда переходим к выполнению."""
    return "execute"


def route_after_execute(state: VoyageState) -> str:
    """Маршрутизация после выполнения шага на основе оценки."""
    if state.evaluation_score >= 0.7:
        return "reflect"
    if state.retry_count < state.max_retries:
        return "retry"
    return "error"


def route_after_reflect(state: VoyageState) -> str:
    """Маршрутизация после рефлексии."""
    if state.should_retry:
        return "retry"
    return "complete"


def route_after_retry(state: VoyageState) -> str:
    """Маршрутизация после retry-ноды."""
    if state.retry_count < state.max_retries:
        return "execute"
    return "error"


def route_for_approval(state: VoyageState) -> str:
    """Human-in-the-loop: если последний результат требует approval — ждём."""
    if state.results and state.results[-1].approval_required:
        return "await_approval"
    return "execute"
