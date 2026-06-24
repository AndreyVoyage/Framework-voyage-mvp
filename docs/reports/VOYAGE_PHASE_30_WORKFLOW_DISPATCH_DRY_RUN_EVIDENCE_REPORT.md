# Phase 30 Workflow Dispatch Dry-Run Evidence Report

## Scope

- Evidence collection phase on branch `docs/phase-30-dry-run-evidence-prompt`.
- Objective: trigger `workflow_dispatch` dry-run on `main` with `dry_run=true`, collect build/test evidence.
- Does not create tags, GitHub Releases, or publish to PyPI.
- Creates only: `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` (this file).

## Inputs

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md` — Decision 4: dry-run is mandatory before v4.3.0 tag.
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md` — Phase 28 implemented workflow_dispatch, dry_run, environment: release, gated release step.
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md` — Phase 29 bumped version to 4.3.0 in pyproject.toml + __init__.py; build produced 4.3.0 wheel + sdist; twine check PASSED.
- `.github/workflows/release.yml` — confirmed workflow_dispatch + dry_run + environment: release + gated release step.
- `pyproject.toml` — `version = "4.3.0"` confirmed.
- `voyage_framework/__init__.py` — `__version__ = "4.3.0"` confirmed.

## Preconditions

All preconditions verified before dry-run attempt:

**Git state:**
- `main` HEAD: `0ac02383708b8768920b4c7f892c231875d35a52` (Merge Phase 29 version bump to 4.3.0) — matches expected. — **SAFE**
- `origin/main`: `0ac02383708b8768920b4c7f892c231875d35a52` — in sync. — **SAFE**
- Working tree: clean (no tracked changes). — **SAFE**
- Local `v4.3*` tag: no output — none. — **SAFE**
- Remote `v4.3*` tag (`git ls-remote --tags origin`): no output — none. — **SAFE**

**Version check:**
- `pyproject.toml:7`: `version = "4.3.0"` — **SAFE**
- `voyage_framework/__init__.py:9`: `__version__ = "4.3.0"` — **SAFE**
- No `4.0.0` remains in either file. — **SAFE**

**Workflow check:**
- `workflow_dispatch`: present at `.github/workflows/release.yml:7` — **SAFE**
- `dry_run` input: present at line 9 — **SAFE**
- `environment: release`: present at line 18 — **SAFE**
- `Create GitHub Release` gating: `if: github.event_name == 'push' && github.ref_type == 'tag'` at line 43 — **SAFE**
- PyPI publish: commented out at line 51 — **SAFE**

## GitHub environment release protection

- Status: **UNKNOWN** — could not be determined because GitHub CLI authentication failed before workflow view could be verified.
- Classification: **UNKNOWN**

## Workflow dispatch command

- Not executed.
- Reason: GitHub CLI authentication check (`gh auth status`) returned exit code 1 with message "You are not logged into any GitHub hosts."
- Per hard-stop rules: dry-run blocked, `gh auth login` was NOT run.

## Workflow run evidence

- Run id: N/A — not executed
- Run URL: N/A
- Event: N/A
- Ref/branch: N/A
- Commit SHA: N/A
- dry_run input: N/A
- Status: N/A
- Conclusion: **BLOCKED** — GitHub CLI not authenticated

## Job evidence

- Not available. Workflow was not triggered due to authentication blocker.

## Build artifact evidence

- Not available. Workflow was not triggered.

## Twine check evidence

- Not available. Workflow was not triggered.
- Note: twine check was validated locally in Phase 29: `voyage_framework-4.3.0-py3-none-any.whl` PASSED, `voyage_framework-4.3.0.tar.gz` PASSED. This is local evidence only, not GitHub Actions evidence.

## GitHub Release gating evidence

- Not available. Workflow was not triggered.
- The `if: github.event_name == 'push' && github.ref_type == 'tag'` condition on the `Create GitHub Release` step is correct per Phase 28 implementation — would skip on `workflow_dispatch`. This is static analysis evidence only.

## PyPI publish evidence

- PyPI publish step remains commented out in `.github/workflows/release.yml:51`. — **SAFE**
- No PyPI publish was run or attempted.

## Tag check

- Local v4.3*: no output — none exists. — **SAFE**
- Remote v4.3*: no output (`git ls-remote --tags origin`) — none exists. — **SAFE**
- v4.1.0-mvp: `43e051219ade3f965de85a69110bf3bd93f1d4fe` → commit `086fefc8` — unchanged. — **SAFE**
- v4.2.0-adapter-contract: `6f6e38093a439eddefde1e1e8b272ffdafa88a13` → commit `8d7b268e` — unchanged. — **SAFE**

## Version check

- pyproject.toml: `version = "4.3.0"` (line 7) — **SAFE**
- voyage_framework/__init__.py: `__version__ = "4.3.0"` (line 9) — **SAFE**

## Downloaded artifacts

- Not available. Workflow was not triggered.

## Validation summary

- Git preconditions: all SAFE — main at correct SHA, versions correct, tags clean, workflow confirmed.
- GitHub CLI auth: **BLOCKER** — `gh auth status` → exit 1, not logged in.
- Workflow execution: not attempted.
- Build evidence from GitHub Actions: not available.

## Forbidden actions check

- No tags created. — **SAFE**
- No GitHub Release created. — **SAFE**
- No PyPI publish. — **SAFE**
- No source files edited. — **SAFE**
- No workflow files edited. — **SAFE**
- `gh auth login` was NOT run. — **SAFE** (per hard-stop rules)

## Remaining blockers

1. **GitHub CLI not authenticated** — **BLOCKER**: `gh auth status` fails. Run `gh auth login` manually (outside this phase) to authenticate with GitHub, then re-run Phase 30.
2. **No dry-run evidence from GitHub Actions** — **BLOCKER** (carry-over from Phase 27): Phase 31 cannot authorize the tag without confirmed dry-run evidence. Phase 30 must be re-run after authentication is resolved.
3. **GitHub environment `release` protection rules** — **WARNING** (carry-over from Phase 28): must be configured in GitHub repository Settings → Environments → `release` → Required reviewers before Phase 32 tag push.

## Next phase

**Resolve GitHub CLI authentication, then re-run Phase 30.**

Steps:
1. Run `gh auth login` manually (outside Claude Code, or with user's explicit approval).
2. Confirm `gh auth status` returns authenticated.
3. Re-run Phase 30 execution:
   - `gh workflow run release.yml --ref main -f dry_run=true`
   - Watch run: `gh run watch <RUN_ID> --exit-status --interval 10`
   - If run waits for environment approval, approve in GitHub Actions UI.
   - Collect log evidence: tests passed, `voyage_framework-4.3.0-*.whl` + `voyage_framework-4.3.0.tar.gz` built, `Create GitHub Release` step skipped.
   - Record run id and run URL.
4. Create updated Phase 30 report with full evidence.
5. Commit updated report.

After Phase 30 completes with evidence: proceed to Phase 31 (final re-audit + v4.3.0 authorization).

## v4.3.0 authorization

- Authorized now: no
- Reason: GitHub CLI authentication failure blocked the dry-run. No GitHub Actions evidence has been collected. Phase 27 Decision 4 requires dry-run evidence before tag authorization. Phase 31 re-audit cannot proceed until Phase 30 completes successfully.

## Risks / deviations

- **`gh auth login` NOT run**: per hard-stop rules. User must authenticate manually. After authentication, Phase 30 can be re-run without changing any source, workflow, or version files.
- **All git preconditions passed**: main is at the correct Phase 29 commit, versions are 4.3.0, no unauthorized tags exist. The only blocker is GitHub CLI authentication.
- **No deviations from allowed scope**: no source files edited, no tags created, no releases triggered.

## Verdict

C. Dry-run evidence blocked — GitHub CLI not authenticated
