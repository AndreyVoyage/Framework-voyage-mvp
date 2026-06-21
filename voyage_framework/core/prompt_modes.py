"""Read-only профили режимов подготовки prompt packages."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class PromptModeNotFoundError(LookupError):
    """Запрошенный режим отсутствует в registry."""


class DuplicateModeError(ValueError):
    """Registry получил несколько профилей с одним id."""


class ModeProfile(BaseModel):
    """Неизменяемое описание режима подготовки prompt package."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, pattern=_ID_PATTERN)
    display_name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    instructions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    output_expectations: tuple[str, ...] = ()
    checklist: tuple[str, ...] = ()


class ModeRegistry:
    """Детерминированный read-only registry профилей режимов."""

    def __init__(self, profiles: list[ModeProfile] | None = None) -> None:
        ordered_profiles = tuple(profiles or ())
        profiles_by_id: dict[str, ModeProfile] = {}
        for profile in ordered_profiles:
            if profile.id in profiles_by_id:
                raise DuplicateModeError(f"Duplicate mode id: {profile.id}")
            profiles_by_id[profile.id] = profile
        self._profiles = ordered_profiles
        self._profiles_by_id = profiles_by_id

    def list_modes(self) -> tuple[str, ...]:
        """Вернуть стабильную последовательность mode ids."""
        return tuple(profile.id for profile in self._profiles)

    def list_profiles(self) -> tuple[ModeProfile, ...]:
        """Вернуть неизменяемую последовательность профилей."""
        return self._profiles

    def get(self, mode_id: str) -> ModeProfile | None:
        """Вернуть профиль или ``None`` для неизвестного режима."""
        return self._profiles_by_id.get(mode_id)

    def require(self, mode_id: str) -> ModeProfile:
        """Вернуть профиль или выбросить domain error."""
        profile = self.get(mode_id)
        if profile is None:
            raise PromptModeNotFoundError(f"Unknown prompt mode: {mode_id}")
        return profile

    def has_mode(self, mode_id: str) -> bool:
        """Проверить наличие режима."""
        return mode_id in self._profiles_by_id

    def describe(self) -> dict[str, Any]:
        """Вернуть JSON-совместимую копию всех профилей."""
        return {profile.id: profile.model_dump(mode="json") for profile in self._profiles}


def _mode(
    mode_id: str,
    display_name: str,
    purpose: str,
    instructions: tuple[str, ...],
    constraints: tuple[str, ...],
    output_expectations: tuple[str, ...],
    checklist: tuple[str, ...],
) -> ModeProfile:
    return ModeProfile(
        id=mode_id,
        display_name=display_name,
        purpose=purpose,
        instructions=instructions,
        constraints=constraints,
        output_expectations=output_expectations,
        checklist=checklist,
    )


def default_mode_registry() -> ModeRegistry:
    """Создать registry шести стандартных режимов Phase 6."""
    profiles = [
        _mode(
            "analysis",
            "Analysis",
            "Understand the problem, contracts, evidence, and risks before proposing changes.",
            ("Inspect relevant evidence.", "Separate facts, assumptions, and open questions."),
            ("Do not modify project files.", "Do not present guesses as verified facts."),
            ("Summarize findings and options.", "Identify risks and missing evidence."),
            ("Relevant contracts inspected", "Assumptions identified", "Risks reported"),
        ),
        _mode(
            "implementation",
            "Implementation",
            "Implement the requested behavior with a focused, tested patch.",
            ("Preserve existing contracts.", "Implement acceptance criteria and tests."),
            ("Avoid broad rewrites.", "Do not expand scope without explicit instruction."),
            ("Provide the implementation.", "Report tests and quality gates."),
            ("Acceptance criteria covered", "Tests added or updated", "Quality gates run"),
        ),
        _mode(
            "review",
            "Review",
            "Assess an existing change for correctness, regressions, and contract compliance.",
            ("Review evidence and diffs.", "Prioritize actionable findings by severity."),
            ("Remain read-only by default.", "Do not implement large new features."),
            ("Lead with concrete findings.", "State residual risks and verification gaps."),
            ("Contracts checked", "Regressions considered", "Findings evidence-backed"),
        ),
        _mode(
            "qa",
            "QA",
            "Verify behavior through reproducible tests, edge cases, and quality gates.",
            ("Build a risk-based test plan.", "Record actual results and reproduction steps."),
            ("Remain read-only by default.", "Do not approve behavior without evidence."),
            ("Report test results.", "Identify failures, flakiness, and coverage gaps."),
            ("Acceptance criteria tested", "Edge cases tested", "Results reproducible"),
        ),
        _mode(
            "security",
            "Security",
            "Assess secrets, injection, command, filesystem, network, and approval risks.",
            ("Model credible threats.", "Recommend proportional mitigations."),
            ("Remain read-only by default.", "Do not weaken sandbox or approval controls."),
            ("Prioritize findings by impact.", "State assumptions and remaining exposure."),
            ("Trust boundaries checked", "Dangerous actions checked", "Mitigations provided"),
        ),
        _mode(
            "handoff",
            "Handoff",
            "Prepare a concise, evidence-based package for the next human or external tool.",
            ("Summarize completed work.", "List verification evidence and remaining work."),
            ("Remain read-only.", "Do not claim unverified completion."),
            ("Provide current state and next steps.", "Highlight blockers and deviations."),
            ("Current state stated", "Evidence listed", "Next steps actionable"),
        ),
    ]
    return ModeRegistry(profiles)
