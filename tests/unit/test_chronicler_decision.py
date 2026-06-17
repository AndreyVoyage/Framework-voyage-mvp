"""Unit tests for DecisionLog."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.core.models import EventType


class TestDecisionLog:
    @pytest.fixture
    def decision_log(self, tmp_engine):
        return DecisionLog(tmp_engine)

    def test_record_decision(self, decision_log):
        event = decision_log.record_decision(
            context="Phase 4",
            question="Which graph library?",
            options=["LangGraph", "SimpleGraph"],
            chosen="LangGraph",
            rationale="Better ecosystem",
            adrs=["ADR-004"],
            project_id="chronicler-test",
        )
        assert event.event_type == EventType.DECISION_RECORDED
        assert event.payload["chosen"] == "LangGraph"
        assert event.payload["adrs"] == ["ADR-004"]

    def test_get_decisions(self, decision_log):
        decision_log.record_decision(
            context="Phase 4",
            question="Q1",
            options=["A", "B"],
            chosen="A",
            rationale="Because",
            project_id="chronicler-test",
        )
        decisions = decision_log.get_decisions(project_id="chronicler-test")
        assert len(decisions) == 1

    def test_get_decisions_filter_adr(self, decision_log):
        decision_log.record_decision(
            context="Phase 4",
            question="Q1",
            options=["A", "B"],
            chosen="A",
            rationale="Because",
            adrs=["ADR-004"],
            project_id="chronicler-test",
        )
        decisions = decision_log.get_decisions(adr="ADR-004")
        assert len(decisions) == 1
        decisions = decision_log.get_decisions(adr="ADR-999")
        assert len(decisions) == 0

    def test_get_rationale_for(self, decision_log):
        decision_log.record_decision(
            context="Phase 4",
            question="Q1",
            options=["A", "B"],
            chosen="A",
            rationale="Better ecosystem",
            adrs=["ADR-004"],
            project_id="chronicler-test",
        )
        rationales = decision_log.get_rationale_for("ADR-004")
        assert rationales == ["Better ecosystem"]

    def test_generate_adr_update_draft(self, decision_log):
        decision_log.record_decision(
            context="Phase 4",
            question="Q1",
            options=["A", "B"],
            chosen="A",
            rationale="Because A",
            adrs=["ADR-004"],
            project_id="chronicler-test",
        )
        draft = decision_log.generate_adr_update_draft("ADR-004")
        assert "# ADR Update Draft: ADR-004" in draft
        assert "Because A" in draft
        assert "✅ A" in draft
