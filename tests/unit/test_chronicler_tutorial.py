"""Tests for TutorialGenerator and TutorialDraft."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.chronicler.tutorial_generator import TutorialDraft, TutorialGenerator


@pytest.fixture
def journal(tmp_engine):
    """ProcessJournal backed by a temporary EventEngine."""
    return ProcessJournal(
        tmp_engine,
        project_id="tutorial-test",
        correlation_id="tutorial-test",
    )


@pytest.fixture
def decision_log(tmp_engine):
    """DecisionLog backed by a temporary EventEngine."""
    return DecisionLog(tmp_engine)


def test_tutorial_generator_returns_markdown(journal, decision_log):
    journal.record_step(
        step_type="plan",
        description="Plan the feature",
        outputs={"code": "def foo(): pass"},
        decision={
            "chosen": "option_b",
            "options": ["option_a", "option_b"],
            "rationale": "better fit",
        },
    )
    journal.record_step(
        step_type="code",
        description="Implement the feature",
        command="pytest",
    )

    generator = TutorialGenerator(journal, decision_log)
    tutorial = generator.generate_tutorial("tutorial-test")

    assert tutorial.startswith("---")
    assert "Plan the feature" in tutorial
    assert "Implement the feature" in tutorial
    assert "def foo(): pass" in tutorial
    assert "pytest" in tutorial
    assert "option_b" in tutorial
    assert "better fit" in tutorial
    assert "Common pitfall" in tutorial


def test_tutorial_generator_empty_correlation_id(journal, decision_log):
    generator = TutorialGenerator(journal, decision_log)
    tutorial = generator.generate_tutorial("missing")
    assert "No steps found" in tutorial


def test_tutorial_generator_example(journal, decision_log, tmp_path):
    journal.record_step(
        step_type="plan",
        description="Plan auth module",
        outputs={"code": "class Auth: pass"},
    )
    journal.record_step(
        step_type="code",
        description="Implement auth module",
    )

    generator = TutorialGenerator(journal, decision_log)
    files = generator.generate_example("tutorial-test", "auth-module")

    assert "TASK.md" in files
    assert "CONTEXT.json" in files
    assert "README.md" in files
    assert "Plan auth module" in files["TASK.md"]
    assert "auth-module" in files["CONTEXT.json"]


def test_tutorial_generator_save_tutorial(journal, decision_log, tmp_path):
    journal.record_step(step_type="plan", description="Plan")
    generator = TutorialGenerator(journal, decision_log)
    path = generator.save_tutorial("tutorial-test", tmp_path / "tutorial.md")
    assert path.exists()
    assert "Plan" in path.read_text(encoding="utf-8")


def test_tutorial_generator_save_example(journal, decision_log, tmp_path):
    journal.record_step(step_type="plan", description="Plan")
    generator = TutorialGenerator(journal, decision_log)
    path = generator.save_example("tutorial-test", "my-example", tmp_path / "examples")
    assert path.is_dir()
    assert (path / "TASK.md").exists()
    assert (path / "CONTEXT.json").exists()
    assert (path / "README.md").exists()


def test_tutorial_draft_uses_generator(journal, decision_log):
    journal.record_step(step_type="plan", description="Plan")
    draft = TutorialDraft(journal)
    text = draft.generate_draft("tutorial-test")
    assert "Plan" in text
