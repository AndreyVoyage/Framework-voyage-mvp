# Phase 32 v4.3.0 Tag and Protected Release Trigger Report

## Scope

- Tag and release trigger phase for Voyage Framework v4.3.0.
- Objective: create annotated tag `v4.3.0` on `main`, push it to trigger the protected GitHub Actions release workflow, obtain environment approval, monitor the run, and collect evidence.
- Creates only: `docs/reports/VOYAGE_PHASE_32_V4_3_0_TAG_RELEASE_TRIGGER_REPORT.md` (this file).
- Does not edit source files, workflow files, or version files. Does not publish to PyPI. Does not bypass environment approval.

## Preconditions

- Branch: `docs/phase-32-v4-3-0-tag-release-trigger-prompt`
- HEAD (main at tag time): `c3e8d5949c042d955c916ba794e44577c5a5eaf4` (Merge Phase 31 final release readiness re-audit) — **matches authorized commit** — SAFE
- origin/main: `c3e8d5949c042d955c916ba794e44577c5a5eaf4` — in sync — SAFE
- Working tree: clean before tag creation — SAFE
- Local v4.3* tags: none before tag creation — SAFE
- Remote v4.3* tags: none before tag push — SAFE
- Phase 31 authorization: `v4.3.0 tag authorized: yes` — 17/17 criteria pass — verdict A — SAFE

## Version readiness

- pyproject.toml: `version = "4.3.0"` at line 7 — **SAFE**
- voyage_framework/__init__.py: `__version__ = "4.3.0"` at line 9 — **SAFE**
- No `4.0.0` remaining in either file — **SAFE**

## Workflow safety readiness

- workflow_dispatch: line 7 — **SAFE**
- dry_run default: `default: true` at line 12 — **SAFE**
- environment release: `environment: release` at line 18 — **SAFE**
- install extras: `pip install -e ".[dev,ast]"` at line 33 — **SAFE** (Phase 30A fix applied)
- GitHub Release gating: `if: github.event_name == 'push' && github.ref_type == 'tag'` at line 43 — **SAFE**
- PyPI publish policy: commented out at line 51 (`# uses: pypa/gh-action-pypi-publish@release/v1`) — **SAFE**

All 6 release workflow safety controls confirmed present and correct. — **SAFE**

## Environment protection

- Required reviewers: `AndreyVoyage` — **SAFE**
- can_admins_bypass: `false` — **SAFE**
- prevent_self_review: `false` — **SAFE** (intentional single-owner configuration)
- Environment id: `17141902974`, name: `release`, updated_at: `2026-06-24T08:52:02Z`
- protection_rules: 1 rule — type `required_reviewers`, reviewer `AndreyVoyage`
- Classification: **SAFE**

## Tag creation

- Tag: `v4.3.0`
- Type: annotated (`git tag -a`) — **SAFE** (not lightweight)
- Message: `Release v4.3.0`
- Target commit: `c3e8d5949c042d955c916ba794e44577c5a5eaf4` (Merge Phase 31 final release readiness re-audit)
- Tagger: `AndreyVoyage <andrcom83@yandex.ru>`
- Local tag created: yes — `git show v4.3.0 --no-patch` confirmed annotated tag object
- Remote tag pushed: yes — `git push origin v4.3.0` → `* [new tag] v4.3.0 -> v4.3.0`
- Remote verification: `e46ebf25cbabab962a4fdd0c7fff7efb7dfe13d9 refs/tags/v4.3.0` (annotated object) + `c3e8d5949c042d955c916ba794e44577c5a5eaf4 refs/tags/v4.3.0^{}` (dereferenced commit) — confirms annotated tag — **SAFE**

## Workflow run

- Run ID: `28089992113`
- Run URL: https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/28089992113
- Event: `push`
- Ref/tag: `v4.3.0`
- Commit SHA: `c3e8d5949c042d955c916ba794e44577c5a5eaf4`
- Status: `completed`
- Conclusion: `success`
- Created at: `2026-06-24T09:48:41Z`
- Updated at: `2026-06-24T10:21:40Z`
- Job name: `Build and release` (ID: `83165320243`)
- Job started: `2026-06-24T10:20:47Z`
- Job completed: `2026-06-24T10:21:39Z`
- Duration: ~52 seconds

Step results:

| Step | Result | Notes |
|------|--------|-------|
| Set up job | ✓ success | |
| Checkout repository | ✓ success | |
| Set up Python | ✓ success | Python 3.12 |
| Install package and build tools | ✓ success | `voyage-framework==4.3.0` + `[dev,ast]` extras installed |
| Run tests | ✓ success | `416 passed in 18.97s` |
| Build distribution packages | ✓ success | `voyage_framework-4.3.0.tar.gz` and `voyage_framework-4.3.0-py3-none-any.whl` built |
| Create GitHub Release | ✓ success | Both artifacts uploaded; release published |
| Post Set up Python | ✓ success | |
| Post Checkout repository | ✓ success | |
| Complete job | ✓ success | |

**No failures. No errors. All steps passed.**

## Environment approval

- Required: yes (`environment: release`, `can_admins_bypass: false`)
- Approved by: `AndreyVoyage` (manual approval in GitHub Actions UI)
- Evidence: run status transitioned from `waiting` to `completed` conclusion `success` after user approval; job started at `2026-06-24T10:20:47Z` (well after tag push at `09:48:41Z`), confirming the approval gate was active and respected

