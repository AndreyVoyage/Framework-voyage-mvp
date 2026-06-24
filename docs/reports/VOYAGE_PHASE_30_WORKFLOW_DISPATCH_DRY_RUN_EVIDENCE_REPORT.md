# Phase 30 Workflow Dispatch Dry-Run Evidence Report

## Scope

- Evidence collection phase on branch `docs/phase-30-dry-run-evidence-prompt`.
- Objective: trigger `workflow_dispatch` dry-run on `main` with `dry_run=true`, collect build/test evidence.
- Does not create tags, GitHub Releases, or publish to PyPI.
- Creates/updates only: `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` (this file).
- Two execution attempts: (1) blocked by GitHub CLI auth failure (prior commit `52f904f`); (2) this run — dry-run triggered, failed at `Run tests` step due to missing `[ast]` extras.

## Inputs

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` — Decision 4: dry-run mandatory before v4.3.0 tag; must produce 4.3.0 wheel and sdist, tests must pass.
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` — Phase 28 workflow implementation: `pip install -e ".[dev]"`, `pytest tests/ -q`, `python -m build`.
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` — version 4.3.0 confirmed; local build validated; twine check PASSED locally.
- `.github/workflows/release.yml` — confirmed: `workflow_dispatch`, `dry_run default: true`, `environment: release`, gated release step, PyPI commented.
- `pyproject.toml` — `version = "4.3.0"` confirmed.
- `voyage_framework/__init__.py` — `__version__ = "4.3.0"` confirmed.

## Preconditions

All preconditions verified:

**Git state:**
- `main` HEAD: `0ac02383708b8768920b4c7f892c231875d35a52` (Merge Phase 29 version bump to 4.3.0) — correct. — **SAFE**
- `origin/main`: `0ac02383708b8768920b4c7f892c231875d35a52` — in sync. — **SAFE**
- Working tree: clean. — **SAFE**
- Local `v4.3*` tag: none. — **SAFE**
- Remote `v4.3*` tag: none. — **SAFE**

**Version check:**
- `pyproject.toml:7`: `version = "4.3.0"` — **SAFE**
- `voyage_framework/__init__.py:9`: `__version__ = "4.3.0"` — **SAFE**
- No `4.0.0` in either file. — **SAFE**

**Workflow check:**
- `workflow_dispatch` at line 7 — **SAFE**
- `dry_run` input at line 9 — **SAFE**
- `environment: release` at line 18 — **SAFE**
- `Create GitHub Release` gated at line 43: `if: github.event_name == 'push' && github.ref_type == 'tag'` — **SAFE**
- PyPI publish commented at line 51 — **SAFE**

**GitHub CLI auth:**
- `gh auth status`: `✓ Logged in to github.com account AndreyVoyage (keyring)` — **SAFE**
- Token scopes: `gist, read:org, repo, workflow` — **SAFE**

## GitHub environment release protection

- Status: **WARNING** — the `release` environment was created implicitly by the YAML `environment: release` key. The workflow job ran immediately without requiring manual approval, indicating that no Required Reviewers are configured in GitHub repository Settings → Environments → `release`.
- The job ran and failed (test failure), so the absence of protection rules did not affect this dry-run. However, protection rules must be configured before Phase 32 tag push.
- Classification: **WARNING** (carry-over from Phase 28).

## Workflow dispatch command

```bash
gh workflow run release.yml --ref main -f dry_run=true
```

Output: `https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28077532312`

## Workflow run evidence

- Run id: `28077532312`
- Run URL: https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28077532312
- Event: `workflow_dispatch`
- Ref/branch: `main`
- Commit SHA: `0ac02383708b8768920b4c7f892c231875d35a52` (Merge Phase 29 version bump to 4.3.0)
- dry_run input: `true` (dispatched with `-f dry_run=true`; default in workflow is also `true`)
- Status: `completed`
- Conclusion: `failure`

## Job evidence

Job: `Build and release` (ID: `83124858428`)
- Duration: 26 seconds
- Conclusion: `failure`

Step results:
| Step | Result | Notes |
|------|--------|-------|
| Set up job | ✓ success | |
| Checkout repository | ✓ success | |
| Set up Python | ✓ success | Python 3.12 |
| Install package and build tools | ✓ success | `voyage-framework-4.3.0` installed |
| Run tests | ✗ failure | Exit code 4 — ImportError in `tests/conftest.py` |
| Build distribution packages | – skipped | Skipped due to test failure |
| Create GitHub Release | – skipped | Skipped (correctly: `event_name == 'workflow_dispatch'`, not `push`) |
| Post Checkout repository | ✓ success | |
| Complete job | ✓ success | |

**Root cause of test failure:**

```
ImportError while loading conftest '/home/runner/work/Framework-voyage-mvp/Framework-voyage-mvp/tests/conftest.py'.
    raise ImportError('tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"') from exc
