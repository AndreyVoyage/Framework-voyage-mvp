# VOYAGE CONTROL LOOP 10C - IMPLEMENTATION PLAN FOR MINIMAL CONTROLLED LAUNCHER

> Implementation plan/spec for CONTROL-LOOP-10C.
>
> Status: **DRAFT / Phase 10C**.
> Baseline: `origin/main` at `0e160fc`.
>
> This document defines the first implementation slice. It does not implement any
> code, tests, or CLI changes.

---

## 1. Title

CONTROL-LOOP-10C: Implementation Plan for Minimal Controlled Launcher.

---

## 2. Purpose

CONTROL-LOOP-10C defines the exact first implementation slice for the minimal
controlled launcher. It specifies which files will be created or modified in the
next phase (CONTROL-LOOP-10D), what the launcher must and must not do, and how it
will be tested.

This phase is plan/spec-only. No code, tests, CLI changes, or runtime files are
produced in 10C.

---

## 3. Baseline

Confirmed baseline:

* CONTROL-LOOP-10A is closed in `origin/main`.
* `origin/main`: `0e160fc` (`docs: define minimal controlled launcher contract`).
* Primary repo branch: `main`.
* Auto worktree branch: `auto/nightly-20260627`.
* No runtime artifacts remain in the auto worktree.

---

## 4. Relationship to CONTROL-LOOP-10A

CONTROL-LOOP-10A defined the contract for the minimal controlled launcher.
CONTROL-LOOP-10C turns that contract into a concrete implementation plan without
writing code. The contract remains the source of truth; this plan must not
contradict it.

---

## 5. Relationship to CONTROL-LOOP-10B

CONTROL-LOOP-10B performed a read-only implementation preflight and identified
likely implementation targets:

* `voyage_framework/core/launcher.py`
* `voyage_framework/cli.py`
* `tests/unit/test_launcher.py`
* `tests/integration/test_launcher_cli.py`

CONTROL-LOOP-10C adopts these targets and defines their exact contracts.

---

## 6. Implementation philosophy

* **Python-first**: the first code slice is pure Python for testability and
  integration with existing `voyage_framework/core/` components.
* **Thin CLI**: the launcher is exposed through a minimal argparse subcommand in
  `voyage_framework/cli.py`.
* **Dry-run first**: the first implementation is report-only and performs no file
  mutations, no AI invocation, and no auto-launch.
* **Single-shot**: one launch, one task, one report, then exit.
* **Human gate**: every future launcher run requires an explicit human approval
  artifact.
* **Manual relay preserved**: `manual_relay` remains permanently available and is
  never replaced by the launcher.

---

## 7. First implementation slice definition

CONTROL-LOOP-10D will implement:

1. `RuntimePackage` parsing from a package directory.
2. `HumanApproval` parsing.
3. YAML frontmatter extraction from `NEXT_ACTION.md`.
4. Full hash validation using `git rev-parse`.
5. Synthetic hash rejection.
6. Preflight gates.
7. Single-shot validation.
8. Dry-run/report-only output generation (`LATEST_AGENT_REPORT.md`).
9. No subprocess agent launch.
10. No actual AI invocation.
11. No scheduler, no night mode, no bridge loop.
12. No automatic commit, push, merge, or deploy.

---

## 8. Explicit non-goals

The first implementation slice must not:

* implement a PowerShell wrapper;
* invoke Claude Code or any other AI tool;
* execute the bridge;
* run overnight;
* create scheduler integration;
* modify files beyond the single report output;
* read `.env` or secrets;
* mutate `.voyage` runtime state;
* push, merge, commit, or deploy;
* delete branches, tags, or worktrees;
* modify global git config.

---

## 9. Future files allowed to be touched in 10D

CONTROL-LOOP-10D is allowed to create or modify only:

1. `voyage_framework/core/launcher.py`
2. `voyage_framework/cli.py`
3. `tests/unit/test_launcher.py`
4. `tests/integration/test_launcher_cli.py`

No other tracked files may be modified without a separate approved phase.

---

## 10. Future files forbidden in 10D

CONTROL-LOOP-10D must not touch:

* `docs/control-loop/CONTROL_LOOP_10_MINIMAL_CONTROLLED_LAUNCHER.md`
* `docs/control-loop/control-loop-10.yaml`
* existing CONTROL-LOOP-1/2/3/4/5/6/7/8/9 files
* `docs/handoff/`
* `logs/` except temporary test fixture directories
* `.voyage/`
* `.env`
* `tools/`
* `pyproject.toml`
* source code outside the launcher/CLI scope
* tests outside the launcher scope

