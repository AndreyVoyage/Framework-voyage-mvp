# Phase 27 Version & Release Workflow Policy Decision Plan

## Scope

- Policy analysis and decision-only phase on branch `docs/phase-27-version-release-policy-decision-plan`.
- No code, tests, package metadata, release workflows, tags, merges, or pushes were performed.
- Analyzes the two remaining blockers identified by Phase 26: version mismatch and unsafe release workflow trigger.
- Produces structured policy decisions for version target, tag naming, release workflow, dry-run requirement, and rollback.
- Creates only: `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`, `docs/handoff/LATEST_AGENT_REPORT.md`, `docs/handoff/NEXT_ACTION.md`.

## Current state

- Branch: `docs/phase-27-version-release-policy-decision-plan`.
- HEAD commit: `fd07626` — `docs: add Phase 27 version release policy prompt`.
- Base `main`: `078922f` — `Merge handoff clipboard UTF-8 fix`.
- `git status --short`: clean (no output before report creation).
- `git tag --list "v4.3*"`: no output — no v4.3 tag exists.
- Existing release tags: `v4.1.0-mvp`, `v4.2.0-adapter-contract`.
- Identity, package/API/CLI, and docs blockers from Phase 21/23/24/25/26 are closed.
- Two blockers remain from Phase 26: version mismatch and unsafe release workflow trigger policy.

## Phase 26 blockers

1. **Version mismatch** — `BLOCKER`: `pyproject.toml` and `voyage_framework/__init__.py` remain at `4.0.0`. Creating a `v4.3` tag while the package version is `4.0.0` would cause `.github/workflows/release.yml` to build and publish distribution artifacts whose metadata version is `4.0.0`, contradicting the tag.
2. **Release workflow trigger** — `BLOCKER`: `.github/workflows/release.yml` fires on every `v*` tag push with no `workflow_dispatch` input, no dry-run gate, no manual approval step, and no explicit rollback procedure. An inadvertent or premature tag push immediately triggers a full build + GitHub Release creation.

## Version inventory

- pyproject.toml: `version = "4.0.0"` (line 7) — **BLOCKER**
- voyage_framework/__init__.py: `__version__ = "4.0.0"` (line 9) — **BLOCKER**
- README/docs: Version references describe v4.1/v4.2 canonical architecture and v4.3 as "current documentation direction, not a published release, tag, or runtime layer" — **WARNING**: docs must be updated to reflect published release once version bump is applied, but no doc content blocks planning today.
- tags: `v4.1.0-mvp` (object `43e051219ade3f965de85a69110bf3bd93f1d4fe`), `v4.2.0-adapter-contract` (object `6f6e38093a439eddefde1e1e8b272ffdafa88a13`). No `v4.3*` tag exists — **SAFE**.

## Release workflow inventory

- `.github/workflows/release.yml` trigger: `on: push: tags: ["v*"]` — fires on any tag matching `v*`. No `workflow_dispatch`. No dry-run input. No manual gate. — **BLOCKER**
- Steps (in order): checkout → setup Python 3.12 → `pip install -e ".[dev]"` + `pip install build` → `pytest tests/ -q` → `python -m build` → `softprops/action-gh-release@v2` (attaches `dist/*`, auto-generates release notes). — **BLOCKER** (no dry-run path)
- PyPI publish step: commented out (`# uses: pypa/gh-action-pypi-publish@release/v1`, secret `PYPI_API_TOKEN`). — **WARNING**: commented-out step is not currently active, but requires explicit policy decision before any tag. Risk: uncommenting without dry-run evidence could inadvertently publish to PyPI.
- `.github/workflows/jekyll-gh-pages.yml`: deploys GitHub Pages from `docs/` on push to `main` and on `workflow_dispatch`. Pages deploy is independent of the release workflow. — **SAFE**
- `.github/workflows/ci.yml`: runs tests on push/PR across Python 3.11/3.12, uploads coverage artifacts. — **SAFE**
- `pyproject.toml` dev extras include `build>=1.0` and `twine>=5.0` — present but not invoked by the current release.yml (uses `python -m build` directly, twine not called). — **SAFE**

