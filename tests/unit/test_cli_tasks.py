"""Тесты CLI tasks commands (Phase 3).

Покрывают:
- voyage tasks create --file ...
- voyage tasks list
- voyage tasks show <id>
- voyage tasks start <id>
- voyage tasks block <id> --reason
- voyage tasks unblock <id>
- voyage tasks complete <id>
- voyage tasks fail <id> --reason
- voyage tasks archive <id>
- Regression: старая команда voyage task <role> --task "..." не сломана

Все тесты используют tmp_path для изоляции БД.
"""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path

import pytest

from voyage_framework.cli import (
    _dispatch_tasks,
    _tasks_archive,
    _tasks_block,
    _tasks_complete,
    _tasks_create,
    _tasks_fail,
    _tasks_list,
    _tasks_show,
    _tasks_start,
    _tasks_unblock,
    generate_task,
)
from voyage_framework.core.task_engine import TaskEngine
from voyage_framework.core.task_models import TaskYamlSpec

# ───────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_engine(tmp_path: Path) -> Iterator[TaskEngine]:
    """TaskEngine с временной БД."""
    db = tmp_path / "tasks.db"
    with TaskEngine(db_path=db) as engine:
        yield engine


@pytest.fixture
def sample_spec() -> TaskYamlSpec:
    """Валидный TaskYamlSpec."""
    return TaskYamlSpec(
        id="VF-001",
        title="CLI Test Task",
        description="Test task for CLI",
        role="developer",
        acceptance_criteria=["Works"],
    )


# ───────────────────────────────────────────────────────────────
# Helper: создать argparse Namespace
# ───────────────────────────────────────────────────────────────


def _ns(**kwargs: object) -> Namespace:
    """Создать argparse Namespace-like объект."""
    return Namespace(**kwargs)


# ───────────────────────────────────────────────────────────────
# Tests: create
# ───────────────────────────────────────────────────────────────


class TestTasksCreate:
    """Тесты создания задачи через CLI."""

    def test_create_from_yaml(self, tmp_path: Path, tmp_engine: TaskEngine) -> None:
        yaml_content = """\
id: VF-002
title: CLI Created Task
description: Created via CLI
role: developer
acceptance_criteria:
  - CLI creates task
"""
        yaml_path = tmp_path / "task.yaml"
        yaml_path.write_text(yaml_content, encoding="utf-8")

        args = _ns(file=str(yaml_path))
        result = _tasks_create(args, tmp_engine)
        assert result == 0

        record = tmp_engine.get("VF-002")
        assert record is not None
        assert record.title == "CLI Created Task"

    def test_create_missing_file(self, tmp_engine: TaskEngine) -> None:
        args = _ns(file="/nonexistent/task.yaml")
        result = _tasks_create(args, tmp_engine)
        assert result == 1

    def test_create_invalid_yaml(self, tmp_path: Path, tmp_engine: TaskEngine) -> None:
        yaml_content = "id: VF-001\nrole: developer\n"  # missing required fields
        yaml_path = tmp_path / "task.yaml"
        yaml_path.write_text(yaml_content, encoding="utf-8")

        args = _ns(file=str(yaml_path))
        result = _tasks_create(args, tmp_engine)
        assert result == 1


# ───────────────────────────────────────────────────────────────
# Tests: list
# ───────────────────────────────────────────────────────────────


