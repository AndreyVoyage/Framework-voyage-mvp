"""Node implementations для графового runtime."""

from __future__ import annotations

import asyncio
from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import AgentState, Event, EventType, NodeResult, ToolResult
from voyage_framework.langgraph_tools.state import VoyageState
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.specs.task_generator import TaskGenerator


def _to_agent_state(state: VoyageState) -> AgentState:
    """Конвертировать VoyageState в AgentState для совместимости с FeedbackLoop."""
    return AgentState(
        agent_id=state.agent_id or "",
        role=state.role,
        task=state.task,
        plan=state.plan,
        current_step=state.current_step,
        retry_count=state.retry_count,
        max_retries=state.max_retries,
        confidence=state.confidence,
        results=state.results,
        project_id=state.project_id,
        correlation_id=state.correlation_id,
        memory_context=[],
    )


async def plan_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Сформировать план выполнения задачи."""
    engine: EventEngine = ctx["engine"]
    if state.plan:
        plan = state.plan
    else:
        generator = TaskGenerator(engine)
        spec = generator.generate(
            role=state.role,
            task=state.task,
            project_id=state.project_id,
        )
        plan = spec.instructions if spec.instructions else [f"echo {state.task}"]

    engine.append(
        Event(
            event_type=EventType.PLAN_CREATED,
            payload={"task": state.task, "plan": plan},
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        )
    )
    return {
        "plan": plan,
        "current_step": 0,
        "status": "planning",
    }


async def execute_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Выполнить текущий шаг плана."""
    executor: SecureExecutor = ctx["executor"]
    engine: EventEngine = ctx["engine"]

    if state.current_step >= len(state.plan):
        return {"status": "executing"}

    step = state.plan[state.current_step]
    parts = step.split()
    result = await executor.execute(parts) if parts else ToolResult(success=True, stdout="")

    engine.append(
        Event(
            event_type=EventType.TOOL_EXECUTED,
            payload={
                "step": step,
                "success": result.success,
                "blocked": result.blocked,
                "exit_code": result.exit_code,
            },
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        )
    )

    new_results = list(state.results) + [result]
    return {
        "results": new_results,
        "current_step": state.current_step + 1,
        "evaluation_score": 1.0 if result.success else 0.0,
        "status": "executing",
    }


async def reflect_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Рефлексия и оценка результата через FeedbackLoop."""
    feedback_loop = ctx.get("feedback_loop")

    if feedback_loop is None:
        return {
            "evaluation_score": 1.0,
            "should_retry": False,
            "confidence": 1.0,
            "status": "reflecting",
        }

    agent_state = _to_agent_state(state)
    node_result = NodeResult(
        node_name="execute",
        success=all(r.success for r in state.results),
        state=agent_state,
    )

    feedback = await feedback_loop.process(node_result, project_id=state.project_id)

    return {
        "evaluation_score": feedback.evaluation.overall_score,
        "should_retry": feedback_loop.should_retry(feedback),
        "confidence": feedback.evaluation.overall_score,
        "status": "reflecting",
    }


async def retry_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Подготовить state к повторной попытке."""
    engine: EventEngine = ctx["engine"]
    engine.append(
        Event(
            event_type=EventType.RETRY_ATTEMPTED,
            payload={
                "retry_count": state.retry_count + 1,
                "max_retries": state.max_retries,
            },
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        )
    )
    return {
        "retry_count": state.retry_count + 1,
        "current_step": 0,
        "status": "retrying",
    }


async def complete_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Финализировать успешное выполнение."""
    engine: EventEngine = ctx["engine"]
    engine.append(
        Event(
            event_type=EventType.AGENT_COMPLETED,
            payload={
                "task": state.task,
                "confidence": state.confidence,
                "retry_count": state.retry_count,
            },
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        )
    )
    return {"status": "completed"}


async def error_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Финализировать выполнение с ошибкой."""
    engine: EventEngine = ctx["engine"]
    error = state.error or "Max retries exceeded"
    engine.append(
        Event(
            event_type=EventType.AGENT_FAILED,
            payload={"task": state.task, "error": error},
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        )
    )
    return {"status": "failed", "error": error}


async def policy_check_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Проверить политику роли перед выполнением опасных операций."""
    policy: PolicyEnforcer = ctx["policy"]
    executor = ctx.get("executor")
    if not state.plan or state.current_step >= len(state.plan) or executor is None:
        return {}

    step = state.plan[state.current_step]
    classification = executor.classify(step.split())
    if classification.value == "dangerous" and not policy.can(state.role, "can_access_dangerous"):
        return {
            "error": f"Role '{state.role}' cannot run dangerous commands",
            "status": "failed",
        }
    return {}


async def parallel_validation_node(state: VoyageState, ctx: dict[str, Any]) -> dict[str, Any]:
    """Параллельно запустить lint и test."""
    executor: SecureExecutor = ctx["executor"]

    async def run_ruff() -> ToolResult:
        return await executor.execute(["ruff", "check", "--quiet", "voyage_framework"])

    async def run_pytest() -> ToolResult:
        return await executor.execute(["pytest", "tests/", "-q"])

    ruff_result, pytest_result = await asyncio.gather(run_ruff(), run_pytest())
    new_results = list(state.results) + [ruff_result, pytest_result]

    return {
        "results": new_results,
        "evaluation_score": 1.0 if (ruff_result.success and pytest_result.success) else 0.0,
        "status": "reflecting",
    }
