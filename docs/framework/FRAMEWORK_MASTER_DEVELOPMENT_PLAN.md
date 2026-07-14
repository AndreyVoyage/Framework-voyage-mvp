# Voyage Framework — Master Development Plan

- Status: Canonical planning document
- Date: 2026-07-14
- Planning baseline: `2b13b67c6bb5999f48f6be404ebd0d6c99ededed`
- Governing decisions: [ADR-0001](adr/ADR-0001-framework-narrative-separation.md), [D-009 through D-014](FRAMEWORK_DECISIONS.md)
- Security gate: [MCP-SEC-01](MCP_THREAT_MODEL.md)
- Implementation authorization: phase-specific only

This plan does not authorize implementation. Every executable phase requires its own accepted prompt or plan, exact baseline, clean read-only preflight, human authorization, scoped validation, and isolated acceptance.

## Status vocabulary

Only these planning states are used: **DONE**, **ACTIVE APPROVED**, **READY FOR READ-ONLY PREFLIGHT**, **PLANNED / NOT AUTHORIZED**, **FUTURE / DEFERRED**, **OPTIONAL**, **RESERVED**, and **BLOCKED**.

Decision acceptance, canonical documentation, plan acceptance, preflight passage, implementation authorization, implementation start, and implementation completion are separate states.

## Product and architecture identity

Voyage is a local project-knowledge and development-memory system combined with validation/evidence, trust/gate/control, and stable interfaces/adapters. The v4.1 contract, ADR-0001, and D-009…D-014 are authoritative for this identity.

- Voyage is not an agent runtime.
- CLI and the human-controlled authorize/apply path remain first-class.
- MCP is a future additive READ/VALIDATE/EXPLAIN facade; restricted PROPOSE is later and optional.
- Autonomous AUTHORIZE, APPROVE, and APPLY remain outside MCP.
- LangGraph is **RESERVED** under D-011 and is not an MCP dependency.
- CONTROL-LOOP-1 is the only currently active control-loop surface; CONTROL-LOOP-2…10 are **FUTURE / DEFERRED**, marked not implemented and not executable.

## Planning principles

1. Evidence precedes status.
2. Human authorization is separate from evidence completeness.
3. Documentation never authorizes implementation.
4. Every implementation phase begins with a clean read-only preflight.
5. Stable core service interfaces precede external facades.
6. Sequential delivery precedes parallel complexity.
7. Deliver small vertical slices with isolated commits.
8. Existing active approved work is not displaced without an explicit decision.
9. Future-only specifications remain future-only.
10. No agent or phase may approve itself.
11. Every phase has entry gate, exit gate, and stop conditions.
12. Authoritative mutation remains on the human-controlled path.
13. Blocking MCP-SEC-01 requirements override phase convenience.
14. No hidden scope expansion is allowed.
15. Canonical repository documents outrank workspace drafts.

## Canonical source audit

| Source | Classification | Planning use |
|---|---|---|
| `docs/VOYAGE_V4_1_CONTRACT.md`, ADR-0001 | CANONICAL CURRENT | Product identity and separation |
| `FRAMEWORK_DECISIONS.md` D-009…D-014 | CANONICAL CURRENT/FUTURE | Binding ownership, role, orchestration, control, modernization, and MCP decisions |
| `FRAMEWORK_PROGRESS.md` | CANONICAL CURRENT | Implemented phase ledger and actual F7 status |
| `FRAMEWORK_ROADMAP.md` | CANONICAL FUTURE | Direction and horizon ordering |
| `MCP_INTERFACE_BOUNDARY.md` | CANONICAL FUTURE | D-014 authority boundary |
| `MCP_THREAT_MODEL.md` | ACTIVE APPROVED security design | Blocking MCP security requirements and tests |
| `MODERNIZATION_CONCEPT.md` | CANONICAL FUTURE | D-013 future direction; implementation not started |
| `guarded_write.py`, `guarded_write_approval.py`, `edit_preview.py` | IMPLEMENTED/PARTIAL | Read-only plans and approval verification; structured apply absent |
| `_git_utils.py`, `report_validator.py`, ContextBuilder, EventEngine, adapters | IMPLEMENTED/PARTIAL | Current service evidence to audit in BASELINE-READ-01 |
| `tests/unit/test_architecture_boundaries.py` | IMPLEMENTED/PARTIAL | Current boundaries; future MCP tests absent |
| `CONTROL_LOOP_SPEC.md`, `control-loop-1.yaml` | CANONICAL CURRENT | CONTROL-LOOP-1 read-only surface |
| CONTROL-LOOP-2…10 documents/YAML | CANONICAL FUTURE | Explicitly not implemented and execution forbidden |
| `langgraph_tools/` | RESERVED | D-011 optional future adapter only |
| Historical reports/plans and nested snapshot | LEGACY / STALE RISK | Evidence/history only, not current plan authority |
| Handoff artifacts and workspace drafts | EXTERNAL / NON-CANONICAL | Validation evidence/provenance only |

