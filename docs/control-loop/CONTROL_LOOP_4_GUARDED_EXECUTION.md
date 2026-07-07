> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 4 - GUARDED EXECUTION MODE

> Specification for CONTROL-LOOP-4: guarded, human-approved execution of one small
> low-risk task inside the auto worktree only.
> Status: **DRAFT / Phase 4**.
> Predecessors:
> - `docs/control-loop/CONTROL_LOOP_SPEC.md`
> - `docs/control-loop/CONTROL_LOOP_2_CONTRACT.md`
> - `docs/control-loop/CONTROL_LOOP_3_CONTRACT.md`
>
> This document is a stop-gate for CONTROL-LOOP-4 only.

---

## 1. Purpose

CONTROL-LOOP-4 introduces the first live execution surface. It allows one small,
low-risk task to be performed inside the auto worktree after a full diff audit and
explicit human approval. The phase is designed to prove that a guarded executor can
touch files safely without escaping the worktree, without invoking external AI
bridges, and without running overnight.

This phase intentionally remains narrow. It does not implement full autonomous
execution, multi-step planning, or background workers.

---

## 2. Baseline and Checkpoint

All CONTROL-LOOP-4 work starts from a verified baseline.

Current baseline:

* `origin/main`: `0bb34a1`
* Primary repo `main`: `0bb34a1`
* Auto worktree branch: `auto/nightly-20260627`
* Auto worktree HEAD: `0bb34a1`
* Fresh rollback target:
  * tag: `voyage-checkpoint-20260627-2246`
  * branch: `checkpoint/20260627-2246`
  * target: `0bb34a1`

Before any executor touches files, the following must be true:

1. Primary repo is on `main` and is clean.
2. Primary repo HEAD matches `origin/main`.
3. Auto worktree is on `auto/nightly-20260627` and is clean.
4. Fresh checkpoint tag and branch exist and point to the current `origin/main`.
5. The exact task, file scope, and acceptance criteria are approved by a human.

---

## 3. Allowed Execution Surface

CONTROL-LOOP-4 execution is allowed only inside the auto worktree:

```text
C:\DEV\FRAMEWORK\Framework-voyage-mvp-auto-night
```

Allowed change types:

* Low-risk documentation files under `docs/control-loop/`.
* Small, isolated, human-approved edits with a clearly bounded file scope.

This phase does **not** allow source-code changes, test changes, tooling changes, or
changes to runtime state.

---

## 4. Forbidden Actions

CONTROL-LOOP-4 forbids the following under all circumstances:

* Push to any remote.
* Merge into `main`.
* Cherry-pick outside the auto branch.
* Edit files in the primary repo working tree.
* Modify existing CONTROL-LOOP-1/2/3 contract files.
* Modify `voyage_framework/` source code.
* Modify tests.
* Modify tools.
* Modify `docs/handoff/**` tracked files.
* Modify `docs/artifacts/**`.
* Modify `.voyage/` runtime state.
* Read `.env` or any secret file.
* Invoke Claude, Codex, Kimi, or any other AI bridge.
* Run overnight or background automation.
* Run rollback, `git reset`, or `git clean`.
* Create or delete tags, branches, or worktrees.
* Deploy, run docker, ssh, or certbot.

---

## 5. Guarded Task Rules

A CONTROL-LOOP-4 task must satisfy all of the following:

1. **Single task**: only one approved task per execution cycle.
2. **Docs-only or low-risk**: changes are documentation or similarly low-risk.
3. **Bounded scope**: the exact file list is approved in advance.
4. **Auto branch only**: all commits happen on `auto/nightly-20260627`.
5. **No new runtime artifacts**: no new tags, branches, or worktrees are created.
6. **Audit before commit**: `git diff --check` and file-scope audit pass.
7. **Stop on anomaly**: if unexpected files are modified or staged, execution stops.

---

## 6. Gates Before Commit

Before a CONTROL-LOOP-4 commit is allowed:

1. Primary repo `main` is clean and matches `origin/main`.
2. Auto worktree is on `auto/nightly-20260627` and is clean before edits.
3. Only the approved files are changed.
4. `git diff --check` passes.
5. Staged files are exactly the approved files.
6. No forbidden paths are touched.
7. A human has approved the exact commit message and scope.

---

## 7. Commit Rules

* Commit only on `auto/nightly-20260627`.
* Use a descriptive commit message starting with the change type.
* Do not use `--no-verify` unless explicitly authorized.
* Do not push.
* Do not merge.
* Do not create a merge commit.

Example commit message for a docs-only task:

```text
docs: define control loop guarded execution mode
```

---

## 8. Handoff/Report Requirements

After the executor completes the task, a handoff report must be produced.

Required local handoff paths:

```text
docs/handoff/LATEST_AGENT_REPORT.md
docs/handoff/NEXT_ACTION.md
```

Rules:

1. `LATEST_AGENT_REPORT.md` contains the full execution report.
2. `NEXT_ACTION.md` contains one explicit next action or prompt.
3. Both files remain untracked local artifacts.
4. Reports must be written as UTF-8.
5. Reports must not contain secrets, credentials, auth URLs, tokens, or `.env` data.
6. Merge to `main` requires a separate human approval after audit.

---

## 9. Rollback Boundary

The rollback target for CONTROL-LOOP-4 is the fresh checkpoint created at the start
of the phase:

```text
voyage-checkpoint-20260627-2246
checkpoint/20260627-2246
```

If the guarded execution fails or produces unsafe changes, the auto worktree can be
reset to this checkpoint. The primary repo `main` must remain untouched and can be
used as a reference baseline.

CONTROL-LOOP-4 itself does **not** perform rollback. Rollback execution is reserved
for CONTROL-LOOP-5.

---

## 10. What Remains Out of Scope for CONTROL-LOOP-5

| Phase | Capability |
|---|---|
| CONTROL-LOOP-5 | Rollback execution inside the worktree only; morning summary; worktree teardown guidance. |

CONTROL-LOOP-4 does not implement:

* automatic rollback;
* morning summary generation;
* worktree teardown;
* unattended overnight operation;
* multi-step autonomous planning;
* bridge invocation;
* push or merge to `main`.

---

## 11. Acceptance Criteria

CONTROL-LOOP-4 is complete when:

1. This contract exists and documents the guarded execution mode.
2. Exactly one approved file is created or modified inside the auto worktree.
3. The change is committed only on `auto/nightly-20260627`.
4. No push, merge, bridge invocation, or overnight mode is performed.
5. Primary repo remains untouched.
6. Handoff report files are produced as UTF-8 without secrets.
7. Fresh checkpoint remains available as the rollback target.

---

## 12. Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-27 | Initial draft. Phase 4 = guarded docs-only execution in auto worktree. |
