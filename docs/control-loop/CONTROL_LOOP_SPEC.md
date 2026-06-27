# VOYAGE CONTROL LOOP — SPEC

> Specification for the local overnight control loop ("nightly automation").
> Status: **DRAFT / Phase 1 (preflight only)**.
> This document is a **stop-gate**, in the spirit of `docs/VOYAGE_V4_1_CONTRACT.md`.
> Phase 1 (`VOYAGE-CONTROL-LOOP-1`) ships **only** the read-only preflight and this spec.
> No checkpoint creation, no worktree creation, no runner, no rollback execution.

---

## 0. Scope of this document

This spec describes the *target* control loop and the *safety contract* it must obey.
It is written so later phases (CONTROL-LOOP-2..5) can be approved one at a time, each
against an explicit, frozen contract.

Phase map:

```text
VOYAGE-CONTROL-LOOP-1   read-only preflight + this spec + task.yaml        <- THIS PHASE
VOYAGE-CONTROL-LOOP-2   checkpoint/worktree dry-run or guarded creation
VOYAGE-CONTROL-LOOP-3   task queue + report parser
VOYAGE-CONTROL-LOOP-4   Claude Code guarded execution (no push/deploy)
VOYAGE-CONTROL-LOOP-5   rollback + morning summary
```

Nothing beyond CONTROL-LOOP-1 is authorized to run yet. The preflight script validates
*readiness* for these phases; it does not perform any of them.

---

## 1. Design principle

The control loop runs against an **isolated working copy**, never the primary repo and
never `main`. The invariant for every phase:

```text
main untouched . origin untouched . secrets untouched
```

If any phase cannot guarantee all three, it must abort before doing work.

```text
origin/main (stable, remote)
     |
main (stable, local)  --------------> NEVER mutated by the loop
     |
     +- checkpoint tag        voyage-checkpoint-YYYYMMDD-HHMM   (immutable marker)
     +- backup branch         checkpoint/YYYYMMDD-HHMM          (safety copy)
     +- nightly worktree      auto/nightly-YYYYMMDD             (the only mutable surface)
```

---

## 2. Checkpoint model

A checkpoint is created (in CONTROL-LOOP-2, **not now**) at three redundant levels before
any overnight work begins:

| Level | Artifact | Purpose |
|---|---|---|
| 1 — tag | `voyage-checkpoint-YYYYMMDD-HHMM` | Immutable return point for `reset --hard`. |
| 2 — branch | `checkpoint/YYYYMMDD-HHMM` | Named backup ref, survives tag pruning. |
| 3 — worktree | `auto/nightly-YYYYMMDD` | Separate physical checkout; the only place edits happen. |

Rules:

1. Checkpoint creation requires a **clean** preflight (`GO`) — see §8.
2. Checkpoint is created from `main` at the verified `origin/main`-synced HEAD only.
3. The checkpoint tag is never moved or deleted by automation.
4. Checkpoint creation is itself a mutation and is therefore **out of scope for Phase 1**.

---

## 3. Worktree / nightly branch model

The loop operates in a **sibling worktree**, physically separate from the primary repo:

```text
C:\DEV\FRAMEWORK\Framework-voyage-mvp              <- primary repo (read-only for the loop)
C:\DEV\FRAMEWORK\Framework-voyage-mvp-auto-night   <- nightly worktree (mutable)
```

Rules:

1. The nightly worktree checks out `auto/nightly-YYYYMMDD`, branched from the checkpoint.
2. All edits, commits, tests, and rollbacks happen **inside the worktree only**.
3. The primary repo is used read-only by the loop (status checks, no edits).
4. The worktree path must not pre-exist at preflight time (so creation later is safe).
5. The worktree is disposable: it may be removed wholesale (`git worktree remove`) in the
   morning without affecting `main`.

---

## 4. Allowed execution modes

Per task the loop may operate only in these modes:

| Mode | Meaning | Side effects |
|---|---|---|
| `READ_ONLY` | Inspect repo, read files, collect facts. | None. |
| `CODE_NO_COMMIT` | Generate/modify code in the worktree, leave uncommitted. | Working-tree changes in worktree only. |
| `TEST` | Run `ruff`, `mypy`, `pytest` (targeted then full). | Test artifacts only. |
| `DIFF_AUDIT` | Produce/inspect `git diff`, run `git diff --check`, forbidden-touch check. | Reports only. |

`COMMIT` is permitted **only** into the nightly branch inside the worktree, and only after
all gates pass (§7). It is not one of the four base modes and is gated separately.

---

