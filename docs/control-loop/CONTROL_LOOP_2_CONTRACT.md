> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 2 — CONTRACT

> Specification for CONTROL-LOOP-2: guarded checkpoint/worktree creation.
> Status: **DRAFT / Phase 2**.
> Predecessor: `docs/control-loop/CONTROL_LOOP_SPEC.md` (master safety contract).
> This document is a **stop-gate** for CONTROL-LOOP-2 only.

---

## 0. Purpose

CONTROL-LOOP-2 ships the one capability that CONTROL-LOOP-1 explicitly deferred:
**creating a three-level checkpoint** (immutable tag + named backup branch + sibling
worktree) so overnight automation has a physically isolated surface to work in.

The deliverable is `tools/control_loop_checkpoint.ps1`, a script that:

- **by default** runs in dry-run mode — validates all preconditions and prints the
  exact commands it would execute, but performs zero mutations;
- **only mutates** when the operator explicitly passes `-Execute`.

Nothing beyond checkpoint/worktree creation is in scope for this phase. There is
no task queue, no runner, no Claude invocation, and no task execution.

---

## 1. Dry-run-first model

The `-Execute` gate enforces a mandatory human review step:

```
operator runs dry-run (default)
    |
    +---> preconditions evaluated (read-only)
    |         * preflight re-run as hard gate (exit must be 0)
    |         * branch, HEAD/origin sync, clean tree verified
    |         * tag/branch/worktree namespace verified free
    |
    +---> execution plan printed (exact commands, no mutations)
    |
    +---> operator reads output, confirms it is safe
    |
    operator re-runs with -Execute (explicit human decision)
    |
    +---> preconditions re-evaluated
    |
    +---> artifacts created in sequence (tag → branch → worktree)
    |
    +---> each artifact verified after creation
    |
    +---> partial-state report on any failure
```

The dry-run path exits 0 if all preconditions pass, 1 if any precondition fails.
The live path exits 0 on full success, 1 on any creation failure.

---

## 2. Checkpoint model

Identical to `CONTROL_LOOP_SPEC.md §2`; reproduced here for completeness.

| Level | Artifact | Purpose |
|---|---|---|
| 1 — tag | `voyage-checkpoint-YYYYMMDD-HHmm` | Immutable return point for `reset --hard`. |
| 2 — branch | `checkpoint/YYYYMMDD-HHmm` | Named backup ref; survives tag pruning. |
| 3 — worktree | `auto/nightly-YYYYMMDD` | Separate physical checkout; only mutable surface. |

Naming convention:

```
Timestamp:         YYYYMMDD-HHmm   (e.g. 20260627-2130)
Checkpoint tag:    voyage-checkpoint-20260627-2130
Checkpoint branch: checkpoint/20260627-2130
Nightly branch:    auto/nightly-20260627   (date only; one branch per calendar day)
Worktree path:     <repo-parent>/<repo-leaf>-auto-night
```

The timestamp defaults to `Get-Date -Format "yyyyMMdd-HHmm"` at script start and
can be overridden with `-Timestamp` to reproduce a prior naming scheme in tests.

Rules:

1. The checkpoint tag is **never** moved or deleted by automation.
2. The backup branch is **never** merged into `main` by automation.
3. The nightly worktree is disposable: `git worktree remove` in the morning.
4. All three are created from the verified `main` HEAD only.
5. Creation requires a fresh GO from the Phase 1 preflight.

---

## 3. Worktree model

