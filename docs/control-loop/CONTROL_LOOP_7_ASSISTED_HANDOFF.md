> **[NOT IMPLEMENTED — FUTURE SPEC ONLY — DO NOT EXECUTE]**
> This document describes a planned phase of the Voyage Control Loop that has not been implemented.
> Phase 1 (`control-loop-1.yaml` + `CONTROL_LOOP_SPEC.md`) is the only currently active control-loop surface.
> See `docs/control-loop/CONTROL_LOOP_SPEC.md` §10 for Phase 1 deliverables.
>
> Status: NOT IMPLEMENTED | Target horizon: F8+ | Last reviewed: 2026-07-06

---

# VOYAGE CONTROL LOOP 7A - ASSISTED HANDOFF DRY-RUN CONTRACT

> Specification for CONTROL-LOOP-7A: the first assisted handoff dry-run contract.
>
> Status: **DRAFT / Phase 7A**.
> Baseline: `origin/main` at `c0e674a`.
>
> This document defines the dry-run. It does not execute the dry-run and does not
> create runtime handoff files.

---

## 1. Purpose

CONTROL-LOOP-7A defines the first assisted handoff dry-run. In this mode, Work
writes a `NEXT_ACTION` handoff file, Andrey manually launches Code, Code executes
the single approved action, Code writes a `LATEST_AGENT_REPORT`, and Work produces
a final `MORNING_REPORT` or stop summary.

This phase is contract/spec only. It does not create runtime handoff files, does
not auto-launch Claude Code, does not run an autonomous loop, does not run
overnight, and does not create scheduler integration.

---

## 2. Current baseline

Confirmed baseline for this phase:

* CONTROL-LOOP-1/2/3/4/5/6 are closed in `origin/main`.
* `origin/main`: `c0e674a` (`docs: add control loop bridge contract`).
* Primary repo branch: `main`.
* Auto worktree branch: `auto/nightly-20260627`.
* Auto worktree HEAD: `c0e674a`.

Before any future assisted handoff dry-run, both primary repo and auto worktree
must be clean and the baseline commit must be verified with `git rev-parse`.

---

## 3. Relationship to CONTROL-LOOP-6 bridge contract

CONTROL-LOOP-6 defined the bridge contract, mode selector, and handoff templates.
CONTROL-LOOP-7A specializes the first operational mode: `assisted_handoff`.

The assisted handoff mode uses the schemas from CONTROL-LOOP-6 but adds explicit
human routing rules and a one-shot execution boundary.

---

## 4. Assisted handoff model

`manual_relay` remains the default and permanent mode. `assisted_handoff` is an
optional, human-gated operating profile.

In `assisted_handoff`:

1. Work writes `NEXT_ACTION.md` in the approved runtime location.
2. Andrey manually launches Code with the next action.
3. Code executes only the next action.
4. Code writes `LATEST_AGENT_REPORT.md` in the approved runtime location.
5. Work reads the report and decides STOP, PASS, FAIL, or needs clarification.
6. Work writes `MORNING_REPORT.md` or a stop summary.
7. Andrey pastes the final report into ChatGPT / Voyage Control.

Code must not report directly to ChatGPT. Work must not auto-send to Code. Andrey
is the human gate for every launch and every paste.

---

## 5. Human routing / where answers go

Answer routing for the first assisted handoff dry-run:

* Work produces written artifacts only.
* Code produces written artifacts only.
* Andrey moves artifacts between Work and Code by manual copy/paste or file share.
* ChatGPT / Voyage Control remains the final audit layer.
* No direct API or automated message passing between Work and Code.
* No automatic publication to origin/main, issues, chat channels, or email.

---

## 6. Runtime artifact policy

This phase defines, but does not create, the runtime location for the first
dry-run.

Runtime directory:

```text
logs/handoff/CONTROL_LOOP_7B/
```

Runtime files for the later phase:

```text
logs/handoff/CONTROL_LOOP_7B/NEXT_ACTION.md
logs/handoff/CONTROL_LOOP_7B/LATEST_AGENT_REPORT.md
logs/handoff/CONTROL_LOOP_7B/MORNING_REPORT.md
```