## Baseline snapshot

| Item | State | Canonical evidence |
|---|---|---|
| Repository | `main` at `2b13b67c6bb5999f48f6be404ebd0d6c99ededed`, synchronized and clean at plan preflight | Git facts |
| D-009…D-012 | DONE as accepted decisions; related implementations vary | `FRAMEWORK_DECISIONS.md`, progress ledger |
| D-013 documentation | DONE at `99cef25a91f2455a2259195c023774af6ebb6bba` | progress ledger and concept |
| D-013 implementation | PLANNED / NOT AUTHORIZED | D-013 concept and roadmap |
| D-014 documentation | DONE at `4433e4760d9d4a93f5bfbbdcc74683ed956ce009` | progress ledger and boundary |
| MCP-SEC-01 | DONE as canonical security design at `2b13b67c6bb5999f48f6be404ebd0d6c99ededed` | threat model and progress |
| MCP implementation | PLANNED / NOT AUTHORIZED; not started | D-014 and threat model |
| F7-B/F7-C1 | DONE read-only planning/verification surfaces | progress ledger |
| F7-D | PLANNED / NOT AUTHORIZED; structured create/replace writes not started | progress ledger |
| F7-D1 identifier | BLOCKED as an execution identifier: no canonical phase definition found; newer MCP planning text uses the name while the ledger uses F7-D | roadmap/threat model versus progress ledger |
| CONTROL-LOOP-1 | ACTIVE APPROVED read-only surface | control-loop canonical spec |
| CONTROL-LOOP-2…10 | FUTURE / DEFERRED; not implemented | explicit document/YAML markers |
| LangGraph | RESERVED | D-011 |
| Implemented services | TaskEngine, EventEngine, ContextBuilder, Chronicler, report-state, validate-report, read-only adapters, edit-preview, guarded-write plan and approval verification | code/tests/progress |
| Partial/unverified areas | Stable MCP-facing service seams, reusable precedence service, MCP identity/redaction/limits/process boundary, and actual F7-D/F7-D1 dependency relationship | MCP-SEC-01 and code audit |
| Planning blocker | Resolve F7-D versus F7-D1 naming/scope and exact interface dependencies before any execution ordering | BASELINE-READ-01 output |

The current active workstream after acceptance of this plan is the read-only planning gate, not an implementation track.

## Workstream map

