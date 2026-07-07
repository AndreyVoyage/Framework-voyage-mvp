> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 10A - MINIMAL CONTROLLED LAUNCHER CONTRACT

> Specification for CONTROL-LOOP-10A: minimal controlled launcher contract.
>
> Status: **DRAFT / Phase 10A**.
> Baseline: `origin/main` at `8ce1b35`.
>
> This document defines a future minimal controlled launcher. It does not
> implement or execute the launcher.

---

## 1. Title

CONTROL-LOOP-10A: Minimal Controlled Launcher Contract.

---

## 2. Purpose

CONTROL-LOOP-10A defines the contract for a future minimal controlled launcher.
The launcher is a small, human-approved, single-shot execution helper that reads
one approved runtime package, performs one low-risk action inside the auto
worktree, writes one report, and stops. It is not a general runner, not a
scheduler, and not an autonomous multi-cycle bridge.

This phase is spec-only. It does not implement the launcher, does not execute the
launcher, does not create runtime files, and does not run overnight.

---

## 3. Baseline from CONTROL-LOOP-9

CONTROL-LOOP-9 proved a single-shot report-only flow with full human approval,
hash verification, and runtime artifact archival. The baseline for CONTROL-LOOP-10
is:

* `origin/main`: `8ce1b35` (`docs: define controlled auto-launch contract`).
* Primary repo branch: `main`.
* Auto worktree branch: `auto/nightly-20260627`.
* CONTROL-LOOP-9B runtime artifacts archived at
  `C:\DEV\FRAMEWORK\_runtime_archive\Framework-voyage-mvp\CONTROL_LOOP_9B`.
* No runtime artifacts remain in the auto worktree.

---

## 4. What CONTROL-LOOP-10 is trying to prove

CONTROL-LOOP-10 will prove that a minimal launcher can:

1. Read exactly one approved runtime package.
2. Verify human approval artifacts.
3. Run preflight gates.
4. Execute exactly one approved task.
5. Produce exactly one report.
6. Stop without looping.

It must do this without escaping the auto worktree, without reading secrets,
without mutating `.voyage`, and without push/merge/deploy.

---

## 5. Minimal controlled launcher definition

The minimal controlled launcher is a deterministic, human-gated script that:

* accepts one runtime package path as input;
* validates the package and approval artifacts;
* runs preflight gates;
* executes one task;
* writes one report;
* exits.

It is not interactive during execution. All decisions are made before launch.

---

## 6. What the launcher may do

The launcher may:

* read the runtime package;
* read approved files inside the auto worktree;
* verify hashes with `git rev-parse`;
* execute one pre-approved task;
* write one report file to the approved runtime location;
* stop on any anomaly.

---

## 7. What the launcher must never do

The launcher must never:

* run without explicit human approval;
* execute more than one task per run;
* create a second `NEXT_ACTION`;
* loop or continue automatically;
* push, merge, commit, deploy, or modify primary repo `main`;
* read `.env` or secrets;
* mutate `.voyage` runtime state;
* delete branches, tags, or worktrees;
* modify global git config;
* run SSH, Docker, or Certbot;
* run overnight or via scheduler;
* report directly to ChatGPT or external APIs.

---

## 8. Human approval model

Every launcher run requires explicit human approval recorded in a dedicated
approval artifact. The approval must include:

* approved runtime package path;
* approved task description;
* approved file scope;
* approved risk level;
* approved baseline commit;
* approver identity and timestamp.

No launch is valid without the approval artifact.

---

## 9. Manual relay preservation

`manual_relay` remains permanently available. The launcher does not replace
manual mode. Any human may fall back to `manual_relay` at any time, especially
for main repo operations, merge, push, deploy, risky code, first runs, and
unexpected state.

---

## 10. Single-shot execution boundary

The launcher is single-shot only:

* `max_cycles: 1`
* `max_tasks: 1`
* After one report, the launcher exits.
* Work must audit the report before any future launch.

---

## 11. Runtime package input contract

The runtime package must be a single file or directory containing:

* `NEXT_ACTION.md` with full schema;
* `HUMAN_APPROVAL.md` with explicit approval;
* optional preflight report from a prior phase.

The launcher must reject any package missing required fields, containing
synthetic hashes, or referencing forbidden paths.

---

## 12. Human approval artifact contract

The approval artifact must:

* be written by the approving human;
* reference the exact runtime package;
* reference the exact baseline commit;
* state the approved risk level;
* list the allowed files;
* list the forbidden paths;
* include the phrase "I approve this launcher run";
* be present before the launcher reads the package.

---

## 13. Preflight gate contract

Before executing the task, the launcher must run these gates:

