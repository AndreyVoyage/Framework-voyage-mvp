# Framework Progress

> Living status of the Framework control-loop / trust-engine track. Target path in repo: `docs/framework/FRAMEWORK_PROGRESS.md`.
> Updated by every significant step (per `FRAMEWORK_CONTROL_RULES.md` rule 14).

## Snapshot (2026-06-29)
- Framework HEAD / origin/main: `cc23e5bfa73834724d49e6737ca218cbc32876f4` (baseline before F1-C-B2-B portability fix).
- Narrative HEAD / origin/main: `5571bd2505715b8f19b092ad1762b8d32449c360`; working tree dirty (handled in Narrative chat - D-007).
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
| F1-C-C-B1 | Low-risk git test setup optimization | IN PROGRESS | Replace local test `git fetch origin "+main:refs/remotes/origin/main"` with `git update-ref refs/remotes/origin/main HEAD`; reduce repeated `git config user.email`/`user.name` subprocesses via `git -c user.email=... -c user.name=... commit`. Shared fixture/copytree architecture deferred. Commit pending. |
| F1-C-C | Test fixture optimization | PLANNED | Shared session/module fixtures + copytree template repo, decided after F1-C-C-B1 timing results. |
| F2 | Generic repo-control adapter | DEFERRED | Until docs are written (D-005). |
| F3 | Trust hardening | PLANNED | `report-state`, `auto_commit` range check, spec-driven forbidden paths (D-006). |
| F4 | Narrative read-only tools | PLANNED | preflight, spec-update (via adapter). |
| F5 | Second adapter (multi-repo) | PLANNED | e.g. SkillTracer, read-only. |
| F6 | Edit-safety & preview | PLANNED | edit-check, preview/render-check. |
| F7 | Guarded write | PLANNED | authorized text edits, gated. |
| F8+ | Agent runtime / scheduler | FAR / GATED | via `AdapterProtocol`. |

## Known debts
- ~~Pre-existing ruff E402 in `tests/unit/test_auto_loop.py` (F1).~~ Addressed in F1-B.
- Narrative adapter tests ~470s (F1 perf).
- Flaky timestamp assertion in `tests/unit/test_task_engine.py` remains a known optional separate fix.
- Validator forbidden-paths hardcoded (`FORBIDDEN_BY_ROLE`) -> spec-driven in F3.
- Validator does not check changed-files vs a named `auto_commit` -> F3.

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
| F1-C-C-B1 | yes | yes (pre-commit) | pending | pending | pending |
