# Phase 28 Release Workflow Implementation Report

## Scope

- Implementation phase on branch `docs/phase-28-release-workflow-implementation-prompt`.
- Updates `.github/workflows/release.yml` only to implement release workflow safety decisions from Phase 27.
- Does not bump version. Does not create tags. Does not run release, deploy, or publish.
- Creates only: `.github/workflows/release.yml` (modified), `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` (new).
- Resolves Phase 27 / Phase 26 BLOCKER 2 (release workflow safety). BLOCKER 1 (version mismatch) remains for Phase 29.

## Inputs

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` — policy decisions for all five areas; Decisions 3 (workflow), 4 (dry-run), 5 (rollback) directly drive this phase.
- `docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md` — origin of the two BLOCKERs.
- `.github/workflows/release.yml` — file being modified.
- `.github/workflows/ci.yml` — read for context; not modified.
- `.github/workflows/jekyll-gh-pages.yml` — read for context; not modified.
- `pyproject.toml` — read to confirm `version = "4.0.0"` is unchanged; not modified.
- `voyage_framework/__init__.py` — read to confirm `__version__ = "4.0.0"` is unchanged; not modified.

## Release workflow before

Before this phase, `.github/workflows/release.yml` had:

```yaml
on:
  push:
    tags:
      - "v*"
```

- Single trigger: `push` on any `v*` tag — fires immediately on any tag push, no gate.
- Job `release`: `runs-on: ubuntu-latest`, no `environment` key — no approval gate.
- Steps: checkout → Python 3.12 → `pip install -e ".[dev]" && pip install build` → `pytest tests/ -q` → `python -m build` → `softprops/action-gh-release@v2` with no condition → PyPI step commented out.
- Classification: **BLOCKER** — no dry-run path, no manual gate, no environment protection.

## Changes implemented

Three minimal, additive changes to `.github/workflows/release.yml`:

1. **Added `workflow_dispatch` trigger** with `dry_run` boolean input (`default: true`).
2. **Added `environment: release`** to the `release` job.
3. **Added `if:` condition** to the `Create GitHub Release` step: `github.event_name == 'push' && github.ref_type == 'tag'`.

No other lines were modified. PyPI publish step remains commented. All build/test steps remain unconditional.

Diff summary: 8 lines added, 0 lines removed.

## workflow_dispatch / dry_run

```yaml
workflow_dispatch:
  inputs:
    dry_run:
      description: "Dry run — build and test only, skip GitHub Release creation"
      type: boolean
      default: true
```

- `default: true` — a manual dispatch is safe by default; the operator must explicitly set `dry_run: false` to attempt a release, and even then the `Create GitHub Release` step will not fire because `github.event_name` will be `workflow_dispatch`, not `push`.
- The `dry_run` input is accepted by the workflow UI but is not referenced in any step condition; its primary role is as a UI signal to the operator and to document intent in the run log. The actual gate is the `github.event_name == 'push' && github.ref_type == 'tag'` condition on the release step.
- Classification: **SAFE**.

## Environment protection

```yaml
jobs:
  release:
    name: Build and release
    runs-on: ubuntu-latest
    environment: release
    permissions:
      contents: write