| Workstream | Purpose | Status | Owner/source | Dependencies/outputs | Parallel-safe / must not overlap | Human gate |
|---|---|---|---|---|---|---|
| WS-A — Current Framework/F7-D | Reconcile and later plan structured writes | READY FOR READ-ONLY PREFLIGHT | progress ledger, F7 decisions | BASELINE-READ-01; exact F7 phase decision | Read-only audit may parallel independent docs; no concurrent code with MCP in one worktree | explicit F7 plan approval |
| WS-B — D-013 modernization | Identify only service modernization actually required | PLANNED / NOT AUTHORIZED | D-013 concept | D013-MOD-PREFLIGHT; small accepted slices | Documentation/read-only work only; no rewrite or hidden MCP work | per-slice approval |
| WS-C — MCP security/read facade | Deliver future least-privilege facade | READY FOR READ-ONLY PREFLIGHT | D-014, MCP-SEC-01 | Master Plan → preflight → gated slices | No MCP/F7 code concurrently in one worktree | security and phase owner approval |
| WS-D — Documentation/progress/acceptance | Keep canonical status and evidence aligned | ACTIVE APPROVED for this documentation step only | repository rules | isolated docs/reports | May accompany phases within exact scope | documentation acceptance |
| WS-E — Reserved future architecture | Preserve LangGraph, later loops, optional UX/proposal/process work | RESERVED / FUTURE | D-011 and future specs | separate decisions | Must not be pulled into active slices | new decision/plan |

## Dependency graph

```text
D-014 canonical (DONE)
    -> MCP-SEC-01 accepted (DONE)
        -> MASTER-PLAN-REFRESH accepted (PLAN-00)
            -> BASELINE-READ-01 accepted
                -> resolve F7-D vs F7-D1 and required service seams
                -> D013-MOD-PREFLIGHT, only if interface debt is evidenced
                    -> optional small D013-MOD-SLICE(s), each separately accepted
                -> MCP-READ-PREFLIGHT accepted
                    -> MCP-READ-01 may be authorized
                        -> MCP-READ-02 may be authorized
                            -> required MCP-SEC-02 hardening accepted
                                -> MCP-PILOT-01 may be authorized
                                    -> MCP-PROPOSE-01 (OPTIONAL, separate review)
                                    -> MCP-PROC-01 (CONDITIONAL trigger)
```

MCP does not depend on LangGraph or future control loops. F7-D is not presumed to precede all modernization or read-only MCP work. Whether a specific F7 structured-write slice or modernization seam must precede MCP-READ-PREFLIGHT is **BLOCKS EXECUTION ORDER** and must be resolved with repository evidence by BASELINE-READ-01.

## Canonical phase sequence

There are 13 plan phases/groups. Only PLAN-00 is completed by this documentation task; the next phase is read-only.

| Phase | Status | Purpose | Hard dependency |
|---|---|---|---|
| PLAN-00 | DONE when this commit is accepted | Canonicalize integrated plan | MCP-SEC-01 |
| BASELINE-READ-01 | READY FOR READ-ONLY PREFLIGHT | Resolve actual seams and exact ordering | PLAN-00 |
| F7-D-PLAN / canonical identifier resolution | PLANNED / NOT AUTHORIZED | Define structured-write slice and resolve F7-D1 alias/question | BASELINE-READ-01 |
| F7-D execution track | PLANNED / NOT AUTHORIZED | Future structured create/replace writes | accepted F7 plan |
| D013-MOD-PREFLIGHT | PLANNED / NOT AUTHORIZED | Prove whether modernization is needed for stable services | BASELINE-READ-01 |
| D013-MOD-SLICE | OPTIONAL | Small compatibility-preserving service seams only | accepted modernization preflight |
| MCP-READ-PREFLIGHT | PLANNED / NOT AUTHORIZED | Freeze tools, dependencies, security design, limits, disable plan | baseline and required seams |
| MCP-READ-01 | FUTURE / DEFERRED | Minimal deterministic read-only vertical slice | accepted MCP preflight |
| MCP-READ-02 | FUTURE / DEFERRED | Validation/explanation tools | MCP-READ-01 accepted |
| MCP-SEC-02 | FUTURE / DEFERRED | Complete hardening for pilot | controls may shift earlier when blocking |
| MCP-PILOT-01 | FUTURE / DEFERRED | One approved client | required hardening accepted |
| MCP-PROPOSE-01 | OPTIONAL | Non-authoritative proposal layer | separate threat review/approval |
| MCP-PROC-01 / FUTURE-RESERVED | CONDITIONAL / RESERVED | Process isolation trigger; LangGraph/loops/autonomy stay reserved | accepted trigger/new decisions |

