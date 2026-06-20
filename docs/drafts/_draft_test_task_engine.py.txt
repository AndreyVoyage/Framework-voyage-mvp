"""Тесты Task Engine Voyage Framework.

Покрывают:
- Создание задачи
- Жизненный цикл: pending → in_progress → completed
- Невалидные переходы
- Список с фильтрацией
- Удаление
- Интеграция с EventEngine
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.task_engine import TaskManager, TaskStatus


@pytest.fixture
def temp_manager():
    """Создать TaskManager во временной директории."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"
        manager = TaskManager(db_path=db_path)
        yield manager


@pytest.fixture
def manager_with_events():
    """Создать TaskManager + EventEngine во временной директории."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"
        events_db = Path(tmpdir) / "events.db"
        events_jsonl = Path(tmpdir) / "events.jsonl"
        engine = EventEngine(db_path=events_db, jsonl_path=events_jsonl)
        manager = TaskManager(db_path=db_path, event_engine=engine)
        yield manager


class TestTaskCreation:
    """Тесты создания задач."""

    def test_create_basic(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(
            title="Test Entry Bot",
            description="Implement FSM for daily entry",
            role="developer",
            project_id="skilltracer",
        )
        assert task.title == "Test Entry Bot"
        assert task.status == TaskStatus.PENDING
        assert task.role == "developer"
        assert task.project_id == "skilltracer"
        assert task.task_id

    def test_create_with_criteria(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(
            title="SSL Certbot",
            description="Setup SSL for domain",
            role="devops",
            criteria=["HTTPS works", "Redirect from HTTP", "Auto-renewal"],
        )
        assert len(task.criteria) == 3
        assert task.criteria[0] == "HTTPS works"

    def test_create_with_metadata(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(
            title="Task with meta",
            description="Desc",
            role="developer",
            metadata={"priority": "high", "sprint": 2},
        )
        assert task.metadata["priority"] == "high"
        assert task.metadata["sprint"] == 2

    def test_create_logs_event(self, manager_with_events: TaskManager) -> None:
        manager = manager_with_events
        task = manager.create(
            title="Event test",
            description="Should log task_created",
            role="developer",
        )
        # Проверить, что событие записалось
        events = manager.event_engine.get_events_by_type(
            event_type=pytest.importorskip("voyage_framework.core.models").EventType.TASK_CREATED,
            limit=10,
        )
        assert len(events) >= 1
        assert any(e.payload.get("task_id") == task.task_id for e in events)


class TestTaskLifecycle:
    """Тесты жизненного цикла задачи."""

    def test_pending_to_in_progress(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T1", description="D", role="dev")
        assert task.status == TaskStatus.PENDING

        task = temp_manager.start(task.task_id)
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

    def test_in_progress_to_completed(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T2", description="D", role="dev")
        temp_manager.start(task.task_id)
        task = temp_manager.complete(task.task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_in_progress_to_failed(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T3", description="D", role="dev")
        temp_manager.start(task.task_id)
        task = temp_manager.fail(task.task_id)
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None

    def test_failed_to_pending(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T4", description="D", role="dev")
        temp_manager.start(task.task_id)
        temp_manager.fail(task.task_id)
        task = temp_manager.transition(task.task_id, TaskStatus.PENDING)
        assert task.status == TaskStatus.PENDING

    def test_invalid_transition_raises(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T5", description="D", role="dev")
        with pytest.raises(ValueError, match="Invalid transition"):
            temp_manager.complete(task.task_id)  # pending → completed нельзя

    def test_completed_to_any_raises(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T6", description="D", role="dev")
        temp_manager.start(task.task_id)
        temp_manager.complete(task.task_id)
        with pytest.raises(ValueError, match="Invalid transition"):
            temp_manager.start(task.task_id)

    def test_cancel_from_pending(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T7", description="D", role="dev")
        task = temp_manager.cancel(task.task_id)
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_from_in_progress(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="T8", description="D", role="dev")
        temp_manager.start(task.task_id)
        task = temp_manager.cancel(task.task_id)
        assert task.status == TaskStatus.CANCELLED


class TestTaskQuery:
    """Тесты запросов задач."""

    def test_get_by_id(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="Get me", description="D", role="dev")
        found = temp_manager.get(task.task_id)
        assert found is not None
        assert found.title == "Get me"

    def test_get_not_found(self, temp_manager: TaskManager) -> None:
        assert temp_manager.get("non-existent-id") is None

    def test_list_all(self, temp_manager: TaskManager) -> None:
        temp_manager.create(title="A", description="D", role="dev")
        temp_manager.create(title="B", description="D", role="dev")
        tasks = temp_manager.list()
        assert len(tasks) == 2

    def test_list_by_project(self, temp_manager: TaskManager) -> None:
        temp_manager.create(title="P1", description="D", role="dev", project_id="skilltracer")
        temp_manager.create(title="P2", description="D", role="dev", project_id="other")
        tasks = temp_manager.list(project_id="skilltracer")
        assert len(tasks) == 1
        assert tasks[0].title == "P1"

    def test_list_by_role(self, temp_manager: TaskManager) -> None:
        temp_manager.create(title="R1", description="D", role="developer")
        temp_manager.create(title="R2", description="D", role="devops")
        tasks = temp_manager.list(role="developer")
        assert len(tasks) == 1

    def test_list_by_status(self, temp_manager: TaskManager) -> None:
        t1 = temp_manager.create(title="S1", description="D", role="dev")
        t2 = temp_manager.create(title="S2", description="D", role="dev")
        temp_manager.start(t2.task_id)
        tasks = temp_manager.list(status=TaskStatus.IN_PROGRESS)
        assert len(tasks) == 1
        assert tasks[0].title == "S2"

    def test_count(self, temp_manager: TaskManager) -> None:
        temp_manager.create(title="C1", description="D", role="dev")
        temp_manager.create(title="C2", description="D", role="dev")
        assert temp_manager.count() == 2

    def test_count_by_project(self, temp_manager: TaskManager) -> None:
        temp_manager.create(title="X", description="D", role="dev", project_id="p1")
        temp_manager.create(title="Y", description="D", role="dev", project_id="p2")
        assert temp_manager.count(project_id="p1") == 1


class TestTaskDelete:
    """Тесты удаления."""

    def test_delete_existing(self, temp_manager: TaskManager) -> None:
        task = temp_manager.create(title="Del", description="D", role="dev")
        assert temp_manager.delete(task.task_id) is True
        assert temp_manager.get(task.task_id) is None

    def test_delete_nonexistent(self, temp_manager: TaskManager) -> None:
        assert temp_manager.delete("no-such-id") is False
