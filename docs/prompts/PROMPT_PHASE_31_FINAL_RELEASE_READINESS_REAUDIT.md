# PROMPT: Phase 31 — Final Release Readiness Re-Audit

## Role

You are an audit agent.
You perform a final release readiness re-audit of the Voyage Framework repository before v4.3.0 is authorized for Phase 32 tag creation.
You read files, run checks, collect evidence, create a report, and write handoff files.
You do NOT create tags. You do NOT run the release workflow. You do NOT publish to PyPI. You do NOT edit source files or workflow files.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 31 — Final Release Readiness Re-Audit

---

## Background

### Phase 27

Phase 27 decided:
- Target package version: `4.3.0`
- Tag naming: `v4.3.0` (three-component SemVer, consistent with `v4.1.0-mvp` and `v4.2.0-adapter-contract`)
- Dry-run is mandatory before tag
- Final re-audit must authorize tag before Phase 32

### Phase 28

Phase 28 implemented release workflow safety:
- `workflow_dispatch` trigger
- `dry_run` input with `default: true`
- `environment: release` on the release job
- GitHub Release gated on `github.event_name == 'push' && github.ref_type == 'tag'`
- PyPI publish disabled/commented out

### Phase 29

Phase 29 implemented version bump:
- `pyproject.toml`: `version = "4.3.0"`
- `voyage_framework/__init__.py`: `__version__ = "4.3.0"`

### Phase 30 (first attempt — failed)

Phase 30 dry-run run `28077532312` failed:
- `Run tests` step — exit code 4
- `ImportError: tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"`
- Root cause: `.github/workflows/release.yml` installed only `.[dev]`; `tests/conftest.py` requires `[ast]` extras

### Phase 30A

Phase 30A fixed `.github/workflows/release.yml`:
- `pip install -e ".[dev]"` → `pip install -e ".[dev,ast]"` (one line only)
- All other safety controls preserved unchanged
- Merged to `main` at `3f50bab`

### Phase 30 (rerun — passed)

Phase 30 rerun `28080683596` succeeded:
- Event: `workflow_dispatch`
- Branch: `main`
- Commit SHA: `3f50babd6554c6fdcbd442c07d8d95671fdb2a73`
- Tests: `416 passed in 18.41s`
- Build: `voyage_framework-4.3.0.tar.gz` and `voyage_framework-4.3.0-py3-none-any.whl`
- `Create GitHub Release` step: **skipped** (correct — event is `workflow_dispatch`)
- No local or remote `v4.3*` tags

### Still NOT authorized

- `v4.3` tag
- `v4.3.0` tag
- GitHub Release
- PyPI publish

### Manual prerequisite

GitHub Environment `release` Required Reviewers must be configured before Phase 32:
```
GitHub → AndreyVoyage/Framework-voyage-mvp → Settings → Environments → release
→ Required reviewers → Add: AndreyVoyage → Save protection rules
```
If not configured when this audit runs, classify as WARNING or BLOCKER (see Authorization Policy below).

---

## FORBIDDEN — do NOT do any of the following

- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py` or any package source file
- Edit `tests/*`
- Edit `.github/workflows/release.yml` or any workflow file
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`
- Edit any file in `docs/prompts/*`
- Edit any file in `tools/*`
- Create any git tag
- Create the `v4.3` or `v4.3.0` tag
- Push any tag
- Run `gh release create`
- Run `gh workflow run`
- Run `twine upload`
- Run release/deploy/publish
- Run `git merge`
- Force-push
- Stage or commit `docs/handoff/LATEST_AGENT_REPORT.md`
- Stage or commit `docs/handoff/NEXT_ACTION.md`

---

## Required input files

Read and analyze all of the following before performing any checks:

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md`
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md`
- `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md`
- `docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md`
- `.github/workflows/release.yml`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## Required checks

### Repository state

```bash
git fetch origin --tags
git switch main
git pull --ff-only origin main
git status --short
git --no-pager log --oneline --decorate -30
git rev-parse HEAD
git rev-parse origin/main
git tag --list
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
```

Expected:
- `main` and `origin/main` in sync
- Phase 27–30 rerun merge commits present in log
- No `v4.3*` tag locally or remotely

### Version check

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0" -- pyproject.toml voyage_framework/__init__.py || true
```

Expected:
- `pyproject.toml`: `version = "4.3.0"`
- `voyage_framework/__init__.py`: `__version__ = "4.3.0"`
- No `4.0.0` in either file

### Workflow check

```bash
git grep -n -E "workflow_dispatch|dry_run|default: true|environment: release|pip install -e|\[dev,ast\]|github.event_name == 'push' && github.ref_type == 'tag'|gh release|twine|publish|pypi" -- .github/workflows/release.yml || true
```

Expected:
- `workflow_dispatch` present
- `dry_run` present with `default: true`
- `environment: release` present
- `pip install -e ".[dev,ast]"` present (not `.[dev]` alone)
- `if: github.event_name == 'push' && github.ref_type == 'tag'` present
- PyPI publish commented out

### Evidence check

```bash
git grep -n -E "28080683596|workflow_dispatch|3f50bab|416 passed|voyage_framework-4\.3\.0\.tar\.gz|voyage_framework-4\.3\.0-py3-none-any\.whl|Create GitHub Release|skipped|Dry-run evidence collected|ready for final re-audit" -- docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md || true
```

Expected: all key evidence strings present in Phase 30 report.

### GitHub environment check

```bash
gh auth status
gh api repos/AndreyVoyage/Framework-voyage-mvp/environments/release
```

If `gh api` fails because the environment does not exist, or if the API response shows no protection rules / no required reviewers, classify as BLOCKER for tag authorization unless the user has explicitly confirmed environment protection is configured externally.

If `gh api` succeeds, inspect the response for:
- `protection_rules` array
- `reviewers` entries
- `deployment_branch_policy`

Absence of `reviewers` with at least one entry → BLOCKER.

Optional — verify run evidence from GitHub API:

```bash
gh run view 28080683596 --json databaseId,workflowName,headBranch,headSha,event,status,conclusion,url,jobs
```

### Local artifact hygiene check

```bash
git status --short --ignored | grep -E "(\.claude|docs/handoff/LATEST_AGENT_REPORT.md|docs/handoff/NEXT_ACTION.md|docs/handoff/phase30|dist/|build/|\.egg-info)" || true
git status --short | grep -E "^(A|M|\?\?).*(dist/|build/|\.egg-info|docs/handoff/LATEST_AGENT_REPORT.md|docs/handoff/NEXT_ACTION.md|docs/handoff/phase30|\.claude)" || true
```

Expected:
- `.claude/`, `dist/`, `build/`, `*.egg-info`, `docs/handoff/*` may appear as ignored (`!!`) — SAFE
- None of the above must appear as staged or tracked changes

### Forbidden tracked changes check

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
git diff -- .github
git diff -- .gitignore
```

Expected: no output for all forbidden paths.

### Existing tag integrity check

```bash
git show-ref --tags v4.1.0-mvp
git rev-list -n 1 v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
git rev-list -n 1 v4.2.0-adapter-contract
```

Expected:
- `v4.1.0-mvp`: tag object `43e051219ade3f965de85a69110bf3bd93f1d4fe` → commit `086fefc8`
- `v4.2.0-adapter-contract`: tag object `6f6e38093a439eddefde1e1e8b272ffdafa88a13` → commit `8d7b268e`

---

## Classification scheme

Every finding must be classified as one of:

| Label | Meaning |
|-------|---------|
| `SAFE` | Verified and not blocking |
| `WARNING` | Safe but needs attention before or after release |
| `BLOCKER` | Prevents v4.3.0 tag authorization |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Authorization policy

The Phase 31 report may authorize the `v4.3.0` tag only if ALL of the following are satisfied:

1. `version = "4.3.0"` in `pyproject.toml` — **SAFE required**
2. `__version__ = "4.3.0"` in `voyage_framework/__init__.py` — **SAFE required**
3. `workflow_dispatch` present in `release.yml` — **SAFE required**
4. `dry_run default: true` present in `release.yml` — **SAFE required**
5. `environment: release` present in `release.yml` — **SAFE required**
6. `pip install -e ".[dev,ast]"` in `release.yml` — **SAFE required**
7. `if: github.event_name == 'push' && github.ref_type == 'tag'` present in `release.yml` — **SAFE required**
8. PyPI publish disabled/commented in `release.yml` — **SAFE required**
9. Phase 30 report references run `28080683596` with conclusion `success` — **SAFE required**
10. CI tests passed: `416 passed` in run `28080683596` — **SAFE required**
11. CI build produced `voyage_framework-4.3.0-py3-none-any.whl` — **SAFE required**
12. CI build produced `voyage_framework-4.3.0.tar.gz` — **SAFE required**
13. `Create GitHub Release` step was skipped in run `28080683596` — **SAFE required**
14. No local `v4.3*` tag — **SAFE required**
15. No remote `v4.3*` tag — **SAFE required**
16. No forbidden repo changes in the current working tree — **SAFE required**
17. GitHub Environment `release` Required Reviewers configured — **SAFE required** (BLOCKER if absent, unless user explicitly accepts as WARNING before audit completion)

If any item above fails, verdict must be **C** and the tag must not be authorized.

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md
```

Also write:
- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked file that may change:

```
docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md
```

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md` must use exactly this structure:

```markdown
# Phase 31 Final Release Readiness Re-Audit

## Scope
-

## Inputs
-

## Current repository state
- Branch:
- HEAD:
- origin/main:
- Working tree:

## Phase history verification
- Phase 27:
- Phase 28:
- Phase 29:
- Phase 30:
- Phase 30A:
- Phase 30 rerun:

## Version readiness
- pyproject.toml:
- voyage_framework/__init__.py:
- Remaining 4.0.0 in version files:

## Release workflow readiness
- workflow_dispatch:
- dry_run default:
- environment release:
- install extras:
- GitHub Release gating:
- PyPI publish policy:

## Dry-run evidence readiness
- Run id:
- Run URL:
- Event:
- Commit SHA:
- Tests:
- Build wheel:
- Build sdist:
- GitHub Release skipped:
- PyPI publish skipped/disabled:

## GitHub environment protection
- Environment exists:
- Required reviewers configured:
- Evidence:
- Classification:

## Tag readiness
- Local v4.3*:
- Remote v4.3*:
- Existing v4.1.0-mvp:
- Existing v4.2.0-adapter-contract:

## Generated artifacts / local hygiene
-

## Remaining warnings
-

## Remaining blockers
-

## Authorization decision
- v4.3.0 tag authorized: yes/no
- Reason:

## Phase 32 instructions if authorized
-

## Phase 32 forbidden actions if not authorized
-

## Risks / deviations
-

## Verdict
A. Final re-audit passed, v4.3.0 tag authorized for Phase 32
B. Final re-audit passed with warnings, v4.3.0 tag conditionally authorized
C. Final re-audit blocked, v4.3.0 tag not authorized
```

Fill in every section. Do not leave placeholders.

---

## Commit message (for use by the audit agent, after checks pass)

```
docs: add Phase 31 final release readiness re-audit report
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
# Phase 31 Audit Summary

- Branch:
- Changed files:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
- v4.3.0 authorized:
```
