"""Smoke tests for package public identity and CLI help compatibility.

Covers Phase 25 requirements:
- canonical Project Knowledge OS identity in package docstring;
- legacy/deprecated/non-canonical wording for runtime/graph surfaces;
- CLI help does not promote AI agent/runtime/orchestration identity;
- CLI help does not create runtime pollution.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LEGACY_WORDING = ("legacy", "deprecated", "non-canonical", "compatibility")
FORBIDDEN_IDENTITY = (
    "AI-native",
    "AI Agent Framework",
    "runtime orchestration framework",
    "Voyage AI Dev Framework v4.0",
)


def _run_cli_help(args: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "voyage_framework.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout + result.stderr


def test_import_voyage_framework() -> None:
    import voyage_framework

    assert voyage_framework.__doc__ is not None
    doc = voyage_framework.__doc__.lower()
    for forbidden in FORBIDDEN_IDENTITY:
        term = forbidden.lower()
        # The term may appear only as an explicit negation of current identity.
        if term in doc:
            pattern = rf"not\s+(an\s+)?{re.escape(term)}"
            assert re.search(pattern, doc), f"docstring asserts current identity: {forbidden}"
    assert "project knowledge os" in doc
    assert "development memory system" in doc


def test_langgraph_runtime_is_available_as_legacy_export() -> None:
    import voyage_framework

    assert hasattr(voyage_framework, "LangGraphRuntime")


def test_cli_top_help_uses_canonical_identity() -> None:
    output = _run_cli_help(["--help"]).lower()
    for forbidden in FORBIDDEN_IDENTITY:
        assert forbidden.lower() not in output, f"top help contains: {forbidden}"
    assert "project knowledge os" in output or "development memory system" in output


def test_cli_run_help_is_legacy() -> None:
    output = _run_cli_help(["run", "--help"]).lower()
    assert "run agent" not in output or any(w in output for w in LEGACY_WORDING)
    assert any(w in output for w in LEGACY_WORDING), "run help missing legacy wording"


def test_cli_graph_help_is_legacy() -> None:
    output = _run_cli_help(["graph", "--help"]).lower()
    assert any(w in output for w in LEGACY_WORDING), "graph help missing legacy wording"


def test_cli_graph_run_help_is_legacy() -> None:
    output = _run_cli_help(["graph", "run", "--help"]).lower()
    assert any(w in output for w in LEGACY_WORDING), "graph run help missing legacy wording"


def test_cli_tasks_help_available() -> None:
    output = _run_cli_help(["tasks", "--help"])
    assert "tasks" in output.lower()


def test_cli_sync_help_available() -> None:
    output = _run_cli_help(["sync", "--help"])
    assert "sync" in output.lower()


def test_cli_help_does_not_create_runtime_pollution(tmp_path: Path) -> None:
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        for args in [
            ["--help"],
            ["tasks", "--help"],
            ["sync", "--help"],
            ["run", "--help"],
            ["graph", "--help"],
            ["graph", "run", "--help"],
        ]:
            _run_cli_help(args)

        assert not (tmp_path / ".voyage").exists()
        assert not (tmp_path / "TASK.md").exists()
        assert not (tmp_path / "CONTEXT.json").exists()
    finally:
        os.chdir(original_cwd)