Rules:

* These files are runtime artifacts.
* They are not created in CONTROL-LOOP-7A.
* They are not committed unless a later human-approved phase explicitly changes the
  policy.
* They are used to preserve the chain and avoid losing answers.
* They are copied/pasted through Andrey as the human gate.

`.voyage/` runtime databases must not be used for handoff files in this phase.

---

## 7. Runtime file paths for first dry-run

The first dry-run uses the runtime directory defined in §6.

Path conventions:

* `NEXT_ACTION.md` is the input to Code.
* `LATEST_AGENT_REPORT.md` is the output from Code.
* `MORNING_REPORT.md` is the final summary from Work.

All paths are local to the auto worktree or a local `logs/` directory. No remote
paths are allowed.

---

## 8. NEXT_ACTION creation rules

Work may create `NEXT_ACTION.md` only if:

1. `manual_relay` or `assisted_handoff` is selected in `loop-config.yaml`.
2. Primary repo and auto worktree are clean.
3. Baseline commit is verified with `git rev-parse`.
4. Allowed files and forbidden paths are explicitly listed.
5. `turn: code` is set.
6. `cycle`, `task_id`, and `baseline_commit` are filled with real values.
7. The task is one-shot: `max_cycles: 1`, `max_tasks: 1`.

`NEXT_ACTION.md` must be UTF-8 and must not contain secrets.

---

## 9. LATEST_AGENT_REPORT creation rules

Code may create `LATEST_AGENT_REPORT.md` only if:

1. `turn: code` was set in `NEXT_ACTION.md`.
2. Code executed only the approved action.
3. No forbidden files were touched.
4. All gates were run or explicitly skipped with reason.
5. `turn: work` is set in the report.
6. `cycle`, `task_id`, and `baseline_commit` echo-match `NEXT_ACTION.md`.
7. Hashes come from real `git rev-parse`; synthetic hashes are invalid.

`LATEST_AGENT_REPORT.md` must be UTF-8 and must not contain secrets.

---

## 10. MORNING_REPORT creation rules

Work may create `MORNING_REPORT.md` only if:

1. `turn: work` was set in `LATEST_AGENT_REPORT.md`.
2. The report was audited.
3. Work has decided STOP, PASS, FAIL, or needs clarification.
4. No continuation is attempted in this one-shot dry-run.

`MORNING_REPORT.md` must include:

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

## 11. Turn-token flow

The `turn:` token controls ownership:

* `turn: code` in `NEXT_ACTION.md` means Code may act and write a report.
* `turn: work` in `LATEST_AGENT_REPORT.md` means Work may audit and decide.
* Any mismatched turn means STOP.

Flow:

1. Work writes `NEXT_ACTION.md` with `turn: code`.
2. Andrey launches Code.
3. Code writes `LATEST_AGENT_REPORT.md` with `turn: work`.
4. Work reads and writes `MORNING_REPORT.md`.
5. Andrey pastes the final report into ChatGPT / Voyage Control.

---

## 12. Validation gates before Code launch

Before Andrey launches Code:

1. Primary repo is on `main` and clean.
2. Auto worktree is on `auto/nightly-20260627` and clean.
3. `loop-config.yaml` mode is `manual_relay` or `assisted_handoff`.
4. `NEXT_ACTION.md` exists and parses.
5. `turn: code` is set.
6. `cycle`, `task_id`, and `baseline_commit` are present.
7. `baseline_commit` matches `git rev-parse HEAD`.
8. Allowed files are inside the auto worktree.
9. Forbidden paths include `.env`, `.voyage/`, primary repo files, tests, tools,
   and source code unless explicitly approved.
10. Human approval is recorded.

---

## 13. Validation gates after Code report

After Code writes `LATEST_AGENT_REPORT.md`:

1. Report exists and parses.
2. `turn: work` is set.
3. `cycle`, `task_id`, and `baseline_commit` echo-match `NEXT_ACTION.md`.
4. `auto_commit`, when present, matches `git rev-parse HEAD` in the auto worktree.
5. `primary_untouched`, `origin_untouched`, `secrets_untouched`, and
   `voyage_untouched` are all `true`.
