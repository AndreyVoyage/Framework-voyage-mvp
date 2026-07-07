> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 6 - WORK<->CODE BRIDGE CONTRACT

> Specification for CONTROL-LOOP-6B: file-based Work<->Code bridge contract,
> selectable mode config, and tracked handoff templates.
>
> Status: **DRAFT / Phase 6B**.
> Baseline: `origin/main` at `a4112b4`.
>
> This document defines the bridge. It does not execute the bridge.

---

## 1. Purpose

CONTROL-LOOP-6 defines a limited Work<->Code bridge for controlled local
handoff. The bridge is file-based first: Work writes a next action, Code executes
only that next action, Code writes a report, and Work audits the report before
any continuation decision.

This phase is docs/spec/templates only. It does not implement a runner, does not
auto-launch Claude Code, does not invoke Claude/Codex/Kimi, does not run
overnight, and does not create scheduler integration.

---

## 2. Current baseline

Confirmed baseline for this phase:

* CONTROL-LOOP-1/2/3/4 are closed in `origin/main`.
* CONTROL-LOOP-5A planning is done.
* CONTROL-LOOP-5B contract/spec is closed in `origin/main`.
* `origin/main`: `a4112b4` (`docs: add control loop overnight dry-run contract`).
* Primary repo branch: `main`.
* Auto worktree branch: `auto/nightly-20260627`.
* Auto worktree HEAD: `a4112b4`.
* CONTROL-LOOP-6A Planning Review verdict: A.
* CONTROL-LOOP-6A recommended next step: contract/spec only.

Before any future bridge run, both primary repo and auto worktree must be clean
and the baseline commit must be verified with `git rev-parse`.

---

## 3. Manual vs automatic modes

`manual_relay` remains permanent and default. Automatic modes do not replace
manual mode.

`manual_relay` is required for:

1. main repo operations;
2. merge;
3. push;
4. deploy;
5. risky code;
6. first run of any new phase;
7. unexpected state;
8. any mismatch in hashes, turn ownership, cycle, task id, or baseline.

Automatic modes are optional future operating profiles. They are constrained by
the selected mode, risk level, file scope, human gate, and one-shot limits.

---

## 4. Mode selector

The tracked selector is `docs/control-loop/loop-config.yaml`.

Allowed modes:

| Mode | Purpose | Continuation |
|---|---|---|
| `manual_relay` | Human copies prompts/reports between Work and Code. | Human-controlled only. |
| `assisted_handoff` | Work writes next action and Code report manually. | Human-controlled only. |
| `bridge_one_shot` | One file-based Work->Code->Work cycle. | Must stop after one Code report. |
| `supervised_loop` | Future supervised multi-cycle loop. | Out of scope for CL6 execution. |
| `overnight_autonomous` | Future unattended profile. | Out of scope for CL6 execution. |

CONTROL-LOOP-6 defines these modes but does not run them.

---

## 5. File-based handoff protocol

The first bridge mode is file-based.

Runtime handoff files are:

* `docs/handoff/NEXT_ACTION.md`
* `docs/handoff/LATEST_AGENT_REPORT.md`
* `docs/handoff/MORNING_REPORT.md`

This phase creates templates only and must not create runtime handoff files.

Protocol:

1. Work writes `NEXT_ACTION.md` from `NEXT_ACTION_TEMPLATE.md`.
2. `turn: code` means Code may act.
3. Code executes only the next action.
4. Code writes `LATEST_AGENT_REPORT.md` from `LATEST_AGENT_REPORT_TEMPLATE.md`.
5. `turn: work` means Work may audit.
6. Work reads the report and decides STOP, PASS, FAIL, or needs clarification.
7. In `bridge_one_shot`, Work must stop after one report even if the report
   passes.

---

## 6. `NEXT_ACTION.md` schema

Required YAML frontmatter fields:

