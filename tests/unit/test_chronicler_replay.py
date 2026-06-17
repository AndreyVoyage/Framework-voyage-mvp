"""Unit tests for ReplayGenerator."""

from __future__ import annotations

import pytest

from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.chronicler.replay import ReplayGenerator


class TestReplayGenerator:
    @pytest.fixture
    def generator(self, tmp_engine):
        journal = ProcessJournal(
            tmp_engine,
            project_id="chronicler-test",
            correlation_id="corr-replay",
        )
        return ReplayGenerator(journal)

    def _seed_steps(self, journal: ProcessJournal) -> None:
        journal.record_step(
            step_type="plan",
            description="Plan DockerBackend",
            command="echo plan",
        )
        journal.record_step(
            step_type="code",
            description="Implement DockerBackend",
            command="echo code",
            outputs={"code": "class DockerBackend: ..."},
        )
        journal.record_step(
            step_type="test",
            description="Run tests",
            command="pytest tests/ -q",
        )

    def test_generate_script_bash(self, generator, tmp_engine):
        self._seed_steps(generator.journal)
        script = generator.generate_script("corr-replay")
        assert "#!/bin/bash" in script
        assert "set -e" in script
        assert "echo plan" in script
        assert "pytest tests/ -q" in script
        assert "corr-replay" in script

    def test_generate_markdown(self, generator, tmp_engine):
        self._seed_steps(generator.journal)
        md = generator.generate_markdown("corr-replay")
        assert "# Process Replay: corr-replay" in md
        assert "Implement DockerBackend" in md
        assert "pytest tests/ -q" in md

    def test_save_script(self, generator, tmp_path):
        self._seed_steps(generator.journal)
        path = generator.save_script("corr-replay", path=tmp_path / "replay.sh")
        assert path.exists()
        assert "#!/bin/bash" in path.read_text(encoding="utf-8")

    def test_save_script_default_path(self, generator, tmp_path):
        self._seed_steps(generator.journal)
        generator.journal.project_id = "default"
        generator.journal.engine._db_path = tmp_path / "events.db"
        generator.journal.engine.jsonl_path = tmp_path / "events.jsonl"
        path = generator.save_script("corr-replay")
        assert path.name.startswith("replay_")
        assert path.suffix == ".sh"

    def test_generate_script_empty(self, generator):
        script = generator.generate_script("corr-empty")
        assert "Total steps: 0" in script
