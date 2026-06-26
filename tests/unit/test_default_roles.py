"""Unit tests for the static methodology RoleProfile catalog."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from voyage_framework.core.agent_registry import default_agent_registry
from voyage_framework.core.default_roles import (
    DEFAULT_ROLE_IDS,
    METHODOLOGY_ROLE_IDS,
    RUNTIME_ROLE_IDS,
    all_profiles,
)

_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def test_all_profiles_returns_20_profiles() -> None:
    assert len(all_profiles()) == 20


def test_all_profiles_have_unique_ids() -> None:
    ids = [p.role_id for p in all_profiles()]
    assert len(ids) == len(set(ids)), "Duplicate role_id detected"


def test_default_role_ids_count() -> None:
    assert len(DEFAULT_ROLE_IDS) == 20


def test_default_role_ids_are_unique() -> None:
    assert len(DEFAULT_ROLE_IDS) == len(set(DEFAULT_ROLE_IDS))


def test_methodology_role_ids_count() -> None:
    assert len(METHODOLOGY_ROLE_IDS) == 16


def test_runtime_role_ids_count() -> None:
    assert len(RUNTIME_ROLE_IDS) == 6


def test_developer_and_reviewer_in_both_sets() -> None:
    assert "developer" in RUNTIME_ROLE_IDS
    assert "developer" in METHODOLOGY_ROLE_IDS
    assert "reviewer" in RUNTIME_ROLE_IDS
    assert "reviewer" in METHODOLOGY_ROLE_IDS


def test_developer_and_reviewer_appear_once_in_default() -> None:
    assert DEFAULT_ROLE_IDS.count("developer") == 1
    assert DEFAULT_ROLE_IDS.count("reviewer") == 1


def test_default_role_ids_starts_with_runtime_roles() -> None:
    assert DEFAULT_ROLE_IDS[: len(RUNTIME_ROLE_IDS)] == RUNTIME_ROLE_IDS


def test_all_methodology_roles_in_default_agent_registry() -> None:
    registry = default_agent_registry()
    for role_id in METHODOLOGY_ROLE_IDS:
        assert registry.has_role(role_id), f"Missing methodology role: {role_id}"


def test_all_methodology_profiles_have_non_empty_fields() -> None:
    registry = default_agent_registry()
    for role_id in METHODOLOGY_ROLE_IDS:
        profile = registry.require(role_id)
        assert profile.responsibilities, f"{role_id}: empty responsibilities"
        assert profile.capabilities, f"{role_id}: empty capabilities"
        assert profile.boundaries, f"{role_id}: empty boundaries"
        assert profile.prompt_hints, f"{role_id}: empty prompt_hints"
        assert profile.output_expectations, f"{role_id}: empty output_expectations"


def test_all_role_ids_match_identifier_pattern() -> None:
    for profile in all_profiles():
        assert _ID_RE.match(profile.role_id), f"Invalid role_id: {profile.role_id!r}"


def test_profiles_order_matches_default_role_ids() -> None:
    profile_ids = tuple(p.role_id for p in all_profiles())
    assert profile_ids == DEFAULT_ROLE_IDS


@pytest.mark.parametrize(
    "role_id",
    [
        "interviewer",
        "business_analyst",
        "ux_architect",
        "domain_architect",
        "event_stormer",
        "feature_architect",
        "solution_architect",
        "consistency_validator",
        "mvp_optimizer",
        "voyage_architect",
        "task_generator",
        "tester",
        "auditor",
        "chronicler",
    ],
)
def test_methodology_only_profiles_exist(role_id: str) -> None:
    registry = default_agent_registry()
    profile = registry.require(role_id)
    assert profile.role_id == role_id
    assert profile.display_name
    assert profile.purpose


def test_no_filesystem_io_during_all_profiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.iterdir())
    profiles = all_profiles()
    assert len(profiles) == 20
    assert list(tmp_path.iterdir()) == before
    assert not (tmp_path / ".voyage").exists()
