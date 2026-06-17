"""Pure-Python fallback StateGraph на случай отсутствия LangGraph."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from voyage_framework.langgraph_tools.state import VoyageState


class CompiledGraph:
    """Скомпилированный simple_graph, готовый к запуску."""

    def __init__(
        self,
        nodes: dict[str, Callable[..., Any]],
        edges: list[tuple[str, str]],
        conditional_edges: list[tuple[str, Callable[..., Any], dict[str, str]]],
    ) -> None:
        self._nodes = nodes
        self._edges = edges
        self._conditional_edges = conditional_edges

    def _next_nodes(self, node_name: str, state: VoyageState) -> list[str]:
        """Определить следующие ноды после выполнения node_name."""
        targets: list[str] = []
        for fr, to in self._edges:
            if fr == node_name:
                targets.append(to)
        for fr, cond, routes in self._conditional_edges:
            if fr == node_name:
                key = cond(state)
                target = routes.get(key)
                if target:
                    targets.append(target)
        return targets

    async def _run_node(
        self,
        node_name: str,
        state: VoyageState,
        checkpoint: Any | None,
    ) -> VoyageState:
        """Выполнить одну ноду и вернуть обновлённый state."""
        if checkpoint is not None:
            checkpoint.on_node_start(node_name, state)

        fn = self._nodes[node_name]
        update = await fn(state)

        if isinstance(update, VoyageState):
            new_state = update
        elif isinstance(update, dict):
            new_state = state.model_copy(update=update, deep=True)
        else:
            new_state = state

        if checkpoint is not None:
            checkpoint.on_node_end(node_name, new_state)
        return new_state

    async def invoke(
        self,
        state: VoyageState,
        config: dict[str, Any] | None = None,
    ) -> VoyageState:
        """Запустить граф от начального состояния до __end__."""
        cfg = config.get("configurable", {}) if config else {}
        checkpoint = cfg.get("checkpoint_callback")
        current_state = state.model_copy(deep=True)
        current_nodes = ["__start__"]

        while current_nodes and "__end__" not in current_nodes:
            next_nodes: list[str] = []

            for node_name in current_nodes:
                if node_name == "__start__":
                    targets = self._next_nodes("__start__", current_state)
                elif node_name == "__end__":
                    continue
                else:
                    current_state = await self._run_node(node_name, current_state, checkpoint)
                    targets = self._next_nodes(node_name, current_state)

                if checkpoint is not None and targets:
                    for target in targets:
                        checkpoint.on_edge_taken(node_name, target, None)

                next_nodes.extend(targets)

            if not next_nodes:
                break
            current_nodes = next_nodes

        return current_state


class StateGraph:
    """Минимальный StateGraph: ноды, рёбра, условные рёбра."""

    def __init__(self, state_schema: type[VoyageState] | None = None) -> None:
        self._state_schema = state_schema or VoyageState
        self._nodes: dict[str, Callable[..., Any]] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable[..., Any], dict[str, str]]] = []

    def add_node(self, name: str, func: Callable[..., Any]) -> StateGraph:
        self._nodes[name] = func
        return self

    def add_edge(self, from_node: str, to_node: str) -> StateGraph:
        self._edges.append((from_node, to_node))
        return self

    def add_conditional_edges(
        self,
        from_node: str,
        condition: Callable[..., Any],
        routes: dict[str, str],
    ) -> StateGraph:
        self._conditional_edges.append((from_node, condition, routes))
        return self

    def compile(self) -> CompiledGraph:
        return CompiledGraph(self._nodes, self._edges, self._conditional_edges)
