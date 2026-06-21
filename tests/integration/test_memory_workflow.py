"""Integration tests for memory + agent runtime."""

import pytest

from voyage_framework.agents.runtime import AgentRuntime
from voyage_framework.ast_tools.indexer import CodeIndexer
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import EventType, SecurityPolicy
from voyage_framework.memory.code_search import CodeSearch
from voyage_framework.memory.semantic_store import SemanticStore
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor


class TestMemoryWorkflow:
    @pytest.fixture
    def tmp_engine(self, tmp_path):
        db = tmp_path / "events.db"
        return EventEngine(db_path=db)

    @pytest.fixture
    def tmp_store(self):
        return SemanticStore(collection_name="test-codebase")

    @pytest.fixture
    def tmp_code_search(self, tmp_engine, tmp_store):
        return CodeSearch(tmp_store, engine=tmp_engine)

    @pytest.fixture
    def tmp_runtime(self, tmp_engine, tmp_code_search):
        policy = PolicyEnforcer()
        security = SecurityPolicy()
        executor = SecureExecutor(security)
        return AgentRuntime(tmp_engine, executor, policy, code_search=tmp_code_search)

    @pytest.mark.asyncio
    async def test_runtime_queries_memory(
        self,
        tmp_engine,
        tmp_store,
        tmp_code_search,
        tmp_runtime,
        tmp_path,
    ) -> None:
        """Агент получает memory_context из semantic search."""
        src = tmp_path / "auth.py"
        src.write_text("def authenticate_user(token: str): ...\n", encoding="utf-8")

        indexer = CodeIndexer(tmp_store)
        indexer.index_project(tmp_path, project_id="mem-test")

        assert tmp_store.count() > 0

        result = await tmp_runtime.run(
            role="developer",
            task="how to authenticate user",
            plan=["python -c print('ok')"],
            project_id="mem-test",
        )

        assert result.success is True
        assert len(result.state.memory_context) > 0

        events = tmp_engine.get_events(event_type=EventType.MEMORY_QUERIED)
        assert len(events) == 1

        stored = tmp_engine.get_events(event_type=EventType.MEMORY_STORED)
        assert len(stored) == 1
