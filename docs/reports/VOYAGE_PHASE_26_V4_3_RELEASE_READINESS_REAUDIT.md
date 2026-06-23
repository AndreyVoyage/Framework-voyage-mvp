# Phase 26 v4.3 Release Readiness Re-Audit

## Scope

- Audit/report-only phase on branch `docs/phase-26-v4-3-release-readiness-reaudit`.
- Created only this report.
- No code, tests, package metadata, CLI behavior, README files, published docs, architecture docs, tutorial docs, release workflows, tags, merge, push, cleanup, provider call, model call, or runtime task creation was performed.
- Re-audited release-readiness blockers after Phase 25 implemented the package/API/CLI compatibility decisions from Phase 24.

## Current main

- Current branch at audit start: `docs/phase-26-v4-3-release-readiness-reaudit`.
- Current prompt commit: `6718c29` — `docs: add Phase 26 v4.3 release readiness re-audit prompt`.
- Base `main`: `2d69b04` — `Merge Phase 25 package API CLI compatibility implementation`.
- Source commits on the Phase 25 branch:
  - `dca7f19` — `docs: add Phase 25 package API CLI compatibility prompt`
  - `2444ca7` — `fix: align package API CLI compatibility identity`
- `git status --short` before report creation: no output.
- `git tag --list "v4.3*"`: no output.

## Inputs