## Phase contracts

### PLAN-00 — Master Plan Canonicalization

- **Status:** DONE when this documentation commit is accepted.
- **Purpose / inputs:** integrate ADR-0001, D-009…D-014, MCP-SEC-01, roadmap, progress, and verified Git baseline.
- **Entry gate:** clean synchronized baseline and canonical sources.
- **Allowed / forbidden:** three documentation files only / all implementation.
- **Deliverables:** this plan, roadmap/progress reconciliation, reports.
- **Validation/security:** links, scope, architecture checks, validate-report, hooks, report-state; all D-014 boundaries preserved.
- **Human approval / commit:** documentation acceptance; one isolated verified commit.
- **Exit / rollback:** canonical commit pushed cleanly; revert commit if rejected.
- **Stop conditions / next:** source conflict or validation failure stops; next BASELINE-READ-01.

### BASELINE-READ-01 — Integrated Read-Only Implementation Preflight

- **Status:** READY FOR READ-ONLY PREFLIGHT; not started by this plan.
- **Purpose / inputs:** inspect actual F7-D/F7-D1 status, D-013 dependencies, service seams, report/context/decision interfaces, Git controls, and MCP-SEC-01 gaps.
- **Entry gate:** separate accepted prompt, clean exact baseline, PLAN-00 accepted.
- **Allowed / forbidden:** read-only code/docs/tests and existing non-mutating checks / repository mutation or phase execution.
- **Deliverables:** evidence inventory, identifier resolution, exact dependency order, gap/risk report, one next task.
- **Validation/security:** current boundary/trust tests; map all blocking requirements/tests without implementing them.
- **Human approval / commit:** human accepts report; normally no repository commit unless separately scoped docs are approved.
- **Exit / rollback:** accepted ordering and baseline; no rollback needed for read-only activity.
- **Stop conditions / next:** contradictions or mutation stop; next exact F7 plan, D013 preflight, or MCP-READ-PREFLIGHT chosen from evidence.

### F7-D-PLAN and F7-D execution track

- **Status:** PLANNED / NOT AUTHORIZED; F7-D1 is not yet a canonical distinct identifier.
- **Purpose / inputs:** define then deliver structured create/replace writes behind verified approval, checkpoint/rollback, drift checks, and post-write validation.
- **Entry gate:** BASELINE-READ-01 resolves identifier/scope; separate F7 plan and human approval.
- **Allowed / forbidden:** only exact accepted write slice / autonomous commit-push, MCP coupling, broad apply, deploy, or modernization.
- **Deliverables:** plan first; implementation only in later authorized slice with tests and reports.
- **Validation/security:** F6/F7 evidence binding, D-012 controls, forbidden paths, rollback and non-autonomy tests.
- **Human approval / commit:** explicit plan and operation approvals; one isolated commit per slice.
- **Exit / rollback:** accepted tests plus disable/revert/checkpoint procedure; no universal rollback promise.
- **Stop conditions / next:** ambiguous scope, dirty/drifted target, invalid approval, or safety failure stops; transition selected by human.

### D013-MOD-PREFLIGHT and D013-MOD-SLICE

- **Status:** PLANNED / NOT AUTHORIZED; slices OPTIONAL until evidence proves need.
- **Purpose / inputs:** map service boundaries/debt, compatibility, precedence/provenance/audit seams; prevent MCP-specific code being hidden as modernization.
- **Entry gate:** BASELINE-READ-01 evidence and separate prompt.
- **Allowed / forbidden:** read-only preflight; later smallest accepted generic seam / big-bang rewrite, manifest activation, scheduler, MCP facade, or F7 execution.
- **Deliverables:** dependency map and, only if approved, stable read/validation/explanation, precedence, metadata, adapter, audit, or boundary seam.
- **Validation/security:** compatibility/regression/boundary tests selected per D-012; no MCP dependencies.
- **Human approval / commit:** per-slice approval and isolated commit.
- **Exit / rollback:** stable backward-compatible interface accepted; Git revert/feature disable as designed.
- **Stop conditions / next:** unproven need, broad rewrite, or contract conflict stops; next MCP-READ-PREFLIGHT only after required seams accepted.

