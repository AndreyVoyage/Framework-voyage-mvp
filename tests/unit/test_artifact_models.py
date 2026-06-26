"""Unit tests for methodology artifact Pydantic contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from voyage_framework.core.models import EventType
from voyage_framework.methodology.artifact_models import (
    METHODOLOGY_ARTIFACT_IDS,
    METHODOLOGY_ARTIFACT_MODEL_BY_ID,
    BusinessArtifact,
    DiscoveryArtifact,
    DomainArtifact,
    EventStormingArtifact,
    FeatureArtifact,
    MethodologyArtifact,
    MVPArtifact,
    ProjectIntakeArtifact,
    SolutionArtifact,
    UXArtifact,
    ValidationArtifact,
    artifact_model_for_id,
)

# ── Minimal valid kwargs for each artifact ──────────────────────────────────

_MINIMAL_KWARGS: dict[str, dict[str, object]] = {
    "00-project-intake": {
        "title": "Project Intake",
        "summary": "Intake summary",
        "raw_idea": "An idea",
        "target_users": ("User",),
        "problem_statement": "The problem",
        "desired_outcomes": ("Outcome",),
    },
    "01-discovery": {
        "title": "Discovery",
        "summary": "Discovery summary",
        "problem": "The problem",
        "why_now": "Why now",
        "current_solution": "Current workaround",
        "success_criteria": ("Success criterion",),
    },
    "02-business": {
        "title": "Business Analysis",
        "summary": "Business summary",
        "audience": ("Target audience",),
        "value_proposition": "Value prop",
        "jobs_to_be_done": ("Job to be done",),
    },
    "03-ux": {
        "title": "UX Architecture",
        "summary": "UX summary",
        "primary_user_flows": ("Flow 1",),
        "screens_or_surfaces": ("Screen 1",),
        "interaction_principles": ("Principle 1",),
    },
    "04-domain": {
        "title": "Domain Model",
        "summary": "Domain summary",
        "entities": ("Entity 1",),
        "relationships": ("Relationship 1",),
        "invariants": ("Invariant 1",),
    },
    "05-events": {
        "title": "Event Storming",
        "summary": "Events summary",
        "domain_events": ("UserRegistered",),
    },
    "06-features": {
        "title": "Feature Catalog",
        "summary": "Features summary",
        "features": ("Feature 1",),
        "must_have": ("Must have 1",),
    },
    "07-solution": {
        "title": "Solution Architecture",
        "summary": "Solution summary",
        "architecture_summary": "Architecture description",
        "technology_choices": ("Python",),
    },
    "08-validation": {
        "title": "Validation Report",
        "summary": "Validation summary",
        "consistency_findings": ("Finding 1",),
        "verdict": "approved",
    },
    "09-mvp": {
        "title": "MVP Definition",
        "summary": "MVP summary",
        "mvp_scope": ("Core feature",),
        "acceptance_criteria": ("All tests pass",),
    },
}

# ── Expected metadata per artifact ─────────────────────────────────────────

_EXPECTED_METADATA: tuple[tuple[str, int, str], ...] = (
    ("00-project-intake", 0, "interviewer"),
    ("01-discovery", 1, "interviewer"),
    ("02-business", 2, "business_analyst"),
    ("03-ux", 3, "ux_architect"),
    ("04-domain", 4, "domain_architect"),
    ("05-events", 5, "event_stormer"),
    ("06-features", 6, "feature_architect"),
    ("07-solution", 7, "solution_architect"),
    ("08-validation", 8, "consistency_validator"),
    ("09-mvp", 9, "mvp_optimizer"),
)

# ── Test 1: Imports succeed (module-level imports verify this) ──────────────


def test_imports_succeed() -> None:
    assert MethodologyArtifact is not None
    assert ProjectIntakeArtifact is not None
    assert MVPArtifact is not None


# ── Test 2: METHODOLOGY_ARTIFACT_IDS has 10 unique IDs in order ────────────


def test_artifact_ids_count() -> None:
    assert len(METHODOLOGY_ARTIFACT_IDS) == 10


def test_artifact_ids_are_unique() -> None:
    assert len(METHODOLOGY_ARTIFACT_IDS) == len(set(METHODOLOGY_ARTIFACT_IDS))


def test_artifact_ids_order() -> None:
    assert METHODOLOGY_ARTIFACT_IDS == (
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


# ── Test 3: METHODOLOGY_ARTIFACT_MODEL_BY_ID has all 10 IDs ────────────────


def test_model_by_id_has_all_artifact_ids() -> None:
    assert set(METHODOLOGY_ARTIFACT_MODEL_BY_ID.keys()) == set(METHODOLOGY_ARTIFACT_IDS)


def test_model_by_id_count() -> None:
    assert len(METHODOLOGY_ARTIFACT_MODEL_BY_ID) == 10


# ── Test 4: Every model is frozen/immutable ─────────────────────────────────


def test_project_intake_is_frozen() -> None:
    instance = ProjectIntakeArtifact(**_MINIMAL_KWARGS["00-project-intake"])  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        instance.title = "changed"  # type: ignore[misc]


def test_mvp_is_frozen() -> None:
    instance = MVPArtifact(**_MINIMAL_KWARGS["09-mvp"])  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        instance.summary = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("artifact_id", METHODOLOGY_ARTIFACT_IDS)
def test_all_models_are_frozen(artifact_id: str) -> None:
    model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    assert model_cls.model_config.get("frozen") is True


# ── Test 5: Extra fields forbidden ─────────────────────────────────────────


def test_extra_fields_forbidden_project_intake() -> None:
    with pytest.raises(ValidationError):
        ProjectIntakeArtifact(
            **_MINIMAL_KWARGS["00-project-intake"],  # type: ignore[arg-type]
            nonexistent_field="x",
        )


@pytest.mark.parametrize("artifact_id", METHODOLOGY_ARTIFACT_IDS)
def test_all_models_forbid_extra_fields(artifact_id: str) -> None:
    model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    assert model_cls.model_config.get("extra") == "forbid"


# ── Tests 6–8: Correct artifact_id, phase, owner_role ──────────────────────


@pytest.mark.parametrize("artifact_id,phase,owner_role", _EXPECTED_METADATA)
def test_model_metadata(artifact_id: str, phase: int, owner_role: str) -> None:
    model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    instance = model_cls(**_MINIMAL_KWARGS[artifact_id])  # type: ignore[arg-type]
    assert instance.artifact_id == artifact_id
    assert instance.phase == phase
    assert instance.owner_role == owner_role


# ── Test 9: Required fields are enforced ───────────────────────────────────


def test_required_fields_project_intake() -> None:
    with pytest.raises(ValidationError):
        ProjectIntakeArtifact(title="t", summary="s")


def test_required_fields_discovery() -> None:
    with pytest.raises(ValidationError):
        DiscoveryArtifact(title="t", summary="s")


def test_required_fields_business() -> None:
    with pytest.raises(ValidationError):
        BusinessArtifact(title="t", summary="s")


def test_required_fields_mvp() -> None:
    with pytest.raises(ValidationError):
        MVPArtifact(title="t", summary="s")


def test_required_fields_validation_artifact() -> None:
    with pytest.raises(ValidationError):
        ValidationArtifact(title="t", summary="s")


# ── Test 10: Minimal valid instance per artifact ───────────────────────────


@pytest.mark.parametrize("artifact_id", METHODOLOGY_ARTIFACT_IDS)
def test_minimal_valid_instance(artifact_id: str) -> None:
    model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    instance = model_cls(**_MINIMAL_KWARGS[artifact_id])  # type: ignore[arg-type]
    assert isinstance(instance, MethodologyArtifact)
    assert instance.artifact_id == artifact_id


# ── Test 11: artifact_model_for_id returns correct model ──────────────────


@pytest.mark.parametrize("artifact_id", METHODOLOGY_ARTIFACT_IDS)
def test_artifact_model_for_id_returns_correct_class(artifact_id: str) -> None:
    model_cls = artifact_model_for_id(artifact_id)
    assert model_cls is METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]


def test_artifact_model_for_id_project_intake() -> None:
    assert artifact_model_for_id("00-project-intake") is ProjectIntakeArtifact


def test_artifact_model_for_id_mvp() -> None:
    assert artifact_model_for_id("09-mvp") is MVPArtifact


# ── Test 12: Unknown artifact ID raises a clear error ─────────────────────


def test_artifact_model_for_id_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown methodology artifact ID"):
        artifact_model_for_id("99-nonexistent")


def test_artifact_model_for_id_empty_raises_key_error() -> None:
    with pytest.raises(KeyError):
        artifact_model_for_id("")


# ── Test 13: JSON serialization works ─────────────────────────────────────


def test_json_serialization_project_intake() -> None:
    instance = ProjectIntakeArtifact(**_MINIMAL_KWARGS["00-project-intake"])  # type: ignore[arg-type]
    json_str = instance.model_dump_json()
    data = json.loads(json_str)
    assert data["artifact_id"] == "00-project-intake"
    assert data["phase"] == 0
    assert data["schema_version"] == "1.0"


def test_json_serialization_mvp() -> None:
    instance = MVPArtifact(**_MINIMAL_KWARGS["09-mvp"])  # type: ignore[arg-type]
    json_str = instance.model_dump_json()
    data = json.loads(json_str)
    assert data["artifact_id"] == "09-mvp"
    assert data["phase"] == 9


@pytest.mark.parametrize("artifact_id", METHODOLOGY_ARTIFACT_IDS)
def test_all_models_json_serializable(artifact_id: str) -> None:
    model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
    instance = model_cls(**_MINIMAL_KWARGS[artifact_id])  # type: ignore[arg-type]
    json_str = instance.model_dump_json()
    data = json.loads(json_str)
    assert data["artifact_id"] == artifact_id
    assert isinstance(data["phase"], int)


# ── Test 14: No filesystem IO on import or instantiation ──────────────────


def test_no_filesystem_io_on_instantiation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.iterdir())
    for artifact_id, kwargs in _MINIMAL_KWARGS.items():
        model_cls = METHODOLOGY_ARTIFACT_MODEL_BY_ID[artifact_id]
        model_cls(**kwargs)  # type: ignore[arg-type]
    assert list(tmp_path.iterdir()) == before
    assert not (tmp_path / ".voyage").exists()


# ── Test 15: EventType includes methodology lifecycle events ───────────────


def test_eventtype_has_artifact_produced() -> None:
    assert "artifact_produced" in {e.value for e in EventType}


def test_eventtype_has_handoff_issued() -> None:
    assert "handoff_issued" in {e.value for e in EventType}


def test_eventtype_has_phase_closed() -> None:
    assert "phase_closed" in {e.value for e in EventType}


def test_eventtype_methodology_names_accessible() -> None:
    assert EventType.ARTIFACT_PRODUCED.name == "ARTIFACT_PRODUCED"
    assert EventType.HANDOFF_ISSUED.name == "HANDOFF_ISSUED"
    assert EventType.PHASE_CLOSED.name == "PHASE_CLOSED"


def test_eventtype_methodology_values_accessible() -> None:
    assert EventType.ARTIFACT_PRODUCED.value == "artifact_produced"
    assert EventType.HANDOFF_ISSUED.value == "handoff_issued"
    assert EventType.PHASE_CLOSED.value == "phase_closed"


# ── Schema defaults ────────────────────────────────────────────────────────


def test_schema_version_default() -> None:
    instance = ProjectIntakeArtifact(**_MINIMAL_KWARGS["00-project-intake"])  # type: ignore[arg-type]
    assert instance.schema_version == "1.0"


def test_status_default_is_draft() -> None:
    instance = ProjectIntakeArtifact(**_MINIMAL_KWARGS["00-project-intake"])  # type: ignore[arg-type]
    assert instance.status == "draft"


def test_open_questions_default_empty() -> None:
    instance = MVPArtifact(**_MINIMAL_KWARGS["09-mvp"])  # type: ignore[arg-type]
    assert instance.open_questions == ()


def test_assumptions_default_empty() -> None:
    instance = MVPArtifact(**_MINIMAL_KWARGS["09-mvp"])  # type: ignore[arg-type]
    assert instance.assumptions == ()


# ── Concrete artifact-specific field tests ─────────────────────────────────


def test_project_intake_specific_fields() -> None:
    instance = ProjectIntakeArtifact(**_MINIMAL_KWARGS["00-project-intake"])  # type: ignore[arg-type]
    assert instance.raw_idea == "An idea"
    assert instance.target_users == ("User",)
    assert instance.problem_statement == "The problem"
    assert instance.desired_outcomes == ("Outcome",)
    assert instance.constraints == ()
    assert instance.non_goals == ()


def test_discovery_specific_fields() -> None:
    instance = DiscoveryArtifact(**_MINIMAL_KWARGS["01-discovery"])  # type: ignore[arg-type]
    assert instance.problem == "The problem"
    assert instance.success_criteria == ("Success criterion",)
    assert instance.switching_triggers == ()


def test_event_storming_specific_fields() -> None:
    instance = EventStormingArtifact(**_MINIMAL_KWARGS["05-events"])  # type: ignore[arg-type]
    assert instance.domain_events == ("UserRegistered",)
    assert instance.commands == ()
    assert instance.actors == ()
    assert instance.external_systems == ()


def test_solution_artifact_specific_fields() -> None:
    instance = SolutionArtifact(**_MINIMAL_KWARGS["07-solution"])  # type: ignore[arg-type]
    assert instance.architecture_summary == "Architecture description"
    assert instance.technology_choices == ("Python",)
    assert instance.integration_points == ()


def test_validation_artifact_verdict_required() -> None:
    with pytest.raises(ValidationError):
        ValidationArtifact(
            title="t",
            summary="s",
            consistency_findings=("Finding",),
        )


def test_mvp_artifact_deferred_scope_optional() -> None:
    instance = MVPArtifact(**_MINIMAL_KWARGS["09-mvp"])  # type: ignore[arg-type]
    assert instance.deferred_scope == ()
    assert instance.milestones == ()


def test_ux_artifact_specific_fields() -> None:
    instance = UXArtifact(**_MINIMAL_KWARGS["03-ux"])  # type: ignore[arg-type]
    assert instance.primary_user_flows == ("Flow 1",)
    assert instance.screens_or_surfaces == ("Screen 1",)
    assert instance.interaction_principles == ("Principle 1",)
    assert instance.accessibility_notes == ()


def test_domain_artifact_specific_fields() -> None:
    instance = DomainArtifact(**_MINIMAL_KWARGS["04-domain"])  # type: ignore[arg-type]
    assert instance.entities == ("Entity 1",)
    assert instance.relationships == ("Relationship 1",)
    assert instance.invariants == ("Invariant 1",)
    assert instance.domain_rules == ()


def test_feature_artifact_specific_fields() -> None:
    instance = FeatureArtifact(**_MINIMAL_KWARGS["06-features"])  # type: ignore[arg-type]
    assert instance.features == ("Feature 1",)
    assert instance.must_have == ("Must have 1",)
    assert instance.should_have == ()
    assert instance.wont_have == ()


def test_business_artifact_specific_fields() -> None:
    instance = BusinessArtifact(**_MINIMAL_KWARGS["02-business"])  # type: ignore[arg-type]
    assert instance.audience == ("Target audience",)
    assert instance.value_proposition == "Value prop"
    assert instance.jobs_to_be_done == ("Job to be done",)
    assert instance.risks == ()
    assert instance.business_constraints == ()
