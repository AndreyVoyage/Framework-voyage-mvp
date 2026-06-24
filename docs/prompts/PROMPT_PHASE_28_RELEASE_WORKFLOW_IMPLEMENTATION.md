# PROMPT: Phase 28 — Release Workflow Implementation

## Role

You are an implementation agent.
You update only `.github/workflows/release.yml` to make the release workflow safe per the Phase 27 policy decisions.
You do NOT bump versions. You do NOT create tags. You do NOT run release, deploy, or publish commands.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 28 — Release Workflow Implementation

---

## Background

Phase 27 (`docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`) identified two BLOCKERs for the `v4.3.0` tag:

1. **Version mismatch** — `pyproject.toml` and `voyage_framework/__init__.py` remain at `4.0.0`. (Phase 29 will resolve this — not in scope here.)
2. **Release workflow safety** — `.github/workflows/release.yml` triggers on every `v*` tag push with no `workflow_dispatch`, no dry-run gate, no environment protection, and no rollback procedure.

Phase 28 resolves blocker 2 only. Blocker 1 remains for Phase 29.

The `v4.3.0` tag remains NOT authorized after Phase 28.

---

## Required input files

Read and analyze all of the following before implementing:

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`
- `docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md`
- `.github/workflows/release.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/jekyll-gh-pages.yml`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## FORBIDDEN — do NOT do any of the following

- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py`
- Edit any package source code
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`, or any other documentation pages
- Edit test files unless a workflow syntax validation test is explicitly required and justified in the report
- Create any git tag
- Create the `v4.3` or `v4.3.0` tag
- Run release, deploy, or publish commands
- Push to `main`
- Merge any branch
- Force-push

---

## Required implementation

Inspect the current `.github/workflows/release.yml` and implement the following minimal safe changes:

### 1. Add `workflow_dispatch` trigger

Add `workflow_dispatch` as a second trigger alongside the existing `push: tags: ["v*"]` trigger.

```yaml
on:
  push:
    tags:
      - "v*"
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry run — build and test only, skip GitHub Release creation"
        type: boolean
        default: true
```

The `dry_run` default must be `true` so that a manual dispatch is safe unless explicitly set to `false`.

### 2. Add `environment: release` to the release job

Add the `environment` key to the release job so that the GitHub repository environment named `release` controls execution approval:

```yaml
jobs:
  release:
    name: Build and release
    runs-on: ubuntu-latest
    environment: release
    permissions:
      contents: write
```

Note: GitHub Actions `environment` protection rules (required reviewers, deployment branches) must be configured in the repository Settings → Environments → `release`. This cannot be done in YAML alone. Your implementation report must note this manual step as a required repository setting.

### 3. Gate the GitHub Release creation step

The `Create GitHub Release` step must only execute when:
- The trigger is a tag push (`github.event_name == 'push'`), AND
- The workflow was NOT dispatched with `dry_run: true`.

Use this condition:

```yaml
      - name: Create GitHub Release
        if: github.event_name == 'push' && github.ref_type == 'tag'
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

This ensures:
- A `workflow_dispatch` run (dry run) never creates a GitHub Release regardless of the `dry_run` input value.
- A tag push always creates the GitHub Release (the environment approval gate is the human control point).

Do NOT add `if: ${{ !inputs.dry_run }}` alone, because `inputs.dry_run` is undefined (empty string, falsy) on a tag push, which would accidentally suppress the release on a real tag push. Use `github.event_name == 'push' && github.ref_type == 'tag'` instead.

### 4. Keep PyPI publish disabled

The PyPI publish step is currently commented out. Keep it commented out. Do NOT uncomment it. PyPI publication governance is deferred to a later phase.

### 5. Build/check steps run unconditionally

The checkout, Python setup, package install, test, and build steps must run on both tag pushes and `workflow_dispatch` runs (including dry runs). Do not add conditions to these steps.

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md
```

Also write:

- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked files that may change:

```
.github/workflows/release.yml
docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md
```

---

## Required git/version checks

Run the following commands and include their output in the report:

```bash
git status --short
git --no-pager log --oneline --decorate -15
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

### Release workflow scan

```bash
git grep -n -E "on:|tags:|v\*|workflow_dispatch|dry_run|dry-run|environment:|release|publish|deploy|pypi|twine|build|gh release|create-release|upload-artifact|download-artifact" -- .github/workflows/release.yml .github/workflows/ci.yml .github/workflows/jekyll-gh-pages.yml || true
```

### Version guard scan

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0|v4\.3|v4.3|tag|release" -- pyproject.toml voyage_framework/__init__.py docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md || true
```

### Post-edit diff scope

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

### Forbidden files check

```bash
git diff -- README.md
git diff -- docs/README.md
git diff -- AGENTS.md
git diff -- pyproject.toml
git diff -- voyage_framework
git diff -- tests
git diff -- docs/prompts
git diff -- docs/handoff/README.md
git diff -- tools
git diff -- docs/index.md
git diff -- docs/FAQ.md
git diff -- docs/_config.yml
git diff -- .gitignore
```

Expected: no output for all forbidden files.

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
| `BLOCKER` | Prevents Phase 29 (version bump) or future tag authorization |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` must use exactly this structure:

```markdown
# Phase 28 Release Workflow Implementation Report

## Scope
-

## Inputs
-

## Release workflow before
-

## Changes implemented
-

## workflow_dispatch / dry_run
-

## Environment protection
-

## GitHub Release gating
-

## PyPI publish policy
-

## Version/tag safety
-

## Manual repository settings required
-

## Validation checks
-

## Forbidden files check
-

## Tag check
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
A. Release workflow safety implemented, ready for version bump phase
B. Release workflow safety implemented with safe warnings
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

## Short terminal response format

Return only:

```markdown
# Phase 28 Implementation Summary

- Branch:
- Changed files:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