1. Primary repo is on `main` and clean.
2. Auto worktree is on `auto/nightly-20260627` and clean.
3. `origin/main` matches local `main`.
4. Baseline commit in the package matches `git rev-parse HEAD`.
5. Approval artifact exists and is valid.
6. Allowed files are inside the auto worktree.
7. Forbidden paths include `.env`, `.voyage/`, `tools/`, `tests/`,
   `voyage_framework/`, and primary repo files.
8. Risk level is within the approved profile.

Any gate failure is a STOP condition.

---

## 14. Hash verification contract

The launcher must verify all hashes with real `git rev-parse`:

1. `baseline_commit` equals `git rev-parse HEAD` in the target worktree.
2. `origin/main` equals `git rev-parse origin/main` or `git ls-remote origin
   refs/heads/main`.
3. Synthetic hashes are rejected.
4. Short hashes are acceptable only for display.

---

## 15. Allowed output contract

The launcher may produce only:

* one `LATEST_AGENT_REPORT.md`;
* one `MORNING_REPORT.md` or stop summary.

All outputs must be UTF-8, must not contain secrets, and must be written to the
approved runtime location.

---

## 16. Report-only task boundary

The first launcher implementation is report-only. It may inspect files, verify
state, and produce reports. It must not modify files unless a later approved
phase explicitly expands the risk profile.

---

## 17. STOP conditions

The launcher must STOP if:

* runtime package is missing or malformed;
* approval artifact is missing or invalid;
* preflight gate fails;
* `turn` token is wrong;
* `cycle`, `task_id`, or `baseline_commit` does not match expectations;
* hash is synthetic or does not match `git rev-parse`;
* primary repo is dirty;
* `origin/main` drifted;
* unexpected files are present;
* forbidden path would be touched;
* `.env` or secrets would be read;
* `.voyage` would be mutated;
* push, merge, commit, deploy, SSH, Docker, or Certbot is requested;
* branch/tag/worktree creation or deletion is requested;
* global git config modification is requested;
* scheduler or night mode is requested;
* second task or second cycle is requested;
* bridge-loop or auto-continuation is requested;
* timeout is exceeded;
* state is ambiguous.

---

## 18. Failure handling

On failure, the launcher must:

1. Stop immediately.
2. Write a failure report explaining the STOP reason.
3. Not retry automatically.
4. Not push or merge.
5. Leave the auto worktree in a diagnosable state.

---

## 19. Repository/worktree policy

All launcher work happens inside the auto worktree. Primary repo `main` remains
read-only. The launcher must not checkout other branches, create worktrees, or
modify global git state.

---

## 20. Runtime artifact policy

Runtime artifacts are local and untracked. They may be archived after the run but
are not committed unless a later approved phase changes the policy. The launcher
must not create runtime artifacts outside the approved runtime location.

---

## 21. No scheduler / no overnight mode rule

CONTROL-LOOP-10 does not implement scheduler integration or overnight operation.
Any future scheduler wrapper requires a separate approved phase after multiple
supervised single-shot runs pass.

---

## 22. No autonomous multi-cycle rule

The launcher must not run multiple cycles autonomously. One launch equals one
task equals one report. Multi-cycle loops are out of scope for CONTROL-LOOP-10.

---

## 23. No bridge-loop rule

The launcher must not feed its own output back as input to create a self-running
bridge loop. Work must always audit the report and explicitly approve the next
launch.

---

## 24. No `.env` / no `.voyage` rule

The launcher must never read `.env` or any secret file. The launcher must never
write to, delete, or modify files under `.voyage/`.

---

## 25. Implementation phases after 10A

| Phase | Candidate capability |
|---|---|
| CONTROL-LOOP-10B | Implement the launcher skeleton in PowerShell with a dry-run mode and no AI invocation. |
| CONTROL-LOOP-10C | Execute one supervised report-only launcher run with Andrey approving and launching manually. |
| CONTROL-LOOP-10D | Harden launcher stop/escalation rules and add anomaly reporting. |

---

## 26. Out of scope for 10A

Out of scope for CONTROL-LOOP-10A:

* launcher code implementation;
* launcher execution;
* runner implementation;
* scheduler integration;
* night run execution;
* bridge execution;
* runtime handoff file creation;
* auto-launch of Claude Code or other AI tools;
* push, merge, or deploy;
* modifying source code, tests, or tools.

---

## 27. Acceptance criteria

CONTROL-LOOP-10A is complete when:

1. This contract exists and documents the minimal controlled launcher, human
   approval model, single-shot boundary, package input contract, approval artifact
   contract, preflight gates, hash verification, output contract, STOP conditions,
   failure handling, repository policy, runtime artifact policy, and future phases.
2. `docs/control-loop/control-loop-10.yaml` exists with valid ID, role, mode, and
   status.
3. The contract states that CONTROL-LOOP-10A is spec-only and does not implement
   or execute the launcher.
4. No runtime files are created in this phase.
5. Primary repo remains untouched.

---

## Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-28 | Initial draft. Phase 10A = minimal controlled launcher contract/spec only. |
