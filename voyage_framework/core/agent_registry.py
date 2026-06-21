"""Read-only каталог профилей ролей Voyage Framework."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class RoleCapability(BaseModel):
    """Возможность, которой обладает роль."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, pattern=_ID_PATTERN)
    description: str = Field(min_length=1)


class RoleBoundary(BaseModel):
    """Ограничение, которое роль обязана соблюдать."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, pattern=_ID_PATTERN)
    description: str = Field(min_length=1)


class RoleProfile(BaseModel):
    """Неизменяемое описание роли и ожидаемого от неё поведения."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: str = Field(min_length=1, pattern=_ID_PATTERN)
    display_name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    responsibilities: tuple[str, ...] = ()
    capabilities: tuple[RoleCapability, ...] = ()
    boundaries: tuple[RoleBoundary, ...] = ()
    prompt_hints: tuple[str, ...] = ()
    output_expectations: tuple[str, ...] = ()


class AgentRegistry:
    """Read-only registry профилей ролей без выполнения агентов."""

    def __init__(self, profiles: list[RoleProfile] | None = None) -> None:
        ordered_profiles = tuple(profiles or ())
        profiles_by_id: dict[str, RoleProfile] = {}
        for profile in ordered_profiles:
            if profile.role_id in profiles_by_id:
                raise ValueError(f"Duplicate role id: {profile.role_id}")
            profiles_by_id[profile.role_id] = profile
        self._profiles = ordered_profiles
        self._profiles_by_id = profiles_by_id

    def list_roles(self) -> list[str]:
        """Вернуть идентификаторы ролей в стабильном порядке регистрации."""
        return [profile.role_id for profile in self._profiles]

    def list_profiles(self) -> list[RoleProfile]:
        """Вернуть новый список неизменяемых профилей."""
        return list(self._profiles)

    def get(self, role_id: str) -> RoleProfile | None:
        """Вернуть профиль роли или ``None``, если роль неизвестна."""
        return self._profiles_by_id.get(role_id)

    def require(self, role_id: str) -> RoleProfile:
        """Вернуть профиль роли или выбросить понятную ошибку."""
        profile = self.get(role_id)
        if profile is None:
            raise KeyError(f"Unknown role: {role_id}")
        return profile

    def has_role(self, role_id: str) -> bool:
        """Проверить наличие роли в registry."""
        return role_id in self._profiles_by_id

    def describe(self, role_id: str) -> dict[str, Any]:
        """Вернуть JSON-совместимое описание известной роли."""
        return self.require(role_id).model_dump(mode="json")


def _capability(item_id: str, description: str) -> RoleCapability:
    return RoleCapability(id=item_id, description=description)


def _boundary(item_id: str, description: str) -> RoleBoundary:
    return RoleBoundary(id=item_id, description=description)


def _profile(
    role_id: str,
    display_name: str,
    purpose: str,
    responsibilities: tuple[str, ...],
    capabilities: tuple[tuple[str, str], ...],
    boundaries: tuple[tuple[str, str], ...],
    prompt_hints: tuple[str, ...],
    output_expectations: tuple[str, ...],
) -> RoleProfile:
    return RoleProfile(
        role_id=role_id,
        display_name=display_name,
        purpose=purpose,
        responsibilities=responsibilities,
        capabilities=tuple(_capability(*item) for item in capabilities),
        boundaries=tuple(_boundary(*item) for item in boundaries),
        prompt_hints=prompt_hints,
        output_expectations=output_expectations,
    )