---

## 11. Launcher module contract

`voyage_framework/core/launcher.py` will provide:

* `RuntimePackage` — dataclass/Pydantic model parsed from a package directory.
* `HumanApproval` — dataclass/Pydantic model parsed from `HUMAN_APPROVAL.md`.
* `Launcher` — class that runs preflight gates and produces a dry-run report.
* `LauncherError` — exception for STOP conditions.

The launcher must:

* accept `primary_repo`, `auto_worktree`, `package_dir`, and `expected_origin_main`
  as inputs;
* reject short hashes;
* verify `expected_origin_main` against `git rev-parse origin/main`;
* verify `baseline_commit` in the package against `git rev-parse HEAD` in the
  target worktree;
* write only `LATEST_AGENT_REPORT.md` inside the package directory;
* refuse if `LATEST_AGENT_REPORT.md` already exists;
* refuse if `MORNING_REPORT.md` exists;
* refuse if a second `NEXT_ACTION` exists;
* never create `MORNING_REPORT.md`;
* never create a second `NEXT_ACTION`;
* never push, merge, commit, or deploy;
* exit non-zero on failed gates.

---

## 12. CLI integration contract

`voyage_framework/cli.py` will add a `launcher` subcommand group:

```text
voyage launcher dry-run \
  --package <runtime_package_dir> \
  --primary-repo <primary_repo> \
  --auto-worktree <auto_worktree> \
  --expected-origin-main <full_hash>
```

CLI behavior:

* all four arguments are required;
* `--expected-origin-main` must be a full 40-character hex hash;
* the CLI delegates to `Launcher.dry_run()`;
* it prints the report path on success;
* it exits non-zero and prints the STOP reason on failure.

---

## 13. Runtime package contract

The runtime package is a directory containing exactly:

* `NEXT_ACTION.md` with YAML frontmatter matching
  `schema: voyage.next_action.v1`.
* `HUMAN_APPROVAL.md` with explicit approval text and reference to the package.

The package location for the first test/demo run is:

```text
logs/handoff/CONTROL_LOOP_10D/
```

The launcher must reject packages containing:

* synthetic hashes;
* forbidden paths (`.env`, `.voyage/`, `tools/`, `tests/`,
  `voyage_framework/`, primary repo files);
* more than one `NEXT_ACTION`;
* missing `HUMAN_APPROVAL`.

---

## 14. Human approval contract

`HUMAN_APPROVAL.md` must:

* be authored by the approving human;
* reference the exact package directory path;
* reference the exact baseline commit hash;
* state the approved risk level (`report-only` for the first slice);
* list allowed files;
* list forbidden paths;
* contain the exact phrase "I approve this launcher run";
* be present before the launcher reads the package.

The launcher must reject any package without a valid approval artifact.

---

## 15. Output report contract

The launcher may produce only one output file per run:

* `LATEST_AGENT_REPORT.md` inside the package directory.

The report must:

* include YAML frontmatter `schema: voyage.agent_report.v1`;
* echo `cycle`, `task_id`, and `baseline_commit` from `NEXT_ACTION.md`;
* set `turn: work`;
* state that the run was dry-run/report-only;
* confirm `primary_untouched`, `origin_untouched`, `secrets_untouched`, and
  `voyage_untouched` are all `true`;
* list any anomalies or STOP reasons;
* recommend `stop` for the first slice.

---

## 16. Preflight gate contract

Before producing a report, the launcher must pass these gates:

1. Primary repo is on `main` and clean.
2. Auto worktree is on `auto/nightly-20260627` and clean.
3. `origin/main` matches the provided `expected_origin_main` hash.
4. Package directory exists and contains exactly one `NEXT_ACTION.md`.
5. `HUMAN_APPROVAL.md` exists and is valid.
6. `NEXT_ACTION.md` frontmatter parses and has `turn: code`.
7. `baseline_commit` in the package matches `git rev-parse HEAD` in the
   target worktree.
8. Allowed files are inside the auto worktree.
9. Forbidden paths include `.env`, `.voyage/`, `tools/`, `tests/`,
   `voyage_framework/`, and primary repo files.
10. Risk level is `report-only` for the first slice.

