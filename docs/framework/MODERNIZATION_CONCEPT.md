# Voyage Application Modernization Concept

> Status: D-013 accepted and documented as future architecture. Implementation has not started. This document does not activate F7-D, F8+ work, R6-PREFLIGHT, or D-014/MCP.

## Purpose

Voyage may help projects remain supported, secure, and maintainable through a continuous but human-gated modernization discipline. This extends the development-control and memory model without turning Voyage into an agent runtime or an automatic upgrade system.

The future modernization loop is:

```text
SENSE -> MAP -> PROPOSE -> PREVIEW -> GATE -> APPLY -> RECORD -> SENSE
```

- **Sense:** observe version, deprecation, end-of-life, vulnerability, and policy signals from allowlisted sources with provenance.
- **Map:** relate a signal to its use in the project, ownership, dependencies, and blast radius.
- **Propose:** produce a prioritized, reviewable change proposal with risk, urgency, affected scope, checks, and rollback needs.
- **Preview:** show a plan or candidate diff without applying it.
- **Gate:** require human approval, trusted evidence, safety checks, and the controls selected under D-012.
- **Apply:** use a separately approved guarded-write capability only; keep the change incremental and reversible.
- **Record:** preserve the decision, evidence, result, and refreshed modernization map in the audit trail.

Only the architectural decision and future direction are accepted today. No modernization detector, manifest, scheduler, or apply workflow is implemented by D-013.

## Operating principles

1. Modernization does not mean always updating to the newest version. Each managed element follows an explicit policy.
2. Work is propose-first and gated-apply-later. No modernization change is automatic.
3. There is no safe modernization without an adequate test and rollback safety net.
4. Validation must address behavioral equivalence at the relevant risk tier, not merely report that some tests passed.
5. Every migration step must be independently reviewable and reversible. Oversized or big-bang proposals are blocked and decomposed.
6. Greenfield systems should expose clean seams, dependency isolation, version decisions, ownership, tests, and rollback information as they are built.
7. Brownfield systems begin with read-only discovery. Where tests are absent, establishing characterization or smoke coverage is step zero before mutation.
8. Framework owns generic control and evidence machinery; project or plugin adapters own domain-specific modernization interpretation, as required by D-009.
9. Decisions consider both risk-of-change under D-012 and risk-of-inaction.

## Greenfield and brownfield paths

For a greenfield project, modernization readiness is accumulated during normal development: dependency and runtime choices are recorded, owners and critical zones are known, and tests and rollback paths exist before an upgrade is proposed.

For a brownfield project, Voyage first builds a read-only map of dependencies, runtimes, integrations, schemas, deployment surfaces, and known safety coverage. It may propose the safety-net work needed to make later change reviewable. It must not treat missing tests or unknown blast radius as permission to proceed.

Modernization should follow an incremental replacement pattern in which old and new behavior can coexist during transition and a fallback remains available.

## Candidate modernization manifest

A future phase may define a semi-automatic `.voyage/modernization.yaml`. D-013 does not create or activate that file.

Candidate mechanically observed fields include dependencies and versions, runtime and package manager, lockfile reference, last-check time, and source provenance. Higher-risk projects may add owners, criticality, blast radius, migration and rollback notes, security-sensitive zones, external integrations, database and deployment surfaces, and licensing constraints.

Candidate per-element policies are:

```text
track-latest | track-LTS | security-only | pinned-frozen | manual-review-only
```

`track-latest` is opt-in. `track-LTS` or `security-only` are safer defaults. A critical security finding may override suppression of routine drift, but it still produces a human-gated proposal; it never silently changes a frozen element.

The map itself must carry freshness and provenance so stale observations cannot silently drive a change.

## Sensing and prioritization

Future sensing is read-only and restricted to trusted, allowlisted sources such as official package registries, advisory databases, release notes, and end-of-life calendars. Every observation records provenance. Semantic judgments that require a model remain future, propose-only work behind the external-tool and human-review boundaries.

The modernization backlog combines:

- **Risk-of-change:** scope, criticality, confidence, migration type, test coverage, rollback quality, and D-012 hard floors.
- **Risk-of-inaction:** vulnerability severity, end-of-life timing, unsupported runtime, abandoned dependency, deprecation, and license exposure.

Security and passed end-of-life conditions may be urgent; major migrations and architecture refactors may be dangerous. Urgency does not remove gates, and high change risk does not justify ignoring inaction.

## Safety net and reversibility

Validation grows with risk. A patch may need targeted and smoke tests; a minor change may add integration coverage; a major runtime or architecture migration may require characterization, contract, golden or snapshot, and full-suite checks. Database changes additionally require dry-run, backup, and reversible migration evidence. User-interface changes may require visual regression evidence.

If no adequate tests exist, modernization is blocked until a safety net is established. A future proposal may recommend those tests, but a human reviews them and their adequacy.

A proposal that exceeds a future blast-radius ceiling must be decomposed into smaller gated steps. Each step retains a rollback or fallback, and old/new coexistence is preferred during migration.

## Ownership and architecture boundaries

Consistent with [D-009](FRAMEWORK_DECISIONS.md#d-009---project-adapter-ownership), Framework may determine that a generic signal exists and enforce common gates, evidence, preview, trust, and reporting rules. Project-side or plugin-side adapters determine what that signal means for a particular product and propose domain-specific work.

Consistent with [D-012](FRAMEWORK_DECISIONS.md#d-012---risk-based-adaptive-control-with-voyage-observed-evidence), modernization cannot lower its own controls through agent claims. Unknown scope increases control until trusted evidence reduces uncertainty. Hard floors remain binding.

Modernization proposals may use `voyage.report.v1` and existing validation surfaces when a future implementation phase authorizes them. D-013 itself makes no runtime or reporting change.

## Explicit exclusions and gates

- No automatic dependency updates, code changes, commits, pushes, deploys, or model execution.
- No big-bang rewrite path.
- No implementation claim for future CONTROL-LOOP-2 through CONTROL-LOOP-10 documents.
- No activation of F7-D or change to the active F7 track.
- No D-014/MCP design or implementation; that remains a separate future decision.
- No mutation of `.voyage/` runtime state by this documentation decision.
- No change to ADR-0001 or the Framework/Narrative separation.

Any implementation requires a separate approved phase with explicit scope, safety controls, tests, and acceptance criteria.
