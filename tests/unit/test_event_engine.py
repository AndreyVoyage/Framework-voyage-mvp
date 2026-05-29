"""Unit tests for EventEngine."""

import pytest
import tempfile
from pathlib import Path
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType


class TestEventEngine:
    def test_init_creates_db(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        assert db.exists()

    def test_append_and_get(self, tmp_path):
        db = tmp_path / "events.db"
        jsonl = tmp_path / "events.jsonl"
        engine = EventEngine(db_path=db, jsonl_path=jsonl)

        ev = Event(event_type=EventType.PLAN_CREATED, payload={"test": True})
        engine.append(ev)

        events = engine.get_events(limit=10)
        assert len(events) == 1
        assert events[0].event_type == EventType.PLAN_CREATED

    def test_get_by_type(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)

        engine.append(Event(event_type=EventType.PLAN_CREATED, payload={}))
        engine.append(Event(event_type=EventType.ERROR_LOGGED, payload={}))
        engine.append(Event(event_type=EventType.PLAN_CREATED, payload={}))

        plans = engine.get_events_by_type(EventType.PLAN_CREATED)
        assert len(plans) == 2

    def test_replay_order(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)

        engine.append(Event(event_type=EventType.PLAN_CREATED, payload={"n": 1}))
        engine.append(Event(event_type=EventType.PLAN_CREATED, payload={"n": 2}))

        replayed = engine.replay()
        assert len(replayed) == 2
        assert replayed[0].payload["n"] == 1
        assert replayed[1].payload["n"] == 2

    def test_project_context(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)

        engine.append(Event(
            event_type=EventType.RULE_ADDED,
            payload={"rule_text": "Test rule"},
            project_id="test-proj",
        ))
        engine.append(Event(
            event_type=EventType.ERROR_LOGGED,
            payload={"error": "Oops"},
            project_id="test-proj",
        ))

        ctx = engine.get_project_context("test-proj")
        assert ctx["total_events"] == 2
        assert len(ctx["rules_added"]) == 1
        assert len(ctx["errors"]) == 1

    def test_count(self, tmp_path):
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        assert engine.count() == 0

        engine.append(Event(event_type=EventType.PLAN_CREATED))
        assert engine.count() == 1

    def test_jsonl_backup(self, tmp_path):
        db = tmp_path / "events.db"
        jsonl = tmp_path / "events.jsonl"
        engine = EventEngine(db_path=db, jsonl_path=jsonl)

        engine.append(Event(event_type=EventType.PLAN_CREATED, payload={"test": True}))
        assert jsonl.exists()
        content = jsonl.read_text()
        assert "PLAN_CREATED" in content
