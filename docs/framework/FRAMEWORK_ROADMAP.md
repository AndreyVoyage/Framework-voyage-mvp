# Framework Roadmap

> Direction: Framework = **generic development-control OS** (multi-repo control via adapters). Narrative is the first integrated repo, not the goal. See `adr/ADR-0001-framework-narrative-separation.md`.
> Target path in repo: `docs/framework/FRAMEWORK_ROADMAP.md`.
> Binding rules live in `FRAMEWORK_CONTROL_RULES.md`; decisions in `FRAMEWORK_DECISIONS.md`; status in `FRAMEWORK_PROGRESS.md`.

## 1. Verified current state (live code)

- CLI (`voyage_framework/cli.py`): `init, status, tasks(create/list/show/start/block/unblock/complete/fail/archive), events, sync(build/status/check), approve, evaluate, chronicler, docs, auto(preflight/plan/validate), narrative(scene-validate/arc-check), validate-report`.
- Trust engine (F0-B): `core/report_validator.py`, schema `voyage.report.v1`; rejects non-40-char/non-hex hashes; `git cat-file -t` existence; compares to `git rev-parse HEAD`/`origin/main`; clean/changed/staged; role-based forbidden paths; verdict A/B/C; BOM-tolerant loader (`utf-8-sig`). CLI wired. Closed: committed `01b1935` and pushed to origin/main.
- Adapter seam present: `core/adapter_protocols.py::AdapterProtocol` (agent adapter), `core/adapter_contract.py` (`AdapterContract`/`AgentRequest`/`AgentResponse`/`ApprovalFlow`). `core/narrative_adapter.py` is a one-off repo-control implementation.
- Read-only git/spec: `core/auto_loop.py` + `core/_git_utils.py`.
- Narrative repo: 31 `SCENARIO_*.json` (SC_003-SC_027), `tools/rn_workflow.py` (`status/safety-scan/validate/baseline-report/audit-source/validate-patch/ready-for-gui`).
- Known debts: pre-existing ruff `E402` in `tests/unit/test_auto_loop.py`; narrative adapter tests ~470s; forbidden paths hardcoded (not spec-driven); no `auto_commit` range check in validator.

## 2. Target architecture (layers; core minimal & independent)

Core (repo-agnostic; stdlib + pydantic + pyyaml + sqlite3) -> CLI (thin, read-only default) -> Runtime Package layer (file-based specs) -> Guard/Safety layer -> Adapter layer (agent adapter `AdapterProtocol`; future repo-control adapter `status/validate/audit/preview`) -> Trust layer (`validate-report` + future `report-state`) -> Storage (SQLite as derived index; files = source of truth) -> Dashboard (much later, read-only).

## 3. Phases (each = its own gated slice)

- **F0-B - Trust engine (DONE).** `validate-report` implemented; dogfood caught a BOM-loader bug, fixed (`utf-8-sig`) + test; committed `01b1935`, pushed to origin/main.
- **F0-D - Documentation & decisions (this set).** ADR + roadmap + control rules + decisions + progress.
- **F0-E - Negative assert.** Feed a report with a synthetic/false 40-char hash to `validate-report`; expect `ok:false`.
- **F1 - Hygiene / performance.** Fix `E402`; shared `conftest.py` temp-repo fixture; target narrative suite <120s.
- **F2 - Generic repo-control adapter.** Define `RepoControlAdapter` (`status/validate/audit/preview`); refactor `narrative_adapter.py` to implement it; extract `_path_guards.py`. (Deferred until docs are written.)
- **F3 - Trust hardening.** `voyage report-state` (canonical observed-state JSON); changed-files vs named `auto_commit` (error-grade); spec-driven forbidden paths.
- **F4 - Narrative read-only tools (via adapter).** `narrative preflight`, `narrative spec-update` (read-only patch proposal). No writes.
- **F5 - Second adapter (prove multi-repo).** e.g. SkillTracer as a `RepoControlAdapter`, read-only.
- **F6 - Edit-safety & preview.** `edit-check` (before/after integrity, no apply); `preview/render-check` - before any write.
- **F7 - Guarded write.** Authorized text edits in the target repo's own worktree, only after edit-check + preview + human approval.
- **F8+ - Agent runtime / scheduler (far, gated).** Use `AdapterProtocol` for agent invocation via package + approval + guards + report validation. No auto-merge/push/deploy ever.

## 4. Estimated gates
F2 ~3, F3 ~3, F4 ~2-3, F5 ~3-4, F6 ~3-4, F7 ~3-4, F8+ ~8-12 (deliberately far).

## 5. Order (locked)
F0-B closeout -> F0-D docs+ADR -> F0-E negative assert -> F1 hygiene/perf -> F2 generic adapter. Do not skip; no new development until ADR + roadmap are written into the repo.

## 6. Future horizon — Role lifecycle safety
- Role versioning and immutable `RoleProfile` catalog.
- Project-side role lockfile / pinned role versions.
- Role Upgrade Gate: role version diff, human approval, regression checks, `validate-report`, audit trail.
- Role regression tests.
- Role Freshness Auditor: read-only external documentation/changelog review; propose-only role update reports; no automatic role mutation; no direct writes to the role catalog.
- Timing: versioning/pinning/gate possible F6/F7 candidate; freshness auditor F8+ candidate; no implementation started in this closeout.

## 7. Future horizon — adapter ownership / plugin model
- Project-specific adapters should move project-side or plugin-side once adapter loading/versioning exists.
- Framework owns contracts, validation, trust engine (`validate-report`, `report-state`), guardrails, and gated workflows.
- Projects/plugins own domain-specific checks and spec-plan logic.
- Built-in Narrative adapter remains a reference / migration bridge until a safe extraction path exists.
- Adapter versions should be pinnable by consuming projects, aligned with D-010 role versioning.
- No implementation started in this closeout.

