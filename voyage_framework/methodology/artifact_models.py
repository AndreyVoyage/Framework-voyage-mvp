"""Pydantic contracts for Voyage Framework methodology artifacts 00–09.

Each artifact corresponds to one step in the methodology pipeline defined in
docs/VOYAGE_METHOD_LOCK.md §4.1. Models are pure data contracts: no filesystem IO,
no database access, no runtime integration.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class MethodologyArtifact(BaseModel):
    """Frozen base model shared by all methodology artifact contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = "1.0"
    artifact_id: str
    phase: int
    title: str
    summary: str
    owner_role: str
    status: str = "draft"
    open_questions: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


class ProjectIntakeArtifact(MethodologyArtifact):
    """00-project-intake.json — Step 0, authored by human, owned by Interviewer."""

    artifact_id: Literal["00-project-intake"] = "00-project-intake"
    phase: Literal[0] = 0
    owner_role: Literal["interviewer"] = "interviewer"

    raw_idea: str
    target_users: tuple[str, ...]
    problem_statement: str
    desired_outcomes: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    non_goals: tuple[str, ...] = ()


class DiscoveryArtifact(MethodologyArtifact):
    """01-discovery.json — Step 1, produced by Interviewer."""

    artifact_id: Literal["01-discovery"] = "01-discovery"
    phase: Literal[1] = 1
    owner_role: Literal["interviewer"] = "interviewer"

    problem: str
    why_now: str
    current_solution: str
    switching_triggers: tuple[str, ...] = ()
    success_criteria: tuple[str, ...]
    constraints: tuple[str, ...] = ()


class BusinessArtifact(MethodologyArtifact):
    """02-business.json — Step 2, produced by Business Analyst."""

    artifact_id: Literal["02-business"] = "02-business"
    phase: Literal[2] = 2
    owner_role: Literal["business_analyst"] = "business_analyst"

    audience: tuple[str, ...]
    value_proposition: str
    jobs_to_be_done: tuple[str, ...]
    risks: tuple[str, ...] = ()
    business_constraints: tuple[str, ...] = ()


class UXArtifact(MethodologyArtifact):
    """03-ux.json — Step 3, produced by UX Architect."""

    artifact_id: Literal["03-ux"] = "03-ux"
    phase: Literal[3] = 3
    owner_role: Literal["ux_architect"] = "ux_architect"

    primary_user_flows: tuple[str, ...]
    screens_or_surfaces: tuple[str, ...]
    interaction_principles: tuple[str, ...]
    accessibility_notes: tuple[str, ...] = ()


class DomainArtifact(MethodologyArtifact):
    """04-domain.json — Step 4, produced by Domain Architect."""

    artifact_id: Literal["04-domain"] = "04-domain"
    phase: Literal[4] = 4
    owner_role: Literal["domain_architect"] = "domain_architect"

    entities: tuple[str, ...]
    relationships: tuple[str, ...]
    invariants: tuple[str, ...]
    domain_rules: tuple[str, ...] = ()


class EventStormingArtifact(MethodologyArtifact):
    """05-events.json — Step 5, produced by Event Stormer."""

    artifact_id: Literal["05-events"] = "05-events"
    phase: Literal[5] = 5
    owner_role: Literal["event_stormer"] = "event_stormer"

    domain_events: tuple[str, ...]
    commands: tuple[str, ...] = ()
    actors: tuple[str, ...] = ()
    external_systems: tuple[str, ...] = ()


class FeatureArtifact(MethodologyArtifact):
    """06-features.json — Step 6, produced by Feature Architect."""

    artifact_id: Literal["06-features"] = "06-features"
    phase: Literal[6] = 6
    owner_role: Literal["feature_architect"] = "feature_architect"

    features: tuple[str, ...]
    must_have: tuple[str, ...]
    should_have: tuple[str, ...] = ()
    wont_have: tuple[str, ...] = ()


class SolutionArtifact(MethodologyArtifact):
    """07-solution.json — Step 7, produced by Solution Architect."""

    artifact_id: Literal["07-solution"] = "07-solution"
    phase: Literal[7] = 7
    owner_role: Literal["solution_architect"] = "solution_architect"

    architecture_summary: str
    technology_choices: tuple[str, ...]
    integration_points: tuple[str, ...] = ()
    data_storage_notes: tuple[str, ...] = ()
    operational_constraints: tuple[str, ...] = ()


class ValidationArtifact(MethodologyArtifact):
    """08-validation.json — Step 8, produced by Consistency Validator."""

    artifact_id: Literal["08-validation"] = "08-validation"
    phase: Literal[8] = 8
    owner_role: Literal["consistency_validator"] = "consistency_validator"

    consistency_findings: tuple[str, ...]
    risks: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    verdict: str


class MVPArtifact(MethodologyArtifact):
    """09-mvp.json — Step 9, produced by MVP Optimizer."""

    artifact_id: Literal["09-mvp"] = "09-mvp"
    phase: Literal[9] = 9
    owner_role: Literal["mvp_optimizer"] = "mvp_optimizer"

    mvp_scope: tuple[str, ...]
    deferred_scope: tuple[str, ...] = ()
    milestones: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...]


METHODOLOGY_ARTIFACT_IDS: tuple[str, ...] = (
    "00-project-intake",
    "01-discovery",
    "02-business",
    "03-ux",
    "04-domain",
    "05-events",
    "06-features",
    "07-solution",
    "08-validation",
    "09-mvp",
)

METHODOLOGY_ARTIFACT_MODEL_BY_ID: dict[str, type[MethodologyArtifact]] = {
    "00-project-intake": ProjectIntakeArtifact,
    "01-discovery": DiscoveryArtifact,
    "02-business": BusinessArtifact,
    "03-ux": UXArtifact,
    "04-domain": DomainArtifact,
    "05-events": EventStormingArtifact,
    "06-features": FeatureArtifact,
    "07-solution": SolutionArtifact,
    "08-validation": ValidationArtifact,
    "09-mvp": MVPArtifact,
}


def artifact_model_for_id(artifact_id: str) -> type[MethodologyArtifact]:
    """Return the Pydantic model class for a methodology artifact ID.

    Raises:
        KeyError: if the artifact_id is not a registered methodology artifact.
    """
    try:
        return METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    except KeyError:
        raise KeyError(
            f"Unknown methodology artifact ID: {artifact_id!r}. "
            f"Valid IDs: {METHODOLOGY_ARTIFACT_IDS}"
        ) from None