## Risk analysis

- **R1 — BLOCKER**: Tag `v*` trigger fires immediately on tag push. No gate. If a `v4.3` or `v4.3.0` tag is pushed today with `4.0.0` metadata, a GitHub Release containing `voyage-framework-4.0.0-*.whl` and `voyage-framework-4.0.0.tar.gz` would be created automatically and attached to a tag claiming to be v4.3.
- **R2 — BLOCKER**: No dry-run evidence exists. The release workflow has never been triggered. Artifact correctness, test pass under the workflow environment, and build output have not been verified non-destructively.
- **R3 — BLOCKER**: No rollback policy exists. If the release workflow fails mid-flight (e.g., after creating the GitHub Release but before all artifacts upload), there is no documented recovery procedure.
- **R4 — WARNING**: PyPI publish is commented out but present. Without a policy decision, a future contributor might uncomment it without first establishing a dry-run record or PyPI API token governance. Once published to PyPI, a release cannot be fully retracted (only yanked).
- **R5 — WARNING**: `pyproject.toml` `langgraph` optional extra is not labeled as deprecated/legacy in metadata. Phase 24 policy decided to retain it as legacy compatibility, but the metadata does not communicate this to consumers. This is not a release blocker but should be addressed in a packaging cleanup phase.
- **R6 — WARNING**: README/docs describe v4.3 as "documentation direction, not a published release." Once `4.3.0` is the package version and a release tag exists, these sentences will need updating to reflect the published release status.
- **R7 — SAFE**: `v4.3*` tag does not exist. No tag has been created or deleted by this or any prior phase.
- **R8 — SAFE**: CI (`ci.yml`) runs independently and is not coupled to the release trigger. Tests pass (Phase 26: 399 unit tests passed).

## Decision 1: version target

- Decision: The package version must be updated to `4.3.0` (SemVer) in both `pyproject.toml` and `voyage_framework/__init__.py` in a single atomic commit before any `v4.3.0` tag is created.
- Rationale: SemVer requires that the version encoded in the package distribution metadata match the version communicated by the tag. `4.3.0` is the logical next release version: major `4` is stable (v4.1.0-mvp established it), minor `3` reflects the documentation/identity milestone series now closing, patch `0` is correct for a first release at this minor. Using `4.3.0` produces `voyage-framework-4.3.0-*.whl` and `voyage-framework-4.3.0.tar.gz`, which are consistent with the tag. Keeping `4.0.0` would produce artifacts whose metadata contradicts the tag and mislead consumers.
- Alternatives rejected:
  - `4.3` (no patch): rejected — not valid PEP 440 normalized form for wheel metadata; setuptools normalizes it to `4.3.0` internally but explicit `4.3.0` is cleaner and unambiguous.
  - `4.2.1` (patch bump from 4.2): rejected — `v4.2.0-adapter-contract` is already the v4.2 tag; a 4.2.x series would imply a patch fix on v4.2, not a documentation-milestone release.
  - Keeping `4.0.0`: rejected — creates artifact/tag mismatch, classified as BLOCKER.

## Decision 2: tag naming

- Decision: The release tag must be `v4.3.0`. An optional descriptive label suffix (e.g., `-knowledge-os` or `-docs-milestone`) may be added at the maintainer's discretion to follow the project's historical convention (`v4.1.0-mvp`, `v4.2.0-adapter-contract`), but the base SemVer form `v4.3.0` is the minimum required form and must be present.
- Rationale: Existing tags use the pattern `v{major}.{minor}.{patch}-{label}`. The plain `v4.3.0` satisfies SemVer and is sufficient for the `v*` wildcard in the release workflow. A label suffix is optional and cosmetic; it does not change the workflow behavior. Using `v4.3` (no patch) is rejected because: (a) it is inconsistent with the existing `v4.1.0-mvp` / `v4.2.0-adapter-contract` pattern; (b) SemVer mandates three-component versions; (c) `softprops/action-gh-release@v2` uses the tag name as the release title — `v4.3.0` is more precise.
- Alternatives rejected:
  - `v4.3` (no patch): rejected — SemVer violation, inconsistent with existing tag pattern.
  - `v4.3.0-alpha` or `v4.3.0-rc1`: rejected — the project is not using pre-release identifiers and the milestone series is complete enough to warrant a stable designation.
  - Annotated vs. lightweight tag: this phase does not mandate one or the other, but annotated tags (with a message) are preferred for release tags as they carry a timestamp and tagger identity. The implementation phase should create an annotated tag.

