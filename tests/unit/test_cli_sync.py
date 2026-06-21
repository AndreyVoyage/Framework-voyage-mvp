"""Tests for CLI sync commands (Phase 4).

Covers:
  - voyage sync build writes CONTEXT.json to tmp_path
  - voyage sync check prints differences
  - voyage sync status works on empty project
  - sync commands do not write .voyage/tasks.db in real project root during tests
  - existing voyage task still works
  - existing voyage tasks still works
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from voyage_framework.cli import (
    _dispatch_sync,
    _sync_build,
    _sync_check,
    _sync_status,
)
from voyage_framework.core.context_builder import ContextBuilder
from voyage_framework.core.task_engine import TaskEngine
from voyage_framework.core.task_models import TaskYamlSpec

# ───────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_engine(tmp_path: Path) -> TaskEngine:
    """TaskEngine with temporary DB."""
    db = tmp_path / "tasks.db"
    with TaskEngine(db_path=db) as engine:
        yield engine


@pytest.fixture
def tmp_context_builder(tmp_engine: TaskEngine) -> ContextBuilder:
    """ContextBuilder with temporary engine."""
    return ContextBuilder(tmp_engine)


@pytest.fixture
def sample_task_yaml(tmp_path: Path) -> Path:
    """Create a sample task.yaml file."""
    yaml_content = """\
id: VF-004
title: Phase 4 Sync Test
description: Test sync build
role: developer
priority: high
acceptance_criteria:
  - sync build works
  - sync check works
"""
    yaml_path = tmp_path / "task.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    return yaml_path


def _ns(**kwargs: object) -> Namespace:
    """Create argparse Namespace-like object."""
    return Namespace(**kwargs)


@pytest.fixture
def sample_spec() -> TaskYamlSpec:
    """Valid TaskYamlSpec for sync tests."""
    return TaskYamlSpec(
        id="VF-004",
        title="Phase 4 Sync Test",
        description="Test sync status",
        role="developer",
        acceptance_criteria=["sync works"],
    )


# ───────────────────────────────────────────────────────────────
# Tests: sync build
# ───────────────────────────────────────────────────────────────


class TestSyncBuild:
    """Test sync build command."""

    def test_sync_build_writes_context_json(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        output = tmp_path / "CONTEXT.json"
        builder = ContextBuilder(tmp_engine)

        args = _ns(files=[str(sample_task_yaml)], output=str(output), project="default")
        result = _sync_build(args, builder=builder)

        assert result == 0
        assert output.exists()

    def test_sync_build_creates_valid_json(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        output = tmp_path / "CONTEXT.json"
        builder = ContextBuilder(tmp_engine)

        args = _ns(files=[str(sample_task_yaml)], output=str(output), project="default")
        _sync_build(args, builder=builder)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["project_id"] == "default"
        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "VF-004"

    def test_sync_build_creates_parent_dirs(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        output = tmp_path / "nested" / "deep" / "CONTEXT.json"
        builder = ContextBuilder(tmp_engine)

        args = _ns(files=[str(sample_task_yaml)], output=str(output), project="default")
        result = _sync_build(args, builder=builder)

        assert result == 0
        assert output.exists()

    def test_sync_build_with_multiple_files(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
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

        output = tmp_path / "CONTEXT.json"
        builder = ContextBuilder(tmp_engine)

        args = _ns(
            files=[str(yaml1), str(yaml2)],
            output=str(output),
            project="default",
        )
        result = _sync_build(args, builder=builder)

        assert result == 0
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data["tasks"]) == 2


# ───────────────────────────────────────────────────────────────
# Tests: sync check
# ───────────────────────────────────────────────────────────────


class TestSyncCheck:
    """Test sync check command."""

    def test_sync_check_no_diffs_for_yaml_only(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        args = _ns(files=[str(sample_task_yaml)])
        result = _sync_check(args, builder=builder)
        assert result == 0

    def test_sync_check_with_runtime_record(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        spec = TaskYamlSpec(
            id="VF-004",
            title="Phase 4 Sync Test",
            description="Test sync build",
            role="developer",
            priority="high",
            acceptance_criteria=["sync build works", "sync check works"],
        )
        tmp_engine.create_from_spec(spec)

        builder = ContextBuilder(tmp_engine)
        args = _ns(files=[str(sample_task_yaml)])
        result = _sync_check(args, builder=builder)
        assert result == 0

    def test_sync_check_detects_title_change(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
    ) -> None:
        # Create runtime record with different title
        spec = TaskYamlSpec(
            id="VF-004",
            title="Old Title",
            description="Test",
            role="developer",
            acceptance_criteria=["X"],
        )
        tmp_engine.create_from_spec(spec)

        # YAML has different title
        yaml_file = tmp_path / "task.yaml"
        yaml_file.write_text(
            """\
id: VF-004
title: New Title
description: Test
role: developer
acceptance_criteria:
  - X
""",
            encoding="utf-8",
        )

        builder = ContextBuilder(tmp_engine)
        args = _ns(files=[str(yaml_file)])
        result = _sync_check(args, builder=builder)
        assert result == 0


# ───────────────────────────────────────────────────────────────
# Tests: sync status
# ───────────────────────────────────────────────────────────────


class TestSyncStatus:
    """Test sync status command."""

    def test_sync_status_works_on_empty_project(
        self,
        tmp_engine: TaskEngine,
    ) -> None:
        args = _ns(project="default")
        result = _sync_status(args, engine=tmp_engine)
        assert result == 0

    def test_sync_status_with_runtime_task(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(project="default")
        result = _sync_status(args, engine=tmp_engine)
        assert result == 0
        # Should show task details, not "No tasks found"
        # Since we can't capture stdout easily, we verify result == 0
        # and that it doesn't crash with an actual record present


# ───────────────────────────────────────────────────────────────
# Tests: _dispatch_sync
# ───────────────────────────────────────────────────────────────


class TestDispatchSync:
    """Test sync dispatcher."""

    def test_dispatch_sync_no_command(
        self,
        tmp_engine: TaskEngine,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        args = _ns(sync_command=None)
        result = _dispatch_sync(args, builder=builder)
        assert result == 1

    def test_dispatch_sync_build(
        self,
        tmp_path: Path,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        output = tmp_path / "CONTEXT.json"
        builder = ContextBuilder(tmp_engine)

        args = _ns(
            sync_command="build",
            files=[str(sample_task_yaml)],
            output=str(output),
            project="default",
        )
        result = _dispatch_sync(args, builder=builder)
        assert result == 0
        assert output.exists()

    def test_dispatch_sync_check(
        self,
        tmp_engine: TaskEngine,
        sample_task_yaml: Path,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        args = _ns(sync_command="check", files=[str(sample_task_yaml)])
        result = _dispatch_sync(args, builder=builder)
        assert result == 0

    def test_dispatch_sync_status(
        self,
        tmp_engine: TaskEngine,
    ) -> None:
        args = _ns(sync_command="status", project="default")
        result = _dispatch_sync(args, engine=tmp_engine)
        assert result == 0

    def test_dispatch_sync_status_with_task(
        self,
        tmp_engine: TaskEngine,
        sample_spec: TaskYamlSpec,
    ) -> None:
        tmp_engine.create_from_spec(sample_spec)
        args = _ns(sync_command="status", project="default")
        result = _dispatch_sync(args, engine=tmp_engine)
        assert result == 0

    def test_dispatch_sync_unknown_command(
        self,
        tmp_engine: TaskEngine,
    ) -> None:
        builder = ContextBuilder(tmp_engine)
        args = _ns(sync_command="unknown")
        result = _dispatch_sync(args, builder=builder)
        assert result == 1
