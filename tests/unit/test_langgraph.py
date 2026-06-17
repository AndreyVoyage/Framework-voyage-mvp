"""Unit tests for LangGraph integration and simple_graph fallback."""

from __future__ import annotations

import pytest

from voyage_framework.core.models import EventType, SecurityPolicy, ToolResult
from voyage_framework.langgraph_tools.edges import (
    route_after_execute,
    route_after_plan,
    route_after_reflect,
    route_after_retry,
)
from voyage_framework.langgraph_tools.graph_builder import VoyageGraphBuilder
from voyage_framework.langgraph_tools.simple_graph import CompiledGraph, StateGraph
from voyage_framework.langgraph_tools.state import VoyageState
from voyage_framework.langgraph_tools.visualizer import MermaidExporter


class TestVoyageState:
    def test_state_defaults(self):
        state = VoyageState()
        assert state.role == ""
        assert state.plan == []
        assert state.retry_count == 0
        assert state.max_retries == 3

    def test_state_update(self):
        state = VoyageState(role="developer", task="hello")
        new_state = state.model_copy(update={"retry_count": 1}, deep=True)
        assert new_state.retry_count == 1
        assert new_state.role == "developer"


class TestSimpleGraph:
    @pytest.mark.asyncio
    async def test_invoke_linear_graph(self):
        graph = StateGraph(VoyageState)

        async def node_a(state: VoyageState):
            return {"status": "a_done"}

        async def node_b(state: VoyageState):
            return {"status": "b_done"}

        graph.add_node("a", node_a)
        graph.add_node("b", node_b)
        graph.add_edge("__start__", "a")
        graph.add_edge("a", "b")
        graph.add_edge("b", "__end__")

        compiled = graph.compile()
        assert isinstance(compiled, CompiledGraph)

        result = await compiled.invoke(VoyageState())
        assert result.status == "b_done"

    @pytest.mark.asyncio
    async def test_invoke_conditional_edges(self):
        graph = StateGraph(VoyageState)

        async def score_node(state: VoyageState):
            return {"evaluation_score": 0.8}

        async def good_node(state: VoyageState):
            return {"status": "good"}

        async def bad_node(state: VoyageState):
            return {"status": "bad"}

        def route(state: VoyageState) -> str:
            return "good" if state.evaluation_score >= 0.7 else "bad"

        graph.add_node("score", score_node)
        graph.add_node("good", good_node)
        graph.add_node("bad", bad_node)
        graph.add_edge("__start__", "score")
        graph.add_conditional_edges("score", route, {"good": "good", "bad": "bad"})
        graph.add_edge("good", "__end__")
        graph.add_edge("bad", "__end__")

        result = await graph.compile().invoke(VoyageState())
        assert result.status == "good"


class TestVoyageGraphBuilder:
    def test_builder_add_node_edge(self):
        builder = VoyageGraphBuilder(VoyageState)

        async def nop(state: VoyageState):
            return {}

        builder.add_node("plan", nop)
        builder.add_edge("__start__", "plan")
        builder.add_edge("plan", "__end__")
        compiled = builder.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_builder_invoke(self):
        builder = VoyageGraphBuilder(VoyageState)

        async def plan_node(state: VoyageState):
            return {"plan": ["echo hello"]}

        async def exec_node(state: VoyageState):
            return {"results": [ToolResult(success=True, stdout="hello")]}

        builder.add_node("plan", plan_node)
        builder.add_node("execute", exec_node)
        builder.add_edge("__start__", "plan")
        builder.add_edge("plan", "execute")
        builder.add_edge("execute", "__end__")

        result = await builder.invoke(VoyageState())
        assert result.plan == ["echo hello"]
        assert len(result.results) == 1
        assert result.results[0].stdout == "hello"

    def test_builder_records_nodes_for_visualizer(self):
        builder = VoyageGraphBuilder(VoyageState)

        async def nop(state: VoyageState):
            return {}

        builder.add_node("plan", nop)
        builder.add_node("execute", nop)
        builder.add_edge("__start__", "plan")
        builder.add_edge("plan", "execute")

        assert "plan" in builder._nodes
        assert "execute" in builder._nodes
        assert ("__start__", "plan") in builder._edges


