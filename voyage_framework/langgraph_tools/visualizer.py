"""Визуализация графа в Mermaid и Graphviz."""

from __future__ import annotations

from typing import Any


class MermaidExporter:
    """Экспорт графа в Mermaid syntax."""

    def __init__(self, builder: Any) -> None:
        self._builder = builder

    def to_mermaid(self) -> str:
        """Вернуть Mermaid-определение без markdown-обёртки."""
        lines = ["graph TD;"]
        for name in self._builder._nodes:
            safe = self._safe(name)
            lines.append(f"    {safe}[{name}]")

        for from_node, to_node in self._builder._edges:
            lines.append(f"    {self._safe(from_node)} --> {self._safe(to_node)}")

        for from_node, _cond, routes in self._builder._conditional_edges:
            for label, to_node in routes.items():
                lines.append(f"    {self._safe(from_node)} --|{label}|--> {self._safe(to_node)}")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Вернуть Mermaid-диаграмму в markdown-блоке."""
        return f"```mermaid\n{self.to_mermaid()}\n```"

    @staticmethod
    def _safe(name: str) -> str:
        """Заменить символы, недопустимые в Mermaid node id."""
        return name.replace("-", "_").replace(" ", "_")


class GraphvizExporter:
    """Экспорт графа в DOT format."""

    def __init__(self, builder: Any) -> None:
        self._builder = builder

    def to_dot(self) -> str:
        """Вернуть DOT-определение графа."""
        lines = ["digraph VoyageGraph {", '    rankdir="TB";']
        for name in self._builder._nodes:
            lines.append(f'    "{name}";')
        for from_node, to_node in self._builder._edges:
            lines.append(f'    "{from_node}" -> "{to_node}";')
        for from_node, _cond, routes in self._builder._conditional_edges:
            for label, to_node in routes.items():
                lines.append(f'    "{from_node}" -> "{to_node}" [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)
