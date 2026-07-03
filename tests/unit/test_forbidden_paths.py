"""Unit tests for the forbidden-path policy module."""

from __future__ import annotations

from pathlib import Path

from voyage_framework.core import forbidden_paths
from voyage_framework.core.forbidden_paths import (
    _FORBIDDEN_PATTERNS_BY_ROLE,
    forbidden_patterns_for_role,
)


def test_framework_role_includes_safety_patterns() -> None:
    patterns = forbidden_patterns_for_role("framework")
    assert ".env" in patterns
    assert ".env.*" in patterns
    assert ".voyage/**" in patterns


def test_generic_role_preserves_current_behavior() -> None:
    patterns = forbidden_patterns_for_role("generic")
    assert patterns == (
        ".env",
        ".env.*",
        ".voyage/**",
    )


def test_narrative_role_preserves_compatibility_patterns() -> None:
    patterns = forbidden_patterns_for_role("narrative")
    assert ".env" in patterns
    assert "*.rpy" in patterns
    assert "novel/game/script.rpy" in patterns
    assert "scenarios/SCENARIO_LIBRARY.json" in patterns
    assert "scenarios/*.py" in patterns
    assert "scenarios/*.md" in patterns


def test_role_lookup_is_case_insensitive() -> None:
    assert forbidden_patterns_for_role("FRAMEWORK") == forbidden_patterns_for_role("framework")
    assert forbidden_patterns_for_role("Narrative") == forbidden_patterns_for_role("narrative")


def test_unknown_role_falls_back_to_generic() -> None:
    patterns = forbidden_patterns_for_role("nonexistent-role")
    assert patterns == forbidden_patterns_for_role("generic")


def test_returned_patterns_are_tuple() -> None:
    patterns = forbidden_patterns_for_role("framework")
    assert isinstance(patterns, tuple)
    assert not isinstance(patterns, list)


def test_registry_is_mapping_of_tuples() -> None:
    assert isinstance(_FORBIDDEN_PATTERNS_BY_ROLE, dict)
    for role, patterns in _FORBIDDEN_PATTERNS_BY_ROLE.items():
        assert isinstance(role, str)
        assert isinstance(patterns, tuple)
        assert all(isinstance(pattern, str) for pattern in patterns)


def test_matching_helpers_behave_like_report_validator() -> None:
    patterns = forbidden_patterns_for_role("framework")
    assert forbidden_paths._matches_any(".env", patterns) is True
    assert forbidden_paths._matches_any(".env.local", patterns) is True
    assert forbidden_paths._matches_any(".voyage/events.jsonl", patterns) is True
    assert forbidden_paths._matches_any("tools/auto-launch.sh", patterns) is True
    assert forbidden_paths._matches_any("src/main.py", patterns) is False


def test_module_has_no_file_io_helpers() -> None:
    source = Path(forbidden_paths.__file__)
    text = source.read_text(encoding="utf-8")  # test-only read of the module under test
    assert "open(" not in text
    assert "os.environ" not in text