E   ImportError: tree-sitter extras not installed. Run: pip install -e ".[ast,dev]"
##[error]Process completed with exit code 4.
```

The workflow install step runs `pip install -e ".[dev]"` only. The test suite's `conftest.py` requires `[ast]` extras (`tree-sitter>=0.22`, `tree-sitter-python>=0.21`, `tree-sitter-typescript>=0.21`). These are defined in `pyproject.toml` under `[project.optional-dependencies]` as `ast = [...]`. The `[dev]` extras do not include `[ast]`.

This is a **pre-existing workflow configuration issue** unrelated to the version bump. Local Phase 29 validation ran `pytest tests/unit -q` (unit tests only, in a venv with all extras installed), which passed. The release workflow runs `pytest tests/ -q` (all tests) in a clean environment with only `[dev]` installed.

## Build artifact evidence

- **Not available.** The `Build distribution packages` step was skipped due to test failure.
- Local evidence from Phase 29: `voyage_framework-4.3.0.tar.gz` and `voyage_framework-4.3.0-py3-none-any.whl` were built and passed `twine check`. This is local evidence only.
- GitHub Actions build evidence: **NOT collected** — **BLOCKER**.

## Twine check evidence

- **Not available from GitHub Actions.** Build step was skipped.
- Local Phase 29 evidence: `twine check dist/voyage_framework-4.3.0-py3-none-any.whl` → `PASSED`; `twine check dist/voyage_framework-4.3.0.tar.gz` → `PASSED`.
- GitHub Actions twine check evidence: **NOT collected** — **BLOCKER**.

## GitHub Release gating evidence

- `Create GitHub Release` step: **skipped** (conclusion: `skipped`).
- This is correct behavior: `github.event_name == 'workflow_dispatch'`, not `'push'`, so the `if:` condition is false.
- The gating works correctly. — **SAFE** (static gating verified; dynamic evidence confirmed by step skip).

## PyPI publish evidence

- PyPI publish step is commented out in `.github/workflows/release.yml:51`. Step does not appear in the job at all.
- No PyPI publish was attempted. — **SAFE**

## Tag check

- Local v4.3*: none — **SAFE**
- Remote v4.3*: none (`git ls-remote --tags origin "refs/tags/v4.3*"` → no output) — **SAFE**
- v4.1.0-mvp: `43e051219ade3f965de85a69110bf3bd93f1d4fe` → commit `086fefc8` — unchanged — **SAFE**
- v4.2.0-adapter-contract: `6f6e38093a439eddefde1e1e8b272ffdafa88a13` → commit `8d7b268e` — unchanged — **SAFE**

## Version check

- pyproject.toml: `version = "4.3.0"` (line 7) — **SAFE**
- voyage_framework/__init__.py: `__version__ = "4.3.0"` (line 9) — **SAFE**
- `voyage-framework-4.3.0` confirmed installed in GitHub Actions run (from install log) — **SAFE**

## Downloaded artifacts

- `gh run download 28077532312 --dir docs/handoff/phase30/artifacts` → no artifacts available (workflow does not upload artifacts; build step was skipped). — **WARNING**: no downloadable artifacts from workflow.

## Validation summary

| Check | Result | Classification |
|-------|--------|----------------|
| Git preconditions | PASS | SAFE |
| GitHub CLI auth | PASS | SAFE |
| Version 4.3.0 in both files | PASS | SAFE |
| Workflow structure (dispatch/dry_run/env/gate) | PASS | SAFE |
| Workflow dispatch executed | PASS | SAFE |
| `voyage-framework-4.3.0` installed in CI | PASS (from log) | SAFE |
| Test suite passed | FAIL — exit code 4 | **BLOCKER** |
| Build step ran | FAIL — skipped | **BLOCKER** |
| 4.3.0 wheel/sdist from CI | NOT collected | **BLOCKER** |
| Twine check from CI | NOT collected | **BLOCKER** |
| Create GitHub Release skipped | PASS — step skipped | SAFE |
| PyPI publish disabled | PASS — commented out | SAFE |
| No v4.3* tag created | PASS | SAFE |

## Forbidden actions check

- No tags created. — **SAFE**
- No GitHub Release created. — **SAFE**
- No PyPI publish. — **SAFE**
- No source files edited. — **SAFE**
- No workflow files edited. — **SAFE**
- `gh auth login` was NOT run in this session. — **SAFE**

## Remaining blockers

1. **Workflow install missing `[ast]` extras** — **BLOCKER**: `.github/workflows/release.yml` install step runs `pip install -e ".[dev]"`. The test suite (`tests/conftest.py`) requires `tree-sitter` packages from the `[ast]` optional extras group. Fix: change `pip install -e ".[dev]"` to `pip install -e ".[dev,ast]"` in the release workflow. This requires a new implementation phase (Phase 28-fix or Phase 30-fix) to update the workflow before re-running Phase 30.
2. **No test pass evidence from GitHub Actions** — **BLOCKER** (follow-on from blocker 1): Phase 27 Decision 4 requires the dry-run to confirm `pytest tests/ -q` passes. Not yet confirmed.
3. **No build artifact evidence from GitHub Actions** — **BLOCKER** (follow-on from blocker 1): Phase 27 Decision 4 requires confirmed `voyage_framework-4.3.0-*.whl` and `voyage_framework-4.3.0.tar.gz` produced in the CI environment.
4. **`release` environment protection rules not configured** — **WARNING** (carry-over from Phase 28): the workflow ran without approval, confirming protection rules are not configured. Must be set before Phase 32 tag push.

## Next phase

**Phase 30-fix — Workflow install fix.**

Before re-running Phase 30:
1. Create a new branch from `main`.
2. Update `.github/workflows/release.yml` install step:
   - Change: `pip install -e ".[dev]"`
   - To: `pip install -e ".[dev,ast]"`
3. Commit: e.g., `ci: fix release workflow to install ast extras for tests`.
4. Merge to `main`.
5. Re-run Phase 30 (workflow_dispatch with `dry_run=true`) on updated `main`.

After Phase 30-fix and Phase 30 re-run succeed: proceed to Phase 31 (final re-audit + v4.3.0 authorization).

## v4.3.0 authorization

- Authorized now: no
- Reason: The dry-run ran but failed (`Run tests` exit code 4). Phase 27 Decision 4 requires the dry-run to confirm test suite passes and build produces 4.3.0 artifacts. Neither was confirmed in the GitHub Actions environment. A workflow install fix is required before Phase 30 can be re-run successfully.

## Risks / deviations

- **Pre-existing workflow install gap**: the `[ast]` extras were not included in the release workflow install step. This was not caught in Phase 28 (which only updated workflow safety structure) or Phase 29 (which only validated local build with `tests/unit`). The gap was caught by Phase 30 dry-run — exactly the purpose of the dry-run gate.
- **No v4.3* tags created**: confirmed. The dry-run failure does not affect tag state.
- **Local vs CI environment divergence**: local Phase 29 validation used `tests/unit` and a fully-provisioned venv. The workflow uses `tests/` (all tests) and a clean Ubuntu environment. This divergence caused the failure.
- **GitHub Release gating verified**: the `Create GitHub Release` step was correctly skipped (`skipped` conclusion) — evidence that the gating condition `github.event_name == 'push' && github.ref_type == 'tag'` works on `workflow_dispatch` runs.

## Verdict

C. Dry-run evidence blocked — workflow install missing `[ast]` extras; test step failed; build not run
