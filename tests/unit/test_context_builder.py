"""Tests for ContextBuilder Lite (Phase 4).

Covers:
  - build() creates ProjectContext
  - build() includes YAML-only task
  - build() includes runtime status when TaskRecord exists
  - build() does not mutate TaskRecord
  - build() does not mutate task.yaml
  - check() reports missing runtime record
  - check() reports changed title
  - check() reports changed role
  - check() ignores runtime-only timestamps
  - write_context() creates CONTEXT.json
  - write_context() writes valid JSON
  - empty task_files returns empty context
  - missing task file returns controlled error
  - invalid YAML returns controlled error
  - EventEngine optional: no event engine does not fail
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from voyage_framework.core.context_builder import (
    ContextBuilder,
    ProjectContext,
)
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.task_engine import TaskEngine
from voyage_framework.core.task_models import TaskYamlSpec

# ───────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_engine(tmp_path: Path) -> Iterator[TaskEngine]:
    """TaskEngine with temporary DB."""
    db = tmp_path / "tasks.db"
    with TaskEngine(db_path=db) as engine:
        yield engine


@pytest.fixture
def tmp_event_engine(tmp_path: Path) -> EventEngine:
    """EventEngine with temporary DB."""
    db = tmp_path / "events.db"
    return EventEngine(db_path=db)


@pytest.fixture
def sample_task_yaml(tmp_path: Path) -> Path:
    """Create a sample task.yaml file."""
    yaml_content = """\
id: VF-001
title: Sample Task
description: A test task
role: developer
priority: high
mode: solution
acceptance_criteria:
  - Criterion 1
  - Criterion 2
"""
    yaml_path = tmp_path / "task.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    return yaml_path


# ───────────────────────────────────────────────────────────────
# Test: build() creates ProjectContext
# ───────────────────────────────────────────────────────────────


class TestContextBuilderBuild:
    """Test ContextBuilder.build() method."""

    def test_build_returns_project_context(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])
        assert isinstance(context, ProjectContext)
        assert context.project_id == "default"

    def test_build_includes_yaml_only_task(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])
        assert len(context.tasks) == 1

        task = context.tasks[0]
        assert task.id == "VF-001"
        assert task.title == "Sample Task"
        assert task.role == "developer"
        assert task.has_runtime_record is False

    def test_build_includes_runtime_status_when_record_exists(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        # Create runtime record
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="A test task",
            role="developer",
            priority="high",
            mode="solution",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )
        tmp_engine.create_from_spec(spec)
        tmp_engine.start("VF-001")

        # Build context
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])
        assert len(context.tasks) == 1

        task = context.tasks[0]
        assert task.has_runtime_record is True
        assert task.runtime_status == "in_progress"

    def test_build_does_not_mutate_task_yaml(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        original_content = sample_task_yaml.read_text(encoding="utf-8")
        builder = ContextBuilder(tmp_engine)
        builder.build([sample_task_yaml])
        modified_content = sample_task_yaml.read_text(encoding="utf-8")
        assert original_content == modified_content

    def test_build_does_not_mutate_task_record(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="A test task",
            role="developer",
            acceptance_criteria=["X"],
        )
        tmp_engine.create_from_spec(spec)
        tmp_engine.start("VF-001")

        original_status = tmp_engine.get("VF-001").status

        builder = ContextBuilder(tmp_engine)
        builder.build([sample_task_yaml])

        final_status = tmp_engine.get("VF-001").status
        assert original_status == final_status

    def test_build_empty_task_files_returns_empty_context(
        self,
        tmp_engine: TaskEngine,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([])
        assert context.tasks == []

    def test_build_missing_task_file_skips_gracefully(
        self,
        tmp_engine: TaskEngine,
        tmp_path: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        nonexistent = tmp_path / "nonexistent.yaml"
        context = builder.build([nonexistent])
        assert context.tasks == []

    def test_build_invalid_yaml_skips_gracefully(
        self,
        tmp_engine: TaskEngine,
        tmp_path: Path,
    ) -> None:
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("not: valid: yaml: content:", encoding="utf-8")

        builder = ContextBuilder(tmp_engine)
        context = builder.build([invalid_yaml])
        assert context.tasks == []

    def test_build_multiple_yaml_files(
        self,
        tmp_engine: TaskEngine,
        tmp_path: Path,
    ) -> None:
        yaml1 = tmp_path / "task1.yaml"
        yaml1.write_text(
            """\
id: VF-001
title: Task 1
description: First task
role: developer
acceptance_criteria:
  - X
""",
            encoding="utf-8",
        )

        yaml2 = tmp_path / "task2.yaml"
        yaml2.write_text(
            """\
id: VF-002
title: Task 2
description: Second task
role: architect
acceptance_criteria:
  - X