## Decision 3: release workflow policy

- Decision: `.github/workflows/release.yml` must be updated (in a dedicated implementation phase, prior to any tag) to: (1) add `workflow_dispatch` as a trigger with a boolean `dry_run` input (default `false`); (2) gate the `Create GitHub Release` step with `if: ${{ !inputs.dry_run }}` so a manual dispatch with `dry_run: true` performs the full build and test pipeline without creating a public release or publishing to PyPI; (3) keep the PyPI publish step commented out until a separate PyPI governance policy is approved and a PYPI_API_TOKEN secret is configured; (4) add an explicit `environment` protection rule (GitHub repository environment named `release`) on the `release` job to require manual approval before any tag-triggered release proceeds.
- Rationale: The current workflow fires immediately on any `v*` tag with no gate. This is unsafe for a project that has not yet performed a dry-run and has no rollback procedure. A `workflow_dispatch` dry-run mode is the minimal-overhead mechanism to verify artifact correctness without publishing. An environment protection rule provides a second gate: even if a tag is pushed, a human reviewer must approve the deployment before it executes. This is standard practice for production Python package releases.
- Alternatives rejected:
  - Disable the `v*` tag trigger entirely and use only `workflow_dispatch`: partially desirable but loses the ergonomics of tag-based releases for future automation; retaining the `v*` trigger with environment approval is the better balance.
  - Add a `concurrency` group only: insufficient — does not prevent execution, only serializes it.
  - Leave workflow unchanged and rely on not pushing a tag: rejected — human error is a real risk; the workflow must be self-protecting.

## Decision 4: dry-run requirement

- Decision: A successful `workflow_dispatch` dry-run of the updated release workflow (with `dry_run: true`) must be completed and documented before the `v4.3.0` tag may be authorized. The dry-run must cover: checkout, Python setup, package install (`.[dev]`), full test suite (`pytest tests/ -q`), and `python -m build`. It must produce `dist/voyage_framework-4.3.0-*.whl` and `dist/voyage_framework-4.3.0.tar.gz` without creating a GitHub Release or publishing to PyPI.
- Rationale: The release workflow has never been triggered in any prior phase. No evidence exists that `python -m build` produces correct artifacts under the workflow environment (Python 3.12, Ubuntu, from the current source state). Releasing without dry-run evidence means the first live trigger is also the first test — an unacceptable risk for a public GitHub Release.
- Evidence required:
  - GitHub Actions workflow run URL showing `workflow_dispatch` with `dry_run: true` completing successfully.
  - Workflow log excerpt confirming: (a) test suite passed (`pytest tests/ -q` exit 0); (b) `python -m build` produced `dist/voyage_framework-4.3.0-py3-none-any.whl` (or equivalent) and `dist/voyage_framework-4.3.0.tar.gz`; (c) no `Create GitHub Release` step was executed.
  - `twine check dist/*` output showing zero errors (this step should be added to the workflow or run manually as part of dry-run verification).

## Decision 5: rollback policy

