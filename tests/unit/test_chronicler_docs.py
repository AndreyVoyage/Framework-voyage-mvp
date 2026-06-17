"""Tests for DocsBuilder."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.docs_builder import DocsBuilder
from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.chronicler.tutorial_generator import TutorialGenerator


@pytest.fixture
def populated_builder(tmp_engine):
    """DocsBuilder with a few recorded steps and decisions."""
    journal = ProcessJournal(
        tmp_engine,
        project_id="docs-test",
        correlation_id="chronicler",
    )
    decision_log = DecisionLog(tmp_engine)

    journal.record_step(
        step_type="plan",
        description="Plan chronicler feature",
        outputs={"code": "class ProcessJournal: pass"},
    )
    journal.record_step(
        step_type="code",
        description="Implement chronicler",
        command="pytest tests/unit/test_chronicler_journal.py",
    )
    decision_log.record_decision(
        context="chronicler",
        question="How to store steps?",
        options=["files", "events"],
        chosen="events",
        rationale="EventEngine already provides persistence and audit.",
        adrs=["ADR-001-events"],
        project_id="docs-test",
    )

    generator = TutorialGenerator(journal, decision_log)
    return DocsBuilder(journal, decision_log, generator)


def test_build_all_creates_expected_files(populated_builder, tmp_path):
    out = populated_builder.build_all(project_id="docs-test", output_dir=tmp_path / "docs")

    assert (out / "index.md").exists()
    assert (out / "_config.yml").exists()
    assert (out / "FAQ.md").exists()
    assert (out / "README.md").exists()
    assert (out / "tutorial" / "06-chronicler.md").exists()
    assert (out / "architecture" / "decision-log.md").exists()
    assert (out / "architecture" / "components.md").exists()
    assert (out / "examples" / "auth-module" / "TASK.md").exists()


def test_build_tutorial_for_known_correlation_id(populated_builder, tmp_path):
    path = populated_builder.build_tutorial(
        "chronicler",
        output_dir=tmp_path / "docs",
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Plan chronicler feature" in text
    assert "Implement chronicler" in text


def test_build_tutorial_missing_correlation_id(populated_builder, tmp_path):
    path = populated_builder.build_tutorial(
        "missing-phase",
        output_dir=tmp_path / "docs",
        filename="missing.md",
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "No steps found" in text


def test_build_faq(populated_builder, tmp_path):
    path = populated_builder.build_faq(output_dir=tmp_path / "docs")
    text = path.read_text(encoding="utf-8")
    assert "Frequently Asked Questions" in text
    assert "What is Voyage Framework?" in text


def test_architecture_decision_log_includes_decisions(populated_builder, tmp_path):
    out = populated_builder.build_all(project_id="docs-test", output_dir=tmp_path / "docs")
    decision_path = out / "architecture" / "decision-log.md"
    text = decision_path.read_text(encoding="utf-8")
    assert "How to store steps?" in text
    assert "events" in text
    assert "EventEngine already provides persistence" in text


def test_architecture_components_lists_exports(populated_builder, tmp_path):
    out = populated_builder.build_all(project_id="docs-test", output_dir=tmp_path / "docs")
    components_path = out / "architecture" / "components.md"
    text = components_path.read_text(encoding="utf-8")
    assert "Voyage Framework Components" in text
    assert "ProcessJournal" in text
    assert "DocsBuilder" in text
