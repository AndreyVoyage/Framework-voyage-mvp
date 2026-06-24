# Phase 30 Workflow Dispatch Dry-Run Evidence Report

## Scope

- Evidence collection phase — two branches used: `docs/phase-30-dry-run-evidence-prompt` (blocked run) and `docs/phase-30-rerun-dry-run-evidence` (this successful rerun).
- Objective: trigger `workflow_dispatch` dry-run on `main` with `dry_run=true`, collect build/test evidence.
- Does not create tags, GitHub Releases, or publish to PyPI.
- Creates/updates only: `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` (this file).
- Three execution history: (1) blocked by GitHub CLI auth failure; (2) run `28077532312` failed `Run tests` — missing `[ast]` extras; (3) this run `28080683596` — all steps passed after Phase 30A fix.

## Inputs

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` — Decision 4: dry-run mandatory before v4.3.0 tag; must produce 4.3.0 wheel and sdist, tests must pass.
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` — Phase 28 workflow: `pytest tests/ -q`, `python -m build`, safety controls.
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` — version 4.3.0 confirmed; local build validated; twine check PASSED locally.
- `docs/reports/VOYAGE_PHASE_30A_RELEASE_WORKFLOW_AST_EXTRAS_FIX_REPORT.md` — Phase 30A fix: `pip install -e ".[dev]"` → `pip install -e ".[dev,ast]"`. Merged to `main` at `3f50bab`.
- `.github/workflows/release.yml` — confirmed: `workflow_dispatch`, `dry_run default: true`, `environment: release`, gated release step, `pip install -e ".[dev,ast]"`, PyPI commented.
- `pyproject.toml` — `version = "4.3.0"` confirmed.
- `voyage_framework/__init__.py` — `__version__ = "4.3.0"` confirmed.

## Preconditions

All preconditions verified before rerun:

**Git state:**
- `main` HEAD: `3f50babd6554c6fdcbd442c07d8d95671fdb2a73` (Merge Phase 30A release workflow AST extras fix) — correct. — **SAFE**
- `origin/main`: `3f50babd6554c6fdcbd442c07d8d95671fdb2a73` — in sync. — **SAFE**
- Working tree: clean. — **SAFE**
- Local `v4.3*` tag: none. — **SAFE**
- Remote `v4.3*` tag: none. — **SAFE**

**Version check:**
- `pyproject.toml:7`: `version = "4.3.0"` — **SAFE**
- `voyage_framework/__init__.py:9`: `__version__ = "4.3.0"` — **SAFE**
- No `4.0.0` in either file. — **SAFE**

**Workflow check (post-Phase 30A):**
- `pip install -e ".[dev,ast]"` at line 33 — **SAFE** (Phase 30A fix applied)
- `workflow_dispatch` at line 7 — **SAFE**
- `dry_run` input at line 9 — **SAFE**
- `environment: release` at line 18 — **SAFE**
- `Create GitHub Release` gated at line 43: `if: github.event_name == 'push' && github.ref_type == 'tag'` — **SAFE**
- PyPI publish commented at line 51 — **SAFE**

**GitHub CLI auth:**
- `gh auth status`: `✓ Logged in to github.com account AndreyVoyage (keyring)` — **SAFE**
- Token scopes: `gist, read:org, repo, workflow` — **SAFE**

## Previous failed dry-run

Run ID `28077532312` (Phase 30 first attempt, ref `main` at `0ac0238`):
- Failed step: `Run tests` — exit code 4 — `ImportError: tree-sitter extras not installed`
- Root cause: `pip install -e ".[dev]"` missing `[ast]` extras
- Fix applied in Phase 30A: `pip install -e ".[dev,ast]"` — merged to `main` at `3f50bab`
- `Create GitHub Release`: correctly skipped (event was `workflow_dispatch`)
- Run URL: https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28077532312

## GitHub environment release protection

- Status: **WARNING** — the `release` environment exists (created by YAML `environment: release`), but no Required Reviewers are configured in GitHub repository Settings → Environments → `release`. The workflow job ran immediately without manual approval gate.
- Both runs (28077532312 and 28080683596) started without approval wait — confirming no protection rules are set.
- Must be configured before Phase 32 tag push.
- Classification: **WARNING** (carry-over from Phase 28).

## Workflow dispatch command

```bash
gh workflow run release.yml --ref main -f dry_run=true
```

Output: `https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28080683596`

## Workflow run evidence

- Run id: `28080683596`
- Run URL: https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28080683596
- Event: `workflow_dispatch`
- Ref/branch: `main`
- Commit SHA: `3f50babd6554c6fdcbd442c07d8d95671fdb2a73` (Merge Phase 30A release workflow AST extras fix)
- dry_run input: `true` (dispatched with `-f dry_run=true`; default in workflow is also `true`)
- Status: `completed`
- Conclusion: `success`
- Created at: `2026-06-24T06:49:58Z`
- Updated at: `2026-06-24T06:50:50Z`

## Job evidence

Job: `Build and release` (ID: `83134677087`)
- Duration: 47 seconds
- Conclusion: `success`

Step results:
| Step | Result | Notes |
|------|--------|-------|
| Set up job | ✓ success | Ubuntu 24.04, runner 2.335.1 |
| Checkout repository | ✓ success | |
| Set up Python | ✓ success | Python 3.12 |
| Install package and build tools | ✓ success | `voyage-framework==4.3.0` installed; `[dev,ast]` extras installed; `tree-sitter>=0.22` downloaded |
| Run tests | ✓ success | `416 passed in 18.41s` |
| Build distribution packages | ✓ success | `voyage_framework-4.3.0.tar.gz` and `voyage_framework-4.3.0-py3-none-any.whl` |
| Create GitHub Release | – skipped | Correct: `github.event_name == 'workflow_dispatch'` ≠ `'push'` |
| Post Set up Python | ✓ success | |
| Post Checkout repository | ✓ success | |
| Complete job | ✓ success | |

**No failures. No errors. All required steps passed.**

## Build artifact evidence

From `Build distribution packages` step log:

```
creating '/home/runner/work/Framework-voyage-mvp/Framework-voyage-mvp/dist/.tmp-wvdnkauo/voyage_framework-4.3.0-py3-none-any.whl'
Successfully built voyage_framework-4.3.0.tar.gz and voyage_framework-4.3.0-py3-none-any.whl
```

- `voyage_framework-4.3.0-py3-none-any.whl` — **confirmed produced in GitHub Actions** — **SAFE**
- `voyage_framework-4.3.0.tar.gz` — **confirmed produced in GitHub Actions** — **SAFE**
- Version label: `4.3.0` — matches `pyproject.toml` and `__init__.py` — **SAFE**

Note: The workflow does not upload artifacts (`upload-artifact` step absent). Artifacts exist in the runner's `dist/` directory during the job but are not downloadable via `gh run download`. Log evidence is the authoritative record.

## Twine check evidence

- The release workflow does not include an explicit `twine check` step. The `python -m build` step produces the artifacts; no post-build twine check is run in CI.
- Local Phase 29 evidence (from `VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md`): `twine check dist/voyage_framework-4.3.0-py3-none-any.whl` → `PASSED`; `twine check dist/voyage_framework-4.3.0.tar.gz` → `PASSED`.
- CI build succeeded (non-zero exit would have failed the step). Artifacts produced are the same package version validated locally.
- Classification: **WARNING** — no in-workflow twine check; local evidence satisfies Phase 27 Decision 4 requirements.

## GitHub Release gating evidence

- `Create GitHub Release` step: **skipped** (conclusion: `skipped`).
- Gating condition: `if: github.event_name == 'push' && github.ref_type == 'tag'` — evaluates to `false` for `workflow_dispatch` event.
- Verified in both run `28077532312` (skipped even on failed job) and run `28080683596` (skipped on successful job).
- No GitHub Release was created. — **SAFE**

## PyPI publish evidence

- PyPI publish step is commented out in `.github/workflows/release.yml:49-53`. Step does not appear in the job at all.
- No PyPI publish was attempted. — **SAFE**

## Tag check

- Local v4.3*: none — **SAFE**
- Remote v4.3*: none (`git ls-remote --tags origin "refs/tags/v4.3*"` → no output) — **SAFE**
- v4.1.0-mvp: `43e051219ade3f965de85a69110bf3bd93f1d4fe` → commit `086fefc8` — unchanged — **SAFE**
- v4.2.0-adapter-contract: `6f6e38093a439eddefde1e1e8b272ffdafa88a13` → commit `8d7b268e` — unchanged — **SAFE**

## Version check

- pyproject.toml: `version = "4.3.0"` (line 7) — **SAFE**
- voyage_framework/__init__.py: `__version__ = "4.3.0"` (line 9) — **SAFE**
- `voyage-framework==4.3.0` confirmed installed in GitHub Actions (from install step log: `Collecting pydantic>=2.0 (from voyage-framework==4.3.0)`) — **SAFE**

## Downloaded artifacts

- `gh run download 28080683596 --dir docs/handoff/phase30/artifacts` → `no valid artifacts found to download`.
- Expected: workflow does not include `upload-artifact` step; artifacts remain in runner's `dist/` during job and are not downloadable.
- Log evidence is the authoritative record. — **WARNING**: no downloadable artifacts from workflow (by design — workflow not configured to upload).

## Validation summary

| Check | Result | Classification |
|-------|--------|----------------|
| Git preconditions | PASS | SAFE |
| GitHub CLI auth | PASS | SAFE |
| Version 4.3.0 in both files | PASS | SAFE |
| Workflow structure (dispatch/dry_run/env/gate) | PASS | SAFE |
| `.[dev,ast]` install (Phase 30A fix) | PASS | SAFE |
| Workflow dispatch executed | PASS | SAFE |
| `voyage-framework==4.3.0` installed in CI | PASS (from log) | SAFE |
| Test suite passed | PASS — 416 passed | SAFE |
| Build step ran | PASS — success | SAFE |
| `voyage_framework-4.3.0-py3-none-any.whl` from CI | PASS (log evidence) | SAFE |
| `voyage_framework-4.3.0.tar.gz` from CI | PASS (log evidence) | SAFE |
| Twine check from CI | WARNING — not in workflow | WARNING |
| Create GitHub Release skipped | PASS — step skipped | SAFE |
| PyPI publish disabled | PASS — commented out | SAFE |
| No v4.3* tag created | PASS | SAFE |

## Forbidden actions check

- No tags created. — **SAFE**
- No GitHub Release created. — **SAFE**
- No PyPI publish. — **SAFE**
- No source files edited (pyproject.toml, voyage_framework/*, tests/*). — **SAFE**
- No workflow files edited. — **SAFE**
- `gh auth login` was NOT run in either session. — **SAFE**
- No force-push. — **SAFE**

## Remaining blockers

1. **`release` environment protection rules not configured** — **WARNING** (carry-over from Phase 28): the workflow ran without approval, confirming protection rules are not configured. Must be configured in GitHub Settings → Environments → `release` → Required reviewers (add `AndreyVoyage`) before Phase 32 tag push.
2. **No in-workflow twine check step** — **WARNING**: the release workflow does not run `twine check` after build. Local Phase 29 evidence passes twine check. If strict CI validation is desired, a `twine check dist/*` step can be added in a future phase.

No remaining BLOCKERs.

## Next phase

**Phase 31 — Final release readiness re-audit.**

All Phase 27 Decision 4 dry-run requirements are now satisfied:
- `pytest tests/ -q` passed: 416 tests in GitHub Actions environment
- `python -m build` produced `voyage_framework-4.3.0-py3-none-any.whl` and `voyage_framework-4.3.0.tar.gz`
- `Create GitHub Release` step correctly skipped on `workflow_dispatch`
- No v4.3* tags exist

Before Phase 32 (tag push):
1. Configure GitHub Settings → Environments → `release` → Required reviewers.
2. Complete Phase 31 final re-audit (check all 5 phases, all safety controls, all version checks, no blockers).
3. Receive explicit v4.3.0 authorization from Phase 31.
4. Only then proceed to Phase 32.

## v4.3.0 authorization

- Authorized now: no
- Reason: Phase 30 dry-run requirements confirmed (tests pass, 4.3.0 artifacts produced). However, Phase 31 final re-audit must be completed before authorization. Additionally, the `release` environment protection rules must be configured before Phase 32 tag push (WARNING carry-over).

## Risks / deviations

- **Node.js 20 deprecation annotation**: GitHub Actions emitted `Node.js 20 is deprecated... actions/checkout@v4, actions/setup-python@v5`. This is a runner-level warning, not a job failure. Not a blocker. Actions should be bumped to @v5 in a future maintenance phase.
- **Test count 416 vs. 399**: local Phase 29 validation ran `pytest tests/unit -q` (399 tests). The release workflow runs `pytest tests/ -q` (all tests, including integration/ast tests enabled by `[ast]` extras). 416 is the authoritative count for the full test suite in the release environment.
- **No in-workflow twine check**: the release workflow builds distribution packages but does not run `twine check`. This is a WARNING, not a blocker. Local Phase 29 evidence confirms twine check passes.
- **No v4.3* tags created**: confirmed.

## Verdict

A. Dry-run evidence collected, ready for final re-audit phase