## 8. Future horizon — orchestration, F8+ only
- LangGraph optional orchestration adapter is reserved for gated control-loop / scheduler work.
- opt-in extra only; behind adapter boundary; human-gated; never core runtime; never auto-run agents.
- Reuse existing `langgraph_tools/` only after a future F8+ design gate.
- No implementation started in this closeout.

## 9. Future horizon — risk-based adaptive control
- Introduce project-pinned control policy after F6/F7 substrate is stable.
- Candidate file:
  `.voyage/control_policy.yaml`
- Risk detector must be read-only/advisory.
- Evidence must be Voyage-observed or policy-backed, not agent-claimed.
- Automation may escalate controls automatically.
- De-escalation requires human approval and must not cross hard floors.
- Hard floors include secrets, deploy, migrations, destructive operations, mainline mutation, auth, payments, infra, compliance/license-sensitive zones.
- F7 guarded writes must consume F6 edit-preview safety findings.
- D-013 modernization remains future and should reuse D-012 rather than bypass it.
- No implementation started in this closeout.

## 10. F7 guarded write status
- **F7-B guarded-write approval/preflight layer completed** (commit `944f3cec2c53a44c95200a27eb867bbda1098759`).
- It consumes F6 `edit-preview` output and produces a human-approval-required plan.
- It is read-only: no file writes, no patch generation, no apply, no staging, no commit to target repo.
- `approval_required=true`, `writes_supported=false`, `next_gate=human_approval_required`.
- **F7-C remains future:** structured writes behind explicit human approval, checkpoint/rollback, drift checks, and post-write validation.
- **F8+ remains future:** orchestration, LangGraph optional adapter, role freshness auditor, adapter loader/versioning, D-013 modernization.

## 11. Future horizon — application modernization
- D-013 is accepted and documented in [Framework Decisions](FRAMEWORK_DECISIONS.md#d-013---application-modernization-and-brownfield-adoption) and the [Modernization Concept](MODERNIZATION_CONCEPT.md).
- Status: documented future direction; implementation not started.
- Candidate capabilities include a semi-automatic modernization manifest, per-element update policies, and read-only freshness sensing from allowlisted sources with provenance.
- Produce a prioritized backlog using both risk-of-change (D-012) and risk-of-inaction.
- Bind safety-net and behavioral-equivalence validation to the applicable risk tier.
- Require incremental, reversible migration with mandatory decomposition of oversized proposals; forbid big-bang rewrites.
- Brownfield onboarding begins with read-only mapping and establishment of a safety net before changes.
- Portfolio/fleet freshness visibility remains an F8+ horizon item.
- D-013 does not activate F7-D, R6-PREFLIGHT, or any modernization implementation task.
- D-014/MCP remains a separate future decision and is not part of this horizon entry.

## 12. D-014 / MCP Interface Boundary — future interface horizon

**Decision status:** D-014 canonical documentation is complete.
**Implementation status:** NOT STARTED / DEFERRED.
**Position:** additive MCP server facade beside the existing CLI; not core, not agent runtime, not autonomous control plane.

### Required ordering

1. **D-014-DOCS** — canonicalize the interface boundary and reconcile progress.
2. **MCP-SEC-01** — create the threat model, abuse cases, source-scope policy, identity model, command allowlist and architectural boundary tests.
3. **MASTER-PLAN-REFRESH** — produce a new approved Master Development Plan that places F7-D1, modernization work and MCP phases in a single gated order.
4. **READ-ONLY PREFLIGHT** — verify the existing core service interfaces and implementation baseline before any MCP code.
5. **MCP-READ-01** — expose a minimal deterministic read-only facade.
6. **MCP-READ-02** — expose approved validation and explanation tools.
7. **MCP-SEC-02** — harden provenance, redaction, caller identity, source precedence and response contracts.
8. **MCP-PILOT-01** — integrate one approved MCP client and validate the boundary.
9. **MCP-PROPOSE-01** — optionally add a non-authoritative, rate-limited proposal store after separate approval.
10. **MCP-PROC-01** — move or harden the facade as a separate process if the initial implementation was in-process.

### Horizon gates

No MCP implementation may start until:

- D-014 is canonical;
- MCP-SEC-01 is accepted;
- the new Master Development Plan is accepted;
- the read-only implementation preflight passes;
- the exact tool list and result contract are approved;
- authoritative operations remain outside the MCP tool set;
- architecture-boundary tests are defined;
- secret, redaction and provenance policies are defined.

### Explicit exclusions

The horizon does not authorize:

- generic file reading;
- arbitrary command execution;
- autonomous approve/apply;
- deploy, commit, merge, rollback or phase transition tools;
- replacement of existing Git/filesystem adapters;
- LangGraph implementation;
- control-loop implementation;
- MCP proposal storage before MCP-PROPOSE-01;
- any implementation merely because D-014 documentation is merged.

Threat modelling and a new approved implementation plan are required before any MCP code.

## 13. Change log
| Version | Date | Notes |
|---|---|---|
| 0.3 | 2026-07-14 | Canonicalized D-014 MCP interface boundary as a future horizon; implementation not started. |
| 0.2 | 2026-07-14 | Canonicalized D-013 Application Modernization as accepted future architecture; implementation not started. |
| 0.1 | 2026-06-28 | Initial draft. Generic dev-control-OS direction; grounded in live inspection. |