```

- `environment: release` references a GitHub repository environment named `release`.
- When an environment with required reviewers is configured in repository Settings → Environments → `release`, all workflow runs (both tag-push and `workflow_dispatch`) that reach this job must be approved by a designated reviewer before executing.
- This provides a human approval gate even for tag-push triggered runs — Phase 27 Decision 3 requirement.
- The environment key in YAML alone does not enforce protection; the environment must be configured in the repository Settings. See "Manual repository settings required" below.
- Classification: **SAFE** (implemented in YAML). **WARNING** (manual repo-settings step required).

## GitHub Release gating

```yaml
      - name: Create GitHub Release
        if: github.event_name == 'push' && github.ref_type == 'tag'
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
```

- The condition `github.event_name == 'push' && github.ref_type == 'tag'` is true only when the workflow was triggered by a tag push to the repository.
- On any `workflow_dispatch` run (regardless of `dry_run` value), `github.event_name` is `workflow_dispatch`, so this step is skipped entirely. Manual dry-run runs can verify the build pipeline without creating a GitHub Release.
- On a tag push (future Phase 32, after authorization), `github.event_name == 'push'` and `github.ref_type == 'tag'`, so the step executes — but only after the `environment: release` approval gate passes.
- The pattern `if: ${{ !inputs.dry_run }}` was explicitly rejected (per Phase 27 prompt guidance): on a tag push `inputs.dry_run` resolves to empty string (falsy in GitHub Actions boolean context), which would suppress the release step on a real tag push. The `event_name + ref_type` pattern is unambiguous.
- Classification: **SAFE**.

## PyPI publish policy

```yaml
      # Раскомментировать после настройки PYPI_API_TOKEN в GitHub Secrets
      # - name: Publish to PyPI
      #   uses: pypa/gh-action-pypi-publish@release/v1
      #   with:
      #     password: ${{ secrets.PYPI_API_TOKEN }}
