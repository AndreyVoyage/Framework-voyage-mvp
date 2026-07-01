# Framework Progress

> Living status of the Framework control-loop / trust-engine track. Target path in repo: `docs/framework/FRAMEWORK_PROGRESS.md`.
> Updated by every significant step (per `FRAMEWORK_CONTROL_RULES.md` rule 14).

## Snapshot (2026-06-29)
- Framework HEAD / origin/main: `f42700fc347353624543133a1fbe23d987c6e83e` (F1-B E402 fix closed; F1-C-A performance audit complete).
- Narrative HEAD / origin/main: `5571bd2505715b8f19b092ad1762b8d32449c360`; working tree dirty (handled in Narrative chat - D-007).
- Direction: generic dev-control-OS (D-001).

## Phase status
| Phase | Title | Status | Notes |
|---|---|---|---|
| F0-A | Trust-engine design audit | DONE (A) | `.git/config` not broken on live repo; risk is report trust. |
| F0-B | Implement `validate-report` | DONE | committed `01b1935`, pushed to origin/main; `_git_utils.py`, `report_validator.py` (BOM-tolerant), CLI; 18 validator tests incl. BOM test; auto-loop regression green; only pre-existing E402 + CRLF warning. |
| F0-D | Documentation + ADR | IN PROGRESS | This set (roadmap/control-rules/decisions/progress + ADR-0001) written + committed (62fa46a, F0-D-B); overview added (F0-D-C). |
| F0-E | Negative assert for validate-report | DONE | negative assert: synthetic 40-char + short hash reports -> validate-report ok:false as expected; closeout report ok:true. |
| F1-A | Read-only audit | DONE | Only ruff error: E402 in `tests/unit/test_auto_loop.py:38`; full pytest/pre-commit ~665 tests / ~812s; perf deferred to F1-C. |
| F1-B | Minimal E402 fix | DONE | Moved auto-loop import to top; imported `_GIT_LOCAL_ENV_VARS` from `_git_utils`; committed/pushed `f42700f`. |
| F1-C-A | Test performance audit/unblock | DONE | Removed stale `.test-tmp-perf/`; ruff/mypy/collect clean; measured slow auto-loop and narrative suites; recommended pre-commit policy fix first. |
| F1-C-B | Pre-commit smoke-test policy fix | IN PROGRESS | Pre-commit now runs the smoke pytest set; full `python -m pytest tests/ -q` remains an explicit closeout/CI-style gate. Expected pre-commit cost drops from ~13.5 min to likely under 2 min. Commit pending. |
| F1-C-C | Test fixture optimization | PLANNED | Cache/scope real git repo setup; target <120s narrative suite. |
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
| F1-C-B | yes | yes (pre-commit) | pending | pending | pending |
