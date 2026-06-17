"""Symbol Extractor — извлечение символов из AST."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from tree_sitter import Node, Tree

from voyage_framework.core.models import Symbol

_SYMBOL_CONFIG: dict[str, dict[str, tuple[str, ...]]] = {
    "python": {
        "function": ("function_definition",),
        "class": ("class_definition",),
        "import": ("import_statement", "import_from_statement"),
    },
    "typescript": {
        "function": ("function_declaration", "method_definition"),
        "class": ("class_declaration",),
        "import": ("import_statement", "import_alias"),
    },
}


class SymbolExtractor:
    """Извлекает функции, классы и импорты из AST."""

    def __init__(self, language: str) -> None:
        if language not in _SYMBOL_CONFIG:
            raise ValueError(f"Unsupported language: {language}")
        self.language = language

    def extract_functions(self, tree: Tree, file: Path | str = "") -> list[Symbol]:
        """Извлечь функции."""
        return self._extract(tree, "function", file)

    def extract_classes(self, tree: Tree, file: Path | str = "") -> list[Symbol]:
        """Извлечь классы."""
        return self._extract(tree, "class", file)

    def extract_imports(self, tree: Tree, file: Path | str = "") -> list[Symbol]:
        """Извлечь импорты."""
        return self._extract(tree, "import", file)

    def extract_all(self, tree: Tree, file: Path | str = "") -> dict[str, list[Symbol]]:
        """Извлечь все типы символов."""
        return {
            "functions": self.extract_functions(tree, file),
            "classes": self.extract_classes(tree, file),
            "imports": self.extract_imports(tree, file),
        }

    def _extract(
        self,
        tree: Tree,
        kind: Literal["function", "class", "import"],
        file: Path | str,
    ) -> list[Symbol]:
        """Обойти AST и собрать символы заданного типа."""
        target_types = _SYMBOL_CONFIG[self.language][kind]
        symbols: list[Symbol] = []
        seen: set[tuple[int, int]] = set()

        for node in self._walk(tree.root_node, target_types):
            key = (node.start_byte, node.end_byte)
            if key in seen:
                continue
            seen.add(key)

            name_node = node.child_by_field_name("name")
            name = ""
            if name_node and name_node.text:
                name = name_node.text.decode("utf-8")

            source = node.text.decode("utf-8") if node.text else ""
            symbols.append(
                Symbol(
                    name=name or source.split()[0][:40],
                    kind=kind,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    file=str(file),
                    source=source,
                )
            )

        return symbols

    def _walk(self, node: Node, target_types: tuple[str, ...]) -> list[Node]:
        """Рекурсивно обойти дерево и найти ноды нужных типов."""
        results: list[Node] = []
        if node.type in target_types:
            results.append(node)
        for child in node.children:
            results.extend(self._walk(child, target_types))
        return results
