# VOYAGE CONTROL LOOP 5 - OVERNIGHT DRY-RUN CONTRACT

> Specification for CONTROL-LOOP-5: first limited overnight dry-run design.
> Status: **DRAFT / Phase 5B**.
> Predecessors:
> - `docs/control-loop/CONTROL_LOOP_SPEC.md`
> - `docs/control-loop/CONTROL_LOOP_2_CONTRACT.md`
> - `docs/control-loop/CONTROL_LOOP_3_CONTRACT.md`
> - `docs/control-loop/CONTROL_LOOP_4_GUARDED_EXECUTION.md`
>
> This document is a stop-gate for CONTROL-LOOP-5 only.

---

## 1. Purpose

CONTROL-LOOP-5 defines the first limited overnight dry-run. It is **not full
autonomy**. The goal is to prove that a single, short, human-triggered "night run"
can produce a deterministic report inside the auto worktree without modifying the
primary repo, without pushing, without merging, and without invoking external AI
bridges.

This phase creates the contract and task spec only. It does **not** implement the
runner, scheduler, or any autonomous execution.

---

## 2. Current Baseline

Current baseline:

* `origin/main`: `ffbca6a`
* Primary repo `main`: `ffbca6a`
* Auto worktree branch: `auto/nightly-20260627`
* Auto worktree HEAD: `ffbca6a`

Before any real night run, the following must be true:

1. Primary repo is on `main` and is clean.
2. Primary repo HEAD matches `origin/main`.
3. Auto worktree is on `auto/nightly-20260627` and is clean.
4. A fresh checkpoint tag and branch are created at the current `origin/main`.
5. A human has approved the exact dry-run profile and file scope.

---

## 3. First Dry-Run Profile

The first dry-run is intentionally minimal and report-only.

Profile name: `report-only-first`

Constraints:

* **Max tasks**: 1.
* **Timeout**: 15 minutes.
* **Execution**: manual `night run` command, not an OS scheduled task.
* **Output**: one UTF-8 report file under `docs/handoff/` or a local log directory.
* **State mutation**: none in the first dry-run.
* **Task selection**: manual or pre-approved single task; no automatic queue selection.
* **Multi-task sequencing**: not allowed.
* **Autonomous bridge/agent invocation**: not allowed.

---

## 4. Runner Model

The future runner (not implemented in this phase) will be a small PowerShell script
that:

1. Validates preconditions.
2. Creates a fresh checkpoint.
3. Runs one approved task inside the auto worktree.
4. Writes a morning report.
5. Stops on any anomaly.

Runner scripts must be pure ASCII for Windows PowerShell 5.1 compatibility. They
must remain read-only by default and require an explicit switch to perform any
mutation.

---

## 5. Task Selection Rules

For the first dry-run:

1. The task is chosen before the run starts.
2. Only one task is allowed.
3. The task must be docs-only or similarly low-risk.
4. The exact file scope is approved in advance.
5. No automatic queue selection is performed.

Future phases may introduce deterministic queue selection, but not in
CONTROL-LOOP-5.

---

## 6. Stop Conditions

The dry-run must stop immediately if any of the following are true:

* primary repo is dirty;
* auto worktree is dirty before the run;
* current branch is not `auto/nightly-20260627`;
* checkpoint tag or branch is missing/stale;
* task spec cannot be parsed or has duplicate IDs;
* timeout is exceeded;
* any prompt asks to push, merge, deploy, bridge, or execute tasks autonomously;
* any prompt asks to read `.env` or secrets;
* any prompt asks to mutate `.voyage/` runtime files;
* any tool would modify files without explicit human approval.

---

## 7. File/Write Policy

First dry-run file policy:

1. Work happens only in the auto worktree.
2. Primary repo remains read-only.
3. Reports are written as UTF-8.
4. Reports must not contain secrets.
5. Reports are left untracked or copied to a local log directory.
6. No auto-push or auto-merge is performed.
7. Clipboard tools are optional convenience only, are never required, are never a
   gate, and must not execute automatically during the first dry-run.

Future variants may allow a docs-only auto-commit on the auto branch after all
gates pass, but not in the first report-only dry-run.

---

## 8. Morning Report Format

The morning report must contain:

1. Run start and end timestamps.
2. Baseline commit used.
3. Checkpoint tag/branch used.
4. Task attempted.
5. Outcome (success, partial, failed, stopped).
6. List of files inspected or produced.
7. Any anomalies or stop reasons.
8. Explicit next action requiring human approval.

