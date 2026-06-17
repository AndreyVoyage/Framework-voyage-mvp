"""LangGraph-based runtime для Voyage Framework."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import AgentState, NodeResult
from voyage_framework.improvement.feedback_loop import FeedbackLoop
from voyage_framework.langgraph_tools.checkpoint_adapter import EventEngineCheckpoint
from voyage_framework.langgraph_tools.edges import (
    route_after_execute,
    route_after_reflect,
    route_after_retry,
)
from voyage_framework.langgraph_tools.graph_builder import VoyageGraphBuilder
from voyage_framework.langgraph_tools.nodes import (
    complete_node,
    error_node,
    execute_node,
    parallel_validation_node,
    plan_node,
    reflect_node,
    retry_node,
)
from voyage_framework.langgraph_tools.state import VoyageState
from voyage_framework.langgraph_tools.visualizer import MermaidExporter
from voyage_framework.memory.code_search import CodeSearch
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor


class LangGraphRuntime:
    """Графовый runtime поверх VoyageGraphBuilder."""

    def __init__(
        self,
        engine: EventEngine,
        executor: SecureExecutor,
        policy: PolicyEnforcer,
        feedback_loop: FeedbackLoop | None = None,
        code_search: CodeSearch | None = None,
    ) -> None:
        self.engine = engine
        self.executor = executor
        self.policy = policy
        self.feedback_loop = feedback_loop
        self.code_search = code_search

    def _apply_update(
        self,
        state: VoyageState,
        update: VoyageState | dict[str, Any],
    ) -> VoyageState:
        """Применить partial update к состоянию."""
        if isinstance(update, VoyageState):
            return update
        if isinstance(update, dict):
            return state.model_copy(update=update, deep=True)
        return state

    def _wrap_node(
        self,
        name: str,
        fn: Callable[..., Any],
        checkpoint: EventEngineCheckpoint,
    ) -> Callable[..., Any]:
        """Обёртка для логирования checkpoint перед/после ноды."""

        async def wrapped(state: VoyageState) -> VoyageState:
            checkpoint.on_node_start(name, state)
            raw = await fn(state)
            new_state = self._apply_update(state, raw)
            checkpoint.on_node_end(name, new_state)
            return new_state

        return wrapped

    def _wrap_condition(
        self,
        from_node: str,
        cond: Callable[[VoyageState], str],
        routes: dict[str, str],
        checkpoint: EventEngineCheckpoint,
    ) -> Callable[[VoyageState], str]:
        """Обёртка для логирования EDGE_TAKEN при условном переходе."""

        def wrapped(state: VoyageState) -> str:
            key = cond(state)
            target = routes.get(key)
            if target:
                checkpoint.on_edge_taken(from_node, target, key)
            return key

        return wrapped

    def _build_graph(
        self,
        checkpoint: EventEngineCheckpoint,
    ) -> VoyageGraphBuilder:
        """Собрать StateGraph с нодами и conditional edges."""
        ctx = {
            "engine": self.engine,
            "executor": self.executor,
            "policy": self.policy,
            "feedback_loop": self.feedback_loop,
            "code_search": self.code_search,
        }

        builder = VoyageGraphBuilder(VoyageState)
        builder.add_node("plan", self._wrap_node("plan", partial(plan_node, ctx=ctx), checkpoint))
        builder.add_node(
            "execute", self._wrap_node("execute", partial(execute_node, ctx=ctx), checkpoint)
        )
        builder.add_node(
            "reflect", self._wrap_node("reflect", partial(reflect_node, ctx=ctx), checkpoint)
        )
        builder.add_node(
            "retry", self._wrap_node("retry", partial(retry_node, ctx=ctx), checkpoint)
        )
        builder.add_node(
            "complete", self._wrap_node("complete", partial(complete_node, ctx=ctx), checkpoint)
        )
        builder.add_node(
            "error", self._wrap_node("error", partial(error_node, ctx=ctx), checkpoint)
        )
        builder.add_node(
            "parallel_validation",
            self._wrap_node(
                "parallel_validation",
                partial(parallel_validation_node, ctx=ctx),
                checkpoint,
            ),
        )

        routes_after_execute = {"reflect": "reflect", "retry": "retry", "error": "error"}
        routes_after_reflect = {"retry": "retry", "complete": "complete"}
        routes_after_retry = {"execute": "execute", "error": "error"}

        builder.add_edge("__start__", "plan")
        builder.add_edge("plan", "execute")
        builder.add_conditional_edges(
            "execute",
            self._wrap_condition("execute", route_after_execute, routes_after_execute, checkpoint),
            routes_after_execute,
        )
        builder.add_conditional_edges(
            "reflect",
            self._wrap_condition("reflect", route_after_reflect, routes_after_reflect, checkpoint),
            routes_after_reflect,
        )
        builder.add_conditional_edges(
            "retry",
            self._wrap_condition("retry", route_after_retry, routes_after_retry, checkpoint),
            routes_after_retry,
        )
        builder.add_edge("complete", "__end__")
        builder.add_edge("error", "__end__")

        return builder

    async def run(
        self,
        role: str,
        task: str,
        plan: list[str],
        project_id: str = "default",
        correlation_id: str | None = None,
    ) -> NodeResult:
        """Запустить графовый workflow."""
        initial_state = VoyageState(
            role=role,
            task=task,
            plan=plan,
            project_id=project_id,
            correlation_id=correlation_id,
        )

        checkpoint = EventEngineCheckpoint(self.engine, project_id=project_id)
        builder = self._build_graph(checkpoint)

        final_state = await builder.invoke(initial_state)

        success = final_state.status == "completed"
        agent_state = AgentState(
            role=role,
            task=task,
            plan=plan,
            retry_count=final_state.retry_count,
            confidence=final_state.confidence,
            results=final_state.results,
            project_id=project_id,
            correlation_id=correlation_id,
        )
        return NodeResult(
            node_name="langgraph_runtime",
            success=success,
            state=agent_state,
            output={"status": final_state.status, "error": final_state.error},
        )

    def visualize(self) -> str:
        """Вернуть Mermaid-представление графа."""
        checkpoint = EventEngineCheckpoint(self.engine)
        builder = self._build_graph(checkpoint)
        exporter = MermaidExporter(builder)
        return exporter.to_markdown()

    def get_state(self, correlation_id: str) -> VoyageState | None:
        """Восстановить последний state по correlation_id."""
        checkpoint = EventEngineCheckpoint(self.engine)
        return checkpoint.get_state(correlation_id)

    async def resume(self, correlation_id: str) -> NodeResult:
        """Возобновить выполнение после остановки."""
        state = self.get_state(correlation_id)
        if state is None:
            return NodeResult(
                node_name="langgraph_runtime",
                success=False,
                state=AgentState(role="", task=""),
                output={"error": f"No state found for {correlation_id}"},
            )
        checkpoint = EventEngineCheckpoint(self.engine, project_id=state.project_id)
        builder = self._build_graph(checkpoint)
        final_state = await builder.invoke(state)
        success = final_state.status == "completed"
        return NodeResult(
            node_name="langgraph_runtime",
            success=success,
            state=AgentState(role=state.role, task=state.task),
            output={"status": final_state.status, "error": final_state.error},
        )