- `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`
- `docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md`
- `docs/prompts/PROMPT_PHASE_25_PACKAGE_API_CLI_COMPATIBILITY_IMPLEMENTATION.md`
- `voyage_framework/__init__.py`
- `voyage_framework/cli.py`
- `tests/unit/test_package_api_cli_identity.py`
- `pyproject.toml`
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/FAQ.md`
- `docs/_config.yml`
- `docs/architecture/components.md`
- `docs/tutorial/05-langgraph.md`
- `.github/workflows/release.yml`
- `.github/workflows/jekyll-gh-pages.yml`

## Phase 21 blockers status

| Phase 21 blocker | Status after Phase 25 |
|---|---|
| `docs/FAQ.md` stale current AI/runtime/LangGraph claims | Resolved. FAQ now frames `voyage run`, Docker backend, and `LangGraphRuntime` as legacy/historical and points to canonical task/sync workflows. |
| `docs/_config.yml` stale AI-Native description | Resolved. Description now reads `Local Project Knowledge OS / Development Memory System`. |
| `docs/index.md` stale AI-Native identity and `voyage run` quickstart | Resolved. Index now uses canonical identity and canonical task/sync quickstart. |
| `voyage_framework/__init__.py` stale v4.0 AI-native package identity | Resolved. Docstring now uses canonical Project Knowledge OS identity; `LangGraphRuntime` is explicitly documented as a legacy compatibility export. |
| `voyage_framework/cli.py` current runtime/agent CLI identity | Resolved. Top-level help uses canonical identity; `run`, `graph`, and `graph run` are labeled legacy/deprecated/non-canonical compatibility. |
| `pyproject.toml` version `4.0.0` | Unchanged. Remains a release-semantics blocker for a `v4.3` tag. |
| `pyproject.toml` `langgraph` optional extra / `all` extra | Unchanged in metadata. Phase 24 decided to keep the extra as legacy compatibility, but `pyproject.toml` does not explicitly label it as legacy/deprecated. |
| `.github/workflows/release.yml` triggers on every `v*` tag and creates a GitHub Release | Unchanged. Remains a release-workflow blocker for a `v4.3` tag. |
| Phase 13/16 unresolved human decisions for public API, legacy CLI, LangGraph support, semver, package destination, Pages, release, and rollback policy | Partially resolved for API/CLI compatibility by Phase 24/25. Version, release workflow, and exact LangGraph extra disposition remain unresolved. |

## Phase 23/24/25 package/API/CLI status

- Phase 23 identified current package/CLI runtime identity blockers.
- Phase 24 recorded conservative compatibility decisions.
- Phase 25 implemented those decisions:
  - aligned `voyage_framework/__init__.py` docstring with canonical identity;
  - kept `LangGraphRuntime` in `__all__` but documented it as legacy/deprecated/non-canonical compatibility;
  - changed CLI top-level help to canonical identity;
  - relabeled `run`, `graph`, and `graph run` as legacy/deprecated/non-canonical compatibility;
  - kept `tasks` and `sync` as canonical/current commands;
  - added `tests/unit/test_package_api_cli_identity.py`.
- The package/API/CLI blockers from Phase 21/23 are now closed as current identity issues.

## Identity scan

- SAFE:
  - `README.md:24-28` — negative-boundary "Voyage is not" list.
  - `README.md:84` — legacy compatibility surfaces framed as non-canonical.
  - `docs/README.md:27-32` — negative-boundary list.
  - `docs/README.md:95` — legacy surfaces explicitly not canonical v4.1/v4.2 core.
  - `docs/index.md:45` — negative-boundary statement.
  - `docs/index.md:47` — historical v4.0 surfaces not canonical core.
  - `docs/FAQ.md:20-25` — `voyage run` described as legacy v4.0 compatibility surface.
  - `docs/FAQ.md:41` — `LangGraphRuntime` described as historical v4.0 module, not canonical core.
  - `docs/architecture/components.md:31-60` — legacy surfaces listed with historical/non-canonical qualifications.
  - `docs/tutorial/05-langgraph.md:8-14` — page labeled historical/legacy reference, not current onboarding.
  - `voyage_framework/__init__.py:1-7` — canonical package docstring with negative boundaries.
  - `voyage_framework/__init__.py:12-15` — `LangGraphRuntime` import inside documented legacy compatibility block.
  - `voyage_framework/__init__.py:70-74` — `LangGraphRuntime` listed in `__all__` under legacy compatibility section.
  - `voyage_framework/cli.py:28-29` — `AgentRuntime` import comment notes legacy `voyage run` compatibility path only.
  - `voyage_framework/cli.py:191` — `AgentRuntime` used inside legacy `run_agent` function.
  - `voyage_framework/cli.py:303,311,325,354,377,385` — `LangGraphRuntime` used inside legacy graph functions.
  - `voyage_framework/cli.py:902-903,1044-1045` — `run` and `graph run` help/description strings include `legacy/non-canonical compatibility`.
- UNSAFE: none
- UNKNOWN: none
- BLOCKER: none

## Published docs status

- `README.md` — canonical identity, negative boundaries, legacy compatibility note. SAFE.
- `docs/README.md` — canonical identity, negative boundaries, legacy compatibility note. SAFE.
- `docs/index.md` — canonical identity, canonical quickstart, negative boundaries. SAFE.
- `docs/FAQ.md` — canonical identity, legacy framing for `voyage run`, Docker backend, and `LangGraphRuntime`. SAFE.
- `docs/_config.yml` — canonical description. SAFE.
- `docs/architecture/components.md` — canonical core separated from legacy/historical surfaces. SAFE.
- `docs/tutorial/05-langgraph.md` — labeled historical/legacy reference. SAFE.

## Package/API/CLI status

- `voyage_framework/__init__.py` — canonical docstring, `__version__` unchanged at `4.0.0`, legacy exports retained with explicit compatibility comments.
- `voyage_framework/cli.py` — canonical top-level help; `tasks` and `sync` current; `run`, `graph`, and `graph run` labeled legacy/deprecated/non-canonical compatibility.
- `tests/unit/test_package_api_cli_identity.py` — exists and covers import identity, CLI help wording, and runtime-pollution prevention.
- CLI help creates no `.voyage/`, root `TASK.md`, or root `CONTEXT.json`.

## Version/release semantics

- `pyproject.toml:7` — `version = "4.0.0"`.
- `voyage_framework/__init__.py:9` — `__version__ = "4.0.0"`.
- README/docs version references describe v4.1/v4.2 canonical architecture and v4.3 as documentation direction, not a published release.
- A `v4.3` tag would conflict with package version `4.0.0`: the tag would cause `.github/workflows/release.yml` to build and publish artifacts whose metadata version is `4.0.0`.
- A version bump is required before a responsible `v4.3` tag.
- A version bump is outside the scope of Phase 25 and must be a separate approved release-policy phase.
- Classification: BLOCKER for `v4.3` tag until version semantics are resolved and `pyproject.toml` / `__version__` are aligned with the intended release.

## Release workflow safety

- `.github/workflows/release.yml:3-6` triggers on every `v*` tag.
- `.github/workflows/release.yml:24-33` installs the package, runs tests, and builds distribution packages.
- `.github/workflows/release.yml:35-39` creates a GitHub Release and attaches `dist/*`.
- `.github/workflows/release.yml:42-45` contains a commented PyPI publishing step.
- Creating a `v4.3` tag would therefore immediately build a `4.0.0` distribution and create a GitHub Release, without an approved release policy or dry-run evidence.
- `.github/workflows/jekyll-gh-pages.yml` deploys GitHub Pages from `docs/`; published docs are now canonical, so Pages output is not a current identity blocker, but any future release should verify Pages deployment timing.
- Classification: BLOCKER for `v4.3` tag until release workflow ownership, trigger policy, dry-run evidence, and rollback policy are approved.

## LangGraph / compatibility policy

- Phase 24 decided to keep the `langgraph` optional dependency as legacy compatibility.
- `pyproject.toml:56-59` still defines the `langgraph` extra with `langgraph>=0.2` and `langchain>=0.3`.
- `pyproject.toml:60-62` still includes `langgraph` in the `all` extra.
- The extra is not labeled as legacy/deprecated/non-canonical in `pyproject.toml`.
- The Phase 24 decision provides a compatibility policy, but the metadata itself does not communicate it to consumers.
- Classification: SAFE with warning. The policy decision exists and is documented; however, a future packaging phase may choose to add explicit deprecation wording or remove `langgraph` from `all`.

## Runtime pollution check

- Commands run:
  - `.venv/Scripts/python.exe -m voyage_framework.cli --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli tasks --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli sync --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli run --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli graph --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli graph run --help`
  - `pytest tests/unit/test_package_api_cli_identity.py -q`
  - `pytest tests/unit -q`
- Result: no tracked, staged, or untracked `.voyage/`, root `TASK.md`, or root `CONTEXT.json` was created.
- Pre-existing ignored `.voyage/` and ignored `docs/examples/*/TASK.md` / `CONTEXT.json` artifacts are unchanged.

## Test status

- `tests/unit/test_package_api_cli_identity.py`: 9 passed.
- `tests/unit` full suite: 399 passed.
- No test failures or new warnings attributable to Phase 25 changes.

## Tag check

- `git tag --list "v4.3*"`: no output.
- `v4.1.0-mvp` tag object: `43e051219ade3f965de85a69110bf3bd93f1d4fe`.
- `v4.1.0-mvp` target commit: `086fefc8cbb0e6dfa57a6ff8f1236fc70a56c98a`.
- `v4.2.0-adapter-contract` tag object: `6f6e38093a439eddefde1e1e8b272ffdafa88a13`.
- `v4.2.0-adapter-contract` target commit: `8d7b268ef46a0e8b8a5634d749fcc5eff3094f50`.
- No tag was created, moved, or deleted.

## Remaining blockers

1. **Version mismatch** — `pyproject.toml` and package `__version__` remain `4.0.0`. A `v4.3` tag would build and release artifacts whose metadata version is `4.0.0`.
2. **Tag-triggered release workflow** — `.github/workflows/release.yml` fires on every `v*` tag, builds distributions, and creates a GitHub Release. There is no approved release policy, dry-run evidence, or rollback plan.

## Recommended next phases

- Phase 27 — Version and release policy decision/implementation:
  - Decide `v4.3` version semantics and update `pyproject.toml` version and `voyage_framework.__version__`.
  - Review and approve `.github/workflows/release.yml` trigger policy, artifact contents, and Pages deployment timing.
  - Perform a non-publishing dry-run of the release workflow.
  - Record rollback and ownership policy.
- Phase 28 — Final release-readiness re-audit after Phase 27, confirming version/workflow blockers are closed before any tag is authorized.

## v4.3 tag authorization

- Authorized: no
- Reason: package version remains `4.0.0`, which conflicts with a `v4.3` tag, and `.github/workflows/release.yml` would automatically build and publish release artifacts on any `v*` tag without an approved release policy or dry-run evidence. Identity and package/API/CLI blockers are closed, but release semantics and workflow safety block a responsible tag.

## Verdict

C. Not ready for v4.3 tag