```yaml
schema: voyage.next_action.v1
cycle: 1
task_id: VF-000
mode: bridge_one_shot
baseline_commit: "<real git rev-parse hash>"
checkpoint_tag: "<checkpoint tag or none>"
auto_branch: auto/nightly-20260627
worktree: C:/DEV/FRAMEWORK/Framework-voyage-mvp-auto-night
risk: docs-only
allowed_files: []
forbidden_paths: []
gates: []
acceptance: []
stop_conditions: []
expires_at: "YYYY-MM-DDTHH:MM:SSZ"
turn: code
```

Body requirements:

* plain-language task description;
* exact allowed file scope;
* explicit forbidden actions;
* expected report path.

---

## 7. `LATEST_AGENT_REPORT.md` schema

Required YAML frontmatter fields:

```yaml
schema: voyage.agent_report.v1
cycle: 1
task_id: VF-000
status: stopped
baseline_commit: "<echo from NEXT_ACTION.md>"
auto_commit: "<real git rev-parse hash or none>"
files_changed: []
gates: []
primary_untouched: true
origin_untouched: true
secrets_untouched: true
voyage_untouched: true
anomalies: []
recommended_next: stop
turn: work
```

Body requirements:

* summary of actions;
* evidence;
* deviations;
* validation results;
* recommended next action.

---

## 8. `MORNING_REPORT.md` schema

Required report fields:

* run date/time;
* mode;
* baseline commit;
* checkpoint;
* cycles attempted;
* tasks attempted;
* tasks passed;
* tasks failed;
* tasks stopped;
* auto commits;
* rollback performed YES/NO;
* anomalies;
* human decision recommendation;
* explicit statement that no push, merge, or deploy occurred.

---

## 9. Turn ownership rules

The `turn:` token controls ownership:

* `turn: code` means Code may act and write a report.
* `turn: work` means Work may audit and decide.
* Any mismatched turn means STOP.

`cycle`, `task_id`, and `baseline_commit` must echo-match between request and
report. Any mismatch means STOP.

---

## 10. Work role responsibilities

Work is responsible for:

1. selecting the mode;
2. writing the next action;
3. verifying baseline hashes with real `git rev-parse`;
4. defining allowed files and forbidden paths;
5. defining gates and acceptance criteria;
6. reading Code reports;
7. deciding STOP, PASS, FAIL, or needs clarification;
8. producing morning/stop reports when required.

Work must not ask Code to exceed the selected mode.

---

## 11. Code role responsibilities

Code is responsible for:

1. acting only when `turn: code`;
2. executing only the next action;
3. respecting allowed files and forbidden paths;
4. stopping on unexpected state;
5. running only approved gates;
6. writing the report;
7. using real hashes from `git rev-parse`;
8. leaving merge, push, deploy, and risky operations to human approval.

Code must not continue to a second task unless a later approved mode explicitly
allows it.

---

## 12. When Work may produce the next prompt

Work may produce a next prompt only if all are true:

1. report `turn` is `work`;
2. cycle, task id, and baseline commit echo-match;
3. real hash verification passes;
4. no forbidden files were touched;
5. no secrets were read or printed;
6. gates and acceptance criteria pass;
7. selected mode allows continuation;
8. human approval is present when required.

In `bridge_one_shot`, continuation is forbidden even after a passing report.

---

## 13. When Work must STOP

Work must STOP if:

* turn token is wrong;
* cycle, task id, or baseline commit does not echo-match;
* any hash is synthetic, missing, shortened when full hash is required, or not
  verified by `git rev-parse`;
* primary repo is touched without approval;
* forbidden paths are touched;
* `.env` or secrets are read;
* `.voyage` runtime files are mutated;
* push, merge, deploy, SSH, Docker, Certbot, branch/tag/worktree deletion, or
  global git config modification is attempted;
* the mode is `bridge_one_shot` and one report has already been produced;
* state is unexpected.

---

## 14. Limits per mode