- Decision: A documented rollback procedure must be approved and recorded before the `v4.3.0` tag is created. The rollback procedure is defined as follows and must be referenced in the implementation phase report.
- Rationale: Once a GitHub Release is created, it is publicly visible. Once published to PyPI, a version cannot be fully deleted (only yanked). Rollback without a pre-approved procedure requires ad-hoc decision-making under pressure. The procedure must be established before the risk exists.
- Required rollback steps:
  1. **If the GitHub Release was created but artifacts are wrong**: delete the release via `gh release delete v4.3.0 --yes --repo AndreyVoyage/Framework-voyage-mvp`; then delete the tag remotely `git push origin :refs/tags/v4.3.0` and locally `git tag -d v4.3.0`. Do not reuse the same tag name on a different commit.
  2. **If the GitHub Release was not yet created** (workflow failed before the release step): delete the tag locally and remotely as above. No public artifact exists; no further action needed.
  3. **If PyPI was published** (requires explicit uncommenting and secret configuration — not applicable today, PyPI step is commented out): file a PyPI support request to yank the release (`pip install --index-url https://pypi.org/simple/ voyage-framework==4.3.0` will still work but `pip install voyage-framework` will skip it). A yanked PyPI release cannot be re-uploaded under the same version; the next attempt must use `4.3.1` or a different version.
  4. **Version revert**: if the version bump commit was merged to `main` and rollback is required, create a new commit reverting `pyproject.toml` and `voyage_framework/__init__.py` to the pre-bump state. Do not use `git reset --hard` on `main`; do not force-push.
  5. **Documentation update**: if a release note or changelog was published referring to `4.3.0`, it must be updated to reflect the rollback with a brief explanation.

## Required implementation phases

- **Phase 28 — Release workflow implementation** (decision/implementation): Update `.github/workflows/release.yml` to add `workflow_dispatch` with `dry_run` input, gate the GitHub Release step, add environment protection (`release` environment), and add `twine check` to the dry-run path. This phase implements Decision 3. Does not create any tag.
- **Phase 29 — Version bump implementation** (implementation): Update `pyproject.toml` and `voyage_framework/__init__.py` to `4.3.0` in a single atomic commit. Verify `twine check dist/*` locally. This phase implements Decision 1. Does not create any tag.
- **Phase 30 — Dry-run execution and evidence collection** (verification): Trigger the updated release workflow via `workflow_dispatch` with `dry_run: true` after the Phase 29 version bump is on `main`. Document the workflow run URL and confirm artifact names contain `4.3.0`. This phase fulfills Decision 4.
- **Phase 31 — Final release readiness re-audit** (audit): Re-audit all Phase 26 and Phase 27 blockers after Phases 28–30. Confirm: (a) workflow updated; (b) version `4.3.0` in both files; (c) dry-run evidence recorded; (d) rollback procedure accepted. Issue v4.3.0 authorization if all pass.
- **Phase 32 — v4.3.0 tag and release** (release): Create annotated tag `v4.3.0` (or `v4.3.0-{label}` per Decision 2 label option). Push tag to trigger the release workflow. Monitor workflow execution and confirm GitHub Release is created with correct artifacts. Record release URL. This phase is authorized only after Phase 31 approval.

## Files expected to change in future implementation

- `pyproject.toml` — version field `"4.0.0"` → `"4.3.0"` (Phase 29)
- `voyage_framework/__init__.py` — `__version__ = "4.0.0"` → `__version__ = "4.3.0"` (Phase 29, same commit as pyproject.toml)
- `.github/workflows/release.yml` — add `workflow_dispatch` trigger with `dry_run` input; add `environment: release` to job; gate GitHub Release step (Phase 28)
- `README.md` — update "References to v4.3 describe the current documentation direction, not a published release" sentence to reflect published release status (Phase 29 or 31, WARNING-level, not a blocker)
- `docs/README.md` — same as README.md (Phase 29 or 31)

## Files that must not change

