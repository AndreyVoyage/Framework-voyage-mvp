> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 8 - SUPERVISED LOOP CONTRACT

> Specification for CONTROL-LOOP-8A: supervised loop contract and task spec.
> Status: **DRAFT / Phase 8A**.
> This phase defines the next supervision level after assisted handoff. It does
> not implement a runner, bridge, scheduler, auto-launch, night mode, or runtime
> handoff files.

---

## 1. Purpose

CONTROL-LOOP-8A defines a future supervised loop model with bounded continuation:

- `max_cycles: 2`;
- `max_tasks: 2`;
- cycle 2 allowed only after strict cycle 1 gates pass;
- cycle 2 allowed only after explicit human approval.

Manual relay remains available permanently. The supervised loop is not autonomous
overnight mode.

---

## 2. Baseline

The baseline for CONTROL-LOOP-8A is:

```text
origin/main: a97b19982ed9af1c621893433178beb60d505b0c
primary repo: C:\DEV\FRAMEWORK\Framework-voyage-mvp
auto worktree: C:\DEV\FRAMEWORK\Framework-voyage-mvp-auto-night
auto branch: auto/nightly-20260627
```

The primary repo and auto worktree must be clean before any later supervised-loop
runtime phase starts.

---

## 3. Relationship to CONTROL-LOOP-7

CONTROL-LOOP-7 proved a manual assisted handoff:

1. ChatGPT / Voyage Control created an explicit runtime `NEXT_ACTION.md`.
2. Code read that action and produced `LATEST_AGENT_REPORT.md`.
3. Work / ChatGPT audited the report and created `MORNING_REPORT.md`.
4. The cycle ended with STOP.

CONTROL-LOOP-8 keeps this human routing:

```text
Code report -> Andrey -> ChatGPT / Voyage Control
```

The next level is a supervised second-cycle option, not automatic execution.

---

## 4. Supervised Loop Model

The supervised loop is a bounded protocol:

```text
cycle 1 -> report -> audit -> human approval -> optional cycle 2 -> report -> STOP
```

It may never exceed:

```yaml
max_cycles: 2
max_tasks: 2
```

The default decision is STOP. Continue is an exception that requires explicit human
approval and all gates passing.

---

## 5. Human Approval Model

Human approval is required before Code launch for every cycle. Cycle 2 requires a
fresh approval after reviewing the cycle 1 report.

Work / ChatGPT must STOP on:

- `turn: human`;
- `recommended_next: stop`;
- unclear routing;
- missing approval;
- any mismatch between the report and observed repository state.

---

## 6. Cycle Limits

`max_cycles: 2` is a hard upper bound.

Rules:

1. Cycle 1 may run only after a human-approved prompt.
2. Cycle 2 may run only after cycle 1 passes strict gates.
3. Cycle 2 may run only after a second explicit human approval.
4. A third cycle is forbidden.
5. Any second-cycle violation is STOP.

---

## 7. Task Limits

`max_tasks: 2` is a hard upper bound for the supervised loop.

Rules:

1. A cycle may describe at most one task unless a later contract says otherwise.
2. The total supervised loop may cover at most two tasks.
3. Any task-count ambiguity is STOP.
4. Task execution is not authorized in CONTROL-LOOP-8A.

---

## 8. Turn-Token Model

Runtime files must carry explicit turn tokens:

```yaml
turn: code
turn: work
turn: human
```

Rules:

1. Code acts only on `turn: code`.
2. Work / ChatGPT audits `turn: work` reports.
3. `turn: human` means STOP for human review.
4. Turn mismatch is STOP.

Cycle 2 requires `turn: code` in the next approved action package.

---

## 9. Cycle 1 Flow

Cycle 1 follows the CONTROL-LOOP-7 pattern:

1. Human approves an exact prompt.
2. A runtime `NEXT_ACTION.md` is created by an approved phase.
3. Code reads it and produces `LATEST_AGENT_REPORT.md`.
4. Code modifies only files allowed by the approved action.
5. Work / ChatGPT audits the report.
6. A final report records STOP or requests human approval for cycle 2.

CONTROL-LOOP-8A creates no runtime handoff files.

---

## 10. Gate Checks After Cycle 1

Cycle 1 report must pass all gates:

- primary repo clean;
- origin/main matches baseline;
- auto worktree clean or exactly expected;
- no unexpected files;
- no source changes outside approved scope;
- no tests changes outside approved scope;
- no tools changes outside approved scope;
- no `docs/control-loop` changes outside approved scope;
- no `docs/handoff` changes;
- no `.voyage` touch;
- no `.env` read;
- no push, merge, deploy, SSH, Docker, or Certbot;
- no bridge loop beyond the approved manual step;
- real hash verification passes.

Any failed gate is STOP.

---

## 11. Conditions for Allowing Cycle 2

Cycle 2 is allowed only if all of these are true:

