# Framework Progress

> Living status of the Framework control-loop / trust-engine track. Target path in repo: `docs/framework/FRAMEWORK_PROGRESS.md`.
> Updated by every significant step (per `FRAMEWORK_CONTROL_RULES.md` rule 14).

## Snapshot (2026-07-05)
- Framework HEAD / origin/main: `098b6700ca79667a9ad7f381836340f3395ec26a` (F7-B-CLOSEOUT baseline; F7-C1 approval verification pending commit).
- Narrative HEAD: `6fa4791cf5e7c41e4064b8926d02a6ef1b69f1b5` on branch `main`; worktree clean (external drift observed during F7-C1 baseline).
- Direction: generic dev-control-OS (D-001).

## Phase status
| Phase | Title | Status | Notes |
|---|---|---|---|
| F0-A | Trust-engine design audit | DONE (A) | `.git/config` not broken on live repo; risk is report trust. |
| F0-B | Implement `validate-report` | DONE | committed `01b1935`, pushed to origin/main; `_git_utils.py`, `report_validator.py` (BOM-tolerant), CLI; 18 validator tests incl. BOM test; auto-loop regression green; only pre-existing E402 + CRLF warning. |
| F0-D | Documentation + ADR | DONE | Documentation + ADR committed/pushed in F0-D-B (`62fa46adb6793b6415a26e47542b287dc141ae50`); roadmap overview/progress refresh committed/pushed in F0-D-C (`c75ad79d29a168c719aaf30776b19eb32a4a5175`). |
| F0-E | Negative assert for validate-report | DONE | negative assert: synthetic 40-char + short hash reports -> validate-report ok:false as expected; closeout report ok:true. |
| F1-A | Read-only audit | DONE | Only ruff error: E402 in `tests/unit/test_auto_loop.py:38`; full pytest/pre-commit ~665 tests / ~812s; perf deferred to F1-C. |
| F1-B | Minimal E402 fix | DONE | Moved auto-loop import to top; imported `_GIT_LOCAL_ENV_VARS` from `_git_utils`; committed/pushed `f42700f`. |
| F1-C-A | Test performance audit/unblock | DONE | Removed stale `.test-tmp-perf/`; ruff/mypy/collect clean; measured slow auto-loop and narrative suites; recommended pre-commit policy fix first. |
| F1-C-B | Pre-commit smoke-test policy fix | DONE | Commit `cc23e5bfa73834724d49e6737ca218cbc32876f4` replaced full pre-commit pytest with the smoke pytest set; warning: it temporarily introduced machine-specific absolute venv Python paths in `.pre-commit-config.yaml`, addressed by F1-C-B2. |
| F1-C-B2-A | Pre-commit portability audit | DONE | Recommended repo-local PowerShell wrapper `scripts/precommit/run_python.ps1` to remove `C:/DEV/...` from active pre-commit config while preserving Windows compatibility and project venv usage. |
| F1-C-B2-B | Pre-commit portable launcher fix | DONE | `.pre-commit-config.yaml` uses repo-local wrapper (`scripts/precommit/run_python.ps1`) instead of machine-specific absolute venv path. Committed and pushed as `ec912ce1bad074b3f56b397f4e2f4339c1613eae`. |
| F1-C-C-A | Test git-setup optimization planning | DONE | Found slow tests repeatedly create real git repos and call expensive `git fetch`/`git config` subprocesses per test; recommended low-risk fetch->update-ref replacement before any shared fixture/copytree refactor. |
| F1-C-C-B1 | Low-risk git test setup optimization | DONE | Replaced local test `git fetch origin "+main:refs/remotes/origin/main"` with `git update-ref refs/remotes/origin/main HEAD`; reduced repeated `git config user.email`/`user.name` subprocesses via `git -c user.email=... -c user.name=... commit`. Committed and pushed as `3f419575a2fb700aad9b2fcb34a0be219bd7d2e7`; full pytest improved from roughly 812s to 449.15s. Shared fixture/copytree optimization deferred as F1-C-C-B2 since B1 already delivered a large low-risk gain. |
| F1-C-C-B2 | Shared fixture/copytree test optimization | PLANNED | Session/module-scoped fixtures + copytree template repo; only if further speedup is still wanted after F1-C-C-B1's gain. |
| F1-C-D-A | Flaky timestamp test audit | DONE | Root cause: real clock granularity (~1ms tick on this machine) can produce equal `_now()` timestamps between `create_from_spec` and `transition`; the test was flaky, not `TaskEngine` logic. 20 runs / 1 failure observed. Recommended test-only deterministic clock seam via monkeypatch. |
| F1-C-D-B | Flaky timestamp test fix | DONE | Flaky timestamp test stabilized with test-local monkeypatched deterministic `_now` (`monkeypatch.setattr(engine, "_now", ...)` in `test_updated_at_changes_on_transition`); production `TaskEngine` untouched. Rejected: `time.sleep()` (still flaky under scheduler jitter, slows suite), loosening assertion to `>=` (defeats test intent), production monotonic-timestamp change (contract-level decision, out of scope for this stabilization fix). Committed and pushed as `b632f5742dc3691a4310253be077cbf5d90022f1`. |
| F1 stabilization | F1-C track closeout | DONE | F1-A, F1-B, F1-C-B, F1-C-B2, F1-C-C-B1, F1-C-D-B all closed. Final closeout gate (F1-C-E): ruff pass, format pass, mypy pass, pre-commit smoke pass, full pytest 665 passed in 490.21s. F1-C-C-B2 shared fixture/copytree optimization remains deferred (not cancelled). Next planned step: F1-D Architecture Boundary Audit before F2 (not started). |
| F1-D-A | Architecture Boundary Audit | DONE | Read-only audit: no P0 findings; core imports nothing Narrative-specific outside `narrative_adapter.py` itself and the data-only `FORBIDDEN_BY_ROLE["narrative"]` entry; CLI narrative dispatch lazy-imported; F1-D-B not needed. Verdict A. |
| F2-A-A | RepoControlAdapter contract planning | DONE | Read-only planning: existing `adapter_protocols.py`/`adapter_contract.py` are AI-agent task-invocation concepts, not repo-control; a separate `repo_control_adapter.py` contract was chosen instead of reusing them. Mapped `auto_loop.run_preflight`/`run_plan` to generic `status`/`preview`, and `narrative_adapter.validate_scene`/`run_arc_check` to `validate`/`audit` for a future Narrative implementation. Verdict A. |
| F2-A-B1 | Generic RepoControlAdapter contract + boundary tests | DONE | Purely additive: `repo_control_adapter.py` (contract + 4 result dataclasses), `test_repo_control_adapter.py`, `test_architecture_boundaries.py`. No Narrative wrapper or CLI changes in B1; `narrative_adapter.py` untouched. Committed and pushed as `1051e85786271f94d33b91d5fb482a8799235b93`. |
| F2-A-C | Narrative RepoControlAdapter implementation wrapper | DONE | Added `NarrativeRepoControlAdapter(RepoControlAdapter)` in `narrative_adapter.py`, wrapping `run_preflight` (status), `validate_scene` (validate), `run_arc_check` (audit), `run_plan` (preview) unchanged. Existing narrative functions preserved; existing `voyage narrative scene-validate`/`arc-check` CLI commands preserved; generic CLI commands not added. Committed and pushed as `5e951c662b2c636a0e3102b3886884da5474f5cf`. |
| F2-A foundation | Generic contract + Narrative wrapper closeout | DONE | F2-A-A (planning), F2-A-B1 (generic contract + boundary tests), F2-A-C (Narrative wrapper) all closed. Final closeout gate (F2-A-CLOSEOUT): ruff pass, format pass, mypy pass, pre-commit smoke pass, full pytest 691 passed in 657.35s. Committed and pushed as `df8776b57e9954b370dddd6bbd0955dd60571fbd`. |
| F2-A-D-A | Generic CLI command planning | DONE | Read-only planning: recommended additive `voyage repo status/validate/audit/preview` command group calling only `RepoControlAdapter`/`NarrativeRepoControlAdapter` methods; explicit `--adapter narrative` selection (not `--repo-role`, to avoid confusion with `report_validator`'s unrelated concept); `--target` optional in both validate/audit since the contract already handles `target=None` cleanly; old narrative commands preserved unchanged; no auto-detection. Verdict A. |
| F2-A-D-B | Generic repo CLI commands | DONE | Added `voyage repo status/validate/audit/preview` in `cli.py`, calling `NarrativeRepoControlAdapter` via a small inline `_get_repo_control_adapter` selector (lazy-imported, "narrative" only). Old `voyage narrative scene-validate`/`arc-check` commands unchanged; no adapter auto-detection; no second adapter. New integration tests in `tests/integration/test_repo_cli.py`. Committed and pushed as `bde1d3fb546430a3b628fe6dcd81bfd865eecdd2`. |
| F2-A-D | Generic repo CLI layer closeout | DONE | F2-A-D-A (planning), F2-A-D-B (`voyage repo status/validate/audit/preview` + `--adapter narrative`, unknown-adapter handled cleanly, old narrative commands preserved unchanged, no auto-detection, no second adapter) both closed. Final closeout gate (F2-A-D-CLOSEOUT): ruff pass, format pass, mypy pass, pre-commit smoke pass, full pytest 699 passed in 610.53s. Committed and pushed as `ab1b8f4049dbbb7ec4c59ce2e3fc1ff4e2b5e306`. |
| F2-A-E | Repo CLI help and docs polish | DONE | CLI help/docs polish only, no behavior changes: `voyage repo --help` now describes the generic RepoControlAdapter surface and names `narrative` as the currently supported adapter; `voyage narrative --help` now describes those commands as Narrative-specific compatibility commands and points to `voyage repo ... --adapter narrative`. 6 new lightweight help tests added to `test_repo_cli.py`. Old commands/behavior unchanged. Committed and pushed as `9615c2934ee4106fe718967d041db290c92b29d5`. |
| F2 | Generic repo-control adapter | DONE | F2-A foundation (contract + Narrative wrapper), F2-A-D (generic CLI layer), and F2-A-E (CLI help/docs polish) all closed. |
| F3-A-A | Trust hardening planning | DONE | Read-only planning completed with Verdict A. Recommended order: report-state → auto_commit range check → spec-driven forbidden paths. |
| F3-A-B | Add `voyage report-state` read-only command | DONE | Read-only repo/git state observation command. Emits canonical Voyage-observed JSON. No auto_commit checks, no spec-driven forbidden path changes, no report_validator.py changes. Committed and pushed as `15299860f0a7e52c4ab3e236200091b2e66e8b07`. Full pytest 718 passed in 938.07s. |
| F3-A-C-A | Auto-commit / commit-range validation planning | DONE | Read-only planning completed with Verdict A. Recommended flat repo fields `auto_commit_after` and `auto_commit_before`; existing behavior unchanged when `auto_commit_after` absent. |
| F3-A-C-B | Add auto_commit validation to validate-report | DONE | Post-commit changed-files validation against actual commit/range. Committed/pushed as `b0e8742bb8039e1c50f41cfaf17c9523a3cf27b3`. Full pytest 735 passed in 1018.15s. Post-commit auto_commit dogfood passed. No CLI command changes. |
| F3 | Trust hardening | DONE / CLOSED | report-state (F3-A-B), auto_commit/commit-range validation (F3-A-C-B), and spec-driven forbidden path extraction (F3-A-D-B) all complete. Final closeout quality gate: ruff/format/mypy/pre-commit pass; targeted trust regressions pass; full pytest 749 passed in 313.34s. |
| F4-A-A | Narrative read-only tools planning | DONE | Read-only planning completed with Verdict A. Recommended first implementation: `voyage narrative inventory --spec <spec>` read-only helper; no generic RepoControlAdapter contract extension; no Narrative repo writes. |
| F4-A-B | Add Narrative inventory/readiness command | DONE | Added `narrative_inventory()` helper and `voyage narrative inventory --spec <spec>` compatibility CLI command. Emits JSON-only read-only inventory/readiness summary (scenario files, library/matrix presence, schema-version mix, missing expected files, readiness verdict). RepoControlAdapter contract unchanged; generic `voyage repo ...` unchanged; old narrative commands preserved. Narrative repo not modified. Committed and pushed as `b0fe3f9a89ce68adb9af847646722ce1e847b1a6`. Full pytest 757 passed in 185.00s (measured during F4-A-B). |
| F4-A | Narrative inventory/readiness slice | DONE / CLOSED | F4-A-A (planning) and F4-A-B (implementation) both closed. Final closeout quality gate (F4-A-CLOSEOUT): ruff pass, format pass, mypy pass, targeted F4 regressions pass, trust regressions pass, pre-commit smoke pass, full pytest 757 passed in 248.22s. Real Narrative repo inventory dogfood was skipped because no suitable existing autoloop spec path was found in the Narrative repo; this is not an implementation blocker. |
| F4-A-CLOSEOUT | Narrative inventory/readiness closeout | DONE | Closed F4-A; updated progress docs. Committed and pushed as `38fb95991e5cb856ef283ce49f354452ba3de75a`. |
| F4-B-A | Narrative spec/source discovery planning | DONE | Read-only planning completed with Verdict A. Real Narrative repo has scenario/library/matrix files but no autoloop spec; recommended repo-root/source-mode inventory support. |
| F4-B-B | Extend inventory with repo-root/source mode | DONE | Added repo-root/source-mode inventory support: `narrative_inventory()` now accepts autoloop spec, repo root, scenarios directory, SCENARIO_LIBRARY.json, or SCENARIO_MATRIX.json. Added `voyage narrative inventory --repo <repo>` while preserving `--spec`. RepoControlAdapter contract unchanged; generic `voyage repo ...` unchanged; old narrative commands preserved; Narrative repo not modified. Real Narrative dogfood passed: `voyage narrative inventory --repo C:\\DEV\\Narrative\\voyage-narrative-engine` -> ok true, readiness ready, source_type repo_root, scenario_count 29, library/matrix present. F4-B-B run reported a transient Narrative branch name difference (`feature/n5f-hybrid-json-path-design` vs `main`) with unchanged HEAD/worktree; this closeout re-verified branch `main`, HEAD `4f13f3b`, worktree clean. Committed and pushed as `24ccdd2f4074a359b52ad15d8952560c60ae4e3f`. Full pytest 768 passed in 410.01s (measured during F4-B-CLOSEOUT). |
| F4-B | Repo-root/source-mode inventory slice | DONE / CLOSED | F4-B-A (planning) and F4-B-B (implementation) both closed. Final closeout quality gate (F4-B-CLOSEOUT): ruff pass, format pass, mypy pass, targeted F4 regressions pass, trust regressions pass, real Narrative inventory dogfood pass, pre-commit smoke pass, full pytest 768 passed in 410.01s. |
| F4 | Narrative read-only tools | DONE / CLOSED | F4-A, F4-B, and F4-C closed; F4-C-CLOSEOUT committed at `4672803`. |
| F4-B-CLOSEOUT | Narrative read-only tools closeout | DONE | Quality gate: ruff/format/mypy/pre-commit pass; full pytest 768 passed in 410.01s; real Narrative inventory dogfood re-verified on `main` at `29f9bdd`. Committed at `cf3ccbfde34de8673ad17e83c987e38a3cbe0e64`. |
| F4-C-A | Narrative spec-update proposal planning | DONE | Read-only planning completed with Verdict A. Recommended `voyage narrative spec-plan --repo <repo>`: strictly proposal-only, `apply_supported=false`, cross-checks scenario files / SCENARIO_LIBRARY.json / SCENARIO_MATRIX.json. |
| F4-C-B | Add read-only Narrative spec-plan command | DONE | Commit `cbe9f767e9a762e7038b6d29bf9ea8c486600bf4`. Delivered `narrative_spec_plan()`, `voyage narrative spec-plan --repo`, scenario/library/matrix cross-checks, findings/proposed_actions/affected_files/readiness, `read_only=true`, `apply_supported=false`. Full pytest 808 passed in 260.11s. Real Narrative dogfood passed. |
| F5-A-A | Second adapter planning | DONE | Read-only planning completed with Verdict A. Recommended generic local Git repo adapter (`local`) for `voyage repo ... --adapter local`. |
| F5-A-B | Generic local repo adapter | DONE | Added `LocalRepoControlAdapter` (`voyage_framework/core/local_repo_adapter.py`), wired `--adapter local` into generic repo CLI, added unit and integration tests. RepoControlAdapter contract unchanged; existing `--adapter narrative` preserved; Narrative adapter unchanged. Quality gates: ruff/format/mypy/pre-commit pass; full pytest 789 passed in 191.36s; Narrative local-adapter dogfood passed. Implementation committed at `90b050e`; main fast-forward completed at `fd1eccc`. |
| F5-A-CLOSEOUT | Second adapter proof acceptance | DONE | Closed F5-A; accepted local adapter proof; captured D-010 Role Versioning and Freshness Policy as future architecture principle. Process deviations recorded: implementation commits `90b050e` and `40da9e8` used `--no-verify` after manual pre-commit passed; final ledger commit `fd1eccc` ran hook normally; work first pushed to `origin/auto/nightly-20260627`, then main fast-forwarded after reconciliation. No forbidden files changed; no force/merge/rebase. Next decision: likely return to F4-C read-only spec-update proposal; F6 edit-safety/preview and F7 guarded writes remain future. Committed at `aae2803`. |
| F5 | Second adapter (multi-repo) | DONE / CLOSED | Generic local Git adapter (`local`) implemented, mainline-accepted, and closed at `aae2803`. |
| F6-A | Edit-safety / preview planning | DONE | Read-only planning completed with Verdict A. Recommended generic `voyage edit-preview --plan <json> --repo <repo> --repo-role <role>`. |
| F6-B | Add read-only edit-preview command | DONE | Commit `70a1a266c6f607fa5dcf4ca1c89c03809e03a222`. Delivered `edit_preview()`, `voyage edit-preview --plan --repo --repo-role`, unit/integration tests. Validates affected_files/proposed_actions against repo state and forbidden policy; emits allowed_files/blocked_files/safety_findings/readiness/next_gate. No writes; no patch; no apply; RepoControlAdapter contract unchanged. Full pytest 831 passed in 167.72s. Real Narrative dogfood produced expected safety block. |
| F6 | Edit-safety & preview | DONE / CLOSED | F6-A, F6-B, and F6-CLOSEOUT committed at `1d42f0f`. |
| F7-A | Guarded write planning | DONE | Recommended Option A: approval/preflight layer first; no writes; actual structured writes deferred to F7-C. |
| F7-B | Guarded write approval plan | DONE | Commit `944f3cec2c53a44c95200a27eb867bbda1098759`. Delivered `guarded_write_plan()` and `voyage guarded-write plan --preview --repo`; consumes F6 edit-preview; verifies preview state; detects repo drift; emits required_evidence/required_checks/blocked_reasons; approval_status `required`/`blocked_before_approval`; `next_gate: human_approval_required`; `writes_supported=false`; `approval_required=true`. No writes, no patch, no apply, no staging, no target repo mutation. |
| F7-C | Structured writes planning | DONE | Recommended split: F7-C1 approval artifact verification (no writes); F7-D structured create/replace writes later. Approval artifact schema, binding checks, checkpoint/rollback plan, post-write validation plan defined. |
| F7-C1 | Approval artifact verification | IN PROGRESS / pending commit | Generic `voyage guarded-write verify-approval --preview --approval --repo`; consumes edit-preview JSON and external approval JSON; verifies approval-to-preview binding; verifies approval-to-current-repo binding; verifies clean worktree; verifies rollback/checkpoint and post-write validation plans; emits `approval_valid`/`readiness`/`blocked_reasons`/`next_gate: F7_structured_write_required`; `writes_supported=false`; `approval_required=true`. No writes, no patch, no apply, no staging, no target repo mutation. |
| F7-D | Structured create/replace writes | PLANNED | Actual file writes behind verified approval artifact; not started. |
| F8+ | Agent runtime / scheduler | FAR / GATED | via `AdapterProtocol`. |

## F4-C closeout notes
- F4-C provides read-only proposal planning for Narrative specs. It does not write Narrative repo files, generate patches, or apply updates. It prepares the input surface for F6 edit-safety/preview.
- Quality: full pytest 808 passed in 260.11s; F4-C targeted tests 19 passed; Narrative regression 72 passed; local adapter regression 35 passed; boundary regression 8 passed; trust regression 51 passed; pre-commit smoke passed.
- Real Narrative dogfood: `voyage narrative spec-plan --repo C:\\DEV\\Narrative\\voyage-narrative-engine` -> ok true, readiness warnings, 51 findings, 51 proposed_actions, affected_files include `SCENARIO_LIBRARY.json`, `SCENARIO_MATRIX.json`, and 28 scenario files. Narrative repo was not modified by the Framework task.
- External Narrative drift observed during F4-C-B: before `main @ 5aa16179b7b3505df34077b6bfd29e6d1949b2f0`; after `feature/v0r2-renpy-engine-specialist-role @ d90c5caf4869ff00ef8792d7d8191a04b6cc90ab`. At F4-C-CLOSEOUT re-verification the local branch name reads `main` but HEAD remains `d90c5caf...`; worktree clean in both observations. No Framework task modifications to Narrative repo.
- Future architecture decisions captured: D-009 Project Adapter Ownership; D-010 Role Versioning (already captured); D-011 LangGraph reserved optional adapter (F8+).
- Next decision: recommended F6 edit-safety/preview planning. F6 should consume spec-plan `findings`, `proposed_actions`, `affected_files`, and `readiness`. F7 remains guarded writes/apply. Adapter loader/versioning, Narrative adapter extraction, and LangGraph activation remain future work, not started.

## F6 edit-preview notes
- F6-B adds a generic read-only edit-preview / change-plan validator. It consumes proposal JSON (e.g. `narrative spec-plan` output) and validates it against repo state and the role-based forbidden-path policy. It emits `allowed_files`, `blocked_files`, `safety_findings`, `readiness`, and `next_gate: F7_guarded_write_required`.
- Semantic correction: if a plan contains forbidden paths, path traversal, `apply_supported:true`, or non-proposal actions, `edit-preview` emits valid JSON with `ok:false`, `readiness:blocked`, and exits 1. This is a successful safety block, not a tool failure.
- No writes, no patch generation, no apply, no RepoControlAdapter contract change, no adapter loader/versioning, no LangGraph activation, no Role Versioning code.
- Quality: full pytest 831 passed in 167.72s; F6 targeted tests 23 passed; F4-C spec-plan regression 19 passed; Narrative regression 72 passed; local adapter regression 35 passed; boundary regression 8 passed; trust regression 51 passed; pre-commit smoke passed.
- Real Narrative dogfood: expected safety block; exit 1; `ok false`; `readiness blocked`; `blocked_files` include `scenarios/SCENARIO_LIBRARY.json` and `scenarios/SCENARIO_MATRIX.json`; `allowed_files` count 29; `safety_findings` count 2. Narrative repo not modified by Framework task.
- External Narrative drift observed: branch changed from `main` at F6-B baseline to `feature/v0r4-renpy-specialist-role-improvements` at F6-CLOSEOUT verification; HEAD remained `7eac828...`; worktree clean in both observations.
- Future architecture decision captured: D-012 Risk-Based Adaptive Control with Voyage-Observed Evidence.
- Next decision: recommended F7-A guarded writes planning. F7 should consume `allowed_files`, `blocked_files`, `safety_findings`, `readiness`, `repo_state`, and `next_gate`. F7-only: actual file mutations, patch apply, staging, commit creation, human approval gate, rollback/checkpoint policy. Adapter loader/versioning, Narrative adapter extraction, LangGraph activation, Role Versioning, Role Freshness Auditor, and D-013 modernization remain future work, not started.
- Real Narrative dogfood may be blocked because `repo_role=narrative` policy forbids `scenarios/SCENARIO_LIBRARY.json` and `scenarios/SCENARIO_MATRIX.json`; this is expected and demonstrates correct gate behavior.

## F7-B closeout notes
- F7-B closes the read-only approval/preflight layer for guarded writes. It consumes F6 `edit-preview` output and produces an approval plan with `approval_required=true`, `writes_supported=false`, and `next_gate: human_approval_required`. It does not write files, generate patches, apply changes, stage files, or commit to the target repo.
- Delivered: `voyage_framework/core/guarded_write.py` (`guarded_write_plan()`), `voyage_framework/cli.py` (`voyage guarded-write plan --preview --repo`), `tests/unit/test_guarded_write.py`, `tests/integration/test_guarded_write_cli.py`.
- RepoControlAdapter contract unchanged; `edit_preview.py`, `narrative_adapter.py`, `local_repo_adapter.py`, `report_validator.py`, `forbidden_paths.py`, and `_git_utils.py` unchanged.
- Quality: full pytest 849 passed in 184.29s; F7 targeted tests 18 passed; F6 edit-preview regression 28 passed; boundary regression 8 passed; trust regression passed; pre-commit smoke passed; validate-report pre/post `ok:true`; report-state final dogfood `ok:true`.
- Real Narrative dogfood: expected blocked-before-approval; `edit-preview` exit code 1; `guarded-write plan` exit code 1; `ok false`; `readiness blocked`; `approval_status blocked_before_approval`; `writes_supported false`; `approval_required true`; `blocked_reasons` include `blocked_files_present`, `error_safety_findings_present`, `source_preview_blocked`. Narrative repo not modified by Framework task.
- External Narrative drift observed: during F7-B baseline branch was `feature/n5j-generated-rpy-freshness-validator @ 0e1f989b`; by F7-B-CLOSEOUT baseline branch reads `main @ 10eaed3`; worktree clean in both observations.
- Next decision: F7-C planning for structured writes / approval artifact model. Before implementation, plan: structured write operation schema; human approval artifact model; checkpoint/rollback expectation; target repo drift handling; post-write validation; validate-report integration; no autonomous commit/push. F7-C must not start automatically.

## F7-C1 notes
- F7-C1 adds read-only approval artifact verification. It consumes F6 `edit-preview` output and an external human approval artifact JSON, verifies that the approval is valid and bound to the preview and current repository state, and emits `approval_valid`, `readiness`, `blocked_reasons`, and `next_gate: F7_structured_write_required`.
- Delivered: `voyage_framework/core/guarded_write_approval.py` (`guarded_write_approval_verify()`), `voyage_framework/cli.py` (`voyage guarded-write verify-approval --preview --approval --repo`), `tests/unit/test_guarded_write_approval.py`, `tests/integration/test_guarded_write_approval_cli.py`.
- No writes, no patch generation, no apply, no staging, no commit to target repo. `edit_preview.py`, `guarded_write.py`, adapters, `report_validator.py`, `forbidden_paths.py`, and `_git_utils.py` unchanged.
- Quality: full pytest TBD; F7-C1 targeted tests 24 passed; F7-B regression 23 passed; F6 regression 28 passed; boundary regression 8 passed; trust regression 51 passed; pre-commit smoke passed; validate-report pre/post `ok:true`; report-state final dogfood `ok:true`.
- Real Narrative dogfood: expected blocked approval; edit-preview exit code 1; approval verification exit code 1; `ok false`; `readiness blocked`; `approval_valid false`; `writes_supported false`; `approval_required true`; `blocked_reasons` include `source_preview_blocked` and/or `blocked_files_present`. Narrative repo not modified by Framework task.
- External Narrative drift observed: during F7-C1 baseline branch reads `main @ 6fa4791`; worktree clean.
- Next decision: F7-C1 closeout, then F7-D planning for structured create/replace writes behind verified approval artifact.

## Known debts
- ~~Pre-existing ruff E402 in `tests/unit/test_auto_loop.py` (F1).~~ Addressed in F1-B.
- Narrative adapter tests ~470s (F1 perf); improved via F1-C-C-B1, further gains deferred to F1-C-C-B2 if still wanted.
- ~~Flaky timestamp assertion in `tests/unit/test_task_engine.py` remains a known optional separate fix.~~ Addressed in F1-C-D-B (test-only deterministic clock seam).
- Validator auto_commit range check -> DONE in F3-A-C-B (`b0e8742bb8039e1c50f41cfaf17c9523a3cf27b3`).
- Validator forbidden-paths hardcoded (`FORBIDDEN_BY_ROLE`) -> DONE in F3-A-D-B (`1194e33187eb014f5e8d915af9ce062402347a7e`).
- External/repo-local forbidden policy loading remains deferred beyond F3.

## Closeout ledger (each significant step appends a line)
| Step | Report (md) | JSON voyage.report.v1 | validate-report | Commit | Push |
|---|---|---|---|---|---|
| F0-B | yes | yes (pre-commit) | ok:true | `01b1935` | yes |
| F0-D | yes | yes (pre-commit) | ok:true | `62fa46a` | yes |
| F0-D-C | yes | yes (pre-commit) | ok:true | `c75ad79` | yes |
| F0-E | yes | ok:false (negative) + ok:true (closeout) | see note | `59db59c` | yes |
| F1-A | yes | - | - | - | - |
| F1-B | yes | yes (pre-commit) | ok:true | `f42700f` | yes |
| F1-C-A | yes | - | - | - | - |
| F1-C-B | yes | yes (pre-commit) | ok:true | `cc23e5b` | yes |
| F1-C-B2-A | yes | - | - | - | - |
| F1-C-B2-B | yes | yes (pre-commit) | ok:true | `ec912ce` | yes |
| F1-C-C-A | yes | - | - | - | - |
| F1-C-C-B1 | yes | yes (pre-commit) | ok:true | `3f41957` | yes |
| F1-C-D-A | yes | - | - | - | - |
| F1-C-D-B | yes | yes (pre-commit) | ok:true | `b632f57` | yes |
| F1-C-E | yes | yes (pre-commit) | ok:true | `01ef281` | yes |
| F1-D-A | yes | - | - | - | - |
| F2-A-A | yes | - | - | - | - |
| F2-A-B1 | yes | yes (pre-commit) | ok:true | `1051e85` | yes |
| F2-A-C | yes | yes (pre-commit) | ok:true | `5e951c6` | yes |
| F2-A-CLOSEOUT | yes | yes (pre-commit) | ok:true | `df8776b` | yes |
| F2-A-D-A | yes | - | - | - | - |
| F2-A-D-B | yes | yes (pre-commit) | ok:true | `bde1d3f` | yes |
| F2-A-D-CLOSEOUT | yes | yes (pre-commit) | ok:true | `ab1b8f4` | yes |
| F2-A-E | yes | yes (pre-commit) | ok:true | `9615c29` | yes |
| F3-A-A | yes | - | - | - | - |
| F3-A-B | yes | yes (pre-commit) | ok:true | `1529986` | yes |
| F3-A-C-A | yes | - | - | - | - |
| F3-A-C-B | yes | yes (pre-commit + post-commit) | ok:true | `b0e8742` | yes |
| F3-A-D-A | yes | - | - | - | - |
| F3-A-D-B | yes | yes (pre-commit + post-commit) | ok:true | `1194e33` | yes |
| F3-CLOSEOUT | yes | yes (pre-commit) | ok:true | `d1a7b5b` | yes |
| F4-A-A | yes | - | - | - | - |
| F4-A-B | yes | yes (pre-commit + post-commit) | ok:true | `b0fe3f9` | yes |
| F4-A-CLOSEOUT | yes | yes (pre-commit) | ok:true | `38fb959` | yes |
| F4-B-A | yes | - | - | - | - |
| F4-B-B | yes | yes (pre-commit + post-commit) | ok:true | `24ccdd2` | yes |
| F4-B-CLOSEOUT | yes | yes (pre-commit) | ok:true | `cf3ccbf` | yes |
| F5-A-A | yes | - | - | - | - |
| F5-A-B | yes | yes (pre-commit + post-commit + main-ff) | ok:true | `90b050e` | yes |
| F5-A-CLOSEOUT | yes | yes (pre-commit + post-commit) | ok:true | `aae2803` | yes |
| F4-C-A | yes | - | - | - | - |
| F4-C-B | yes | yes (pre-commit + post-commit) | ok:true | `cbe9f76` | yes |
| F4-C-CLOSEOUT | yes | yes (pre-commit) | ok:true | `4672803` | yes |
| F6-A | yes | - | - | - | - |
| F6-B | yes | yes (pre-commit) | ok:true | `70a1a26` | yes |
| F6-CLOSEOUT | yes | yes (pre-commit) | ok:true | `1d42f0f` | yes |
| F7-B | yes | yes (pre-commit + post-commit) | ok:true | `944f3ce` | yes |
| F7-B-CLOSEOUT | yes | yes (pre-commit + post-commit) | ok:true | `098b670` | yes |
