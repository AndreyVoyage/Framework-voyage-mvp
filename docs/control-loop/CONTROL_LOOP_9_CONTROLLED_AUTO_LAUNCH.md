# VOYAGE CONTROL LOOP 9 - CONTROLLED AUTO-LAUNCH CONTRACT

> Specification for CONTROL-LOOP-9A: controlled auto-launch contract and task spec.
> Status: **DRAFT / Phase 9A**.
> CONTROL-LOOP-9A is documentation/spec only. It does not implement auto-launch,
> execute auto-launch, execute a bridge, implement a runner, implement a scheduler,
> start night mode, or create runtime handoff files.

---

## 1. Purpose

CONTROL-LOOP-9 defines the contract for a future controlled auto-launch capability.
The purpose is to specify the boundary for a single approved handoff execution
without converting Voyage into unattended autonomous operation.

CONTROL-LOOP-9A only drafts this contract. No auto-launch is implemented in 9A.
No bridge execution is performed in 9A. No runner is implemented in 9A. No
runtime handoff files are created in 9A.

---

## 2. Baseline

The baseline for CONTROL-LOOP-9A is:

```text
origin/main: b89d879e79a51302f60cc78c74f5d22f35dea28e
primary repo: C:\DEV\FRAMEWORK\Framework-voyage-mvp
auto worktree: C:\DEV\FRAMEWORK\Framework-voyage-mvp-auto-night
auto branch: auto/nightly-20260627
archive: C:\DEV\FRAMEWORK\_runtime_archive\Framework-voyage-mvp\CONTROL_LOOP_8B
```

The primary repo and auto worktree must be clean before any later controlled
auto-launch runtime phase starts.

---

## 3. Relationship to CONTROL-LOOP-8

CONTROL-LOOP-8 proved a supervised, two-cycle dry-run:

1. A runtime package was created manually.
2. Cycle 1 produced a report-only `LATEST_AGENT_REPORT.md`.
3. Cycle 2 required explicit human approval.
4. Cycle 2 produced a report-only `LATEST_AGENT_REPORT_CYCLE_2.md`.
5. `MORNING_REPORT.md` closed the loop with STOP.
6. Runtime artifacts were archived outside the repo and cleaned from the auto worktree.

CONTROL-LOOP-9 does not expand the number of cycles. It narrows the next question:
whether a future launcher may start exactly one approved handoff task after
explicit human approval.

---

## 4. Controlled Auto-Launch Definition

Controlled auto-launch is a future, single-shot handoff execution mechanism.
It may start one approved task package after human approval and after all
preflight gates pass.

Controlled auto-launch is not overnight mode. Controlled auto-launch is not
unattended autonomous operation. Controlled auto-launch is not a scheduler,
agent runtime, bridge loop, or task executor for arbitrary work.

Manual relay remains available permanently.

---

## 5. What Auto-Launch Means In CONTROL-LOOP-9

In CONTROL-LOOP-9, auto-launch means a future launcher may:

- read one approved runtime task package;
- verify full commit hashes and repository gates;
- start one approved external handoff command after human approval;
- wait for exactly one agent report;
- write or collect the one report defined by the approved package;
- stop immediately after that report.

It is a bounded launch of a single approved package, not an autonomous loop.

---

## 6. What Auto-Launch Does NOT Mean

Controlled auto-launch does not mean:

- unattended autonomous operation;
- overnight mode;
- scheduler execution;
- background runner installation;
- repeated task execution;
- automatic creation of a second `NEXT_ACTION`;
- bridge loops;
- push, merge, deploy, docker, ssh, or certbot actions;
- reading `.env`;
- touching `.voyage`;
- bypassing manual relay.

---

## 7. Human Approval Model

Human approval is required before every launch. Approval must identify the exact
runtime package, target repo, target worktree, baseline full commit hash, and
allowed report output.

The launcher must reject implicit approval, stale approval, inferred approval,
or approval copied from a previous phase. Any attempt to start a second task
without human approval is STOP.

---

## 8. Launch Boundary

A launch boundary is the exact package and command surface approved by the human.
The launcher must not expand that boundary.

The boundary includes:

- one runtime package;
- one baseline commit;
- one auto worktree;
- one expected output report;
- one allowed execution attempt;
- one STOP decision after report collection.

---

## 9. Single-Shot Launch Model

The launcher must only run one approved task package. The launcher must stop
after one agent report. The launcher must not create a second `NEXT_ACTION` by
itself. The launcher must not loop.

If the report is missing, malformed, late, or failed, the launcher stops and
returns a failure report for human review.

---

## 10. No Overnight Mode Rule

Controlled auto-launch is not overnight mode. It must not run unattended across
multiple tasks, multiple cycles, a queue, or a time window.

Any attempt to start night mode is STOP.

---

## 11. No Scheduler Rule

CONTROL-LOOP-9 does not define a scheduler. A launcher must not install,
configure, or trigger scheduled execution.

Any attempt to start scheduler mode is STOP.

---

## 12. No Autonomous Multi-Cycle Rule

The launcher must not make autonomous continuation decisions. It may not create
or execute another action after the approved single report.

Any second task, second launch, or continuation requires a new explicit human
approval and a separate phase.

---

## 13. Required Preflight Gates

The future launcher must pass all gates before launch:

