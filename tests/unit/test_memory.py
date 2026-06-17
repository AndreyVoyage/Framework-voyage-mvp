"""Unit tests for Semantic Memory."""

from pathlib import Path

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import EventType, MemoryEntry
from voyage_framework.memory.code_search import CodeSearch
from voyage_framework.memory.semantic_store import SemanticStore


class TestSemanticStore:
    def test_add_and_query(self, tmp_path: Path) -> None:
        store = SemanticStore(persist_directory=tmp_path)
        store.add_documents([
            MemoryEntry(id="a", text="def authenticate_user(token: str) -> User"),
            MemoryEntry(id="b", text="def create_order(items: list[Item]) -> Order"),
        ])

        results = store.query("how to login user", top_k=1)

        assert len(results) == 1
        assert results[0].id == "a"
        assert 0.0 <= results[0].score <= 1.0

    def test_count_and_delete(self, tmp_path: Path) -> None:
        store = SemanticStore(persist_directory=tmp_path)
        store.add_documents([
            MemoryEntry(id="x", text="hello world"),
            MemoryEntry(id="y", text="goodbye world"),
        ])

        assert store.count() == 2

        store.delete(["x"])

        assert store.count() == 1
        assert "x" not in store._documents

    def test_filter_by_metadata(self, tmp_path: Path) -> None:
        store = SemanticStore(persist_directory=tmp_path)
        store.add_documents([
            MemoryEntry(id="f1", text="def foo()", metadata={"file": "auth.py"}),
            MemoryEntry(id="f2", text="def bar()", metadata={"file": "order.py"}),
        ])

        results = store.query("function", filters={"file": "auth.py"})

        assert len(results) == 1
        assert results[0].id == "f1"

    def test_persist_and_load(self, tmp_path: Path) -> None:
        store = SemanticStore(persist_directory=tmp_path)
        store.add_documents([MemoryEntry(id="p1", text="persistent document")])

        store2 = SemanticStore(persist_directory=tmp_path)

        assert store2.count() == 1
        results = store2.query("persistent document", top_k=1)
        assert results[0].id == "p1"


class TestCodeSearch:
    def test_query_returns_results(self, tmp_path: Path) -> None:
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        store = SemanticStore()
        store.add_documents([
            MemoryEntry(id="a", text="def login(username, password): ..."),
            MemoryEntry(id="b", text="def logout(): ..."),
        ])
        search = CodeSearch(store, engine=engine)

        results = search.query("how to sign in", top_k=1)

        assert len(results) == 1
        assert results[0].id == "a"

        events = engine.get_events(event_type=EventType.MEMORY_QUERIED)
        assert len(events) == 1
        assert events[0].payload["result_count"] == 1