```

- PyPI publish step remains commented out. No change made.
- Phase 27 Decision 3: PyPI publication requires a separate governance approval phase and PYPI_API_TOKEN secret configuration. Not in scope for Phase 28.
- Classification: **SAFE** (correctly unchanged). **WARNING** (future phase must explicitly approve before uncommenting).

## Version/tag safety

- `pyproject.toml`: `version = "4.0.0"` — unchanged. **BLOCKER** remains for Phase 29.
- `voyage_framework/__init__.py`: `__version__ = "4.0.0"` — unchanged. **BLOCKER** remains for Phase 29.
- `git tag --list "v4.3*"`: no output — no v4.3 tag created or exists.
- `v4.1.0-mvp`: object `43e051219ade3f965de85a69110bf3bd93f1d4fe`, commit `086fefc8` — unchanged.
- `v4.2.0-adapter-contract`: object `6f6e38093a439eddefde1e1e8b272ffdafa88a13`, commit `8d7b268e` — unchanged.
- No release, deploy, or publish command was run.
- Classification: version files **BLOCKER** (carry-over to Phase 29), tags **SAFE**.

## Manual repository settings required

The following repository setting must be configured manually by the maintainer before Phase 30 (dry-run) and before any tag push:

**GitHub repository → Settings → Environments → Create environment named `release`**

Required protection settings:
- **Required reviewers**: add at least one reviewer (e.g., `AndreyVoyage`) who must approve each deployment before the workflow job executes.
- **Deployment branches**: restrict to `tag` refs or specific protected branches as appropriate (optional but recommended).

Without this setting, `environment: release` in the YAML is syntactically valid and the environment is created implicitly on first run with no protection rules — meaning the approval gate will not be enforced. The YAML change alone does not protect the release; the repository Settings step is mandatory.

Classification: **WARNING** (cannot be done in YAML; requires human action in GitHub UI before Phase 30).

## Validation checks

Pre-edit git state:
- `git status --short`: clean (no output).
- Branch: `docs/phase-28-release-workflow-implementation-prompt` at `8405ef9`.
- `git tag --list "v4.3*"`: no output.
- `v4.1.0-mvp` and `v4.2.0-adapter-contract` refs: confirmed present and unchanged.

Release workflow scan (before edit):
- `release.yml:3` — `on:` with only `push: tags: ["v*"]` — no `workflow_dispatch`, no `environment`, no condition on release step. Confirmed BLOCKER state.

Version guard scan:
- `pyproject.toml:7` — `version = "4.0.0"` — confirmed unchanged.
- `voyage_framework/__init__.py:9` — `__version__ = "4.0.0"` — confirmed unchanged.

Post-edit diff:
- `git --no-pager diff --name-status`: `M .github/workflows/release.yml` only.
- `git diff --check`: no whitespace errors.
- `git status --short`: `M .github/workflows/release.yml` (modified, unstaged) and untracked report file.

## Forbidden files check

```
git diff -- README.md            → no output
git diff -- docs/README.md       → no output
git diff -- AGENTS.md            → no output
git diff -- pyproject.toml       → no output
git diff -- voyage_framework     → no output
git diff -- tests                → no output
git diff -- docs/prompts         → no output
git diff -- docs/handoff/README.md → no output
git diff -- tools                → no output
git diff -- docs/index.md        → no output
git diff -- docs/FAQ.md          → no output
git diff -- docs/_config.yml     → no output
git diff -- .gitignore           → no output
```

All forbidden file diffs: empty. SAFE.

## Tag check

- `git tag --list "v4.3*"`: no output — no v4.3 tag exists.
- `v4.1.0-mvp`: tag object `43e051219ade3f965de85a69110bf3bd93f1d4fe`, target commit `086fefc8cbb0e6dfa57a6ff8f1236fc70a56c98a` — unchanged.
- `v4.2.0-adapter-contract`: tag object `6f6e38093a439eddefde1e1e8b272ffdafa88a13`, target commit `8d7b268ef46a0e8b8a5634d749fcc5eff3094f50` — unchanged.

## Remaining blockers

1. **Version mismatch** — **BLOCKER** (carry-over): `pyproject.toml` and `voyage_framework/__init__.py` remain at `4.0.0`. Phase 29 must update both to `4.3.0` in a single atomic commit. Phase 28 does not touch these files.
2. **Environment protection rules not configured** — **WARNING**: The `release` environment in GitHub Settings must have required reviewers added before Phase 30 dry-run; without this, the environment approval gate is not enforced.
3. **No dry-run evidence** — **WARNING** (carry-over): Phase 30 must execute a `workflow_dispatch` dry-run after Phase 29 version bump is on `main` to confirm artifact names contain `4.3.0`.

## Next phase

**Phase 29 — Version bump implementation.**

After Phase 28 is merged to `main`:
1. Create a new branch from `main`.
2. Update `pyproject.toml` `version` field: `"4.0.0"` → `"4.3.0"`.
3. Update `voyage_framework/__init__.py` `__version__`: `"4.0.0"` → `"4.3.0"`.
4. Both changes must be in the same atomic commit.
5. Run `python -m build` locally and confirm artifact names include `4.3.0`.
6. Run `twine check dist/*` and confirm zero errors.
7. Commit and merge to `main`.

After Phase 29: proceed to Phase 30 (dry-run execution).

**Before Phase 30**: configure the `release` environment in GitHub repository Settings with required reviewer protection.

## v4.3.0 authorization

- Authorized now: no
- Reason: Phase 28 resolves the release workflow safety BLOCKER at the implementation level. However, the version BLOCKER remains (`pyproject.toml` and `voyage_framework/__init__.py` at `4.0.0`). Additionally, the `release` environment protection rules have not yet been configured in repository settings, and no dry-run evidence exists. The `v4.3.0` tag remains unauthorized until Phases 29–31 complete and Phase 31 re-audit issues authorization.

## Risks / deviations

- **LF/CRLF warning**: Git reports `LF will be replaced by CRLF` for `release.yml` on the next touch (Windows core.autocrlf=true). This is expected behavior on Windows and does not affect the file content or GitHub Actions execution (Linux). Not a risk.
- **`environment: release` without protection rules**: The YAML change is safe. If the environment is not configured in Settings before a workflow run, the job will execute without approval. This is a WARNING, not a BLOCKER for Phase 28 completion, because no tag push is authorized in Phase 28. The gap must be closed before Phase 30.
- **No deviations** from Phase 27 Decision 3 policy. The `if: github.event_name == 'push' && github.ref_type == 'tag'` pattern was used as specified, rejecting the `!inputs.dry_run` anti-pattern.

## Verdict

B. Release workflow safety implemented with safe warnings

Core implementation complete: `workflow_dispatch` + `dry_run` added, `environment: release` added to job, `Create GitHub Release` step gated on tag-push event. One WARNING remains: the `release` environment protection rules must be configured manually in GitHub Settings before Phase 30 dry-run. The version BLOCKER (Phase 29) also remains. Both are carry-over items, not regressions from Phase 28.