## 5. Forbidden modes / actions (hard denylist)

The following must be **blocked unconditionally** in every phase of the loop:

```text
git push                   (any remote)
git merge into main
git reset / git clean       in the PRIMARY repo
deploy / release publish
docker compose up|down, docker build|run
ssh to any host
certbot / TLS / cert issuance
reading or writing .env (and any *.env, secrets, credentials)
modifying .voyage/ runtime files (events.db, events.jsonl, tasks.db)
deleting files outside the worktree allowlist
auto-accepting risky Claude permission prompts
network calls beyond `git ls-remote` (read) for the sync check
```

Violation of any denylist item is a fatal error: the loop stops and writes a failure report.

---

## 6. Rollback rules

Rollback applies **only inside the nightly worktree**, never the primary repo:

```powershell
# executed INSIDE the worktree only (CONTROL-LOOP-5, not now)
git -C <worktree> reset --hard voyage-checkpoint-YYYYMMDD-HHMM
# git clean is NOT run automatically — see note
```

Rules:

1. Rollback target is always the checkpoint tag created at the start of the run.
2. `git reset --hard` and `git clean` are **forbidden in the primary repo**, always.
3. `git clean -fd` is dangerous (removes untracked files) and is **not** run automatically
   in Phase 5's first version; untracked generated reports must be copied to
   `logs/nightly/` *before* any clean is ever considered.
4. Generated handoff reports are preserved outside the reset surface (copied to
   `logs/nightly/<date>/`) so rollback never destroys the audit trail.
5. After rollback the loop either proceeds to the next safe task or stops (stop
   conditions, §8).

---

## 7. Quality gates (per task)

Each task runs this gate sequence; a task only "passes" if every gate passes:

```text
1. ruff check .
2. ruff format --check voyage_framework tests
3. mypy voyage_framework
4. targeted pytest (task-scoped tests)
5. full pytest tests/
6. git diff --check
7. forbidden-touch check (no denylist paths in the diff)
```

- PASS -> commit the task's changes into the nightly branch.
- FAIL -> save failure report + isolated patch/diff, roll back the nightly branch to the
  last good checkpoint, then continue to the next safe task or stop.

---

## 8. Human approval gates & stop conditions

The loop is **opt-in and bounded**. Before it may ever create a checkpoint (Phase 2+):

Preconditions (checked read-only in Phase 1):

```text
- primary repo git status is clean
- local main is synced with origin/main
- no important untracked files / no .env at risk of loss
- worktree target path does not already exist
- denylist tooling is confirmed present so it can be blocked
```

Stop conditions (loop must halt and write a report):

```text
- preflight returns NO-GO
- any denylist action is attempted
- N consecutive task failures (default N=2)
- disk/time budget exceeded
- a gate harness itself errors (ruff/mypy/pytest cannot run)
- the working tree of the PRIMARY repo changes during the run
```

Human approval is required to: start the loop, merge any nightly branch into `main`, and
delete checkpoints. Automation never merges to `main`.

---

## 9. Morning report format

Written to `docs/handoff/nightly-YYYYMMDD.md` (and mirrored to `logs/nightly/`):

```text
Nightly run summary — YYYY-MM-DD
--------------------------------
checkpoint created:      YES (voyage-checkpoint-YYYYMMDD-HHMM)
branch/worktree created: YES (auto/nightly-YYYYMMDD)
tasks attempted:         8
tasks passed:            5
tasks failed:            2
tasks skipped:           1
rollback performed:      YES | NO
main untouched:          YES
origin untouched:        YES
secrets untouched:       YES
final recommendation:    review | merge | discard

Per-task:
  [PASS] VF-101  parser refactor          commit abc1234
  [FAIL] VF-102  engine edge case         report: docs/handoff/VF-102-fail.md
  [SKIP] VF-103  blocked by VF-102
```

The report is the canonical human-facing output. It is generated, not a source of truth
(consistent with the Voyage TASK.md / CONTEXT.json rule).

---

## 10. Phase 1 deliverables (this phase only)

```text
docs/control-loop/CONTROL_LOOP_SPEC.md      this document
tools/control_loop_preflight.ps1            read-only preflight (GO/NO-GO), no mutations
.voyage/tasks/control-loop-1.yaml           Voyage v4.1 task spec for this track
```

Explicitly NOT in Phase 1: checkpoint creation, worktree creation, the runner, Claude
invocation, rollback execution, any commit/push, any `.voyage` or source-code change.

---

## 11. Change log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-26 | Initial draft. Phase 1 = read-only preflight + spec + task.yaml. |
