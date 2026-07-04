# Framework Progress

> Living status of the Framework control-loop / trust-engine track. Target path in repo: `docs/framework/FRAMEWORK_PROGRESS.md`.
> Updated by every significant step (per `FRAMEWORK_CONTROL_RULES.md` rule 14).

## Snapshot (2026-07-04)
- Framework HEAD: `90b050e` (F5-A-B implementation committed; pending push to origin/main at `cf3ccbf`).
- Narrative HEAD: `29f9bdd3811ab016274efcec20334811dc94e8d0` on branch `main`; worktree clean (observed read-only during F5-A-B verification).
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
| F4 | Narrative read-only tools | DONE / CLOSED | F4-A and F4-B closed; F4-B-CLOSEOUT committed at `cf3ccbf`. |
| F4-B-CLOSEOUT | Narrative read-only tools closeout | DONE | Quality gate: ruff/format/mypy/pre-commit pass; full pytest 768 passed in 410.01s; real Narrative inventory dogfood re-verified on `main` at `29f9bdd`. Committed at `cf3ccbfde34de8673ad17e83c987e38a3cbe0e64`. |
| F5-A-A | Second adapter planning | DONE | Read-only planning completed with Verdict A. Recommended generic local Git repo adapter (`local`) for `voyage repo ... --adapter local`. |
| F5-A-B | Generic local repo adapter | DONE | Added `LocalRepoControlAdapter` (`voyage_framework/core/local_repo_adapter.py`), wired `--adapter local` into generic repo CLI, added unit and integration tests. Quality gates: ruff/format/mypy/pre-commit pass; full pytest 789 passed in 191.36s; Narrative local-adapter dogfood passed. Committed at `90b050e`. |
| F5 | Second adapter (multi-repo) | DONE / CLOSED | Generic local Git adapter (`local`) implemented and committed at `90b050e`; push pending. |
| F6 | Edit-safety & preview | PLANNED | edit-check, preview/render-check. |
| F7 | Guarded write | PLANNED | authorized text edits, gated. |
| F8+ | Agent runtime / scheduler | FAR / GATED | via `AdapterProtocol`. |

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
| F5-A-B | yes | yes (pre-commit + post-commit) | ok:true | `90b050e` | yes |
