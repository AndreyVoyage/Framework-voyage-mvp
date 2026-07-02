"""Тесты TaskEngine (Phase 2).

Покрывают:
- Создание TaskRecord из TaskYamlSpec
- Жизненный цикл: все разрешённые переходы
- Невалидные переходы
- Список с фильтрацией
- Timestamp rules (created_at, updated_at, started_at, completed_at, archived_at)
- EventEngine integration (lifecycle logging)
- Windows safety (ресурсы освобождаются)
- Context manager
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import EventType
from voyage_framework.core.task_engine import (
    TaskAlreadyExistsError,
    TaskEngine,
    TaskNotFoundError,
    TaskTransitionError,
)
from voyage_framework.core.task_models import TaskYamlSpec

# ───────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def sample_spec() -> TaskYamlSpec:
    """Валидный TaskYamlSpec для тестов."""
    return TaskYamlSpec(
        id="VF-001",
        title="Implement Task Engine",
        description="Create runtime lifecycle",
        role="developer",
        acceptance_criteria=["Works"],
    )


@pytest.fixture
def tmp_engine(tmp_path: Path) -> TaskEngine:
    """TaskEngine с временной БД."""
    db = tmp_path / "tasks.db"
    return TaskEngine(db_path=db)


@pytest.fixture
def engine_with_events(tmp_path: Path) -> TaskEngine:
    """TaskEngine + EventEngine с временными файлами."""
    db = tmp_path / "tasks.db"
    events_db = tmp_path / "events.db"
    events_jsonl = tmp_path / "events.jsonl"
    ee = EventEngine(db_path=events_db, jsonl_path=events_jsonl)
    return TaskEngine(db_path=db, event_engine=ee)


# ───────────────────────────────────────────────────────────────
# Creation
# ───────────────────────────────────────────────────────────────


class TestCreateFromSpec:
    """Тесты создания TaskRecord из TaskYamlSpec."""

    def test_create_basic(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        record = tmp_engine.create_from_spec(sample_spec)
        assert record.id == "VF-001"
        assert record.title == "Implement Task Engine"
        assert record.status == "pending"
        assert record.role == "developer"
        assert record.priority == "medium"
        assert record.mode == "solution"

    def test_create_full_metadata(self, tmp_engine: TaskEngine) -> None:
        spec = TaskYamlSpec(
            id="VF-002",
            title="Full task",
            description="With metadata",
            role="architect",
            priority="high",
            mode="discover",
            acceptance_criteria=["A", "B"],
            metadata={"sprint": 3, "estimated_hours": 8},
        )
        record = tmp_engine.create_from_spec(spec)
        assert record.priority == "high"
        assert record.mode == "discover"
        assert record.metadata == {"sprint": 3, "estimated_hours": 8}

    def test_create_sets_created_at(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        before = datetime.now(UTC)
        record = tmp_engine.create_from_spec(sample_spec)
        after = datetime.now(UTC)
        assert before <= record.created_at <= after

    def test_create_sets_updated_at(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        record = tmp_engine.create_from_spec(sample_spec)
        assert record.updated_at == record.created_at

    def test_create_stores_criteria(self, tmp_engine: TaskEngine) -> None:
        spec = TaskYamlSpec(
            id="VF-003",
            title="Criteria test",
            description="Test criteria storage",
            role="developer",
            acceptance_criteria=["C1", "C2", "C3"],
        )
        record = tmp_engine.create_from_spec(spec)
        assert record.acceptance_criteria == ["C1", "C2", "C3"]

    def test_create_duplicate_raises(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        with pytest.raises(TaskAlreadyExistsError, match="already exists"):
            tmp_engine.create_from_spec(sample_spec)

    def test_create_event_logged(
        self, engine_with_events: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        engine_with_events.create_from_spec(sample_spec)
        events = engine_with_events.event_engine.get_events_by_type(
            EventType.TASK_CREATED,
            limit=10,
        )
        assert len(events) >= 1
        assert any(e.payload.get("task_id") == "VF-001" for e in events)


# ───────────────────────────────────────────────────────────────
# Get / List
# ───────────────────────────────────────────────────────────────


class TestGetAndList:
    """Тесты получения и списка задач."""

    def test_get_existing(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        found = tmp_engine.get("VF-001")
        assert found is not None
        assert found.title == "Implement Task Engine"

    def test_get_missing_returns_none(self, tmp_engine: TaskEngine) -> None:
        assert tmp_engine.get("nonexistent") is None

    def test_list_all(self, tmp_engine: TaskEngine) -> None:
        tmp_engine.create_from_spec(
            TaskYamlSpec(
                id="VF-001", title="A", description="D", role="developer", acceptance_criteria=["X"]
            )
        )
        tmp_engine.create_from_spec(
            TaskYamlSpec(
                id="VF-002", title="B", description="D", role="developer", acceptance_criteria=["X"]
            )
        )
        tasks = tmp_engine.list()
        assert len(tasks) == 2

    def test_list_by_status(self, tmp_engine: TaskEngine) -> None:
        s1 = TaskYamlSpec(
            id="VF-001", title="A", description="D", role="developer", acceptance_criteria=["X"]
        )
        s2 = TaskYamlSpec(
            id="VF-002", title="B", description="D", role="developer", acceptance_criteria=["X"]
        )
        tmp_engine.create_from_spec(s1)
        tmp_engine.create_from_spec(s2)
        tmp_engine.start("VF-002")
        tasks = tmp_engine.list(status="in_progress")
        assert len(tasks) == 1
        assert tasks[0].id == "VF-002"

    def test_list_by_role(self, tmp_engine: TaskEngine) -> None:
        tmp_engine.create_from_spec(
            TaskYamlSpec(
                id="VF-001", title="A", description="D", role="developer", acceptance_criteria=["X"]
            )
        )
        tmp_engine.create_from_spec(
            TaskYamlSpec(
                id="VF-002", title="B", description="D", role="devops", acceptance_criteria=["X"]
            )
        )
        tasks = tmp_engine.list(role="devops")
        assert len(tasks) == 1
        assert tasks[0].id == "VF-002"

    def test_list_limit(self, tmp_engine: TaskEngine) -> None:
        for i in range(5):
            tmp_engine.create_from_spec(
                TaskYamlSpec(
                    id=f"VF-{i:03d}",
                    title=f"T{i}",
                    description="D",
                    role="developer",
                    acceptance_criteria=["X"],
                )
            )
        tasks = tmp_engine.list(limit=2)
        assert len(tasks) == 2

    def test_list_ordered_by_updated_desc(self, tmp_engine: TaskEngine) -> None:
        s1 = TaskYamlSpec(
            id="VF-001", title="A", description="D", role="developer", acceptance_criteria=["X"]
        )
        s2 = TaskYamlSpec(
            id="VF-002", title="B", description="D", role="developer", acceptance_criteria=["X"]
        )
        tmp_engine.create_from_spec(s1)
        tmp_engine.create_from_spec(s2)
        tmp_engine.start("VF-001")  # обновит updated_at
        tasks = tmp_engine.list()
        assert tasks[0].id == "VF-001"  # последний обновлённый первый

    def test_delete_existing(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        assert tmp_engine.delete("VF-001") is True
        assert tmp_engine.get("VF-001") is None

    def test_delete_nonexistent(self, tmp_engine: TaskEngine) -> None:
        assert tmp_engine.delete("no-such-id") is False


# ───────────────────────────────────────────────────────────────
# Valid transitions
# ───────────────────────────────────────────────────────────────


class TestValidTransitions:
    """Тесты разрешённых переходов."""

    @pytest.fixture
    def engine_with_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> TaskEngine:
        tmp_engine.create_from_spec(sample_spec)
        return tmp_engine

    def test_pending_to_in_progress(self, engine_with_task: TaskEngine) -> None:
        record = engine_with_task.start("VF-001")
        assert record.status == "in_progress"
        assert record.started_at is not None

    def test_pending_to_blocked(self, engine_with_task: TaskEngine) -> None:
        record = engine_with_task.block("VF-001", reason="Need clarification")
        assert record.status == "blocked"

    def test_in_progress_to_blocked(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        record = engine_with_task.block("VF-001", reason="Waiting for API")
        assert record.status == "blocked"

    def test_blocked_to_in_progress(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.block("VF-001", reason="Blocked")
        record = engine_with_task.unblock("VF-001")
        assert record.status == "in_progress"

    def test_in_progress_to_completed(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        record = engine_with_task.complete("VF-001")
        assert record.status == "completed"
        assert record.completed_at is not None

    def test_in_progress_to_failed(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        record = engine_with_task.fail("VF-001", reason="Tests failed")
        assert record.status == "failed"
        assert record.completed_at is not None

    def test_failed_to_in_progress(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.fail("VF-001", reason="Bug")
        record = engine_with_task.start("VF-001")
        assert record.status == "in_progress"
        # started_at не перезаписывается
        first_started = record.started_at
        assert first_started is not None

    def test_completed_to_archived(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        record = engine_with_task.archive("VF-001")
        assert record.status == "archived"
        assert record.archived_at is not None

    def test_failed_to_archived(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.fail("VF-001", reason="Deprecated")
        record = engine_with_task.archive("VF-001")
        assert record.status == "archived"
        assert record.archived_at is not None

    def test_in_progress_to_archived(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        record = engine_with_task.archive("VF-001")
        assert record.status == "archived"

    def test_blocked_to_archived(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.block("VF-001", reason="Stale")
        record = engine_with_task.archive("VF-001")
        assert record.status == "archived"

    def test_pending_to_archived_not_allowed(self, engine_with_task: TaskEngine) -> None:
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.archive("VF-001")


# ───────────────────────────────────────────────────────────────
# Invalid transitions
# ───────────────────────────────────────────────────────────────


class TestInvalidTransitions:
    """Тесты запрещённых переходов."""

    @pytest.fixture
    def engine_with_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> TaskEngine:
        tmp_engine.create_from_spec(sample_spec)
        return tmp_engine

    def test_pending_to_completed(self, engine_with_task: TaskEngine) -> None:
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.complete("VF-001")

    def test_pending_to_failed(self, engine_with_task: TaskEngine) -> None:
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.fail("VF-001", reason="No")

    def test_completed_to_in_progress(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.start("VF-001")

    def test_completed_to_failed(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.fail("VF-001", reason="No")

    def test_archived_to_any(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.archive("VF-001")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.start("VF-001")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.complete("VF-001")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.archive("VF-001")

    def test_failed_to_completed(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.fail("VF-001", reason="Bug")
        with pytest.raises(TaskTransitionError, match="Invalid transition"):
            engine_with_task.complete("VF-001")

    def test_not_found_raises(self, tmp_engine: TaskEngine) -> None:
        with pytest.raises(TaskNotFoundError, match="not found"):
            tmp_engine.start("nonexistent")


# ───────────────────────────────────────────────────────────────
# Timestamp rules
# ───────────────────────────────────────────────────────────────


class TestTimestampRules:
    """Тесты правил timestamps."""

    @pytest.fixture
    def engine_with_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> TaskEngine:
        tmp_engine.create_from_spec(sample_spec)
        return tmp_engine

    def test_updated_at_changes_on_transition(
        self, engine_with_task: TaskEngine, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        before = engine_with_task.get("VF-001").updated_at
        # Coarse system clock ticks can make two quick _now() calls equal;
        # pin the transition's timestamp strictly after `before` deterministically.
        monkeypatch.setattr(engine_with_task, "_now", lambda: before + timedelta(milliseconds=1))
        engine_with_task.start("VF-001")
        after = engine_with_task.get("VF-001").updated_at
        assert after > before

    def test_started_at_set_once(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        first = engine_with_task.get("VF-001").started_at
        engine_with_task.block("VF-001", reason="Pause")
        engine_with_task.unblock("VF-001")
        second = engine_with_task.get("VF-001").started_at
        assert first == second

    def test_completed_at_set_on_complete(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        record = engine_with_task.get("VF-001")
        assert record.completed_at is not None
        assert record.completed_at >= record.started_at

    def test_completed_at_set_on_fail(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.fail("VF-001", reason="Bug")
        record = engine_with_task.get("VF-001")
        assert record.completed_at is not None

    def test_archived_at_set_on_archive(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        engine_with_task.archive("VF-001")
        record = engine_with_task.get("VF-001")
        assert record.archived_at is not None


# ───────────────────────────────────────────────────────────────
# JSON roundtrip
# ───────────────────────────────────────────────────────────────


class TestJsonRoundtrip:
    """Тесты сериализации/десериализации JSON-полей."""

    def test_metadata_roundtrip(self, tmp_engine: TaskEngine) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Meta",
            description="Test metadata",
            role="developer",
            acceptance_criteria=["OK"],
            metadata={"sprint": 2, "tags": ["urgent", "backend"]},
        )
        tmp_engine.create_from_spec(spec)
        record = tmp_engine.get("VF-001")
        assert record.metadata == {"sprint": 2, "tags": ["urgent", "backend"]}

    def test_criteria_roundtrip(self, tmp_engine: TaskEngine) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Criteria",
            description="Test criteria",
            role="developer",
            acceptance_criteria=["C1", "C2", "C3"],
        )
        tmp_engine.create_from_spec(spec)
        record = tmp_engine.get("VF-001")
        assert record.acceptance_criteria == ["C1", "C2", "C3"]


# ───────────────────────────────────────────────────────────────
# EventEngine integration
# ───────────────────────────────────────────────────────────────


class TestEventLogging:
    """Тесты логирования событий в EventEngine."""

    @pytest.fixture
    def engine_with_task(
        self, engine_with_events: TaskEngine, sample_spec: TaskYamlSpec
    ) -> TaskEngine:
        engine_with_events.create_from_spec(sample_spec)
        return engine_with_events

    def _events_for_task(self, engine: TaskEngine, event_type: EventType) -> list:
        return engine.event_engine.get_events_by_type(event_type, limit=10)

    def test_event_logged_on_create(self, engine_with_task: TaskEngine) -> None:
        events = self._events_for_task(engine_with_task, EventType.TASK_CREATED)
        assert len(events) == 1
        assert events[0].payload["task_id"] == "VF-001"
        assert events[0].payload["new_status"] == "pending"

    def test_event_logged_on_start(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        events = self._events_for_task(engine_with_task, EventType.TASK_STARTED)
        assert len(events) == 1
        assert events[0].payload["old_status"] == "pending"
        assert events[0].payload["new_status"] == "in_progress"

    def test_event_logged_on_block(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.block("VF-001", reason="Waiting")
        events = self._events_for_task(engine_with_task, EventType.TASK_BLOCKED)
        assert len(events) == 1
        assert events[0].payload["reason"] == "Waiting"

    def test_event_logged_on_unblock(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.block("VF-001", reason="Blocked")
        engine_with_task.unblock("VF-001")
        events = self._events_for_task(engine_with_task, EventType.TASK_UNBLOCKED)
        assert len(events) == 1
        assert events[0].payload["old_status"] == "blocked"
        assert events[0].payload["new_status"] == "in_progress"

    def test_event_logged_on_complete(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        events = self._events_for_task(engine_with_task, EventType.TASK_COMPLETED)
        assert len(events) == 1

    def test_event_logged_on_fail(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.fail("VF-001", reason="Tests failed")
        events = self._events_for_task(engine_with_task, EventType.TASK_FAILED)
        assert len(events) == 1
        assert events[0].payload["reason"] == "Tests failed"

    def test_event_logged_on_archive(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001")
        engine_with_task.complete("VF-001")
        engine_with_task.archive("VF-001")
        events = self._events_for_task(engine_with_task, EventType.TASK_ARCHIVED)
        assert len(events) == 1

    def test_actor_in_event_payload(self, engine_with_task: TaskEngine) -> None:
        engine_with_task.start("VF-001", actor="codex")
        events = self._events_for_task(engine_with_task, EventType.TASK_STARTED)
        assert events[0].payload["actor"] == "codex"

    def test_source_path_in_event_payload(
        self, engine_with_events: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        spec = sample_spec.model_copy(
            update={"metadata": {"source_path": "/tasks/VF-001/task.yaml"}}
        )
        engine_with_events.create_from_spec(spec)
        events = self._events_for_task(engine_with_events, EventType.TASK_CREATED)
        assert events[0].payload["source_path"] == "/tasks/VF-001/task.yaml"


# ───────────────────────────────────────────────────────────────
# Windows safety / Resource management
# ───────────────────────────────────────────────────────────────


class TestResourceManagement:
    """Тесты освобождения ресурсов на Windows."""

    def test_close_releases_sqlite_file(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        engine = TaskEngine(db_path=db)
        engine.create_from_spec(
            TaskYamlSpec(
                id="VF-001",
                title="CM",
                description="Close test",
                role="developer",
                acceptance_criteria=["OK"],
            )
        )
        engine.close()
        # Дать Windows время освободить файловый дескриптор
        import gc
        import time

        gc.collect()
        time.sleep(0.2)
        # Файл должен быть доступен для удаления
        assert db.exists()
        db.unlink()
        assert not db.exists()

    def test_context_manager_releases(self, tmp_path: Path) -> None:
        db = tmp_path / "tasks.db"
        with TaskEngine(db_path=db) as engine:
            engine.create_from_spec(
                TaskYamlSpec(
                    id="VF-001",
                    title="CM",
                    description="Context manager test",
                    role="developer",
                    acceptance_criteria=["OK"],
                )
            )
        import gc
        import time

        gc.collect()
        time.sleep(0.2)
        assert db.exists()
        db.unlink()
        assert not db.exists()

    def test_no_event_engine_does_not_fail(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        # TaskEngine без EventEngine не должен падать
        record = tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start(record.id)
        assert tmp_engine.get(record.id).status == "in_progress"

    def test_to_dict(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        record = tmp_engine.create_from_spec(sample_spec)
        d = record.to_dict()
        assert d["id"] == "VF-001"
        assert d["status"] == "pending"
        assert "created_at" in d
        assert "metadata" in d
        assert "acceptance_criteria" in d