Identical to `CONTROL_LOOP_SPEC.md §3`; reproduced here for completeness.

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp              <- primary repo (read-only for the loop)
C:\DEV\FRAMEWORK\Framework-voyage-mvp-auto-night   <- nightly worktree (mutable)
```

Rules:

1. The nightly worktree checks out `auto/nightly-YYYYMMDD`, branched from the checkpoint.
2. All edits, commits, tests, and rollbacks happen inside the worktree only.
3. The primary repo is used read-only by the loop (status checks, no edits).
4. The worktree path must not pre-exist at creation time.
5. The worktree is disposable: remove with `git worktree remove` without affecting `main`.

---

## 4. Explicit `-Execute` gate

The `-Execute` switch is the **sole authorization mechanism** for live execution.
It is designed to be hard to activate by accident:

- The default (no `-Execute`) is always safe to run.
- The operator must read the dry-run output before deciding to pass `-Execute`.
- The script re-validates all preconditions at the start of live execution.
- There is no environment variable, config file, or flag alias that bypasses it.

This phase does NOT implement a scheduled runner, daemon, or CI trigger. The
script is always operator-invoked.

---

## 5. No task execution

CONTROL-LOOP-2 creates the isolated surface; it does not use it.

Explicitly out of scope:

- Task queue (CONTROL-LOOP-3)
- Claude Code invocation (CONTROL-LOOP-4)
- Rollback execution (CONTROL-LOOP-5)
- Morning report generation (CONTROL-LOOP-5)
- Any changes to `voyage_framework/` source
- Any changes to `.voyage/` runtime files

---

## 6. No Claude bridge

CONTROL-LOOP-2 does not invoke Claude in any form. The Claude CLI is checked for
presence (by the Phase 1 preflight), but it is not called and no permission prompts
are issued or auto-accepted.

Claude invocation is deferred to CONTROL-LOOP-4, which will require its own
contract and explicit human authorization.

---

## 7. Rollback boundaries

In CONTROL-LOOP-2:

- Rollback is **not implemented** (deferred to CONTROL-LOOP-5).
- The script reports partial state clearly if any step fails.
- It does NOT automatically delete a tag or branch that was created before a later
  step failed — those artifacts are left for human inspection.
- The primary repo working tree is **never** reset or cleaned by this script.

Partial-state reporting format (on failure):

```
[FAIL] Step N failed.
  Partial state:
    Tag 'voyage-checkpoint-...' EXISTS (do not delete automatically).
    Branch 'checkpoint/...' EXISTS.
    Worktree may be partial — inspect: git worktree list
```

---

## 8. Forbidden actions

All denylist items from `CONTROL_LOOP_SPEC.md §5` apply. CONTROL-LOOP-2 additionally
enforces:

```text
git push                       (the checkpoint tag stays local until human decision)
git merge into main            (nightly branch is never merged automatically)
git reset in the PRIMARY repo  (only allowed inside worktree, deferred to CL-5)
git clean in the PRIMARY repo  (same)
deploy / release publish
docker compose up|down, docker build|run
ssh to any host
certbot / TLS / cert issuance
reading or writing .env
modifying .voyage/ runtime files (events.db, events.jsonl, tasks.db)
launching Claude
running tasks or task queues
auto-accepting permission prompts
```

---

## 9. Human approval gates

The following require explicit human action and are never automated:

| Gate | When |
|---|---|
| Dry-run review | Before passing `-Execute` |
| Live run authorization | Passing `-Execute` explicitly |
| Merging nightly branch into `main` | Morning review |
| Deleting checkpoint tags | Morning cleanup |
| Deleting the worktree | Morning cleanup |

The script never initiates any of the "morning" actions. They are left to the
operator after reviewing the nightly run results.

---

## 10. Acceptance criteria

CONTROL-LOOP-2 is complete when:

1. `tools/control_loop_checkpoint.ps1` exists and is PS 5.1-compatible.
2. Default (no `-Execute`) mode:
   a. Re-runs Phase 1 preflight; aborts if not GO.
   b. Evaluates all 8 preconditions (branch, HEAD sync, clean tree, tag/branch/nightly branch free, worktree path free, parent exists).
   c. Prints exact `git` commands; performs zero mutations.
   d. Exits 0 if all preconditions pass.
3. Live (`-Execute`) mode creates the three artifacts in sequence, verifies each, and reports partial state on failure.
4. `docs/control-loop/CONTROL_LOOP_2_CONTRACT.md` (this document) exists.
5. `docs/control-loop/control-loop-2.yaml` exists with valid id, role, mode, and status.
6. No source code under `voyage_framework/` modified.
7. No `.voyage` runtime files modified.
8. Dry-run run produces no tags, branches, or worktrees.
9. All pre-commit hooks pass on commit.

---

## 11. What remains for CONTROL-LOOP-3/4/5

| Phase | Capability |
|---|---|
| CONTROL-LOOP-3 | Task queue parser; morning report skeleton; per-task gate sequence (ruff, mypy, pytest, diff audit) |
| CONTROL-LOOP-4 | Guarded Claude Code invocation inside the worktree; `CODE_NO_COMMIT` and `COMMIT` mode execution; no push |
| CONTROL-LOOP-5 | Rollback execution (`git reset --hard` inside worktree only); morning summary; worktree teardown |

---

## 12. Change log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-27 | Initial draft. Phase 2 = dry-run-first checkpoint/worktree script. |
