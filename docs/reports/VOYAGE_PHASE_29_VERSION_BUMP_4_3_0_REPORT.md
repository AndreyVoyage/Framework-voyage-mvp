# Phase 29 Version Bump to 4.3.0 Report

## Scope

- Implementation phase on branch `docs/phase-29-version-bump-prompt`.
- Updates `pyproject.toml` and `voyage_framework/__init__.py` only to bump package version from `4.0.0` to `4.3.0`.
- Does not bump to a different version. Does not create tags. Does not run release, deploy, or publish.
- Creates only: `pyproject.toml` (modified), `voyage_framework/__init__.py` (modified), `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` (new).
- Resolves Phase 27 BLOCKER 1 (version mismatch). BLOCKER 2 (release workflow safety) was resolved in Phase 28.

## Inputs

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` — Decision 1: version must be `4.3.0` in both `pyproject.toml` and `voyage_framework/__init__.py` in a single atomic commit.
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` — confirms Phase 28 merged to `main` at `2054524`; release workflow safety implemented; version BLOCKER carry-over to Phase 29.
- `pyproject.toml` — `version = "4.0.0"` (line 7) confirmed before edit.
- `voyage_framework/__init__.py` — `__version__ = "4.0.0"` (line 9) confirmed before edit.
- `.github/workflows/release.yml` — read for context; not modified. Contains `workflow_dispatch`, `environment: release`, `if: github.event_name == 'push' && github.ref_type == 'tag'` — Phase 28 implementation confirmed present.
- `docs/handoff/README.md`, `tools/copy_latest_report.ps1`, `tools/copy_report_to_clipboard.ps1` — read for handoff procedure.

## Version before

- pyproject.toml: `version = "4.0.0"` (line 7) — **BLOCKER** (resolved in this phase)
- voyage_framework/__init__.py: `__version__ = "4.0.0"` (line 9) — **BLOCKER** (resolved in this phase)

## Changes implemented

Two minimal, single-line edits:

1. **`pyproject.toml` line 7**: `version = "4.0.0"` → `version = "4.3.0"`
2. **`voyage_framework/__init__.py` line 9**: `__version__ = "4.0.0"` → `__version__ = "4.3.0"`

No other lines modified in either file. Diff summary: 2 files changed, 2 insertions(+), 2 deletions(-).

## Version after

- pyproject.toml: `version = "4.3.0"` (line 7) — **SAFE**
- voyage_framework/__init__.py: `__version__ = "4.3.0"` (line 9) — **SAFE**

Post-edit version scan confirms no remaining `4.0.0` in either file:

```
pyproject.toml:7:version = "4.3.0"
voyage_framework/__init__.py:9:__version__ = "4.3.0"
```

## Validation checks

All validation passed:

**pytest (399 unit tests):**
- `pytest tests/unit -q` → `399 passed in 54.16s` — **SAFE**
- No test failures. No version assertion failures. No test files modified.

**ruff (both files):**
- `ruff check voyage_framework/__init__.py` → `All checks passed!` — **SAFE**
- `ruff check pyproject.toml` → `All checks passed!` — **SAFE**

**mypy:**
- `mypy voyage_framework/__init__.py` → `Success: no issues found in 1 source file` — **SAFE**

**python -m build:**
- Build completed successfully.
- Artifacts produced:
  - `dist/voyage_framework-4.3.0-py3-none-any.whl`
  - `dist/voyage_framework-4.3.0.tar.gz`
- Artifact names contain `4.3.0` — consistent with version bump. — **SAFE**

**twine check:**
- `twine check dist/voyage_framework-4.3.0-py3-none-any.whl` → `PASSED` — **SAFE**
- `twine check dist/voyage_framework-4.3.0.tar.gz` → `PASSED` — **SAFE**
- (Also present from earlier builds: `dist/voyage_framework-4.0.0-*` — pre-existing artifacts, not regenerated in this phase.)

## Forbidden files check

```
git diff -- README.md               → no output
git diff -- docs/README.md          → no output
git diff -- AGENTS.md               → no output
git diff -- .github                 → no output
git diff -- tests                   → no output
git diff -- docs/prompts            → no output
git diff -- docs/handoff/README.md  → no output
git diff -- tools                   → no output
git diff -- docs/index.md           → no output
git diff -- docs/FAQ.md             → no output
git diff -- docs/_config.yml        → no output
git diff -- .gitignore              → no output
```

