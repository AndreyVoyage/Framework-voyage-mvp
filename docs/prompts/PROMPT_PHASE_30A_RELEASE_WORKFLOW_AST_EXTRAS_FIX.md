# PROMPT: Phase 30A — Release Workflow AST Extras Fix

## Role

You are an implementation agent.
You apply a single minimal fix to `.github/workflows/release.yml`: change `pip install -e ".[dev]"` to `pip install -e ".[dev,ast]"` so that the test suite can run in the GitHub Actions environment.
You do NOT create tags. You do NOT run the release workflow. You do NOT run `gh workflow run`. You do NOT change version files.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 30A — Release Workflow AST Extras Fix

---

## Background

Phase 30 dry-run was executed (run ID `28077532312`, event `workflow_dispatch`, ref `main`, SHA `0ac0238`, `dry_run=true`). It failed at the `Run tests` step:

```
ImportError: tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"
```

Root cause: `.github/workflows/release.yml` install step runs `pip install -e ".[dev]"` only. `tests/conftest.py` imports `tree-sitter` packages which are in the `[ast]` optional dependency group (`pyproject.toml` → `[project.optional-dependencies]` → `ast = ["tree-sitter>=0.22", ...]`). The `[dev]` extras group does not include `[ast]`.

The rest of the dry-run behaved correctly:
- `voyage-framework-4.3.0` was installed (version correct)
- `Create GitHub Release` step was correctly **skipped** (event is `workflow_dispatch`, not `push`)
- PyPI publish was not present (commented out)
- No v4.3* tags were created

Phase 30A resolves only the install extras gap. No other workflow change is needed.

---

## Required input files

Read and analyze all of the following before implementing:

- `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md`
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md`
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md`
- `.github/workflows/release.yml`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## FORBIDDEN — do NOT do any of the following

- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py` or any package source file
- Edit `tests/*`
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`, or any documentation page other than the Phase 30A report
- Edit `docs/prompts/*`
- Change the workflow triggers (`on:` block — keep `push: tags: ["v*"]` and `workflow_dispatch` unchanged)
- Change the `dry_run` input definition or its `default: true`
- Change `environment: release`
- Change the `Create GitHub Release` step `if:` condition
- Uncomment or modify the PyPI publish step
- Change the version in any file
- Create any git tag
- Create the `v4.3` or `v4.3.0` tag
- Run `gh workflow run` or any release/deploy/publish command
- Run `gh release create`
- Run `twine upload`
- Push to `main`
- Merge any branch
- Force-push

---

## Required implementation

### 1. Inspect `.github/workflows/release.yml`

Locate the `Install package and build tools` step. It currently contains:

```yaml
- name: Install package and build tools
  run: |
    pip install -e ".[dev]"
    pip install build
```

### 2. Apply the minimal fix

Change only the first `pip install` line:

```
pip install -e ".[dev]"
→
pip install -e ".[dev,ast]"
```

The result must be:

```yaml
- name: Install package and build tools
  run: |
    pip install -e ".[dev,ast]"
    pip install build
```

Do not change any other line in `.github/workflows/release.yml`.

### 3. Verify preserved safety controls

After the edit, confirm via `git grep` that all of the following are still present and unchanged:
- `workflow_dispatch` trigger
- `dry_run` input with `default: true`
- `environment: release` on the job
- `if: github.event_name == 'push' && github.ref_type == 'tag'` on the `Create GitHub Release` step
- PyPI publish step remains commented out

### 4. Do not run the workflow

Do not run `gh workflow run`, `gh release`, or any release/deploy/publish command. Phase 30 dry-run re-execution is a separate step after this fix is merged to `main`.

---

## Required git/version checks

Run these commands before making any edits and include their output in the report:

```bash
git status --short
git --no-pager log --oneline --decorate -15
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
```

### Workflow scan before edit

```bash
git grep -n -E "pip install -e|\[dev\]|\[dev,ast\]|workflow_dispatch|dry_run|environment: release|github.event_name == 'push' && github.ref_type == 'tag'|gh release|twine|publish|pypi" -- .github/workflows/release.yml || true
```

### Version guard scan

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0" -- pyproject.toml voyage_framework/__init__.py || true
```

Expected: `version = "4.3.0"` and `__version__ = "4.3.0"` — confirm both are 4.3.0 and unchanged.

### Post-edit workflow scan

```bash
git grep -n -E "pip install -e|\[dev\]|\[dev,ast\]|workflow_dispatch|dry_run|environment: release|github.event_name == 'push' && github.ref_type == 'tag'|gh release|twine|publish|pypi" -- .github/workflows/release.yml || true
```

Expected:
- `.[dev,ast]` present (not `.[dev]` alone in the install step)
- `workflow_dispatch` present
- `dry_run` present with `default: true`
- `environment: release` present
- `github.event_name == 'push' && github.ref_type == 'tag'` present
- PyPI publish remains commented

### Post-edit diff scope

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed files only:

```
M       .github/workflows/release.yml
A       docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md
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

Expected: no output for all forbidden paths.

### Tag check

```bash
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
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
| `SAFE` | Implemented or verified and not blocking |
| `WARNING` | Safe but needs later dry-run validation |
| `BLOCKER` | Prevents re-run of Phase 30 dry-run |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md
```

Also write:

- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked files that may change:

```
.github/workflows/release.yml
docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md
```

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md` must use exactly this structure:

```markdown
# Phase 30A Release Workflow AST Extras Fix Report

## Scope
-

## Inputs
-

## Phase 30 blocker
-

## Workflow before
-

## Change implemented
-

## Workflow after
-

## Preserved safety controls
- workflow_dispatch:
- dry_run:
- environment release:
- GitHub Release gating:
- PyPI publish policy:
- Version/tag safety:

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
A. AST extras workflow fix implemented, ready to rerun Phase 30 dry-run
B. AST extras workflow fix implemented with safe warnings
C. Implementation blocked
```

Fill in every section. Do not leave placeholders.

---

## Commit message (for use by the implementation agent, after checks pass)

```
ci: fix release workflow to install ast extras for tests
```

---

## Handoff requirements

After commit:

1. Write `docs/handoff/LATEST_AGENT_REPORT.md` as a full terminal-style final report (UTF-8).
2. Write `docs/handoff/NEXT_ACTION.md` with the recommended next step (UTF-8).
3. Do NOT commit either handoff file.
4. Keep your terminal response short — use the summary format below.

---

## Short terminal response format

Return only:

```markdown
# Phase 30A Implementation Summary

- Branch:
- Changed files:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