class TestEdges:
    def test_route_after_plan(self):
        state = VoyageState()
        assert route_after_plan(state) == "execute"

    def test_route_after_execute_high_score(self):
        state = VoyageState(evaluation_score=0.8)
        assert route_after_execute(state) == "reflect"

    def test_route_after_execute_retry(self):
        state = VoyageState(evaluation_score=0.3, retry_count=0, max_retries=3)
        assert route_after_execute(state) == "retry"

    def test_route_after_execute_error(self):
        state = VoyageState(evaluation_score=0.3, retry_count=3, max_retries=3)
        assert route_after_execute(state) == "error"

    def test_route_after_reflect_retry(self):
        state = VoyageState(should_retry=True)
        assert route_after_reflect(state) == "retry"

    def test_route_after_reflect_complete(self):
        state = VoyageState(should_retry=False)
        assert route_after_reflect(state) == "complete"

    def test_route_after_retry_execute(self):
        state = VoyageState(retry_count=1, max_retries=3)
        assert route_after_retry(state) == "execute"

    def test_route_after_retry_error(self):
        state = VoyageState(retry_count=3, max_retries=3)
        assert route_after_retry(state) == "error"


class TestVisualizer:
    def test_mermaid_exporter(self):
        builder = VoyageGraphBuilder(VoyageState)

        async def nop(state: VoyageState):
            return {}

        builder.add_node("plan", nop)
        builder.add_node("execute", nop)
        builder.add_edge("__start__", "plan")
        builder.add_edge("plan", "execute")

        exporter = MermaidExporter(builder)
        md = exporter.to_markdown()
        assert "```mermaid" in md
        assert "plan" in md
        assert "execute" in md

    def test_graphviz_exporter(self):
        builder = VoyageGraphBuilder(VoyageState)

        async def nop(state: VoyageState):
            return {}

        builder.add_node("plan", nop)
        builder.add_node("execute", nop)
        builder.add_edge("__start__", "plan")
        builder.add_conditional_edges("plan", lambda s: "go", {"go": "execute"})

        from voyage_framework.langgraph_tools.visualizer import GraphvizExporter

        exporter = GraphvizExporter(builder)
        dot = exporter.to_dot()
        assert "digraph VoyageGraph" in dot
        assert "plan" in dot
        assert "execute" in dot


class TestCheckpointAdapter:
    @pytest.mark.asyncio
    async def test_checkpoint_logs_events(self, tmp_engine):
        from voyage_framework.langgraph_tools.checkpoint_adapter import EventEngineCheckpoint

        checkpoint = EventEngineCheckpoint(tmp_engine, project_id="graph-test")
        state = VoyageState(role="developer", project_id="graph-test")
        checkpoint.on_node_start("plan", state)
        checkpoint.on_node_end("plan", state)
        checkpoint.on_edge_taken("plan", "execute", None)

        started = tmp_engine.get_events(event_type=EventType.NODE_STARTED)
        completed = tmp_engine.get_events(event_type=EventType.NODE_COMPLETED)
        edges = tmp_engine.get_events(event_type=EventType.EDGE_TAKEN)
        assert len(started) == 1
        assert len(completed) == 1
        assert len(edges) == 1

    @pytest.mark.asyncio
    async def test_checkpoint_get_state(self, tmp_engine):
        from voyage_framework.langgraph_tools.checkpoint_adapter import EventEngineCheckpoint

        checkpoint = EventEngineCheckpoint(tmp_engine, project_id="graph-test")
        state = VoyageState(
            role="developer",
            task="hello",
            project_id="graph-test",
            correlation_id="corr-1",
        )
        checkpoint.on_node_end("plan", state)

        restored = checkpoint.get_state("corr-1")
        assert restored is not None
        assert restored.role == "developer"
        assert restored.task == "hello"


class TestParallelNode:
    @pytest.mark.asyncio
    async def test_parallel_validation_updates_state(self, tmp_path):
        from voyage_framework.core.event_engine import EventEngine
        from voyage_framework.langgraph_tools.nodes import parallel_validation_node
        from voyage_framework.security.sandbox import SecureExecutor

        engine = EventEngine(db_path=tmp_path / "events.db")
        executor = SecureExecutor(SecurityPolicy(), project_root=tmp_path)
        ctx = {"executor": executor, "engine": engine}
        state = VoyageState()

        update = await parallel_validation_node(state, ctx)
        assert "results" in update
        assert len(update["results"]) == 2