""",
            encoding="utf-8",
        )

        builder = ContextBuilder(tmp_engine)
        context = builder.build([yaml1, yaml2])
        assert len(context.tasks) == 2

    def test_build_with_event_engine(
        self,
        tmp_engine: TaskEngine,
        tmp_event_engine: EventEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine, event_engine=tmp_event_engine)
        context = builder.build([sample_task_yaml])

        assert context.events_summary is not None
        assert isinstance(context.events_summary.total_events, int)


# ───────────────────────────────────────────────────────────────
# Test: check() diffs
# ───────────────────────────────────────────────────────────────


class TestContextBuilderCheck:
    """Test ContextBuilder.check() method."""

    def test_check_reports_missing_runtime_record(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        diffs = builder.check([sample_task_yaml])
        assert len(diffs) == 1

        diff = diffs[0]
        assert diff.task_id == "VF-001"
        assert diff.exists_in_yaml is True
        assert diff.exists_in_runtime is False

    def test_check_reports_changed_title(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Old Title",
            description="Test",
            role="developer",
            acceptance_criteria=["X"],
        )
        tmp_engine.create_from_spec(spec)

        builder = ContextBuilder(tmp_engine)
        diffs = builder.check([sample_task_yaml])

        diff = diffs[0]
        assert "title" in diff.changed_fields
        assert diff.changed_fields["title"]["yaml"] == "Sample Task"
        assert diff.changed_fields["title"]["runtime"] == "Old Title"

    def test_check_reports_changed_role(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="Test",
            role="architect",
            acceptance_criteria=["X"],
        )
        tmp_engine.create_from_spec(spec)

        builder = ContextBuilder(tmp_engine)
        diffs = builder.check([sample_task_yaml])

        diff = diffs[0]
        assert "role" in diff.changed_fields
        assert diff.changed_fields["role"]["yaml"] == "developer"
        assert diff.changed_fields["role"]["runtime"] == "architect"

    def test_check_ignores_runtime_only_timestamps(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="Test",
            role="developer",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
        )
        tmp_engine.create_from_spec(spec)
        tmp_engine.start("VF-001")

        builder = ContextBuilder(tmp_engine)
        diffs = builder.check([sample_task_yaml])

        # Check should report no changes (timestamps ignored)
        diff = diffs[0]
        assert "created_at" not in diff.changed_fields
        assert "updated_at" not in diff.changed_fields
        assert "started_at" not in diff.changed_fields

    def test_check_reports_changed_acceptance_criteria(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="Test",
            role="developer",
            acceptance_criteria=["Different criteria", "Another one"],
        )
        tmp_engine.create_from_spec(spec)

        builder = ContextBuilder(tmp_engine)
        diffs = builder.check([sample_task_yaml])

        diff = diffs[0]
        assert "acceptance_criteria" in diff.changed_fields
        yaml_criteria = diff.changed_fields["acceptance_criteria"]["yaml"]
        assert yaml_criteria == ["Criterion 1", "Criterion 2"]

    def test_check_does_not_mutate_anything(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-001",
            title="Sample Task",
            description="Test",
            role="developer",
            acceptance_criteria=["X"],
        )
        tmp_engine.create_from_spec(spec)

        original_yaml = sample_task_yaml.read_text(encoding="utf-8")
        original_status = tmp_engine.get("VF-001").status

        builder = ContextBuilder(tmp_engine)
        builder.check([sample_task_yaml])

        assert sample_task_yaml.read_text(encoding="utf-8") == original_yaml
        assert tmp_engine.get("VF-001").status == original_status


# ───────────────────────────────────────────────────────────────
# Test: write_context()
# ───────────────────────────────────────────────────────────────


class TestContextBuilderWrite:
    """Test ContextBuilder.write_context() method."""

    def test_write_context_creates_file(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
        tmp_path: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])

        output = tmp_path / "CONTEXT.json"
        builder.write_context(context, output)

        assert output.exists()

    def test_write_context_writes_valid_json(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
        tmp_path: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])

        output = tmp_path / "CONTEXT.json"
        builder.write_context(context, output)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["project_id"] == "default"
        assert "tasks" in data
        assert "events_summary" in data
        assert "last_sync" in data

    def test_write_context_creates_parent_directories(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
        tmp_path: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        context = builder.build([sample_task_yaml])

        output = tmp_path / "nested" / "deep" / "CONTEXT.json"
        builder.write_context(context, output)

        assert output.exists()
        assert output.parent.exists()


# ───────────────────────────────────────────────────────────────
# Test: EventEngine optional
# ───────────────────────────────────────────────────────────────


class TestContextBuilderOptionalEvents:
    """Test ContextBuilder without EventEngine."""

    def test_build_without_event_engine_succeeds(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        # No event_engine passed
        builder = ContextBuilder(tmp_engine, event_engine=None)
        context = builder.build([sample_task_yaml])

        assert context is not None
        assert context.events_summary is not None
        assert context.events_summary.total_events == 0