Any gate failure is a STOP condition.

---

## 17. Hash verification contract

The launcher must verify hashes with real `git rev-parse`:

1. `expected_origin_main` equals `git rev-parse origin/main` in the primary repo.
2. `baseline_commit` equals `git rev-parse HEAD` in the target worktree.
3. Synthetic hashes are rejected.
4. Short hashes are rejected for machine decisions (full 40-character hex
   required).

---

## 18. Single-shot enforcement contract

The launcher is single-shot:

* `max_cycles: 1`
* `max_tasks: 1`
* After writing `LATEST_AGENT_REPORT.md`, the launcher exits.
* The launcher refuses to run if `LATEST_AGENT_REPORT.md` already exists.
* The launcher never reads its own output as a new input.

---

## 19. Failure/STOP behavior

On any STOP condition:

1. Do not write `LATEST_AGENT_REPORT.md`.
2. Print a concise STOP reason to stderr.
3. Exit with a non-zero code.
4. Do not retry.
5. Do not push, merge, commit, or deploy.

---

## 20. Test plan

`tests/unit/test_launcher.py` will cover:

* successful parsing of a valid `RuntimePackage`;
* rejection of missing `NEXT_ACTION.md`;
* rejection of missing `HUMAN_APPROVAL.md`;
* rejection of invalid approval text;
* rejection of synthetic `baseline_commit`;
* rejection of short hashes;
* rejection of forbidden paths in `allowed_files`;
* rejection when `LATEST_AGENT_REPORT.md` already exists;
* successful dry-run report generation.

Tests must use `tmp_path` for package directories and `monkeypatch` or
`subprocess` mocks for `git rev-parse` calls.

---

## 21. CLI test plan

`tests/integration/test_launcher_cli.py` will cover:

* CLI rejects missing `--package`;
* CLI rejects missing `--expected-origin-main`;
* CLI rejects short `--expected-origin-main`;
* CLI rejects non-existent package directory;
* CLI produces a report for a valid dry-run package using `tmp_path`;
* CLI exits non-zero on a failed gate.

---

## 22. Security constraints

The launcher must:

* never read `.env` or any file named like a secret;
* never write to `.voyage/`;
* never modify global git config;
* never execute arbitrary shell commands from the package;
* never invoke external AI tools;
* validate all paths are within allowed scopes.

---

## 23. Repository/worktree constraints

The launcher must:

* work only inside the auto worktree for any file operations;
* keep primary repo `main` read-only;
* not create, delete, or modify branches, tags, or worktrees;
* not run `git clean`, `git reset`, or rollback commands.

---

## 24. Windows path and UTF-8 constraints

* All paths must be handled with `pathlib.Path` for cross-platform safety.
* All report and package files must be read and written as UTF-8.
* Hashes must be compared case-insensitively (git rev-parse returns lowercase).
* Line endings may be normalized by Git; diffs must use `git diff --check`.

---

## 25. Out of scope for 10C

CONTROL-LOOP-10C does not:

* implement code;
* implement tests;
* modify CLI;
* create runtime files;
* execute the launcher;
* define scheduler or overnight behavior;
* define bridge-loop behavior;
* define PowerShell wrapper behavior.

---

## 26. Acceptance criteria

CONTROL-LOOP-10C is complete when:

1. This implementation plan exists and defines the first slice.
2. `docs/control-loop/control-loop-10c.yaml` exists with valid metadata.
3. The plan limits 10D file scope to exactly four files.
4. The plan defines parsing, gates, hash verification, single-shot enforcement,
   dry-run output, test plans, and security constraints.
5. The plan forbids AI invocation, scheduler, night mode, bridge loop, and
   push/merge/commit/deploy.
6. No code, tests, or CLI changes are made in 10C.

---

## 27. Proposed next phase: CONTROL-LOOP-10D

CONTROL-LOOP-10D will implement the first code slice:

* create `voyage_framework/core/launcher.py`;
* add `launcher dry-run` command to `voyage_framework/cli.py`;
* create `tests/unit/test_launcher.py`;
* create `tests/integration/test_launcher_cli.py`;
* perform dry-run test with a `tmp_path` package.

No runtime handoff files will be created unless a separate approved phase
explicitly changes the policy.

---

## Change Log

| Version | Date | Notes |
|---|---|---|
| 0.1 | 2026-06-28 | Initial draft. Phase 10C = implementation plan/spec only. |
