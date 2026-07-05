# Framework Decisions Log

> Append-only record of significant decisions. Target path in repo: `docs/framework/FRAMEWORK_DECISIONS.md`.
> Each entry: id, date, status, decision, rationale. Reversal requires a new entry, not an edit.

## D-001 - Framework is a generic dev-control-OS
- Date: 2026-06-28, Status: Accepted
- Decision: Framework's direction is a repository-agnostic development-control OS (multi-repo control via adapters), not a Narrative-only tool and not an autonomous agent runtime.
- Rationale: avoids domain leakage; enables a second repo via an adapter rather than core changes.

## D-002 - Framework / Narrative separation
- Date: 2026-06-28, Status: Accepted (see `adr/ADR-0001`)
- Decision: Narrative is a separate product; Framework inspects/validates/audits/plans it via adapters/specs only and never becomes its runtime, nor writes to Narrative-`main`.
- Rationale: clear ownership; prevents the control layer from absorbing product concerns.

## D-003 - Structured JSON reports are mandatory
- Date: 2026-06-28, Status: Accepted
- Decision: Completion reports use structured `voyage.report.v1` JSON. Free-form markdown is human-only and is not the validation target.
- Rationale: stable parse target; closes the synthetic/short-hash gap that free-form markdown allowed.

## D-004 - Dogfood/closeout ritual via validate-report
- Date: 2026-06-28, Status: Accepted
- Decision: From F0-B onward, every significant step emits human-readable + `voyage.report.v1`, and `voyage validate-report` must pass; if it fails, the closeout is not closed. Dogfood is a continuous ritual, not a one-off phase.
- Rationale: the whole strategy rests on the trust engine; it must be exercised on every real artifact.

## D-005 - Phase ordering; Phase 2 deferred
- Date: 2026-06-28, Status: Accepted
- Decision: Locked order F0-B closeout -> F0-D docs+ADR -> F0-E negative assert -> F1 hygiene/perf -> F2 generic adapter. No new development until ADR + roadmap are written into the repo.
- Rationale: avoid building the adapter contract without a recorded map.

## D-006 - Validator hardening deferred to Phase 3
- Date: 2026-06-28, Status: Accepted
- Decision: `voyage report-state`, changed-files vs named `auto_commit` (error-grade), and spec-driven forbidden paths (replacing hardcoded `FORBIDDEN_BY_ROLE`) are deferred to F3.
- Rationale: the F0-B validator is sufficient as a consistency check now; hardening is additive and non-blocking.

## D-007 - Dirty Narrative handled outside Framework
- Date: 2026-06-28, Status: Accepted
- Decision: The Narrative working tree being dirty (observed at HEAD `5571bd2`) is handled in the Narrative chat/repo via a read-only dirty-state audit. Framework does not clean Narrative.
- Rationale: respects separation; Framework must not perform product-repo maintenance.

## D-008 - validate-report loader is BOM-tolerant
- Date: 2026-06-28, Status: Accepted (implemented in F0-B closeout, commit `01b1935`)
- Decision: `report_validator.ReportClaim.from_file` reads with `encoding="utf-8-sig"`, accepting reports with or without a UTF-8 BOM. Report writers should still prefer UTF-8 without BOM for clean diffs.
- Rationale: Windows/PowerShell commonly writes a BOM; the trust engine must not be brittle to it. Surfaced by the F0-B dogfood (validate-report initially failed to load a BOM-prefixed report).

