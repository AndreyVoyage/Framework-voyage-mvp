"""Code Search — semantic search по кодовой базе."""

from __future__ import annotations

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType, SearchResult
from voyage_framework.memory.semantic_store import SemanticStore


class CodeSearch:
    """High-level semantic search по codebase.

    Args:
        store: SemanticStore с проиндексированным кодом.
        engine: Опциональный EventEngine для логирования запросов.
    """

    def __init__(
        self,
        store: SemanticStore,
        engine: EventEngine | None = None,
    ) -> None:
        self.store = store
        self.engine = engine

    def query(self, question: str, top_k: int = 5) -> list[SearchResult]:
        """Найти фрагменты кода, релевантные вопросу."""
        results = self.store.query(text=question, top_k=top_k)
        self._log_query(question, len(results))
        return results

    def query_by_file(
        self,
        file_pattern: str,
        question: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Найти фрагменты кода в файлах, подходящих под шаблон."""
        candidates = self.store.query(
            text=question,
            top_k=top_k * 2,
            filters={"file": file_pattern},
        )
        results = [r for r in candidates if file_pattern in r.metadata.get("file", "")]
        self._log_query(f"{question} (file:{file_pattern})", len(results))
        return results[:top_k]

    def _log_query(self, question: str, result_count: int) -> None:
        """Залогировать MEMORY_QUERIED событие."""
        if not self.engine:
            return

        self.engine.append(Event(
            event_type=EventType.MEMORY_QUERIED,
            payload={
                "collection": self.store.collection_name,
                "question": question,
                "result_count": result_count,
            },
        ))