### MCP-READ-PREFLIGHT

- **Status:** PLANNED / NOT AUTHORIZED.
- **Purpose / inputs:** freeze exact tool shortlist/services; SDK/transport, identity/exposure, result contract, Git allowlist, redaction/provenance/precedence, numeric limits, packaging/process, tests, rollback/disable.
- **Entry gate:** BASELINE-READ-01 and required generic seams accepted; D-014/MCP-SEC-01 unchanged.
- **Allowed / forbidden:** read-only design and verification / MCP code or dependency installation.
- **Deliverables:** executable MCP-READ-01 plan with requirement/test trace and explicit accepted choices.
- **Validation/security:** all MCP-SEC-REQ-001…024 classified; MCP-SEC-TEST-001…025 assigned; critical/high threats controlled by plan.
- **Human approval / commit:** security and architecture owners approve; documentation commit only if separately scoped.
- **Exit / rollback:** preflight verdict A; no runtime rollback.
- **Stop conditions / next:** any open blocker or authority leak stops; next MCP-READ-01 only after separate implementation authorization.

### MCP-READ-01

- **Status:** FUTURE / DEFERRED.
- **Purpose / inputs:** minimal deterministic subset of `project_status`, `report_state`, `get_decision`, `get_task`, `list_tasks`, or `list_required_evidence` selected by preflight.
- **Entry gate:** approved MCP preflight, exact baseline, blocking controls/tests ready.
- **Allowed / forbidden:** semantic project-scoped reads / generic files, commands, network expansion, proposals, authorize/apply.
- **Deliverables:** smallest facade slice, versioned results, audit, disable switch, tests/reports.
- **Validation/security:** blocking architecture, identity, path, secret, Git, result, limit, isolation, and non-mutation tests.
- **Human approval / commit:** explicit implementation approval; isolated commit; no self-approval.
- **Exit / rollback:** tests and security validation accepted; disable switch and Git revert proven.
- **Stop conditions / next:** boundary/test/identity/redaction failure stops; next MCP-READ-02 only after acceptance.

### MCP-READ-02

- **Status:** FUTURE / DEFERRED.
- **Purpose / inputs:** approved `validate_report`, gate evidence, decision/gate explanations, and policy-controlled context/search subset.
- **Entry gate:** MCP-READ-01 accepted and no unresolved critical/high risk.
- **Allowed / forbidden:** deterministic validation and labelled derived/advisory explanation / authority, mutation, generic retrieval.
- **Deliverables:** selected tools, precedence/provenance/redaction, injection containment, tests/reports.
- **Validation/security:** completeness-versus-authorization, advisory semantics, conflict, injection, budget, and consistency tests.
- **Human approval / commit:** explicit slice approval and isolated commit.
- **Exit / rollback:** accepted tools can be disabled/reverted independently.
- **Stop conditions / next:** ambiguous authority or unsafe context stops; required MCP-SEC-02 controls follow.

### MCP-SEC-02

- **Status:** FUTURE / DEFERRED; blocking controls move earlier when their requirement applies to READ-01/02.
- **Purpose / inputs:** harden provenance, redaction, identity, precedence, compatibility, limits, injection containment, audit, and package/process boundaries.
- **Entry gate:** accepted read slices and explicit remaining-control inventory.
- **Allowed / forbidden:** security hardening only / new tools or expanded authority.
- **Deliverables:** blocking controls/tests and operational security evidence.
- **Validation/security:** remaining MCP-SEC-TEST matrix, dependency/transport review, negative tests.
- **Human approval / commit:** security acceptance; isolated commits.
- **Exit / rollback:** pilot gate A and disable/revert plan.
- **Stop conditions / next:** any high/critical uncontrolled risk stops; next MCP-PILOT-01.