## GitHub Release evidence

- Release URL: https://github.com/AndreyVoyage/Framework-voyage-mvp/releases/tag/v4.3.0
- Tag: `v4.3.0`
- Name: `v4.3.0`
- Draft: `false`
- Prerelease: `false`
- Target commitish: `main`
- Created at: `2026-06-24T09:48:23Z`
- Published at: `2026-06-24T10:21:37Z`
- Release ID: `344032542`
- Assets uploaded:
  - `voyage_framework-4.3.0-py3-none-any.whl` — ✅ uploaded (from CI log: `✅ Uploaded voyage_framework-4.3.0-py3-none-any.whl`)
  - `voyage_framework-4.3.0.tar.gz` — ✅ uploaded (from CI log: `✅ Uploaded voyage_framework-4.3.0.tar.gz`)
- CI log: `🎉 Release ready at https://github.com/AndreyVoyage/Framework-voyage-mvp/releases/tag/v4.3.0`

## PyPI publish evidence

- PyPI publish step is commented out in `.github/workflows/release.yml:49-53`. Step does not appear in the job.
- No `twine upload` was executed. No `Publish to PyPI` step in CI log.
- No upload to `pypi.org` occurred.
- `twine` installed as a package dependency (listed in `pyproject.toml` extras) — installation only, not execution.
- Classification: **SAFE** — no PyPI publish

## Tag verification

- Local v4.3.0: exists — annotated tag object → commit `c3e8d59` — **SAFE**
- Remote v4.3.0: exists — `e46ebf25cbabab962a4fdd0c7fff7efb7dfe13d9` (annotated object) → `c3e8d5949c042d955c916ba794e44577c5a5eaf4^{}` — **SAFE**
- Unexpected v4.3* tags: none — only `v4.3.0` exists among `v4.3*` — **SAFE**
- Existing tags unchanged: `v4.1.0-mvp` and `v4.2.0-adapter-contract` — not touched — **SAFE**

## Generated artifacts / local hygiene

- `.claude/`: ignored (`!!`), not staged — **SAFE**
- `dist/`: ignored (`!!`), not staged — **SAFE**
- `docs/handoff/LATEST_AGENT_REPORT.md`: ignored (`!!`), not staged — **SAFE**
- `docs/handoff/NEXT_ACTION.md`: ignored (`!!`), not staged — **SAFE**
- `voyage_framework.egg-info/`: ignored (`!!`), not staged — **SAFE**
- Only tracked change: `A docs/reports/VOYAGE_PHASE_32_V4_3_0_TAG_RELEASE_TRIGGER_REPORT.md` — **SAFE**

## Remaining warnings

1. **Node.js 20/24 transition** — CI log: `Node 20 is being deprecated. This workflow is running with Node 24 by default.` — `softprops/action-gh-release@v2` ran on Node 24 automatically. Non-blocking. `actions/checkout@v4` and `actions/setup-python@v5` should still be bumped to @v5 in a future maintenance phase. — **WARNING**
2. **Release tag discoverability delay** — CI log: `Release 344032542 is not yet discoverable by tag v4.3.0, retrying... (2 retries remaining)` / `⚠️ Continuing with newly created release 344032542 because tag v4.3.0 is still not discoverable`. This is a known GitHub API propagation delay — the release was created immediately before the tag was fully indexed. Both assets were uploaded and the release was published successfully. Non-blocking. — **WARNING**
3. **No in-workflow twine check** (carry-over): non-blocking. Local Phase 29 twine check passed; CI build succeeded.
4. **`prevent_self_review: false`** (carry-over): reviewer is also the tag pusher. Intentional single-owner configuration. — **WARNING** (informational only)

## Remaining blockers

None. — **SAFE**

## Rollback needed

- no
- Reason: All steps completed successfully. GitHub Release v4.3.0 is published with both dist artifacts. No errors or incorrect state.

## Final release status

- v4.3.0 GitHub Release: **PUBLISHED** at https://github.com/AndreyVoyage/Framework-voyage-mvp/releases/tag/v4.3.0
- Assets: `voyage_framework-4.3.0-py3-none-any.whl` and `voyage_framework-4.3.0.tar.gz` uploaded
- Tests: `416 passed` in GitHub Actions
- PyPI: **not published** (step commented out — intentional)
- Tag: `v4.3.0` annotated, pushed, verified on remote
- Environment gate: respected — `AndreyVoyage` approved manually before job ran

## Risks / deviations

- **Node.js 24 automatic migration**: `softprops/action-gh-release@v2` ran on Node 24 (GitHub migrated it automatically from Node 20). This is a carry-over WARNING from Phase 28/30/31. No impact on release quality. Action should be pinned to @v3 (Node 20) or upgraded to a Node 24-native version in a future maintenance phase.
- **Release discoverability retry**: `softprops/action-gh-release@v2` retried 2 times due to GitHub API propagation latency, then continued with a warning. Both assets were uploaded and release was finalized — not a concern.
- **Phase 30 dry-run ran without approval gate**: historical note — dry-runs in Phase 30 ran without environment protection rules. In this Phase 32 real release, the gate was active and required manual approval. No deviation.
- **No deviations from prompt specification.** All checks ran as specified. No forbidden actions taken.

## Verdict

A. v4.3.0 tag pushed and protected release completed