1. Human approval is explicit and current.
2. Cycle 1 report status is `PASS`.
3. Cycle 1 report recommends continuation, not `stop`.
4. Real full hash verification passes.
5. Primary repo is clean.
6. Auto worktree is clean or exactly expected.
7. Runtime action has `turn: code`.
8. No synthetic hash is present.
9. No unexpected files are present.
10. `max_cycles: 2` and `max_tasks: 2` are still respected.

Short hashes are display-only. Full hashes are required for gates.

---

## 12. Conditions That Force STOP

STOP is mandatory for:

- ambiguity;
- baseline mismatch;
- origin drift;
- dirty primary repo;
- dirty or unexpected auto worktree state;
- unexpected files;
- failed gate;
- synthetic hash;
- short hash used as gate evidence;
- turn mismatch;
- `turn: human`;
- `recommended_next: stop`;
- missing human approval;
- second-cycle violation;
- `.env` read attempt;
- `.voyage` touch attempt;
- push, merge, deploy, SSH, Docker, Certbot, or scheduler attempt.

---

## 13. LATEST_AGENT_REPORT Rules

`LATEST_AGENT_REPORT.md` must:

- use a declared schema;
- include full hashes for baseline and observed commits;
- include cycle and task IDs;
- include turn token;
- list changed files;
- list gate results;
- list anomalies;
- state `recommended_next`;
- avoid secrets and `.env` content.

Malformed reports are STOP.

---

## 14. MORNING_REPORT Rules

`MORNING_REPORT.md` or equivalent final audit report must:

- audit the latest Code report;
- confirm whether gates passed;
- decide STOP or request human approval for cycle 2;
- preserve human routing;
- avoid creating a new `NEXT_ACTION.md` unless a later approved phase permits it.

---

## 15. Hash Verification Rules

Full hashes from `git rev-parse HEAD` or `git ls-remote origin refs/heads/main` are
required for gates.

Rules:

1. Synthetic hashes are rejected.
2. Short hashes are display-only.
3. Full hashes are required for baseline, origin, and worktree checks.
4. Hash mismatch is STOP.

---

## 16. Repository / Worktree Policy

The primary repo remains read-only for supervised-loop runtime phases unless a later
explicit contract says otherwise.

The auto worktree is the only candidate mutable surface. Even there, changes require
an exact prompt and file scope.

Forbidden without a later explicit phase:

- branch deletion;
- tag deletion;
- worktree deletion;
- global git config modification;
- `--no-verify`.

---

## 17. Runtime Artifact Policy

CONTROL-LOOP-8A creates no runtime handoff files.

Runtime artifacts remain generated, not source of truth. Runtime files may be archived
outside the repository by a separate approved disposition step.

`docs/handoff/**` is not used for CONTROL-LOOP-8A runtime output.

---

## 18. Explicitly Forbidden Actions

CONTROL-LOOP-8A forbids:

- automatic Claude Code launch;
- bridge execution;
- runner implementation;
- scheduler implementation;
- night run;
- task execution;
- push;
- merge;
- deploy;
- SSH;
- Docker;
- Certbot;
- `.env` read;
- `.voyage` touch;
- branch, tag, or worktree deletion;
- global git config modification;
- `--no-verify`;
- runtime handoff file creation.

---

## 19. Out of Scope for CONTROL-LOOP-8A

Out of scope:

- implementation of bridge calls;
- implementation of auto-launch;
- implementation of a runner;
- implementation of scheduler or night mode;
- any task execution;
- any commit or push;
- runtime `NEXT_ACTION.md`;
- runtime `LATEST_AGENT_REPORT.md`;
- runtime `MORNING_REPORT.md`.

---

## 20. Future CONTROL-LOOP-8B/8C/9

Potential future phases:

| Phase | Possible scope |
|---|---|
| CONTROL-LOOP-8B | Dry-run package for supervised cycle 1 with `max_cycles: 2`. |
| CONTROL-LOOP-8C | Report-only execution of one supervised cycle. |
| CONTROL-LOOP-9 | Separate decision on runner or bridge automation, still gated by humans. |

None of these future phases are authorized by CONTROL-LOOP-8A.

---

## 21. Acceptance Criteria

CONTROL-LOOP-8A is complete when:

1. `docs/control-loop/CONTROL_LOOP_8_SUPERVISED_LOOP.md` defines the supervised loop model.
2. The contract requires `max_cycles: 2` and `max_tasks: 2`.
3. The contract requires human approval before any second cycle.
4. The contract requires strict gates before cycle 2.
5. The contract forbids auto-launch, runner implementation, scheduler, and night mode in CONTROL-LOOP-8A.
6. The contract rejects synthetic hashes and requires real full `git rev-parse` hashes.
7. `docs/control-loop/control-loop-8.yaml` validates and contains CONTROL-LOOP-8 metadata.
8. No runtime handoff files are created in CONTROL-LOOP-8A.
