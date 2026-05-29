"""Unit tests for TaskGenerator."""

import pytest
import tempfile
from pathlib import Path
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.specs.task_generator import TaskGenerator


class TestTaskGenerator:
    def test_generate_task(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        generator = TaskGenerator(engine)

        spec = generator.generate(
            role="developer",
            task="Implement login feature",
            micro_phase="M1",
            project_id="test-proj",
        )

        assert spec.role == "developer"
        assert spec.task == "Implement login feature"
        assert spec.micro_phase == "M1"
        assert spec.project_id == "test-proj"
        assert spec.task_markdown != ""
        assert spec.context_json != {}
        assert "developer" in spec.task_markdown

    def test_task_has_criteria(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        generator = TaskGenerator(engine)

        spec = generator.generate(role="developer", task="Test")
        assert len(spec.criteria) > 0
        assert "mypy" in str(spec.criteria).lower() or "pytest" in str(spec.criteria).lower()

    def test_write_task_files(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        generator = TaskGenerator(engine)

        spec = generator.generate(role="developer", task="Test")
        task_path, context_path = generator.write_task_files(
            spec,
            task_path=tmp_path / "TASK.md",
            context_path=tmp_path / "CONTEXT.json",
        )

        assert task_path.exists()
        assert context_path.exists()
        assert "TASK" in task_path.read_text()
        assert "developer" in context_path.read_text()

    def test_event_logged(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        generator = TaskGenerator(engine)

        spec = generator.generate(role="developer", task="Test", project_id="test")
        events = engine.get_events(project_id="test")
        assert len(events) == 1
        assert events[0].event_type.value == "plan_created"
