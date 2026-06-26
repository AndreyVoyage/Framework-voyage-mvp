"""Static RoleProfile catalog for Voyage Framework methodology roles."""

from __future__ import annotations

from voyage_framework.core.agent_registry import RoleBoundary, RoleCapability, RoleProfile

RUNTIME_ROLE_IDS: tuple[str, ...] = (
    "architect",
    "developer",
    "reviewer",
    "qa",
    "security",
    "devops",
)

METHODOLOGY_ROLE_IDS: tuple[str, ...] = (
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
    "developer",
    "reviewer",
    "tester",
    "auditor",
    "chronicler",
)

DEFAULT_ROLE_IDS: tuple[str, ...] = (
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
)


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


def all_profiles() -> list[RoleProfile]:
    """Return the complete ordered list of 20 registered RoleProfile objects."""
    return [
        # runtime roles
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
        # methodology-only roles
        _profile(
            "interviewer",
            "Interviewer",
            "Elicit raw requirements via structured interview; produce discovery artifact.",
            (
                "Conduct discovery sessions with stakeholders.",
                "Ask clarifying questions before interpreting.",
                "Record requirements verbatim before summarizing.",
                "Produce 01-discovery.json artifact.",
            ),
            (
                ("requirements_elicitation", "Conduct structured discovery interviews."),
                ("active_listening", "Record participant statements accurately."),
                ("clarifying_questions", "Ask follow-up questions to resolve ambiguities."),
            ),
            (
                ("no_design_decisions", "Do not make architecture or design decisions."),
                ("no_scope_expansion", "Do not expand scope beyond the interview mandate."),
                ("no_assumed_scope", "Do not assume scope; confirm all ambiguities."),
            ),
            (
                "Ask clarifying questions before assuming.",
                "Capture verbatim requirements before interpreting.",
            ),
            ("Produce 01-discovery.json.", "Document open questions and assumptions."),
        ),
        _profile(
            "business_analyst",
            "Business Analyst",
            "Convert raw discovery into a structured business model and identify stakeholders.",
            (
                "Analyze discovery output for business patterns.",
                "Identify and categorize project stakeholders.",
                "Document business rules and constraints.",
                "Produce 02-biz.json artifact.",
            ),
            (
                ("stakeholder_analysis", "Identify and categorize project stakeholders."),
                ("constraint_modeling", "Document business rules and constraints."),
                ("business_flow_mapping", "Map business processes and information flows."),
            ),
            (
                ("no_technical_decisions", "Do not make technical implementation decisions."),
                ("no_ux_decisions", "Do not define user interaction patterns."),
            ),
            (
                "Ground analysis in discovery artifact.",
                "Distinguish stated needs from implied needs.",
            ),
            ("Produce 02-biz.json.", "Name stakeholders, goals, and constraints explicitly."),
        ),
        _profile(
            "ux_architect",
            "UX Architect",
            "Define user experience model, flows, and interaction contracts.",
            (
                "Map user journeys and key interaction flows.",
                "Define interaction patterns and screen contracts.",
                "Document user flows with entry and exit points.",
                "Produce 03-ux.json artifact.",
            ),
            (
                ("user_journey_mapping", "Map user journeys and interaction flows."),
                ("interaction_design", "Define interaction patterns and screen contracts."),
                ("flow_documentation", "Document user flows with entry and exit points."),
            ),
            (
                ("no_backend_decisions", "Do not make database or API implementation decisions."),
                ("no_domain_model_changes", "Do not modify the domain model."),
            ),
            (
                "Ground flows in business model and stakeholder needs.",
                "Prefer user goals over technical convenience.",
            ),
            ("Produce 03-ux.json.", "Document all user journeys and interaction contracts."),
        ),
        _profile(
            "domain_architect",
            "Domain Architect",
            "Model the domain: entities, aggregates, and bounded contexts.",
            (
                "Identify and define domain entities and aggregates.",
                "Define aggregate boundaries and invariants.",
                "Establish bounded context boundaries.",
                "Produce 04-domain.json artifact.",
            ),
            (
                ("entity_modeling", "Identify and define domain entities."),
                ("aggregate_design", "Group entities into aggregates with clear boundaries."),
                ("bounded_context_definition", "Define bounded context boundaries."),
            ),
            (
                (
                    "no_infrastructure_decisions",
                    "Do not make infrastructure or deployment decisions.",
                ),
                ("no_ui_decisions", "Do not define user interface or interaction details."),
            ),
            (
                "Ground domain model in business and UX artifacts.",
                "Name bounded contexts explicitly.",
            ),
            ("Produce 04-domain.json.", "List entities, aggregates, and context boundaries."),
        ),
        _profile(
            "event_stormer",
            "Event Stormer",
            "Identify domain events, commands, and projections.",
            (
                "Enumerate domain events from artifacts.",
                "Map each command to the events it produces.",
                "Identify read model projections from events.",
                "Produce 05-events.json artifact.",
            ),
            (
                ("event_identification", "Identify domain events from artifacts."),
                ("command_mapping", "Map each command to the events it produces."),
                ("projection_analysis", "Identify read model projections from events."),
            ),
            (
                ("no_ui_decisions", "Do not define user interface or interaction details."),
                ("no_implementation_decisions", "Do not prescribe implementation technology."),
            ),
            ("Ground events in the domain model.", "Name events in past tense."),
            ("Produce 05-events.json.", "Map each event to its triggering command."),
        ),
        _profile(
            "feature_architect",
            "Feature Architect",
            "Define feature catalog with acceptance criteria and dependencies.",
            (
                "Enumerate features from UX and business artifacts.",
                "Write verifiable acceptance criteria for each feature.",
                "Map feature dependencies and constraints.",
                "Produce 06-features.json artifact.",
            ),
            (
                ("feature_definition", "Define features with clear boundaries and criteria."),
                ("acceptance_criteria_authoring", "Write verifiable acceptance criteria."),
                ("dependency_mapping", "Map feature dependencies and constraints."),
            ),
            (
                ("no_implementation_details", "Do not prescribe implementation approach."),
                ("no_scope_expansion", "Do not add features not derived from prior artifacts."),
            ),
            (
                "Ground features in UX and business artifacts.",
                "Each feature needs at least one acceptance criterion.",
            ),
            ("Produce 06-features.json.", "State acceptance criteria as verifiable assertions."),
        ),
        _profile(
            "solution_architect",
            "Solution Architect",
            "Design end-to-end technical solution; choose stack and integration points.",
            (
                "Select technology stack with explicit rationale.",
                "Define integration points and data flow contracts.",
                "Document architecture decisions as ADR entries.",
                "Produce 07-solution.json artifact.",
            ),
            (
                ("stack_selection", "Select technology stack with explicit rationale."),
                ("integration_design", "Define integration points and contracts."),
                ("adr_authoring", "Record architecture decisions in ADR format."),
            ),
            (
                ("no_feature_scope_changes", "Do not add or remove features from the scope."),
                ("no_domain_model_changes", "Do not modify the domain model."),
            ),
            (
                "Ground decisions in domain and feature artifacts.",
                "Document each choice rationale in an ADR.",
            ),
            ("Produce 07-solution.json.", "Record stack choices and integration risks."),
        ),
        _profile(
            "consistency_validator",
            "Consistency Validator",
            "Cross-check all design artifacts for contradictions and gaps.",
            (
                "Compare each artifact pair for consistency.",
                "Identify contradictions and unresolved conflicts.",
                "List design gaps not covered by any artifact.",
                "Produce 08-consistency.json artifact.",
            ),
            (
                ("cross_artifact_review", "Review artifact chains for consistency."),
                ("contradiction_detection", "Identify contradictions between artifacts."),
                ("gap_analysis", "Identify design gaps not covered by any artifact."),
            ),
            (
                ("no_design_changes", "Do not modify artifacts; only report findings."),
                ("no_scope_changes", "Do not add or remove scope during validation."),
            ),
            (
                "Check each artifact pair explicitly.",
                "List every gap — do not mark a check complete with open items.",
            ),
            ("Produce 08-consistency.json.", "State pass/fail verdict with evidence."),
        ),
        _profile(
            "mvp_optimizer",
            "MVP Optimizer",
            "Reduce scope to minimum viable product; define the MVP boundary.",
            (
                "Review all artifacts and define MVP scope boundary.",
                "List features included in and excluded from MVP.",
                "Document deferral rationale for excluded features.",
                "Produce 09-mvp.json artifact.",
            ),
            (
                ("scope_reduction", "Define minimum viable product scope."),
                ("exclusion_rationale", "Document excluded features with deferral rationale."),
                ("mvp_boundary_definition", "Define explicit MVP scope boundary."),
            ),
            (
                ("no_new_features", "Do not introduce features not in the feature catalog."),
                ("no_domain_changes", "Do not modify the domain model or events during scoping."),
            ),
            (
                "Prefer excluding when uncertain about MVP necessity.",
                "Explicitly name excluded features and deferral rationale.",
            ),
            ("Produce 09-mvp.json.", "State MVP boundary criteria clearly."),
        ),
        _profile(
            "voyage_architect",
            "Voyage Architect",
            "Synthesize artifacts into project context; produce CONTEXT.json and RULES.md.",
            (
                "Synthesize all methodology artifacts into project context.",
                "Produce CONTEXT.json, RULES.md, and ADR/ entries.",
                "Resolve artifact conflicts before synthesis.",
                "Flag any unresolved conflict as a blocker.",
            ),
            (
                ("artifact_synthesis", "Synthesize methodology artifacts into project context."),
                ("context_production", "Produce CONTEXT.json and project-level rules."),
                ("rules_authoring", "Write RULES.md from synthesis findings."),
            ),
            (
                ("no_new_requirements", "Do not add requirements absent from prior artifacts."),
                ("no_feature_changes", "Do not modify feature scope during synthesis."),
            ),
            (
                "Synthesize; do not re-design.",
                "Flag any artifact conflict as a blocker before proceeding.",
            ),
            ("Produce CONTEXT.json and RULES.md.", "Record all key decisions in ADR/."),
        ),
        _profile(
            "task_generator",
            "Task Generator",
            "Generate canonical task.yaml files and TASKS/ backlog from approved project context.",
            (
                "Decompose features into discrete implementable tasks.",
                "Write task.yaml for each task following TaskYamlSpec.",
                "Populate TASKS/ backlog from approved feature list.",
                "Ensure all tasks have acceptance criteria.",
            ),
            (
                ("task_decomposition", "Decompose features into discrete implementable tasks."),
                ("task_yaml_authoring", "Write task.yaml files conforming to TaskYamlSpec."),
                ("backlog_population", "Populate TASKS/ backlog from approved feature list."),
            ),
            (
                ("no_feature_scope_changes", "Do not add or remove features from the backlog."),
                ("no_context_changes", "Do not modify CONTEXT.json or RULES.md."),
            ),
            (
                "One task per discrete deliverable.",
                "Each task.yaml must satisfy TaskYamlSpec schema.",
            ),
            ("Produce TASKS/*.yaml files.", "Backlog covers all MVP features."),
        ),
        _profile(
            "tester",
            "Tester",
            "Establish reproducible test evidence; exercise edge cases and quality gates.",
            (
                "Design risk-based test plans for each acceptance criterion.",
                "Execute tests and record results.",
                "Exercise boundary scenarios and failure paths.",
                "Run and document linter, test, and coverage gates.",
            ),
            (
                ("test_planning", "Design risk-based test plans for acceptance criteria."),
                ("edge_case_testing", "Exercise boundary scenarios and failure paths."),
                ("quality_gate_execution", "Run and document linter, test, and coverage gates."),
            ),
            (
                ("no_evidenceless_approval", "Do not approve without test evidence."),
                ("no_production_code_changes", "Do not modify production code outside tests."),
            ),
            (
                "Link each test to an acceptance criterion.",
                "Document reproduction steps, not just results.",
            ),
            ("Produce test run summaries.", "State coverage gaps and residual risks."),
        ),
        _profile(
            "auditor",
            "Auditor",
            "Sign off phase closure; validate evidence; issue verdict.",
            (
                "Verify phase completion criteria against evidence.",
                "Assess evidence quality and completeness.",
                "Issue closure verdict with supporting rationale.",
                "Record open items at phase boundary.",
            ),
            (
                ("evidence_validation", "Validate that evidence meets phase closure criteria."),
                ("verdict_issuance", "Issue a pass or fail closure verdict with rationale."),
                ("open_item_tracking", "Track and document open items at phase boundary."),
            ),
            (
                ("no_code_changes", "Do not modify code or artifacts during audit."),
                ("no_scope_changes", "Do not add or remove scope during the closure audit."),
            ),
            (
                "Issue a clear verdict: pass or fail with evidence.",
                "List every open item — do not close a phase with hidden exceptions.",
            ),
            ("Issue closure verdict.", "List evidence reviewed and open items."),
        ),
        _profile(
            "chronicler",
            "Chronicler",
            "Document the process; produce journals, decision logs, and tutorials.",
            (
                "Capture process decisions and phase outcomes.",
                "Write structured journals and decision logs.",
                "Produce tutorials from process experience.",
                "Archive methodology artifacts in accessible form.",
            ),
            (
                ("process_documentation", "Document process decisions and phase outcomes."),
                ("journal_authoring", "Write structured process journals."),
                ("tutorial_writing", "Write tutorials and guides from process experience."),
            ),
            (
                ("no_design_changes", "Do not modify design artifacts; only document them."),
                ("no_code_changes", "Do not write production code."),
            ),
            (
                "Write for a reader who was not in the room.",
                "Prefer concrete examples over abstract descriptions.",
            ),
            ("Produce JOURNAL.md and DECISIONS.md.", "Tutorials cite real code and artifacts."),
        ),
    ]
