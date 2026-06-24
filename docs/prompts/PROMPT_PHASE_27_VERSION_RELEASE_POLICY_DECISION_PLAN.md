# PROMPT: Phase 27 — Version & Release Workflow Policy Decision Plan

## Role

You are a policy analyst and documentation agent.
You do NOT implement anything. You do NOT edit source files, workflow files, or configuration.
You analyze, decide, and document.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 27 — Version & Release Workflow Policy Decision Plan

---

## Background

Phase 26 (`docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md`) found the following blockers:

1. **Version mismatch**: `pyproject.toml` and `voyage_framework/__init__.py` remain at `4.0.0`, but the prospective tag is `v4.3`.
2. **Release workflow risk**: `.github/workflows/release.yml` triggers on `v*` tags and could auto-publish mismatched `4.0.0` artifacts if the `v4.3` tag is created prematurely.

Phase 26 explicitly states:

> `v4.3` tag is NOT authorized.

This phase must not implement any fix. It must analyze and produce a structured policy decision report only.

---

## Output

Create exactly one file:

```
docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md
```

Also write:

- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

Do NOT commit `docs/handoff/LATEST_AGENT_REPORT.md` or `docs/handoff/NEXT_ACTION.md`.

---

## FORBIDDEN — do NOT do any of the following

- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py`
- Edit `.github/workflows/release.yml`
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, or any other documentation pages
- Create any git tag
- Create the `v4.3` tag
- Run release, deploy, or publish commands
- Push to `main`
- Merge any branch
- Run `pip install`, `build`, `twine`, or any package distribution command

Phase 27 is **decision/report-only**. Zero implementation.

---

## Required input files

Read and analyze all of the following before writing the report:

- `docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `.github/workflows/release.yml`
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/FAQ.md`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## Required git/version checks

Run the following commands and include their output in the report:

```bash
git status --short
git --no-pager log --oneline --decorate -15
git tag --list
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

### Version scan

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.1|4\.2|4\.3|v4\.3|v4.3|release|tag" -- pyproject.toml voyage_framework/__init__.py README.md docs/README.md docs/index.md docs/FAQ.md docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md || true
```

### Release workflow scan

```bash
git grep -n -E "on:|tags:|v\*|release|publish|deploy|pypi|twine|build|gh release|create-release|upload-artifact|pages|workflow_dispatch|dry-run|dry_run" -- .github || true
```

### Package build/release scan

```bash
git grep -n -E "build|twine|pypi|publish|release|version|setuptools|wheel|sdist" -- pyproject.toml .github README.md docs/README.md || true
```

### Runtime/generated files check

```bash
git status --short --ignored | grep -E "(\.claude|docs/handoff/LATEST_AGENT_REPORT.md|docs/handoff/NEXT_ACTION.md|docs/handoff/SESSION_EXPORT.md|TASK.md|CONTEXT.json)" || true
```

---

## Goal — questions to answer

Analyze and make a documented policy decision on each of the following:

1. Should the project version become `4.3.0` before the `v4.3` tag is created?
2. Should the tag be `v4.3.0` or `v4.3`?
3. Must `pyproject.toml` and `voyage_framework/__init__.py` be updated together (atomically)?
4. Do `README.md` and other docs references need version alignment before the tag?
5. Must `.github/workflows/release.yml` be changed before any tag is created?
6. Should the release workflow support a manual dry-run mode?
7. Should automatic `v*` publish be disabled or gated behind a manual approval step?
8. What exact rollback policy is needed if a release fails mid-flight?
9. What minimum implementation phases are required before the tag can be authorized?

---

## Classification scheme

Every finding, risk, and check result must be classified as one of:

| Label | Meaning |
|-------|---------|
| `SAFE` | Documented/expected; does not block planning |
| `WARNING` | Does not block planning but must be handled before release |
| `BLOCKER` | Prevents responsible implementation or `v4.3` tag |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` must use exactly this structure:

```markdown
# Phase 27 Version & Release Workflow Policy Decision Plan

## Scope
-

## Current state
-

## Phase 26 blockers
-

## Version inventory
- pyproject.toml:
- voyage_framework/__init__.py:
- README/docs:
- tags:

## Release workflow inventory
-

## Risk analysis
-

## Decision 1: version target
- Decision:
- Rationale:
- Alternatives rejected:

## Decision 2: tag naming
- Decision:
- Rationale:
- Alternatives rejected:

## Decision 3: release workflow policy
- Decision:
- Rationale:
- Alternatives rejected:

## Decision 4: dry-run requirement
- Decision:
- Rationale:
- Evidence required:

## Decision 5: rollback policy
- Decision:
- Rationale:
- Required rollback steps:

## Required implementation phases
-

## Files expected to change in future implementation
-

## Files that must not change
-

## Pre-tag checklist
-

## v4.3 authorization
- Authorized now: no
- Reason:

## Handoff notes
-

## Verdict
A. Policy decisions complete, ready for implementation phase
B. Policy decisions complete with safe warnings
C. Policy decision blocked
```

Fill in every section. Do not leave placeholders.

---

## Handoff requirements

After writing the report:

1. Write `docs/handoff/LATEST_AGENT_REPORT.md` as a full terminal-style final report (UTF-8).
2. Write `docs/handoff/NEXT_ACTION.md` with the recommended next step (UTF-8).
3. Do NOT commit either handoff file.
4. Keep your terminal response short — use the summary format below.

---

## Short terminal response format

Return only:

```markdown
# Phase 27 Decision Plan Summary

- Branch:
- Changed files:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
