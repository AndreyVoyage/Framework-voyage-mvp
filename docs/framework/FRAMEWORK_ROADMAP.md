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

## 7. Change log
| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-28 | Initial draft. Generic dev-control-OS direction; grounded in live inspection. |