The report must be UTF-8 and must not contain secrets.

---

## 9. Checkpoint Strategy

A fresh checkpoint must be created at the start of each real night run:

* checkpoint tag: `voyage-checkpoint-YYYYMMDD-HHMM`
* checkpoint branch: `checkpoint/YYYYMMDD-HHMM`
* target: current `origin/main` HEAD

Old checkpoints are preserved as historical rollback points. Deletion of old
checkpoints is not required and must not happen automatically.

---

## 10. Gate Sequence

Before a real night run:

1. Primary repo clean and synced.
2. Auto worktree clean.
3. Correct auto branch.
4. Fresh checkpoint created.
5. Exact dry-run profile approved.
6. Exact file scope approved.
7. Human approval recorded.

After the run:

1. Worktree status checked.
2. Diff scoped to allowed paths.
3. `git diff --check` passes.
4. Morning report exists and is UTF-8.
5. No forbidden paths touched.
6. No push/merge/deploy occurred.

---

## 11. Failure Handling

If the dry-run fails:

1. Stop immediately.
2. Record the failure reason in the morning report.
3. Do not retry automatically.
4. Do not push or merge.
5. Human reviews the report and decides the next action.

---

## 12. Drift Handling

If `origin/main` drifts after the checkpoint is taken:

1. The current run continues against the captured baseline.
2. The morning report notes the drift.
3. A future run must create a fresh checkpoint against the new `origin/main`.
4. No automatic rebase or merge is performed.

---

## 13. Rollback Boundary

The rollback target for CONTROL-LOOP-5 is the fresh checkpoint created at the start
of the night run. The auto worktree may be reset to that checkpoint if the run
produces unsafe changes.

CONTROL-LOOP-5 does not perform automatic rollback. The rollback action itself is a
human-approved step documented in the morning report.

---

## 14. Human Approval Gates

CONTROL-LOOP-5 requires explicit human approval for:

1. Creating the fresh checkpoint.
2. Starting the night run.
3. Any file modification beyond report writing.
4. Any commit on the auto branch.
5. Any merge to `main`.
6. Any push.

No step may bypass these gates.

---

## 15. Explicitly Forbidden Actions

CONTROL-LOOP-5 forbids the following under all circumstances:

* Push to any remote.
* Merge into `main`.
* Deploy.
* SSH to remote hosts.
* Run Docker containers.
* Run Certbot or certificate automation.
* Read `.env` or any secret file.
* Modify `.voyage/` runtime state.
* Delete tags, branches, or worktrees.
* Modify global git config.
* Automatic multi-task queue selection in the first dry-run.
* Multi-task sequencing in the first dry-run.
* Autonomous bridge/agent invocation.
* Overnight scheduling via OS task scheduler in the first dry-run.

---

## 16. Out of Scope for CONTROL-LOOP-5

CONTROL-LOOP-5 does not implement:

* the runner script;
* the scheduler;
* OS-level scheduled tasks;
* multi-task sequencing;
* automatic task queue selection;
* autonomous AI bridge invocation;
* automatic commit on the auto branch in the first dry-run;
* automatic rollback execution;
* push or merge to `main`;
* production deployment.

---

## 17. Future CONTROL-LOOP-6+ Items

| Phase | Capability |
|---|---|
| CONTROL-LOOP-6 | Implement the PowerShell runner skeleton with dry-run and report-only modes. |
| CONTROL-LOOP-7 | Implement deterministic single-task selection and gated auto-commit on the auto branch. |
| CONTROL-LOOP-8 | Add OS scheduler wrapper and unattended operation policy. |
| CONTROL-LOOP-9 | Add automatic rollback execution and morning summary distribution. |

---

## 18. Acceptance Criteria

CONTROL-LOOP-5 is complete when:

1. This contract exists and documents the first overnight dry-run profile.
2. `docs/control-loop/control-loop-5.yaml` exists with valid ID, role, mode, and status.
3. The contract specifies that the first dry-run is report-only, manual, single-task, and 15-minute bounded.
4. No runner, scheduler, or overnight execution is implemented in this phase.
5. Primary repo remains untouched.
6. All required safety gates and forbidden actions are documented.

---

## 19. Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-27 | Initial draft. Phase 5B = overnight dry-run contract/spec only. |
