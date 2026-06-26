"""Unit-тесты read-only registry профилей ролей."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from voyage_framework.core.agent_registry import (
    AgentRegistry,
    RoleBoundary,
    RoleCapability,
    RoleProfile,
    default_agent_registry,
)

EXPECTED_ROLES = [
    "architect",
    "developer",
    "reviewer",
    "qa",
    "security",
    "devops",
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
]


def _custom_profile(role_id: str = "custom") -> RoleProfile:
    return RoleProfile(
        role_id=role_id,
        display_name="Custom",
        purpose="Provide a custom profile for tests.",
        responsibilities=("Test registry construction.",),
        capabilities=(RoleCapability(id="testing", description="Run focused tests."),),
        boundaries=(RoleBoundary(id="stay_scoped", description="Stay in scope."),),
        prompt_hints=("Be precise.",),
        output_expectations=("Return evidence.",),
    )


def test_default_registry_contains_only_expected_roles() -> None:
    assert default_agent_registry().list_roles() == EXPECTED_ROLES


def test_list_roles_is_stable_and_returns_a_copy() -> None:
    registry = default_agent_registry()
    roles = registry.list_roles()
    roles.append("mutated")
    assert registry.list_roles() == EXPECTED_ROLES


def test_get_known_and_unknown_role() -> None:
    registry = default_agent_registry()
    assert isinstance(registry.get("developer"), RoleProfile)
    assert registry.get("unknown") is None


def test_require_known_and_unknown_role() -> None:
    registry = default_agent_registry()
    assert registry.require("developer").role_id == "developer"
    with pytest.raises(KeyError, match="Unknown role: unknown"):
        registry.require("unknown")


def test_has_role_for_known_and_unknown_role() -> None:
    registry = default_agent_registry()
    assert registry.has_role("developer") is True
    assert registry.has_role("unknown") is False


def test_describe_returns_json_serializable_copy() -> None:
    registry = default_agent_registry()
    description = registry.describe("developer")
    assert json.loads(json.dumps(description))["role_id"] == "developer"
    description["role_id"] = "mutated"
    assert registry.require("developer").role_id == "developer"


def test_all_profiles_are_complete() -> None:
    for profile in default_agent_registry().list_profiles():
        assert profile.responsibilities
        assert profile.capabilities
        assert profile.boundaries
        assert profile.prompt_hints
        assert profile.output_expectations


def test_registry_accepts_custom_profiles() -> None:
    profile = _custom_profile()
    registry = AgentRegistry([profile])
    assert registry.list_roles() == ["custom"]
    assert registry.require("custom") == profile


def test_duplicate_role_ids_are_rejected() -> None:
    profile = _custom_profile()
    with pytest.raises(ValueError, match="Duplicate role id: custom"):
        AgentRegistry([profile, profile])


@pytest.mark.parametrize("role_id", ["Developer", "developer-role", " developer", ""])
def test_role_ids_are_strict_lowercase_identifiers(role_id: str) -> None:
    with pytest.raises(ValidationError):
        _custom_profile(role_id)


def test_profiles_and_nested_values_are_immutable() -> None:
    profile = default_agent_registry().require("developer")
    with pytest.raises(ValidationError):
        profile.display_name = "Changed"
    with pytest.raises(ValidationError):
        profile.capabilities[0].description = "Changed"
    with pytest.raises(AttributeError):
        profile.responsibilities.append("Changed")  # type: ignore[attr-defined]


def test_list_profiles_does_not_expose_registry_container() -> None:
    registry = default_agent_registry()
    profiles = registry.list_profiles()
    profiles.clear()
    assert registry.list_roles() == EXPECTED_ROLES


def test_registry_does_not_touch_filesystem_or_create_voyage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.iterdir())
    registry = default_agent_registry()
    registry.describe("developer")
    assert list(tmp_path.iterdir()) == before
    assert not (tmp_path / ".voyage").exists()