### MCP-PILOT-01

- **Status:** FUTURE / DEFERRED.
- **Purpose / inputs:** one approved client, accepted identity/exposure/tool allowlist and hardening.
- **Entry gate:** MCP-SEC-02 acceptance, disable switch, operations plan.
- **Allowed / forbidden:** one client and approved read tools / authoritative tools, extra clients, silent remote exposure.
- **Deliverables:** pilot evidence, audit review, acceptance report.
- **Validation/security:** identity, isolation, abuse/load, disable, incident and non-mutation checks.
- **Human approval / commit:** explicit operational approval; no automatic expansion.
- **Exit / rollback:** pilot accepted or facade disabled/shut down.
- **Stop conditions / next:** boundary/identity/availability failure stops; optional proposal or process decision only by human.

### MCP-PROPOSE-01

- **Status:** OPTIONAL / FUTURE / DEFERRED.
- **Purpose / inputs:** non-authoritative proposal store after separate threat review.
- **Entry gate:** accepted pilot and proposal-specific security/approval plan.
- **Allowed / forbidden:** typed immutable proposals with rate, dedup, TTL, replay/version controls / direct state mutation or MCP approval.
- **Deliverables:** isolated store, human channel binding, tests/reports.
- **Validation/security:** MCP-THR-016/017 and MCP-SEC-TEST-022 plus store/audit limits.
- **Human approval / commit:** separate decision and operation approval.
- **Exit / rollback:** feature disable; purge only through approved operational procedure.
- **Stop conditions / next:** any authority/storage ambiguity stops; no mandatory successor.

### MCP-PROC-01 and FUTURE-RESERVED

- **Status:** CONDITIONAL / RESERVED.
- **Purpose / inputs:** extract/harden separate process if initial slice is in-process, risk review requires isolation, pilot exposes lifecycle issues, or deployment requires it; preserve future architecture.
- **Entry gate:** accepted trigger and dedicated plan.
- **Allowed / forbidden:** boundary/lifecycle hardening / LangGraph dependency, autonomy, control-loop activation, generic MCP client ingestion.
- **Deliverables:** physical isolation/operations evidence if triggered; otherwise no work.
- **Validation/security:** process boundary, shutdown, transport, compatibility, supply-chain tests.
- **Human approval / commit:** separate approval and isolated changes.
- **Exit / rollback:** process shutdown/package revert; no automatic external cleanup.
- **Stop conditions / next:** absent trigger means no phase; reserved work requires new decisions.

## Gate matrix

| Transition state | Required evidence / validator | Human approver | Automatic actions allowed | Automatic actions forbidden |
|---|---|---|---|---|
| Documentation accepted | scoped diff, links, validate-report, hooks, Git facts | documentation/architecture owner | read-only validation | implementation, self-approval |
| Preflight passed | canonical inventory, clean baseline, conflicts resolved | phase owner | inspection/tests | mutation or phase launch |
| Implementation authorized | accepted phase contract, threat/control/test mapping, rollback/disable | architecture/security/product owner as applicable | only scoped implementation | scope expansion, authority escalation |
| Implementation complete | tests, changed files, report, commit facts | phase owner/reviewer | post-commit validation | self-declared completion |
| Security validation passed | blocking tests and risk review | security owner | advance to human gate | waive critical/high controls |
| Human approval granted | identity, exact version/scope, evidence | named human | approved transition only | reuse for changed content |
| Push accepted | remote race check, hooks, post-commit validation | repository owner policy | normal push | force/rebase/hidden merge |
| Operational pilot accepted | audit, identity, limits, disable/incident evidence | operational/security owner | approved single client | tool/client expansion |

No phase authorizes itself. Evidence completeness never equals authorization.

## Security traceability

The detailed register remains canonical in [MCP-SEC-01](MCP_THREAT_MODEL.md). No high/critical risk disappears from this plan.