| Mode | Max cycles | Max tasks | Risk | Human gate |
|---|---:|---:|---|---|
| `manual_relay` | 1 | 1 | `report-only` by default | required |
| `assisted_handoff` | 1 | 1 | `docs-only` max in CL6 | required |
| `bridge_one_shot` | 1 | 1 | `docs-only` max in CL6 | required |
| `supervised_loop` | not authorized in CL6 | not authorized in CL6 | out of scope | required |
| `overnight_autonomous` | not authorized in CL6 | not authorized in CL6 | out of scope | required |

CL6 bridge is one-shot first: `max_cycles: 1`, `max_tasks: 1`. Even if the
report passes, Work must STOP after one cycle.

---

## 15. Hash verification rules

Hashes in requests and reports must be verified using real `git rev-parse`.
Synthetic hashes must be rejected.

Required checks:

1. `baseline_commit` equals the requested baseline.
2. `auto_commit`, when present, equals `git rev-parse HEAD` in the auto
   worktree.
3. `origin/main`, when referenced, is verified with `git rev-parse origin/main`
   or `git ls-remote origin refs/heads/main`.
4. Short hashes are acceptable only for display, never for machine decisions.

---

## 16. File/write policy

File writes are allowed only in the auto worktree and only inside the explicit
allowed file list for the current next action.

Primary repo remains read-only unless a human explicitly approves a main repo
operation through `manual_relay`.

Reports and handoff files must be UTF-8. Future PowerShell runner scripts must be
pure ASCII.

---

## 17. Safety boundary

The autonomy boundary is:

```text
auto branch + report
```

The bridge may produce a report on the auto branch. It may not push, merge,
deploy, delete branches/tags/worktrees, read secrets, mutate `.voyage` runtime
state, or modify global git config.

---

## 18. Human approval gates

Human approval is required for:

1. switching away from `manual_relay`;
2. first run of any new phase;
3. any merge;
4. any push;
5. any deploy;
6. risky code;
7. scheduler setup;
8. overnight execution;
9. branch/tag/worktree deletion;
10. rollback execution.

Merge, push, and deploy always require human approval.

---

## 19. Explicitly forbidden actions

CONTROL-LOOP-6 forbids:

* automatic push;
* automatic merge;
* automatic merge to main;
* deploy;
* SSH;
* Docker;
* Certbot;
* `.env` read;
* `.voyage` runtime mutation;
* branch/tag/worktree deletion;
* global git config modification;
* unlimited loops;
* automatic scheduler integration;
* night run execution;
* bridge execution in this phase;
* Claude/Codex/Kimi auto-launch in this phase;
* runner implementation in this phase.

---

## 20. Out of scope for CONTROL-LOOP-6

Out of scope:

* runner code;
* bridge execution;
* auto-launching Claude Code;
* invoking Claude, Codex, Kimi, or other AI bridge;
* scheduler integration;
* night run execution;
* automatic push or merge;
* deploy;
* multi-task autonomous loops;
* modifying runtime handoff files.

---

## 21. Future CONTROL-LOOP-7/8 items

| Phase | Candidate capability |
|---|---|
| CONTROL-LOOP-7 | Implement a dry-run runner skeleton that reads templates and validates mode config without launching AI tools. |
| CONTROL-LOOP-8 | Add supervised bridge execution with human approval gates and explicit one-shot stop behavior. |
| CONTROL-LOOP-9 | Consider scheduler wrappers only after multiple supervised runs pass. |

---

## Acceptance criteria

CONTROL-LOOP-6B is complete when:

1. This contract exists.
2. `docs/control-loop/control-loop-6.yaml` exists.
3. `docs/control-loop/loop-config.yaml` exists with `manual_relay` default.
4. The three handoff templates exist.
5. The contract documents mode selector, schemas, turn ownership, hash
   verification, one-shot limits, file policy, safety boundary, human gates,
   forbidden actions, and future items.
6. No runner, scheduler, auto-launch, bridge execution, night run, push, or merge
   is implemented.
