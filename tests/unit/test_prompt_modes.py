"""Тесты read-only registry режимов Phase 6."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from voyage_framework.core.prompt_modes import (
    DuplicateModeError,
    ModeProfile,
    ModeRegistry,
    PromptModeNotFoundError,
    default_mode_registry,
)

EXPECTED_MODES = ("analysis", "implementation", "review", "qa", "security", "handoff")


def _profile(mode_id: str = "custom") -> ModeProfile:
    return ModeProfile(
        id=mode_id,
        display_name="Custom",
        purpose="Test a custom mode.",
        instructions=("Inspect input.",),
        constraints=("Stay scoped.",),
        output_expectations=("Report evidence.",),
        checklist=("Input inspected",),
    )


def test_default_registry_contains_exact_modes() -> None:
    assert default_mode_registry().list_modes() == EXPECTED_MODES


def test_mode_ids_are_stable() -> None:
    assert default_mode_registry().list_modes() == default_mode_registry().list_modes()


def test_get_known_mode() -> None:
    assert default_mode_registry().get("review") == default_mode_registry().require("review")


def test_get_unknown_mode_returns_none() -> None:
    assert default_mode_registry().get("unknown") is None


def test_require_unknown_mode_raises_domain_error() -> None:
    with pytest.raises(PromptModeNotFoundError, match="Unknown prompt mode: unknown"):
        default_mode_registry().require("unknown")


def test_has_mode_true_and_false() -> None:
    registry = default_mode_registry()
    assert registry.has_mode("qa") is True
    assert registry.has_mode("unknown") is False


def test_describe_is_json_serializable_copy() -> None:
    registry = default_mode_registry()
    description = registry.describe()
    assert json.loads(json.dumps(description))["analysis"]["id"] == "analysis"
    description["analysis"]["id"] = "changed"
    assert registry.require("analysis").id == "analysis"


def test_mode_profile_is_deeply_immutable() -> None:
    profile = default_mode_registry().require("analysis")
    with pytest.raises(ValidationError):
        profile.display_name = "Changed"
    with pytest.raises(AttributeError):
        profile.instructions.append("Changed")  # type: ignore[attr-defined]


def test_registry_rejects_duplicate_ids() -> None:
    profile = _profile()
    with pytest.raises(DuplicateModeError, match="Duplicate mode id: custom"):
        ModeRegistry([profile, profile])


@pytest.mark.parametrize("mode_id", ["Review", "security-review", " qa", ""])
def test_mode_ids_are_strict_lowercase_identifiers(mode_id: str) -> None:
    with pytest.raises(ValidationError):
        _profile(mode_id)


def test_custom_registry_preserves_order() -> None:
    registry = ModeRegistry([_profile("first"), _profile("second")])
    assert registry.list_modes() == ("first", "second")


def test_read_only_modes_prefer_read_only_behavior() -> None:
    registry = default_mode_registry()
    for mode_id in ("review", "qa", "security", "handoff"):
        constraints = " ".join(registry.require(mode_id).constraints).lower()
        assert "read-only" in constraints