| Security items | Designed/frozen | Implemented | Blocking test gate |
|---|---|---|---|
| MCP-THR-001…006 (identity, deputy, path, secrets) | MCP-READ-PREFLIGHT | MCP-READ-01 / SEC-02 as applicable | TEST-003…008, 017, 023 |
| MCP-THR-007…011 (content/command/Git/TOCTOU) | MCP-READ-PREFLIGHT | MCP-READ-01/02 | TEST-009, 012…014, 024 |
| MCP-THR-012…015 (canonicality/provenance/result/version) | BASELINE-READ-01 + MCP preflight | MCP-READ-01/02/SEC-02 | TEST-010, 011, 015, 016, 021, 025 |
| MCP-THR-016…017 (proposal abuse/version binding) | proposal-specific review | MCP-PROPOSE-01 only | TEST-022 |
| MCP-THR-018…021 (audit, resources, supply chain, transport) | Master Plan + MCP preflight | READ-01/SEC-02/operations | TEST-018…021 |
| MCP-THR-022…024 (architecture and availability) | MCP-READ-PREFLIGHT | READ-01/SEC-02/operations | TEST-001, 002, 019, 020, 024 |
| MCP-SEC-INV-001…020 | Master Plan and MCP preflight | phase where applicable | all relevant phase gates |
| MCP-SEC-REQ-001…024 | MCP-READ-PREFLIGHT classifies all; OPEN choices must close | phase named in threat model | blocking at first applicable phase |
| MCP-SEC-TEST-001…025 | fixture/expected result frozen in MCP preflight | never in this planning task | first phase named by MCP-SEC-01 |

All MCP-SEC-01 threats are high or critical. Blocking requirements cannot be deferred past the first phase they protect; controls labelled MCP-SEC-02 move into MCP-READ-01/02 when required for safe entry.

## F7-D and modernization reconciliation

1. **What is F7-D?** Canonically, the progress ledger defines F7-D as future structured create/replace writes behind verified approval; implementation is not started.
2. **What is F7-D1?** No distinct canonical phase definition was found. Its newer references are planning placeholders. Treating it as an executable ID is **BLOCKS EXECUTION ORDER**.
3. **Does it modify MCP-relevant services?** Not currently provable. F7-D is an authoritative write path, which MCP must not import; any shared service-interface effect requires BASELINE-READ-01 evidence.
4. **D-013 relationship:** D-013 requires future guarded application but does not activate F7-D and does not prove that all modernization precedes/follows it.
5. **Independent documentation:** F7 and MCP documentation/read-only audits may proceed independently when scoped; neither authorizes code.
6. **Concurrent code:** F7 and MCP code must not run concurrently in one worktree. Separate worktrees still require accepted plans and conflict analysis; parallel-safe is not automatic authorization.
7. **Stable baseline before MCP preflight:** accepted BASELINE-READ-01 output, resolved F7 identifier/dependency, accepted required generic service seams, clean synchronized commit.
8. **Human decision:** after BASELINE-READ-01, the architecture/control owner must accept whether the next executable slice is F7-D-PLAN, a D013 modernization preflight/slice, or MCP-READ-PREFLIGHT.

## Worktree and branch policy

- One implementation phase per controlled branch/worktree unless an accepted plan states otherwise.
- Clean worktree is required at entry and exit; baseline is `HEAD == origin/main` or an exact approved branch commit.
- Agents do not silently switch branches or use reset, clean, rebase, non-fast-forward merge, or force push.
- External drift is observed and reported, never repaired out of scope.
- Handoff reports remain outside the repository; only exact approved files are staged.
- Perform a remote race check before normal push; use one isolated commit per accepted slice.

## Report and evidence policy

Every phase produces a preflight report, pre-commit validation report when files change, post-commit report, exact changed-file list, commit hash, push status, final clean-state proof, and one next action. Implementation phases use `voyage.report.v1`, `validate-report`, and `report-state` where applicable. Documentation alone never proves implementation.

## Rollback and disable strategy

