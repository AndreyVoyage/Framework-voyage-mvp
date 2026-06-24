# Phase 30A Release Workflow AST Extras Fix Report

## Scope

- Implementation phase on branch `docs/phase-30a-release-workflow-ast-extras-fix-prompt`.
- Applies one minimal fix to `.github/workflows/release.yml`: changes `pip install -e ".[dev]"` to `pip install -e ".[dev,ast]"` in the `Install package and build tools` step.
- Does not change version files, run the workflow, create tags, or modify any other file.
- Creates only: `.github/workflows/release.yml` (modified, 1 line), `docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md` (new).
- Resolves the Phase 30 dry-run test failure blocker. Does not authorize v4.3.0 tag.

## Inputs

- `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` — confirms root cause: `pip install -e ".[dev]"` missing `[ast]` extras; `tests/conftest.py` ImportError at `tree-sitter`; run ID `28077532312`, exit code 4.
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` — version 4.3.0 in both files; local build validated.
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` — Phase 28 implemented `workflow_dispatch`, `environment: release`, gated release step. Install step was `pip install -e ".[dev]"` — Phase 28 did not change this line.
- `.github/workflows/release.yml` — inspected before edit; `pip install -e ".[dev]"` at line 33 confirmed.
- `pyproject.toml` — `version = "4.3.0"` confirmed; `[project.optional-dependencies]` `ast` group contains `tree-sitter>=0.22`, `tree-sitter-python>=0.21`, `tree-sitter-typescript>=0.21`.
- `voyage_framework/__init__.py` — `__version__ = "4.3.0"` confirmed; not modified.

## Phase 30 blocker

- Run ID: `28077532312`
- Failed step: `Run tests` — exit code 4
- Error:
  ```
  ImportError while loading conftest '/home/runner/work/Framework-voyage-mvp/Framework-voyage-mvp/tests/conftest.py'.
      raise ImportError('tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"') from exc
  E   ImportError: tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"
  ```
- Root cause: the workflow install step installs only `.[dev]` extras. `tests/conftest.py` imports tree-sitter packages defined in the `[ast]` optional dependency group. `[dev]` does not transitively include `[ast]`.
- Fix: change `pip install -e ".[dev]"` to `pip install -e ".[dev,ast]"`. — **SAFE** (one-line, additive, no safety controls changed).

## Workflow before

```yaml
- name: Install package and build tools
  run: |
    pip install -e ".[dev]"
    pip install build
```

- `pip install -e ".[dev]"` at line 33. — **BLOCKER** (missing `[ast]` extras for tests)

## Change implemented

Single one-line edit:
- File: `.github/workflows/release.yml`, line 33
- Before: `          pip install -e ".[dev]"`
- After: `          pip install -e ".[dev,ast]"`

Diff summary: 1 file changed, 1 insertion(+), 1 deletion(-).

## Workflow after

```yaml
- name: Install package and build tools
  run: |
    pip install -e ".[dev,ast]"
    pip install build
```

Post-edit scan confirms `.[dev,ast]` at line 33. — **SAFE** (install gap resolved; `[ast]` extras will be available in CI environment)

## Preserved safety controls

- workflow_dispatch: present at line 7 — unchanged. — **SAFE**
- dry_run: `type: boolean, default: true` at line 9 — unchanged. — **SAFE**
- environment release: `environment: release` at line 18 — unchanged. — **SAFE**
- GitHub Release gating: `if: github.event_name == 'push' && github.ref_type == 'tag'` at line 43 — unchanged. — **SAFE**
- PyPI publish policy: step commented out at line 51 — unchanged. — **SAFE**
- Version/tag safety: `pyproject.toml` `version = "4.3.0"` unchanged; `voyage_framework/__init__.py` `__version__ = "4.3.0"` unchanged; no v4.3* tag created. — **SAFE**

## Validation checks

Pre-edit state:
- `git status --short`: clean. — **SAFE**
- `git tag --list "v4.3*"`: no output. — **SAFE**
- `git ls-remote --tags origin "refs/tags/v4.3*"`: no output. — **SAFE**
- `pyproject.toml`: `version = "4.3.0"`. — **SAFE**
- `voyage_framework/__init__.py`: `__version__ = "4.3.0"`. — **SAFE**
- `release.yml` line 33: `pip install -e ".[dev]"` — confirmed before edit.