- `pyproject.toml` — must not change before Phase 28 workflow update is complete and merged.
- `voyage_framework/__init__.py` — must not change before Phase 28 workflow update is complete and merged.
- `.github/workflows/release.yml` — must not change outside of an explicitly approved implementation phase.
- All test files (`tests/`) — must not change in any release-related phase.
- All documentation files not listed under "expected to change" — `docs/FAQ.md`, `docs/index.md`, `docs/_config.yml`, `docs/architecture/`, `docs/tutorial/`, `AGENTS.md` — must not change in release phases.
- `docs/reports/VOYAGE_PHASE_26_V4_3_RELEASE_READINESS_REAUDIT.md` and all prior phase reports — must never be edited.

## Pre-tag checklist

The following items must all be confirmed TRUE before the `v4.3.0` tag may be created:

- [ ] `pyproject.toml` `version` field reads `4.3.0` (not `4.0.0`).
- [ ] `voyage_framework/__init__.py` `__version__` reads `"4.3.0"` (not `"4.0.0"`).
- [ ] Both version files were updated in the same atomic commit on `main`.
- [ ] `.github/workflows/release.yml` has `workflow_dispatch` trigger with `dry_run` boolean input.
- [ ] `.github/workflows/release.yml` `Create GitHub Release` step is gated: `if: ${{ !inputs.dry_run }}`.
- [ ] A GitHub Actions `workflow_dispatch` dry-run with `dry_run: true` has completed successfully.
- [ ] Dry-run artifacts confirmed: `dist/voyage_framework-4.3.0-*.whl` and `dist/voyage_framework-4.3.0.tar.gz` present.
- [ ] `twine check dist/*` (or equivalent) confirmed zero errors for `4.3.0` artifacts.
- [ ] Full test suite (`pytest tests/ -q`) passed within the dry-run workflow.
- [ ] Rollback procedure (Decision 5 above) has been reviewed and accepted by the maintainer.
- [ ] Phase 31 final re-audit has issued v4.3.0 authorization.
- [ ] PyPI publish step in `release.yml` remains commented out (or has its own separate governance approval).
- [ ] `git tag --list "v4.3*"` returns no output immediately before tagging.

## v4.3 authorization

- Authorized now: no
- Reason: Two BLOCKER conditions remain unresolved: (1) `pyproject.toml` and `voyage_framework/__init__.py` are at version `4.0.0` — creating a `v4.3` or `v4.3.0` tag today would produce distribution artifacts with metadata version `4.0.0`, contradicting the tag; (2) `.github/workflows/release.yml` triggers on every `v*` tag with no `workflow_dispatch` dry-run gate, no environment protection rule, no dry-run evidence, and no approved rollback procedure. Phase 27 resolves these blockers at the policy level only. Implementation (Phases 28–31) is required before authorization.

## Handoff notes

- This phase is policy/documentation only. No source files, workflow files, or version metadata were modified.
- The two BLOCKER conditions from Phase 26 are now documented with explicit policy decisions (Decisions 1–5 above).
- Next phase is Phase 28 (release workflow implementation). It must be approved and merged to `main` before Phase 29 (version bump) begins, because the workflow update must be in place before any version tag is created.
- The Phase 28–29 ordering matters: updating the workflow first means the `v*` tag trigger will already have the dry-run gate and environment protection before any new tag-triggering version exists.
- The PyPI secret (`PYPI_API_TOKEN`) is not configured. The commented-out PyPI step in `release.yml` should remain commented out until a separate governance decision is made for PyPI publication scope and ownership.
- `docs/handoff/LATEST_AGENT_REPORT.md` and `docs/handoff/NEXT_ACTION.md` are written as UTF-8 local-only files. They must not be staged or committed.
- Copy command: `powershell -ExecutionPolicy Bypass -File tools\copy_latest_report.ps1`

## Verdict

A. Policy decisions complete, ready for implementation phase

All five policy decisions are made with rationale and alternatives documented. No implementation was performed. The path to a responsible `v4.3.0` tag is: Phase 28 (workflow) → Phase 29 (version bump) → Phase 30 (dry-run) → Phase 31 (re-audit) → Phase 32 (tag + release). Two BLOCKERs remain at the implementation level; they are now resolved at the policy level.