## D-010 - Role Versioning and Freshness Policy
- Date: 2026-07-04, Status: Accepted (future architecture principle; no implementation yet)
- Decision:
  - `RoleProfile` versions are immutable; a published version never changes.
  - Improvements ship as new versions, for example `developer@1.1`, never as in-place edits to `developer@1.0`.
  - The Framework role catalog is append-only across versions.
  - Consuming projects pin exact role versions in a project-side role lockfile.
  - Updating the Framework role catalog does not affect any running project until that project explicitly upgrades its pinned role versions.
  - Role upgrades require explicit human approval, version diff review, tests/regression checks, `validate-report`, and audit trail.
  - Automatic role self-modification is forbidden.
  - Role freshness checks are allowed only as read-only / propose-only audits.
  - Role Freshness Auditor may propose role updates, but must not apply them.
  - Role Upgrade Gate applies approved updates through the normal guarded workflow.
  - Sequence:
    1. Implement role versioning, project-side role pinning, and role upgrade gate first.
    2. Add role regression tests.
    3. Only later add Role Freshness Auditor as read-only/propose-only, likely F8+.
- Rationale:
  - Roles are part of the Framework control surface.
  - In-place role mutation would make project behavior non-reproducible.
  - Versioning and pinning give dependency-lockfile style safety: reproducibility, explicit upgrades, auditability, and rollback clarity.
  - Existing trust/guarded-write machinery should become the substrate for safe role evolution.

## D-009 - Project Adapter Ownership
- Date: 2026-07-04, Status: Accepted (future architecture principle; no implementation yet)
- Decision:
  - Framework owns adapter contracts, loading/validation infrastructure, trust engine, reports, guardrails, and gated workflows.
  - Consuming projects or external plugin packages own project-specific adapters, project-specific checks, and domain-specific spec-plan logic.
  - Framework core must not accumulate product-specific adapters for every consuming project.
  - Product-specific adapters should ultimately live project-side or plugin-side.
  - Built-in product adapters are allowed only as reference adapters, bootstrap examples, or migration bridges.
  - The current Narrative adapter in Framework core is a reference / first-real-product bridge, not the long-term pattern for 20+ projects.
  - Future adapter loading should allow project-side or plugin-side adapters to be discovered, validated, and run through the Framework trust engine.
  - Adapter versions should be pinnable by consuming projects, following the same dependency-management philosophy as D-010 role versioning.
  - Framework must keep product content ownership outside core: no story/runtime/business-domain logic in core.
  - Adapter extraction must not happen until an adapter loader/versioning path exists.
  - Existing built-in adapters remain supported until a safe migration path exists.
- Rationale:
  - The `RepoControlAdapter` contract and the local adapter proof show that adapters can be interchangeable.
  - If every product-specific adapter is added directly to Framework core, the Framework will become coupled to product domains and will not scale to many projects.
  - Project-side/plugin-side ownership keeps the Framework generic while still allowing deep project-specific checks.
- Consequences:
  - Narrative-specific code in core is accepted as a reference bridge for now.
  - Future work should introduce adapter loader/versioning before extracting Narrative-specific adapter code.
  - Framework remains responsible for verification and trust, not product semantics.
  - This decision complements D-010: projects should pin both role versions and adapter versions.

## D-011 - LangGraph orchestration is a reserved optional adapter (F8+), never core
- Date: 2026-07-04, Status: Accepted / Reservation Decision; activation deferred to F8+
- Decision:
  - `voyage_framework/langgraph_tools/` is reserved as a future optional orchestration adapter for the gated control-loop / scheduled runtime at F8+.
  - LangGraph must never be the Voyage core runtime.
  - LangGraph must never auto-run agents.
  - LangGraph must stay an opt-in extra, behind the adapter boundary, and human-gated.
  - It must not be deleted as part of legacy cleanup.
- Rules:
  - `langgraph_tools/` is KEEP / reserved.
  - LangGraph may be used only as an optional orchestration adapter.
  - LangGraph must not become core runtime.
  - LangGraph must not bypass `validate-report`, `report-state`, human approval, or guarded workflows.
  - LangGraph activation is F8+ only, not part of F4/F5/F6/F7.
  - `simple_graph` fallback and `checkpoint_adapter` may be preserved as useful infrastructure.
  - `checkpoint_adapter` is recognized as future infrastructure for checkpoint/replay/control-loop state, not as current autonomy.
  - `agents/langgraph_runtime` requires separate review before cleanup because it may wire legacy CLI commands to `langgraph_tools`.
  - `voyage_framework_v4_mvp/` remains a separate cleanup candidate and is not protected by this decision.
