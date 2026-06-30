# ADR-0001 - Framework / Narrative separation; Framework is a generic dev-control-OS

- Status: Accepted
- Date: 2026-06-28
- Target path in repo: `docs/framework/adr/ADR-0001-framework-narrative-separation.md`
- Deciders: Andrey + Voyage Control

## Context

Voyage Framework grew while building the Narrative game, which created two risks: (1) the Framework began absorbing Narrative-product concerns (scenarios, RenPy runtime, personas), and (2) trust in agent reports was unverified (the "synthetic hash" incident). A read-only control layer now exists (`voyage auto`, `voyage narrative scene-validate|arc-check`, and the F0-B `voyage validate-report` trust engine). Before adding features we fix the architecture.

## Decision

1. Framework and Narrative are separate projects.
   - Narrative owns: story, scenarios, characters, POV, choices, RenPy runtime, personas, display to the player.
   - Framework owns: validation, reports, guardrails, workflow control, audit, development automation - across repositories.
2. Framework is a generic development-control OS. Its core is repository-agnostic. Specific repos (Narrative, future SkillTracer, etc.) integrate only through adapters and specs, never by embedding their domain logic in the core.
3. Framework may inspect, validate, audit, and plan other repos through adapters/specs. Framework must not become the Narrative runtime, story engine, RenPy app, persona store, or scenario-authoring product.
4. Separation is enforced on three levels, not only documented:
   - Documentary: this ADR + roadmap + control rules.
   - Mechanical: `report_validator.py` role-based forbidden paths (`FORBIDDEN_BY_ROLE`); the adapter seam (`core/adapter_protocols.py::AdapterProtocol`, `core/adapter_contract.py`).
   - Process: every significant step passes approval -> report -> `validate-report` -> commit gate.
5. Autonomy boundary is fixed: any automation ends at `auto branch + report`. It never reaches `main`, `origin/main`, deploy, or the product runtime. Merge/push/deploy and any model/agent invocation remain human-gated.

## Invariants (binding; full list in FRAMEWORK_CONTROL_RULES.md)

1. Framework never writes directly to Narrative-`main`. Narrative edits go through the Narrative repo's own worktree + gates + human approval.
2. All Framework commands default to read-only; `write-authorized` requires explicit enablement and must pass `validate-report`.
3. No product-repo domain logic in core; integration via adapters only.
4. No push/merge/deploy/SSH/Docker/Certbot/`.env` read/`.voyage` mutation under automation without separate human approval.

## Consequences

Positive: clear ownership; repo-agnostic core enables adding a second repo by writing an adapter; trust is verifiable via `validate-report`.

Costs: Narrative product decisions move to the Narrative repo/chat; adding a repo requires an adapter + spec; existing Narrative-specific code (`narrative_adapter.py`, hardcoded `FORBIDDEN_BY_ROLE`) must be refactored toward the generic contract over time (roadmap Phase 2/3, not here).

## Related decisions

See `FRAMEWORK_DECISIONS.md` (D-001 through D-008) for the generic-OS direction, JSON-report mandate, dogfood/closeout ritual, phase ordering, the dirty-Narrative boundary, and the BOM-tolerant loader.
