# Framework Progress

> Living status of the Framework control-loop / trust-engine track. Target path in repo: `docs/framework/FRAMEWORK_PROGRESS.md`.
> Updated by every significant step (per `FRAMEWORK_CONTROL_RULES.md` rule 14).

## Snapshot (2026-06-28)
- Framework HEAD / origin/main: `01b193546167ecd797e3df69916252e40d40c320` (F0-B closed: committed + pushed; previous baseline was `5757aa3`).
- Narrative HEAD / origin/main: `5571bd2505715b8f19b092ad1762b8d32449c360`; working tree dirty (handled in Narrative chat - D-007).
- Direction: generic dev-control-OS (D-001).

## Phase status
| Phase | Title | Status | Notes |
|---|---|---|---|
| F0-A | Trust-engine design audit | DONE (A) | `.git/config` not broken on live repo; risk is report trust. |
| F0-B | Implement `validate-report` | DONE | committed `01b1935`, pushed to origin/main; `_git_utils.py`, `report_validator.py` (BOM-tolerant), CLI; 18 validator tests incl. BOM test; auto-loop regression green; only pre-existing E402 + CRLF warning. |
| F0-D | Documentation + ADR | IN PROGRESS | This set (roadmap/control-rules/decisions/progress + ADR-0001) written + committed (62fa46a, F0-D-B); overview added (F0-D-C). |
| F0-E | Negative assert for validate-report | DONE | negative assert: synthetic 40-char + short hash reports -> validate-report ok:false as expected; closeout report ok:true. |
| F1 | Hygiene / performance | PLANNED | Fix E402; shared `conftest.py`; narrative suite target <120s. |
| F2 | Generic repo-control adapter | DEFERRED | Until docs are written (D-005). |
| F3 | Trust hardening | PLANNED | `report-state`, `auto_commit` range check, spec-driven forbidden paths (D-006). |
| F4 | Narrative read-only tools | PLANNED | preflight, spec-update (via adapter). |
| F5 | Second adapter (multi-repo) | PLANNED | e.g. SkillTracer, read-only. |
| F6 | Edit-safety & preview | PLANNED | edit-check, preview/render-check. |
| F7 | Guarded write | PLANNED | authorized text edits, gated. |
| F8+ | Agent runtime / scheduler | FAR / GATED | via `AdapterProtocol`. |

## Known debts
- Pre-existing ruff E402 in `tests/unit/test_auto_loop.py` (F1).
- Narrative adapter tests ~470s (F1 perf).
- Validator forbidden-paths hardcoded (`FORBIDDEN_BY_ROLE`) -> spec-driven in F3.
- Validator does not check changed-files vs a named `auto_commit` -> F3.

## Closeout ledger (each significant step appends a line)
| Step | Report (md) | JSON voyage.report.v1 | validate-report | Commit | Push |
|---|---|---|---|---|---|
| F0-B | yes | yes (pre-commit) | ok:true | `01b1935` | yes |
| F0-D | yes | yes (pre-commit) | ok:true | `62fa46a` | yes |
| F0-D-C | yes | yes (pre-commit) | ok:true | `c75ad79` | yes |
| F0-E | yes | ok:false (negative) + ok:true (closeout) | see note | pending | pending |
