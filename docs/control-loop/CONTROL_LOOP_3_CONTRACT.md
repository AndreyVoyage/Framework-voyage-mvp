# VOYAGE CONTROL LOOP 3 - CONTRACT

> Specification for CONTROL-LOOP-3: task queue and handoff/report protocol.
> Status: **DRAFT / Phase 3**.
> Predecessors:
> - `docs/control-loop/CONTROL_LOOP_SPEC.md`
> - `docs/control-loop/CONTROL_LOOP_2_CONTRACT.md`
>
> This document is a stop-gate for CONTROL-LOOP-3 only.

---

## 0. Purpose

CONTROL-LOOP-3 defines the task queue and handoff protocol for safe work inside the
nightly auto worktree.

This phase creates protocol/tooling only. It does not execute development tasks,
does not invoke Claude or Codex as a bridge, does not push, and does not merge.

The deliverables are:

- this contract;
- `docs/control-loop/control-loop-3.yaml`;
- `tools/control_loop_next_task.ps1`;
- `tools/control_loop_handoff.ps1`.

---

## 1. Task Queue Model

CONTROL-LOOP task specs are tracked documentation and planning inputs. Runtime state
and generated handoff reports are local artifacts and are not source of truth.

Tracked task specs:

```text
docs/control-loop/*.yaml
```

Runtime or generated local files:

```text
docs/handoff/LATEST_AGENT_REPORT.md
docs/handoff/NEXT_ACTION.md
docs/handoff/SESSION_EXPORT.md
```

Rules:

1. Tracked task specs describe authorized phases and expected file scope.
2. Runtime queues, reports, and session exports stay untracked.
3. `.voyage/` runtime databases are never modified by CONTROL-LOOP-3.
4. The helper scripts may inspect tracked task specs and print recommendations.
5. Helpers must stop on ambiguity and require a human decision.

---

## 2. Manual Task Selection

CONTROL-LOOP-3 does not automatically select and execute development work.

The next task is chosen manually:

1. Inspect tracked `docs/control-loop/*.yaml` specs.
2. Print known tasks and their status/metadata.
3. Recommend the next manual planning or approval step.
4. Stop if multiple plausible next actions exist.
5. Require an exact human-approved prompt before any executor touches files.

The recommended helper for this is `tools/control_loop_next_task.ps1`.

---

## 3. Stop Conditions

CONTROL-LOOP-3 must stop and report if any of the following are true:

- primary repo is dirty;
- auto worktree is dirty before task selection;
- current branch is not the expected auto branch;
- checkpoint tag or checkpoint branch is missing;
- task spec cannot be parsed or has duplicate IDs;
- task priority or next action is ambiguous;
- any prompt asks to push, merge, deploy, bridge, or execute tasks;
- any prompt asks to read `.env` or secrets;
- any prompt asks to mutate `.voyage/` runtime files;
- any tool would modify files without explicit human approval.

---

## 4. Handoff Report Protocol

The handoff protocol keeps terminal output short and puts durable information in
local handoff files.

Required local handoff paths:

```text
docs/handoff/LATEST_AGENT_REPORT.md
docs/handoff/NEXT_ACTION.md
```

Rules:

1. `LATEST_AGENT_REPORT.md` contains the full final report from the current agent.
2. `NEXT_ACTION.md` contains one explicit next action or prompt.
3. Both files are generated local artifacts and should remain untracked.
4. Reports must be written as UTF-8.
5. Reports must not contain secrets, credentials, auth URLs, tokens, or `.env` data.
6. When a report file exists, agents should not paste huge terminal output manually.

The recommended helper for this is `tools/control_loop_handoff.ps1`.

---

## 5. UTF-8 Rules

Generated handoff files must be UTF-8. Tools that read these files must read them as
UTF-8 explicitly. This avoids mojibake in multilingual text and keeps reports
portable between Windows PowerShell, VS Code, and chat tools.

PowerShell helpers should use .NET UTF-8 APIs when reading report files. CONTROL-LOOP-3
helpers themselves are ASCII-only for PowerShell 5.1 compatibility.

---

## 6. Clipboard Rules

Clipboard operations are manual. CONTROL-LOOP-3 helpers may print the safe command to
copy a report, but must not execute clipboard copying by default.

Existing copy helpers:

```text
tools/copy_latest_report.ps1
tools/copy_report_to_clipboard.ps1
```

Safe examples:

```powershell
powershell -ExecutionPolicy Bypass -File tools\copy_latest_report.ps1
powershell -ExecutionPolicy Bypass -File tools\copy_report_to_clipboard.ps1 -Path docs\reports\REPORT_NAME.md
```

---

## 7. Role Split

| Role | Responsibility |
|---|---|
| ChatGPT | Control room and final auditor. Reviews reports, decides whether the next gate is safe. |
| Claude Work | Planner and reviewer. Produces plans, audits, and prompts for human approval. |
| Claude Code / Codex | Executor only after an exact prompt and file scope are approved. |
| Human | Approval gate. Authorizes live gates, commits, pushes, merges, bridge automation, and cleanup. |

No role may bypass the human approval gates.

---

## 8. Safety Gates

Before task:

- primary repo clean and synced;
- auto worktree clean;
- correct auto branch;
- checkpoint tag and branch exist;
- no `.env` or secrets read;
- exact prompt and file scope approved.

After task:

- worktree status checked;
- diff scoped to allowed paths;
- `git diff --check` passes;
- forbidden-touch check passes;
- handoff report and next action are written as UTF-8.

Before commit in auto branch:

- quality gates appropriate to the task pass;
- staged files are exactly expected;
- commit happens only on the auto branch;
- no push is performed.

Before push or merge:

- separate human approval;
- final diff audit;
- no automatic merge to `main`;
- no automatic push.

Before bridge automation:

- separate CONTROL-LOOP-4 contract;
- explicit human authorization;
- denylist enforced before invocation;
- no permission prompt is auto-accepted.

---

## 9. Out of Scope

CONTROL-LOOP-3 does not implement:

- Claude bridge;
- Codex bridge;
- overnight automation;
- task execution;
- deployment;
- automatic merge;
- automatic push;
- rollback;
- reading `.env`;
- modifying `.voyage/` runtime databases;
- source-code changes under `voyage_framework/`;
- tests for product behavior.

---

## 10. What Remains for CONTROL-LOOP-4/5

| Phase | Capability |
|---|---|
| CONTROL-LOOP-4 | Guarded Claude Code invocation inside the worktree; no push; no deploy; explicit approval only. |
| CONTROL-LOOP-5 | Rollback execution inside worktree only; morning summary; worktree teardown guidance. |

---

## 11. Acceptance Criteria

CONTROL-LOOP-3 is complete when:

1. This contract exists and documents the task queue model and handoff protocol.
2. `docs/control-loop/control-loop-3.yaml` exists with valid ID, role, mode, and status.
3. `tools/control_loop_next_task.ps1` exists, parses under PowerShell 5.1, and is read-only by default.
4. `tools/control_loop_handoff.ps1` exists, parses under PowerShell 5.1, and is read-only by default.
5. Helpers do not edit files, stage, commit, push, read `.env`, touch `.voyage`, invoke bridges, or execute tasks.
6. Handoff report rules require UTF-8 and forbid secrets.
7. Primary repo remains untouched.

---

## 12. Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-27 | Initial draft. Phase 3 = task queue and handoff/report protocol. |