- primary repo branch is expected;
- primary repo is clean;
- primary HEAD is the expected full commit hash;
- `origin/main` is the expected full commit hash;
- auto worktree is on the expected branch;
- auto worktree HEAD is the expected full commit hash;
- runtime package exists and is the approved package;
- allowed output path is inside the approved runtime directory;
- no unexpected files are present;
- no staged files exist;
- no `.env` access is required;
- no `.voyage` mutation is required.

Dirty primary repo is STOP. Unexpected files are STOP. Origin drift is STOP.

---

## 14. Required Runtime Package Inputs

A launch package must include:

- task id;
- phase id;
- full baseline commit hash;
- expected `origin/main` full commit hash;
- target primary repo path;
- target auto worktree path;
- allowed command or handoff target;
- allowed output report path;
- forbidden paths;
- STOP conditions;
- human approval token or approval record.

Synthetic hashes are rejected.

---

## 15. Allowed Launcher Behavior

The future launcher may:

- read the approved runtime package;
- read repository state;
- verify hashes and gates;
- invoke one approved handoff command;
- wait for one agent report;
- capture exit code and report path;
- return the report to the human routing path;
- stop.

---

## 16. Forbidden Launcher Behavior

The launcher must not:

- push;
- merge;
- deploy;
- read `.env`;
- touch `.voyage`;
- create branches, tags, or worktrees;
- run `git reset`;
- run `git clean`;
- create a second `NEXT_ACTION`;
- start a loop;
- start scheduler mode;
- start night mode;
- execute a second task without human approval.

---

## 17. Turn-Token Model

The runtime package must include a turn-token or equivalent phase marker. The
launcher may only act when the token explicitly grants launch authority for the
current phase.

The launcher must not infer authority from old reports, archived artifacts, or
previous approvals.

---

## 18. Report Contract

The launched handoff must produce exactly one expected report. The report must
include:

- schema;
- task id;
- phase;
- status;
- baseline full commit hash;
- observed `origin/main` full commit hash;
- files changed;
- gates;
- anomalies;
- recommended next action;
- STOP or human-review disposition.

Missing report is STOP. Malformed report is STOP.

---

## 19. Hash Verification Rules

Full commit hashes are required for all gates. Short hashes may be displayed for
human readability only, but they are not sufficient for gate checks.

Synthetic hashes are rejected. Hash mismatch is STOP. Origin drift is STOP.

---

## 20. Repository/Worktree Policy

The primary repo remains the protected integration surface. The auto worktree is
the controlled work surface.

The launcher must not modify the primary repo except through a separately
approved later merge/push phase. The launcher must not leave staged files. The
launcher must not hide state by editing `.gitignore`.

---

## 21. Runtime Artifact Policy

Runtime artifacts are not source of truth. They must remain untracked unless a
future phase explicitly approves another policy.

Runtime artifacts should be archived outside the repo after review and cleaned
only after archive verification.

CONTROL-LOOP-9A creates no runtime handoff files.

---

## 22. STOP Conditions

The launcher must STOP for:

- dirty primary repo;
- origin drift;
- unexpected files;
- staged files;
- missing runtime package;
- malformed runtime package;
- missing report;
- malformed report;
- synthetic hash;
- hash mismatch;
- attempt to read `.env`;
- attempt to touch `.voyage`;
- push, merge, deploy, docker, ssh, or certbot attempt;
- scheduler or night mode attempt;
- second task attempt without human approval;
- loop attempt.

---

## 23. Failure Handling

On failure, the launcher must stop and return a failure report. It must not try
to repair the repo, clean files, reset state, retry another task, create a new
action, or escalate into a loop.

Human review decides the next phase.

---

## 24. Out Of Scope For CONTROL-LOOP-9A

CONTROL-LOOP-9A does not:

- implement auto-launch;
- execute auto-launch;
- execute a bridge;
- implement a runner;
- implement a scheduler;
- create runtime handoff files;
- create `NEXT_ACTION.md`;
- create `LATEST_AGENT_REPORT.md`;
- create `MORNING_REPORT.md`;
- start CONTROL-LOOP-9 runtime.

---

## 25. Future CONTROL-LOOP-9B/9C/9D

Future phases may separately define:

- CONTROL-LOOP-9B: runtime package for a controlled launch dry-run;
- CONTROL-LOOP-9C: read-only audit of the package;
- CONTROL-LOOP-9D: a single-shot live launch gate, only if explicitly approved.

Those future phases must preserve manual relay and must not add scheduler,
overnight mode, or autonomous multi-cycle behavior.

---

## 26. Acceptance Criteria

- CONTROL-LOOP-9A is spec-only.
- No auto-launch is implemented in 9A.
- No auto-launch is executed in 9A.
- No bridge execution is performed in 9A.
- No runner is implemented in 9A.
- No scheduler is implemented in 9A.
- No runtime handoff files are created in 9A.
- Manual relay remains available permanently.
- Human approval is required before every launch.
- The future launcher is single-shot only.
- The future launcher stops after one report.
- The future launcher does not create a second `NEXT_ACTION` by itself.
- The future launcher does not loop.
- The future launcher does not push, merge, deploy, read `.env`, or touch `.voyage`.
- Full commit hashes are required for gates.
- Synthetic hashes are rejected.
- Dirty primary repo is STOP.
- Unexpected files are STOP.
- Origin drift is STOP.
- Missing report is STOP.
- Malformed report is STOP.
- Any attempt to start scheduler or night mode is STOP.
- Any attempt to start a second task without human approval is STOP.