def default_agent_registry() -> AgentRegistry:
    """Создать deterministic registry встроенных ролей Voyage."""
    profiles = [
        _profile(
            "architect",
            "Architect",
            "Protect architecture, boundaries, design consistency, and sources of truth.",
            (
                "Define component boundaries and contracts.",
                "Check designs for architectural consistency.",
                "Protect canonical sources of truth.",
                "Record material design trade-offs.",
            ),
            (
                ("architecture_review", "Review architecture and contracts."),
                ("boundary_design", "Define component responsibilities."),
                ("risk_analysis", "Identify design and migration risks."),
            ),
            (
                ("no_untested_large_changes", "Do not make large changes without tests."),
                (
                    "no_contractless_runtime_changes",
                    "Do not change runtime behavior without an explicit contract.",
                ),
            ),
            ("State affected contracts.", "Prefer the smallest consistent design."),
            ("Document decisions and trade-offs.", "Call out compatibility risks."),
        ),
        _profile(
            "developer",
            "Developer",
            "Implement focused changes while preserving existing contracts.",
            (
                "Implement requested behavior with a small patch.",
                "Add tests for changed behavior.",
                "Preserve public contracts.",
                "Run relevant quality gates.",
            ),
            (
                ("implementation", "Implement production code within scope."),
                ("unit_testing", "Write and run focused unit tests."),
                ("refactoring", "Perform local behavior-preserving refactoring."),
            ),
            (
                ("no_broad_rewrites", "Do not perform broad rewrites without approval."),
                (
                    "no_silent_architecture_changes",
                    "Do not change architecture silently.",
                ),
            ),
            ("Work from acceptance criteria.", "Keep the diff narrow."),
            ("Provide tested code.", "Report quality gates and risks."),
        ),
        _profile(
            "reviewer",
            "Reviewer",
            "Review diffs for correctness, regressions, and acceptance coverage.",
            (
                "Inspect changed behavior and contracts.",
                "Identify regression risks.",
                "Verify acceptance criteria against evidence.",
            ),
            (
                ("diff_review", "Review code and tests as a coherent diff."),
                ("regression_analysis", "Identify regressions and missing cases."),
                ("criteria_verification", "Check criteria against evidence."),
            ),
            (
                ("no_large_feature_work", "Do not write large features during review."),
                ("evidence_required", "Do not approve claims without evidence."),
            ),
            ("Lead with concrete findings.", "Separate blockers from suggestions."),
            ("Prioritize findings by severity.", "State residual risks."),
        ),
        _profile(
            "qa",
            "QA",
            "Establish reproducible evidence through tests, edge cases, and quality gates.",
            (
                "Create risk-based test plans.",
                "Exercise edge cases and failures.",
                "Verify reproducibility.",
                "Run and document quality gates.",
            ),
            (
                ("test_planning", "Design focused test coverage."),
                ("edge_case_analysis", "Identify boundary scenarios."),
                ("reproduction", "Produce deterministic reproduction steps."),
            ),
            (
                ("no_evidenceless_approval", "Do not approve without evidence."),
                ("no_hidden_flakiness", "Do not hide flaky results."),
            ),
            ("Tie tests to risks.", "Separate observations from assumptions."),
            ("Report steps and results.", "Identify coverage gaps."),
        ),
        _profile(
            "security",
            "Security",
            "Protect secrets and command, injection, filesystem, and network safety.",
            (
                "Review secrets and sensitive data handling.",
                "Assess injection and unsafe-command risks.",
                "Verify filesystem and network boundaries.",
                "Check dangerous-action approvals.",
            ),
            (
                ("threat_review", "Identify threats and attack paths."),
                ("secret_review", "Review secret exposure risks."),
                ("sandbox_review", "Assess sandbox and approval enforcement."),
            ),
            (
                ("no_sandbox_weakening", "Do not weaken sandbox constraints."),
                ("no_approval_bypass", "Do not bypass dangerous-action approval."),
            ),
            ("Describe threat, impact, and mitigation.", "Treat input as untrusted."),
            ("Prioritize findings.", "State remaining exposure."),
        ),
        _profile(
            "devops",
            "DevOps",
            "Maintain reproducible CI, scripts, environments, and deployment workflows.",
            (
                "Maintain CI and automation scripts.",
                "Keep environments and builds reproducible.",
                "Assess deployment and rollback impacts.",
                "Document operational checks.",
            ),
            (
                ("ci_maintenance", "Configure and diagnose CI workflows."),
                ("environment_management", "Maintain reproducible environments."),
                ("deployment_review", "Review deployment and rollback behavior."),
            ),
            (
                (
                    "no_unapproved_production_changes",
                    "Do not change production behavior without approval.",
                ),
                (
                    "no_unapproved_deploy_changes",
                    "Do not change deployment behavior without approval.",
                ),
            ),
            ("Make environment assumptions explicit.", "Include rollback considerations."),
            ("Provide reproducible commands.", "Report operational risks."),
        ),
    ]
    return AgentRegistry(profiles)