- Rationale:
  - The original constraint is not that LangGraph is banned. The constraint is that LangGraph must not become the core runtime and must not auto-run agents.
  - As an optional adapter behind human gates, it may become useful later for the scheduled control-loop / orchestration phase.
  - Deleting tested graph infrastructure during cleanup would remove a potentially useful future asset.
- Consequences:
  - Legacy cleanup must not delete `langgraph_tools/`.
  - Any activation of LangGraph requires a future F8+ design gate.
  - The Framework remains deterministic and human-gated in current phases.
  - This decision is consistent with keeping autonomy last.

## D-012 - Risk-Based Adaptive Control with Voyage-Observed Evidence
- Date: 2026-07-05, Status: Accepted / Future Architecture Principle; no implementation yet
- Decision:
  - Voyage should adapt control intensity per proposed change, but only using evidence it can observe or policy it can verify.
  - Control level is not based on project size alone. It is based on:
    - risk of the proposed change;
    - criticality of the affected zone;
    - confidence in the known blast-radius;
    - repository state;
    - quality of the safety net;
    - hard-floor categories.
- Rules:
  - Risk classification is read-only and advisory.
  - Agent claims may be recorded, but cannot lower risk.
  - Tier evidence must be Voyage-observed, adapter-observed, CI-observed, or human-policy-backed.
  - Automation may escalate control automatically.
  - Automation may not de-escalate below policy or hard floors without explicit human approval from the relevant owner.
  - Unknown or low-confidence scope increases risk.
  - Unknown must also produce a path to reduce uncertainty through deterministic analysis, coverage maps, ownership maps, affected-file discovery, and rollback planning.
  - Hard floors override soft scoring.
  - Each gate must name the failure mode it prevents.
  - Gates without a clear prevented failure mode are ceremony and should be removed or downgraded.
  - Break-glass emergency paths, if introduced later, must be explicit, audited, time-limited, and followed by review/postmortem.
  - CI/CD is an execution plane; Voyage is the control plane.
- Hard-floor categories include:
  - secrets;
  - `.env`;
  - deploy;
  - production release;
  - database migrations;
  - mainline mutation;
  - destructive operations;
  - reset / clean / delete;
  - authentication;
  - payments;
  - infrastructure;
  - dependency major upgrades;
  - compliance-sensitive zones;
  - license-sensitive changes.
- Future policy file candidate:
  `.voyage/control_policy.yaml`
- A future control policy may define:
  - tiers;
  - hard floors;
  - forbidden paths;
  - zone criticality;
  - owners;
  - required checks per tier;
  - auto-escalation rules;
  - de-escalation approval rules;
  - break-glass rules;
  - evidence requirements;
  - allowed fast paths.
- Rationale:
  - Voyage exists because AI agents are not trusted reporters. If an agent can provide the evidence used to weaken its own gates, it can bypass the safety model. Adaptive control must reduce ceremony for genuinely low-risk changes, but only when the lower risk is supported by trusted evidence and does not cross hard floors.
- Consequences:
  - Low-risk work can eventually use lighter gates.
  - High-risk work remains strongly gated.
  - Unknown scope increases control until evidence reduces uncertainty.
  - The future risk detector must be tested.
  - F6 edit-preview provides the first substrate for this decision.
  - F7 guarded writes must respect this decision.
- Relationship to other decisions:
  - D-009 Project Adapter Ownership:
    project adapters may provide domain-specific risk signals, but Framework keeps the trust/control model.
  - D-010 Role Versioning:
    control policies should also be pinned/versioned.
  - D-011 LangGraph Reserved:
    future orchestration must remain behind D-012 gates.
  - D-013 Application Modernization:
    future modernization must balance risk-of-change and risk-of-inaction through this control model.
