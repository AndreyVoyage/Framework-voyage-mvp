# PROMPT: Phase 29 — Version Bump to 4.3.0

## Role

You are an implementation agent.
You update only `pyproject.toml` and `voyage_framework/__init__.py` to bump the package version from `4.0.0` to `4.3.0`.
You do NOT create tags. You do NOT run release, deploy, or publish commands. You do NOT touch the release workflow.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 29 — Version Bump to 4.3.0

---

## Background

Phase 27 (`docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`) identified two BLOCKERs for the `v4.3.0` tag:

1. **Version mismatch** — `pyproject.toml` and `voyage_framework/__init__.py` remain at `4.0.0`. Phase 29 resolves this.
2. **Release workflow safety** — Resolved in Phase 28.

Phase 28 merged to `main` at `2054524`. Phase 28 implemented:
- `workflow_dispatch` trigger with `dry_run` boolean input (`default: true`)
- `environment: release` on the release job
- `Create GitHub Release` step gated on `github.event_name == 'push' && github.ref_type == 'tag'`
- PyPI publish remains commented out

Phase 29 resolves BLOCKER 1 only (version mismatch). The `v4.3.0` tag remains NOT authorized after Phase 29.

---

## Required input files

Read and analyze all of the following before implementing:

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `.github/workflows/release.yml`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## FORBIDDEN — do NOT do any of the following

- Edit `.github/workflows/*` or any release workflow file
- Edit test files unless explicitly required by a version-test failure (document any such case)
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`, or any documentation page other than the Phase 29 report
- Create any git tag
- Create the `v4.3` or `v4.3.0` tag
- Run release, deploy, or publish commands
- Run the GitHub Actions release workflow
- Push to `main`
- Merge any branch
- Force-push

---

## Required implementation

### 1. Update `pyproject.toml`

Change the version field:

```
version = "4.0.0"  →  version = "4.3.0"
```

Do not change any other lines in `pyproject.toml`.

### 2. Update `voyage_framework/__init__.py`

Change the `__version__` assignment:

```
__version__ = "4.0.0"  →  __version__ = "4.3.0"
```

Do not change any other lines in `voyage_framework/__init__.py`.

### 3. Atomic commit

Both version changes must be in one atomic commit. Do not split into two commits.

### 4. Documentation version references

Do not update docs version references (README, CHANGELOG, etc.) unless they are strict package metadata blockers — i.e., tests fail because they assert the version string from `__version__` and the test expected value does not match. If a doc-only reference would cause a test failure, document it in the report and update only the failing assertion, nothing else.

### 5. Build validation

After the version bump, run:

```powershell
.venv\Scripts\python.exe -m build
```

Confirm that the generated artifact names contain `4.3.0`:

```
dist/voyage_framework-4.3.0-*.whl
dist/voyage_framework-4.3.0.tar.gz
```

If `build` is not installed in the venv, install it first:

```powershell
.venv\Scripts\pip.exe install build
```

Then run:

```powershell
.venv\Scripts\python.exe -m twine check dist/*
```

Confirm zero errors. Document the exact artifact names in the report.

### 6. No tag, no release

Do not create or push `v4.3.0` or any other tag. Do not run the GitHub release workflow.

---

## Required git/version checks

Run these commands before making any edits and include their output verbatim in the report:

```bash
git status --short
git --no-pager log --oneline --decorate -15
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

### Version scan before edit

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0|v4\.3|v4.3|tag|release" -- pyproject.toml voyage_framework/__init__.py docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md || true
```

### Post-edit version scan

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0" -- pyproject.toml voyage_framework/__init__.py || true
```

Expected: no `4.0.0` in either file; `4.3.0` present in both.

### Validation commands

```powershell
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m ruff check voyage_framework/__init__.py
.venv\Scripts\python.exe -m mypy voyage_framework/__init__.py
```

If `ruff` does not accept `pyproject.toml` as a lint target, run it only on `voyage_framework/__init__.py` and document the deviation in the report.

### Post-edit diff scope

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed files only:

```
M       pyproject.toml
M       voyage_framework/__init__.py
A       docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md
```

### Forbidden files check

```bash
git diff -- README.md
git diff -- docs/README.md
git diff -- AGENTS.md
git diff -- .github
git diff -- tests
git diff -- docs/prompts
git diff -- docs/handoff/README.md
git diff -- tools
git diff -- docs/index.md
git diff -- docs/FAQ.md
git diff -- docs/_config.yml
git diff -- .gitignore
```

Expected: no output for all forbidden paths.

### Tag check

```bash
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git rev-list -n 1 v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
git rev-list -n 1 v4.2.0-adapter-contract
```

Expected: no `v4.3*` tag; `v4.1.0-mvp` and `v4.2.0-adapter-contract` unchanged.

---

## Classification scheme

Every finding and check result must be classified as one of:

| Label | Meaning |
|-------|---------|
| `SAFE` | Implemented or intentionally unchanged and not blocking |
| `WARNING` | Safe but needs later human or repository-setting verification |
| `BLOCKER` | Prevents Phase 30 (dry-run) or future tag authorization |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md
```

Also write:

- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked files that may change:

```
pyproject.toml
voyage_framework/__init__.py
docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md
```

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` must use exactly this structure:

```markdown
# Phase 29 Version Bump to 4.3.0 Report

## Scope
-

## Inputs
-

## Version before
- pyproject.toml:
- voyage_framework/__init__.py:

## Changes implemented
-

## Version after
- pyproject.toml:
- voyage_framework/__init__.py:

## Validation checks
-

## Forbidden files check
-

## Tag check
-

## Release workflow status
-

## Remaining blockers
-

## Next phase
-

## v4.3.0 authorization
- Authorized now: no
- Reason:

## Risks / deviations
-

## Verdict
A. Version bump implemented, ready for dry-run phase
B. Version bump implemented with safe warnings
C. Implementation blocked
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

## Commit message (for use by the implementation agent, after checks pass)

```
release: bump version to 4.3.0
```

---

## Short terminal response format

Return only:

```markdown
# Phase 29 Implementation Summary

- Branch:
- Changed files:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