6. No forbidden files were changed.
7. `git diff --check` would pass on the changed files.
8. Anomalies list is empty or fully explained.
9. Recommended next action is `stop` or `manual review` for this one-shot run.

---

## 14. STOP conditions

Work or Code must STOP if:

* `NEXT_ACTION.md` or `LATEST_AGENT_REPORT.md` is missing or malformed;
* turn token is wrong;
* `cycle`, `task_id`, or `baseline_commit` does not echo-match;
* any hash is synthetic, missing, shortened when full hash is required, or not
  verified by `git rev-parse`;
* primary repo is touched without approval;
* `.env` or secrets are read;
* `.voyage` runtime files are mutated;
* push, merge, deploy, SSH, Docker, Certbot, branch/tag/worktree deletion, or
  global git config modification is attempted;
* timeout is exceeded;
* state is ambiguous or unexpected;
* a second cycle is attempted;
* a forbidden file is modified;
* Code reports directly to ChatGPT;
* Work attempts to auto-launch Code;
* `--no-verify` is requested without explicit human approval.

---

## 15. Hash verification rules

Hashes must be verified using real `git rev-parse`. Synthetic hashes must be
rejected.

Required checks:

1. `baseline_commit` equals the requested baseline.
2. `auto_commit`, when present, equals `git rev-parse HEAD` in the auto worktree.
3. `origin/main`, when referenced, is verified with `git rev-parse origin/main`
   or `git ls-remote origin refs/heads/main`.
4. Short hashes are acceptable only for display, never for machine decisions.

---

## 16. Repository/worktree policy

Work happens only in the auto worktree. Primary repo remains read-only unless a
human explicitly approves a main repo operation through `manual_relay`.

Runtime handoff files are local and untracked. They are not pushed or merged.

---

## 17. Explicitly forbidden actions

CONTROL-LOOP-7A forbids:

* auto-launching Claude Code or any external AI tool;
* executing the bridge in this phase;
* creating runtime handoff files in this phase;
* running an autonomous loop;
* running overnight;
* creating scheduler integration;
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
* using `--no-verify` without explicit human approval;
* Code reporting directly to ChatGPT;
* Work auto-sending prompts to Code.

---

## 18. No `--no-verify` rule

Commit hooks must not be bypassed with `--no-verify` unless a human explicitly
approves the bypass in a separate step. A blocked commit hook is a stop condition.
The correct response is to diagnose and fix the blocker, not to bypass it.

---

## 19. Out of scope for CONTROL-LOOP-7A

Out of scope:

* creating runtime handoff files;
* launching Code;
* executing the Work Code bridge;
* auto-launching Claude Code;
* invoking Claude, Codex, Kimi, or other AI bridge;
* scheduler integration;
* night run execution;
* automatic push or merge;
* deploy;
* multi-task autonomous loops;
* modifying `.voyage` runtime files.

---

## 20. Future CONTROL-LOOP-7B/7C/7D items

| Phase | Candidate capability |
|---|---|
| CONTROL-LOOP-7B | Create the first runtime handoff files in `logs/handoff/CONTROL_LOOP_7B/` and perform a report-only dry-run without launching AI tools. |
| CONTROL-LOOP-7C | Execute one supervised assisted handoff cycle with Andrey launching Code manually and Work auditing the report. |
| CONTROL-LOOP-7D | Harden the assisted handoff stop/escalation rules and add anomaly handling. |

---

## Acceptance criteria

CONTROL-LOOP-7A is complete when:

1. This contract exists and documents the assisted handoff model, human routing,
   runtime artifact policy, file creation rules, turn-token flow, validation
   gates, STOP conditions, hash verification, repository policy, forbidden
   actions, no-`--no-verify` rule, out-of-scope items, and future items.
2. `docs/control-loop/control-loop-7.yaml` exists with valid ID, role, mode, and
   status.
3. Runtime handoff files are defined but not created.
4. No auto-launch, bridge execution, scheduler, night run, push, or merge is
   implemented.
5. Primary repo remains untouched.

---

## Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-27 | Initial draft. Phase 7A = assisted handoff dry-run contract/spec only. |
