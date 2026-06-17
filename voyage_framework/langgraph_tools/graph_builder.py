"""VoyageGraphBuilder — обёртка над LangGraph или simple_graph fallback."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from voyage_framework.langgraph_tools.simple_graph import StateGraph as SimpleStateGraph
from voyage_framework.langgraph_tools.state import VoyageState

try:
    from langgraph.graph import END, START
    from langgraph.graph import StateGraph as LangStateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - fallback
    LANGGRAPH_AVAILABLE = False


class VoyageGraphBuilder:
    """Строитель графового workflow с единым API для LangGraph и fallback."""

    def __init__(self, state_schema: type[VoyageState] | None = None) -> None:
        self.state_schema = state_schema or VoyageState
        self._nodes: dict[str, Callable[..., Any]] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable[..., Any], dict[str, str]]] = []
        self._compiled: Any = None

        if LANGGRAPH_AVAILABLE:
            self._graph: Any = LangStateGraph(self.state_schema)
        else:
            self._graph = SimpleStateGraph(self.state_schema)

    def add_state_class(self, state_schema: type[VoyageState]) -> VoyageGraphBuilder:
        """Задать Pydantic-схему состояния (используется при инициализации)."""
        self.state_schema = state_schema
        return self

    def add_node(self, name: str, func: Callable[..., Any]) -> VoyageGraphBuilder:
        """Добавить ноду в граф."""
        self._nodes[name] = func
        self._graph.add_node(name, func)
        return self

    def add_edge(self, from_node: str, to_node: str) -> VoyageGraphBuilder:
        """Добавить прямое ребро."""
        self._edges.append((from_node, to_node))
        if LANGGRAPH_AVAILABLE:
            self._graph.add_edge(self._normalize(from_node), self._normalize(to_node))
        else:
            self._graph.add_edge(from_node, to_node)
        return self

    def add_conditional_edges(
        self,
        from_node: str,
        condition: Callable[..., Any],
        routes: dict[str, str],
    ) -> VoyageGraphBuilder:
        """Добавить условное ветвление."""
        self._conditional_edges.append((from_node, condition, routes))
        if LANGGRAPH_AVAILABLE:
            self._graph.add_conditional_edges(
                self._normalize(from_node),
                condition,
                {k: self._normalize(v) for k, v in routes.items()},
            )
        else:
            self._graph.add_conditional_edges(from_node, condition, routes)
        return self

    def compile(self) -> Any:
        """Скомпилировать граф."""
        self._compiled = self._graph.compile()
        return self._compiled

    async def invoke(
        self,
        initial_state: VoyageState | dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> VoyageState:
        """Запустить граф от начального состояния."""
        if isinstance(initial_state, dict):
            state = self.state_schema(**initial_state)
        else:
            state = initial_state

        compiled: Any = self._compiled if self._compiled is not None else self.compile()

        if LANGGRAPH_AVAILABLE:
            result = await compiled.ainvoke(state, config=config)
            if isinstance(result, self.state_schema):
                return result
            return self.state_schema(**result) if isinstance(result, dict) else state
        result = await compiled.invoke(state, config=config)
        return result if isinstance(result, self.state_schema) else self.state_schema(**result)

    def _normalize(self, node: str) -> Any:
        """Преобразовать служебные имена нод в константы LangGraph."""
        if not LANGGRAPH_AVAILABLE:
            return node
        if node == "__start__":
            return START
        if node == "__end__":
            return END
        return node
