"""Unit tests for ProcessJournal."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.core.models import EventType


class TestProcessJournal:
    @pytest.fixture
    def journal(self, tmp_engine):
        return ProcessJournal(
            tmp_engine,
            project_id="chronicler-test",
            correlation_id="corr-1",
        )

    def test_record_step(self, journal, tmp_engine):
        event = journal.record_step(
            step_type="plan",
            description="Plan the feature",
            inputs={"task": "feature"},
            outputs={"plan": ["step1"]},
        )
        assert event.event_type == EventType.PROCESS_STEP
        assert event.payload["step_type"] == "plan"
        assert event.payload["description"] == "Plan the feature"

    def test_unknown_step_type_raises(self, journal):
        with pytest.raises(ValueError):
            journal.record_step("unknown", "description")

    def test_get_steps(self, journal):
        journal.record_step("plan", "Plan")
        journal.record_step("code", "Code")
        steps = journal.get_steps()
        assert len(steps) == 2
        assert steps[0].payload["step_type"] == "code"  # DESC order by default

    def test_get_steps_filter_by_type(self, journal):
        journal.record_step("plan", "Plan")
        journal.record_step("code", "Code")
        steps = journal.get_steps(step_type="plan")
        assert len(steps) == 1
        assert steps[0].payload["step_type"] == "plan"

    def test_get_step_count(self, journal):
        journal.record_step("plan", "Plan")
        journal.record_step("code", "Code")
        assert journal.get_step_count("corr-1") == 2

    def test_get_last_step(self, journal):
        journal.record_step("plan", "Plan")
        journal.record_step("code", "Code")
        last = journal.get_last_step("corr-1")
        assert last is not None
        assert last.payload["step_type"] == "code"

    def test_get_last_step_empty(self, journal):
        assert journal.get_last_step("corr-missing") is None
