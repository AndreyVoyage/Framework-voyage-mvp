"""Integration tests for Chronicler workflow."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.chronicler.replay import ReplayGenerator
from voyage_framework.chronicler.tutorial_generator import TutorialDraft


class TestChroniclerWorkflow:
    @pytest.fixture
    def journal(self, tmp_engine):
        return ProcessJournal(
            tmp_engine,
            project_id="chronicler-workflow",
            correlation_id="corr-workflow",
        )

    @pytest.fixture
    def decision_log(self, tmp_engine):
        return DecisionLog(tmp_engine)

    def test_journal_to_replay(self, journal):
        journal.record_step(
            step_type="plan",
            description="Plan feature",
            command="echo plan",
        )
        journal.record_step(
            step_type="code",
            description="Write code",
            command="echo code",
            outputs={"code": "print('hello')"},
        )

        generator = ReplayGenerator(journal)
        script = generator.generate_script("corr-workflow")
        assert "echo plan" in script
        assert "echo code" in script

    def test_decision_log_to_adr_draft(self, journal, decision_log):
        decision_log.record_decision(
            context="Phase 1 Chronicler",
            question="Where to store steps?",
            options=["SQLite", "Files"],
            chosen="SQLite",
            rationale="Use existing EventEngine",
            adrs=["ADR-007"],
            project_id="chronicler-workflow",
        )

        draft = decision_log.generate_adr_update_draft("ADR-007")
        assert "Use existing EventEngine" in draft

    def test_tutorial_draft(self, journal):
        journal.record_step(
            step_type="plan",
            description="Build Chronicler",
            decision={
                "chosen": "Standalone module",
                "rationale": "Keep runtime clean",
            },
        )
        draft = TutorialDraft(journal).generate_draft("corr-workflow")
        assert "Build Chronicler" in draft
        assert "Standalone module" in draft