class TestTasksList:
    """Тесты списка задач."""

    def test_list_empty(self, tmp_engine: TaskEngine) -> None:
        args = _ns(status=None, role=None, limit=20)
        result = _tasks_list(args, tmp_engine)
        assert result == 0

    def test_list_shows_created_task(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(status=None, role=None, limit=20)
        result = _tasks_list(args, tmp_engine)
        assert result == 0

    def test_list_by_role(self, tmp_engine: TaskEngine) -> None:
        spec1 = TaskYamlSpec(
            id="VF-001",
            title="Dev task",
            description="D",
            role="developer",
            acceptance_criteria=["X"],
        )
        spec2 = TaskYamlSpec(
            id="VF-002", title="Ops task", description="D", role="devops", acceptance_criteria=["X"]
        )
        tmp_engine.create_from_spec(spec1)
        tmp_engine.create_from_spec(spec2)

        args = _ns(status=None, role="devops", limit=20)
        result = _tasks_list(args, tmp_engine)
        assert result == 0

    def test_list_by_status(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")

        args = _ns(status="in_progress", role=None, limit=20)
        result = _tasks_list(args, tmp_engine)
        assert result == 0

    def test_list_limit(self, tmp_engine: TaskEngine) -> None:
        for i in range(5):
            spec = TaskYamlSpec(
                id=f"VF-{i:03d}",
                title=f"T{i}",
                description="D",
                role="developer",
                acceptance_criteria=["X"],
            )
            tmp_engine.create_from_spec(spec)

        args = _ns(status=None, role=None, limit=2)
        result = _tasks_list(args, tmp_engine)
        assert result == 0


# ───────────────────────────────────────────────────────────────
# Tests: show
# ───────────────────────────────────────────────────────────────


class TestTasksShow:
    """Тесты показа деталей задачи."""

    def test_show_existing_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(task_id="VF-001")
        result = _tasks_show(args, tmp_engine)
        assert result == 0

    def test_show_missing_task_returns_error(self, tmp_engine: TaskEngine) -> None:
        args = _ns(task_id="nonexistent")
        result = _tasks_show(args, tmp_engine)
        assert result == 1


# ───────────────────────────────────────────────────────────────
# Tests: start / block / unblock / complete / fail / archive
# ───────────────────────────────────────────────────────────────


class TestTasksLifecycle:
    """Тесты жизненного цикла задач через CLI."""

    def test_start_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(task_id="VF-001")
        result = _tasks_start(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "in_progress"

    def test_block_task_with_reason(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(task_id="VF-001", reason="Need clarification")
        result = _tasks_block(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "blocked"

    def test_unblock_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        tmp_engine.block("VF-001", reason="Blocked")
        args = _ns(task_id="VF-001")
        result = _tasks_unblock(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "in_progress"

    def test_complete_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(task_id="VF-001")
        result = _tasks_complete(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "completed"

    def test_fail_task_with_reason(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(task_id="VF-001", reason="Tests failed")
        result = _tasks_fail(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "failed"

    def test_archive_task(self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        tmp_engine.complete("VF-001")
        args = _ns(task_id="VF-001")
        result = _tasks_archive(args, tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-001").status == "archived"

    def test_invalid_transition_returns_error(
        self, tmp_engine: TaskEngine, sample_spec: TaskYamlSpec
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        # pending → completed напрямую нельзя
        args = _ns(task_id="VF-001")
        result = _tasks_complete(args, tmp_engine)
        assert result == 1

    def test_not_found_returns_error(self, tmp_engine: TaskEngine) -> None:
        args = _ns(task_id="nonexistent")
        result = _tasks_start(args, tmp_engine)
        assert result == 1


# ───────────────────────────────────────────────────────────────
# Tests: _dispatch_tasks
# ───────────────────────────────────────────────────────────────


class TestDispatchTasks:
    """Тесты диспетчера tasks."""

    def test_dispatch_no_command(self, tmp_engine: TaskEngine) -> None:
        args = _ns(tasks_command=None)
        result = _dispatch_tasks(args, engine=tmp_engine)
        assert result == 1

    def test_dispatch_create_uses_injected_engine(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
    ) -> None:
        yaml_content = """\
id: VF-101
title: Dispatched
description: Via dispatch
role: developer
acceptance_criteria:
  - OK
"""
        yaml_path = tmp_path / "task.yaml"
        yaml_path.write_text(yaml_content, encoding="utf-8")

        args = _ns(tasks_command="create", file=str(yaml_path))
        result = _dispatch_tasks(args, engine=tmp_engine)
        assert result == 0
        assert tmp_engine.get("VF-101") is not None

    def test_dispatch_list_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(tasks_command="list", status=None, role=None, limit=20)
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_show_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(tasks_command="show", task_id="VF-001")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_start_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(tasks_command="start", task_id="VF-001")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_block_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(tasks_command="block", task_id="VF-001", reason="Waiting")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_unblock_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        tmp_engine.block("VF-001", reason="Waiting")
        args = _ns(tasks_command="unblock", task_id="VF-001")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_complete_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(tasks_command="complete", task_id="VF-001")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_fail_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        args = _ns(tasks_command="fail", task_id="VF-001", reason="Tests failed")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0

    def test_dispatch_archive_uses_injected_engine(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        tmp_engine.start("VF-001")
        tmp_engine.complete("VF-001")
        args = _ns(tasks_command="archive", task_id="VF-001")
        assert _dispatch_tasks(args, engine=tmp_engine) == 0


# ───────────────────────────────────────────────────────────────
# Regression tests: old CLI not broken
# ───────────────────────────────────────────────────────────────


class TestLegacyTaskCommand:
    """Тесты, что старая команда voyage task <role> --task не сломана."""

    def test_legacy_task_command_still_works(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        # Эмулируем вызов generate_task с правильными аргументами
        args = _ns(
            role="developer",
            task="Implement test feature",
            phase=None,
            project="default",
        )
        # Функция должна выполниться без ошибок (сгенерирует TASK.md + CONTEXT.json)
        result = generate_task(args)
        assert result == 0
        assert (tmp_path / "TASK.md").exists()
        assert (tmp_path / "CONTEXT.json").exists()
        assert not (tmp_path / ".voyage" / "tasks.db").exists()

    def test_legacy_task_command_with_phase(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        args = _ns(
            role="architect",
            task="Design database schema",
            phase="M2",
            project="default",
        )
        result = generate_task(args)
        assert result == 0
        assert (tmp_path / "TASK.md").exists()
        assert (tmp_path / "CONTEXT.json").exists()

    def test_legacy_task_command_does_not_route_to_tasks_runtime(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import voyage_framework.cli as cli

        monkeypatch.chdir(tmp_path)
        called = False

        def fail_if_called(args: Namespace, engine: TaskEngine | None = None) -> int:
            del args, engine
            nonlocal called
            called = True
            return 1

        monkeypatch.setattr(cli, "_dispatch_tasks", fail_if_called)
        monkeypatch.setattr(
            "sys.argv",
            ["voyage", "task", "developer", "--task", "Legacy task"],
        )

        assert cli.main() == 0
        assert called is False