All forbidden file diffs: empty. — **SAFE**

## Tag check

- `git tag --list "v4.3*"`: no output — no v4.3 tag created or exists. — **SAFE**
- `v4.1.0-mvp`: tag object `43e051219ade3f965de85a69110bf3bd93f1d4fe`, target commit `086fefc8cbb0e6dfa57a6ff8f1236fc70a56c98a` — unchanged. — **SAFE**
- `v4.2.0-adapter-contract`: tag object `6f6e38093a439eddefde1e1e8b272ffdafa88a13`, target commit `8d7b268ef46a0e8b8a5634d749fcc5eff3094f50` — unchanged. — **SAFE**

## Release workflow status

- `.github/workflows/release.yml` — not modified in Phase 29.
- Phase 28 changes confirmed present (read before edit): `workflow_dispatch`, `dry_run boolean default: true`, `environment: release`, `if: github.event_name == 'push' && github.ref_type == 'tag'` on the `Create GitHub Release` step. PyPI publish step remains commented out.
- `release.yml` diff in this phase: no output (no change). — **SAFE**
- **WARNING**: `release` environment protection rules (required reviewers) must still be configured in GitHub repository Settings → Environments → `release` before Phase 30 dry-run. This is a carry-over WARNING from Phase 28; no YAML change is needed.

## Remaining blockers

1. **No dry-run evidence** — **WARNING** (carry-over): Phase 30 must execute a `workflow_dispatch` dry-run with `dry_run: true` after this version bump is on `main` to confirm artifact names contain `4.3.0` under the GitHub Actions environment (Python 3.12, Ubuntu).
2. **Environment protection rules not configured** — **WARNING** (carry-over from Phase 28): The `release` environment in GitHub Settings must have required reviewers added before Phase 30. Without this, the environment approval gate in the YAML is not enforced at runtime.
3. **Old `dist/voyage_framework-4.0.0-*` artifacts in `dist/`** — **WARNING** (local only): The `dist/` directory contains pre-existing `4.0.0` artifacts from prior local builds. These are not tracked by git (`.gitignore` excludes `dist/`). They do not affect the release workflow or PyPI, but a local `twine upload dist/*` would mistakenly include them. Before any future PyPI publish, `dist/` should be cleaned and rebuilt from the `4.3.0` state.

No remaining BLOCKERs that would prevent Phase 30 (dry-run).

## Next phase

**Phase 30 — Dry-run execution.**

After Phase 29 is merged to `main`:
1. Ensure `release` environment is configured with required reviewers in GitHub Settings.
2. Trigger `workflow_dispatch` with `dry_run: true` (or leave default `true`) from the GitHub Actions UI.
3. Confirm workflow log shows: tests pass, `python -m build` produces `dist/voyage_framework-4.3.0-*.whl` and `dist/voyage_framework-4.3.0.tar.gz`, `Create GitHub Release` step is **skipped** (condition `github.event_name == 'push' && github.ref_type == 'tag'` is false on `workflow_dispatch`).
4. Record workflow run URL and artifact names in Phase 30 report.

**Before Phase 30**: merge Phase 29 to `main` via no-FF merge, push `main`.

## v4.3.0 authorization

- Authorized now: no
- Reason: Phase 29 resolves the last BLOCKER (version mismatch). However, two WARNINGs remain: no dry-run evidence (Phase 30 required) and `release` environment protection rules not yet configured in GitHub Settings. The `v4.3.0` tag must not be created until Phase 31 re-audit issues explicit authorization after Phase 30 dry-run evidence is collected.

## Risks / deviations

- **LF/CRLF warning on Windows**: Git reports `LF will be replaced by CRLF` for modified files (`pyproject.toml`, `voyage_framework/__init__.py`) due to `core.autocrlf=true` on Windows. Expected behavior; does not affect file content in GitHub Actions (Linux). — Not a risk.
- **Old `dist/4.0.0` artifacts**: Pre-existing `dist/voyage_framework-4.0.0-*` files are present locally. They are gitignored and do not appear in git diff. They pose no risk to the repository or release workflow, but should be cleaned before any future PyPI publish attempt. Documented as WARNING above.
- **No deviations from Phase 27 Decision 1**. Both files updated in a single atomic commit exactly as specified.

## Verdict

A. Version bump implemented, ready for dry-run phase