- Repository changes use reviewed Git revert, not history rewriting.
- MCP phases require a feature/transport disable switch and package/process shutdown plan before authorization.
- Schema migration reversal requires a separately approved migration plan.
- Proposal-store disable/purge requires an approved operational procedure.
- No phase promises automatic external-service cleanup or universal rollback.
- Each implementation phase must name its specific rollback or disable approach at entry.

## Planning risk register

| Risk | Impact | Mitigation | Owner phase | Blocking gate | Residual risk |
|---|---|---|---|---|---|
| Scope explosion | unsafe mixed change | exact files/services, small slices | every phase | entry/scope review | discovery may expand backlog |
| F7-D/F7-D1/MCP conflict | wrong execution order | BASELINE-READ-01 resolution | BASELINE-READ-01 | blocks order | later interface drift |
| Modernization becomes rewrite | compatibility loss | evidence-only slices, D-013 gates | D013 preflight | slice approval | latent debt |
| Facade bypasses services | authority leak | stable interfaces, forbidden dependencies | MCP preflight/READ-01 | security tests | host compromise |
| Security deferred too late | critical exposure | requirements block first applicable phase | all MCP phases | security gate | new threats |
| Precedence not reusable | inconsistent authority | inspect/refactor generic seam only if approved | baseline/D013 | MCP preflight | classification error |
| report-state/validate-report side effects | repository mutation | before/after non-mutation tests | baseline/READ-01 | TEST-024/025 | external Git races |
| Windows path bypass | secret/cross-root read | case/separator/junction tests | READ-01 | TEST-004…006 | OS races |
| SDK/protocol churn | rework/supply risk | Master Plan choice, pinning, compatibility | MCP preflight | dependency gate | upstream change |
| Weak client identity | excess access | minimum scope, explicit identity model | READ-01/SEC-02 | TEST-017 | compromised client |
| Prompt injection | policy bypass | content-as-data, labelled outputs | READ-01/02 | TEST-009 | persuasive content |
| Secret leakage | credential compromise | structural exclusion/redaction | READ-01 | TEST-007/008 | secrets in history |
| Unbounded context | local DoS/data leak | numeric limits and budgets | MCP preflight | TEST-019/020 | large legitimate repo |
| False implementation status | governance failure | canonical evidence/status labels | WS-D | acceptance review | human reporting error |
| Parallel worktree drift | conflicts/stale baseline | isolated work, race checks | all | entry/push gate | remote concurrency |
| Documentation/code divergence | obsolete controls | traceability and acceptance reports | WS-D/operations | phase closeout | later unreviewed refactor |

## Milestones

These are evidence milestones, not calendar promises.

| Milestone | Evidence state | Planning size |
|---|---|---|
| M0 — canonical decisions and threat model | DONE | — |
| M1 — master plan accepted | PLAN-00 acceptance | S |
| M2 — integrated read-only preflight accepted | BASELINE-READ-01 verdict A | M |
| M3 — required modernization/service seams accepted | zero or more evidence-required slices accepted | M–L |
| M4 — MCP-READ-01 accepted | minimal read slice/security tests accepted | L |
| M5 — MCP-READ-02 accepted | validation/explanation slice accepted | L |
| M6 — security hardening accepted | pilot blockers closed | L |
| M7 — single-client pilot accepted | operational report accepted | L |
| M8 — optional proposal decision | explicit decision, not implied | M |
| M9 — optional process hardening | trigger and acceptance evidence | M–L |

Sizes are planning estimates, not commitments.

## Immediate next action

**BASELINE-READ-01 — perform an integrated read-only implementation preflight covering F7-D/F7-D1 identifier and status, D-013 modernization dependencies, stable service interfaces, and MCP-READ prerequisites.**

This Master Development Plan is canonical planning documentation.
It does not start F7-D1, D-013 modernization, MCP-READ-01, LangGraph, control-loop work or any other implementation.
The next executable task requires a separate approved prompt and a clean read-only preflight.