Post-edit state:
- `git --no-pager diff --name-status`: `M .github/workflows/release.yml` only. — **SAFE**
- `git diff --check`: no output (no whitespace errors). — **SAFE**
- Post-edit workflow scan:
  - `.[dev,ast]` at line 33 — **SAFE**
  - `workflow_dispatch` at line 7 — **SAFE**
  - `dry_run` at line 9 — **SAFE**
  - `environment: release` at line 18 — **SAFE**
  - `github.event_name == 'push' && github.ref_type == 'tag'` at line 43 — **SAFE**
  - PyPI commented at line 51 — **SAFE**

## Forbidden files check

```
git diff -- README.md                → no output
git diff -- docs/README.md           → no output
git diff -- AGENTS.md                → no output
git diff -- pyproject.toml           → no output
git diff -- voyage_framework         → no output
git diff -- tests                    → no output
git diff -- docs/prompts             → no output
git diff -- docs/handoff/README.md   → no output
git diff -- tools                    → no output
git diff -- docs/index.md            → no output
git diff -- docs/FAQ.md              → no output
git diff -- docs/_config.yml         → no output
git diff -- .gitignore               → no output
```

All forbidden file diffs: empty. — **SAFE**

## Tag check

- Local `v4.3*`: no output — none. — **SAFE**
- Remote `v4.3*` (`git ls-remote --tags origin`): no output — none. — **SAFE**
- `v4.1.0-mvp`: object `43e051219ade3f965de85a69110bf3bd93f1d4fe`, target commit `086fefc8cbb0e6dfa57a6ff8f1236fc70a56c98a` — unchanged. — **SAFE**
- `v4.2.0-adapter-contract`: object `6f6e38093a439eddefde1e1e8b272ffdafa88a13`, target commit `8d7b268ef46a0e8b8a5634d749fcc5eff3094f50` — unchanged. — **SAFE**

## Remaining blockers

1. **No dry-run pass evidence from GitHub Actions** — **WARNING**: the `[ast]` fix has been applied but not yet validated by a new dry-run. Phase 30 must be re-run after this fix merges to `main` to confirm all steps pass (tests, build, twine check) and produce `voyage_framework-4.3.0-py3-none-any.whl` + `voyage_framework-4.3.0.tar.gz`.
2. **`release` environment protection rules not configured** — **WARNING** (carry-over from Phase 28): must be configured in GitHub Settings → Environments → `release` → Required reviewers before Phase 32 tag push.

No remaining BLOCKERs that would prevent Phase 30 dry-run re-run after this fix is merged.

## Next phase

**Phase 30-retry — Re-run workflow_dispatch dry-run.**

After Phase 30A merges to `main`:
1. Confirm `main` contains the `.[dev,ast]` install fix.
2. Trigger: `gh workflow run release.yml --ref main -f dry_run=true`.
3. Watch run: `gh run watch <RUN_ID> --exit-status --interval 10`.
4. If run enters waiting/approval state due to environment protection, approve in GitHub Actions UI.
5. Confirm all steps pass:
   - `Run tests`: all tests pass (no ImportError, exit 0).
   - `Build distribution packages`: `voyage_framework-4.3.0-py3-none-any.whl` + `voyage_framework-4.3.0.tar.gz`.
   - `Create GitHub Release`: skipped (event is `workflow_dispatch`).
6. Record run ID, run URL, and artifact names in Phase 30 updated report.

After Phase 30-retry: proceed to Phase 31 (final re-audit + v4.3.0 authorization).

## v4.3.0 authorization

- Authorized now: no
- Reason: Phase 30A resolves the workflow install gap. However, no successful dry-run from GitHub Actions has been completed yet — Phase 30-retry must confirm tests pass and 4.3.0 artifacts are produced. Phase 31 re-audit must then be completed before the tag can be authorized.

## Risks / deviations

- **LF/CRLF warning on Windows**: Git reports `LF will be replaced by CRLF` for `release.yml`. Expected behavior on Windows; does not affect GitHub Actions execution (Linux). Not a risk.
- **One-line change, additive only**: `.[dev,ast]` is a superset of `.[dev]`. All `[dev]` packages are still installed; `[ast]` packages are added. No existing behavior is removed or changed.
- **No deviations from prompt specification.** All safety controls verified unchanged.

## Verdict

A. AST extras workflow fix implemented, ready to rerun Phase 30 dry-run
