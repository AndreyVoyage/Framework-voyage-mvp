"""AST Indexer — индексация исходного кода в Semantic Memory."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from voyage_framework.ast_tools.parser import ASTParser
from voyage_framework.ast_tools.symbols import SymbolExtractor
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType, MemoryEntry
from voyage_framework.memory.semantic_store import SemanticStore


class CodeIndexer:
    """Индексирует файлы проекта в Semantic Store.

    Args:
        store: Хранилище для embeddings.
        parser: Парсер AST. Если None — создаётся для каждого файла по расширению.
        engine: Опциональный EventEngine для логирования.
        include_extensions: Расширения файлов для индексации.
        exclude_patterns: Glob-паттерны для исключения.
    """

    def __init__(
        self,
        store: SemanticStore,
        parser: ASTParser | None = None,
        engine: EventEngine | None = None,
        include_extensions: set[str] | None = None,
        exclude_patterns: set[str] | None = None,
    ) -> None:
        self.store = store
        self.parser = parser
        self.engine = engine
        self.include_extensions = include_extensions or {".py", ".ts", ".tsx"}
        self.exclude_patterns = exclude_patterns or {
            "*/.venv/*", "*/__pycache__/*", "*/node_modules/*", "*/.git/*",
        }

    def index_project(
        self,
        root: Path | str,
        project_id: str = "default",
    ) -> dict[str, int]:
        """Проиндексировать все подходящие файлы в директории.

        Returns:
            Статистика: {"files": N, "symbols": M}.
        """
        root = Path(root)
        files = self._collect_files(root)

        total_symbols = 0
        for path in files:
            symbol_ids = self.index_file(path, project_id=project_id)
            total_symbols += len(symbol_ids)

        self._log_indexed(project_id, len(files), total_symbols)
        return {"files": len(files), "symbols": total_symbols}

    def index_file(
        self,
        path: Path | str,
        project_id: str = "default",
    ) -> list[str]:
        """Проиндексировать один файл.

        Returns:
            Список ID добавленных символов.
        """
        path = Path(path)
        try:
            language = ASTParser.detect_language(path)
        except ValueError:
            return []

        parser = self.parser or ASTParser(language)
        try:
            tree = parser.parse_file(path)
        except ValueError:
            return []
        extractor = SymbolExtractor(language)
        symbols = extractor.extract_all(tree, file=path)

        entries: list[MemoryEntry] = []
        for _kind, symbol_list in symbols.items():
            for symbol in symbol_list:
                entry_id = (
                    f"{project_id}:{path.as_posix()}:{symbol.kind}:"
                    f"{symbol.name}:{symbol.start_line}"
                )
                entries.append(MemoryEntry(
                    id=entry_id,
                    text=symbol.source,
                    metadata={
                        "project_id": project_id,
                        "file": path.as_posix(),
                        "kind": symbol.kind,
                        "name": symbol.name,
                        "start_line": symbol.start_line,
                        "end_line": symbol.end_line,
                    },
                ))

        return self.store.add_documents(entries)

    def _collect_files(self, root: Path) -> list[Path]:
        """Собрать файлы для индексации."""
        files: list[Path] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in self.include_extensions:
                continue
            if any(fnmatch.fnmatch(str(path), pattern) for pattern in self.exclude_patterns):
                continue
            files.append(path)
        return sorted(files)

    def _log_indexed(self, project_id: str, files: int, symbols: int) -> None:
        """Залогировать AST_INDEXED событие."""
        if not self.engine:
            return

        self.engine.append(Event(
            event_type=EventType.AST_INDEXED,
            payload={
                "project_id": project_id,
                "collection": self.store.collection_name,
                "files": files,
                "symbols": symbols,
            },
            project_id=project_id,
        ))
