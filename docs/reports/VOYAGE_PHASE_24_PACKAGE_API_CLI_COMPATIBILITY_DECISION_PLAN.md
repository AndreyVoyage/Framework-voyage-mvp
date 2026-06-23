# Phase 24 Package/API/CLI Compatibility Decision Plan

## Scope

- Decision/report-only phase on branch `docs/phase-24-package-api-cli-compatibility-decision-plan`.
- Created this report only.
- No code, tests, package metadata, CLI behavior, README files, published docs, architecture docs, tutorial docs, release workflows, tags, merge, push, cleanup, provider call, model call, or runtime task creation was performed.
- Decision target identity: Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

## Current main

- Current branch at decision-plan start: `docs/phase-24-package-api-cli-compatibility-decision-plan`.
- Current prompt commit: `5df4cec` - `docs: add Phase 24 package API CLI decision plan prompt`.
- Base `main`: `f3ea751` - `Merge Phase 23 package API CLI compatibility audit`.
- `git status --short` before report creation: no output.
- `git tag --list "v4.3*"`: no output.

## Inputs

- `docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`
- `voyage_framework/__init__.py`
- `voyage_framework/cli.py`
- `pyproject.toml`
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/FAQ.md`
- `docs/architecture/components.md`
- `docs/tutorial/05-langgraph.md`

## Phase 23 blockers

- `voyage_framework/__init__.py` still contains stale v4.0 AI-native package identity.
- `voyage_framework/__init__.py` imports and exports `LangGraphRuntime` as top-level public API without a compatibility boundary.
- `voyage_framework/cli.py` top-level help still says `Voyage AI Dev Framework v4.0`.
- `voyage run` is visible as `Run agent`.
- `graph` and `graph run` are visible as LangGraph workflow and agent execution commands.
- `AgentRuntime` is used by `voyage run`.
- `LangGraphRuntime` is used by graph CLI commands.
- `pyproject.toml` still includes a `langgraph` optional extra and includes it in `all`.
- API/CLI state blocks a responsible v4.3 release proposal until compatibility decisions are implemented and re-audited.

## Decision summary

- Choose a conservative compatibility path for Phase 25: align current identity while preserving legacy surfaces as explicitly legacy/deprecated/non-canonical compatibility.
- Do not remove public exports or commands in Phase 25 unless a separate breaking-change decision is approved later.
- Do not present `LangGraphRuntime`, `AgentRuntime`, `voyage run`, or `graph run` as canonical current workflow.
- Keep `voyage tasks` and `voyage sync` available as canonical command groups.
- Keep CLI help safe: canonical commands are current; legacy commands, if visible, must say legacy/deprecated/non-canonical.
- Keep CLI help non-mutating: no `.voyage`, root `TASK.md`, or root `CONTEXT.json` creation.
- Phase 24 does not decide version bump, v4.3 tag, release workflow behavior, or package publishing; those remain separate release-policy work.

## Public API decision

- Decision: **Option A for package identity** - rewrite `voyage_framework/__init__.py` docstring/metadata wording to the canonical Project Knowledge OS / Development Memory System identity in Phase 25.
- Decision: keep backward compatibility for existing public names, but make legacy exports explicit as compatibility/deprecated/non-canonical surfaces.
- Phase 25 should not delete legacy exports from `__all__` by default. It should either group them under a documented legacy compatibility section or add clear comments/docstrings/deprecation metadata where feasible.
- Phase 25 should make canonical current exports clear, including task/context/audit surfaces such as `TaskYamlSpec`, `TaskRecord`, `TaskEngine`, `TaskParser`, `EventEngine`, and `ContextBuilder` if import boundaries allow doing so without broad refactor.
- `__version__ = "4.0.0"` remains a release/version-policy issue. Phase 25 may note it but should not change package version unless the Phase 25 prompt explicitly authorizes version semantics.

## CLI decision

- Decision: keep canonical command groups `tasks` and `sync` visible and unchanged in behavior.
- Decision: update top-level CLI branding to canonical identity: local Project Knowledge OS / Development Memory System for task memory, context packaging, audit logs, and external AI tool handoff.
- Decision: remove current-agent wording from top-level help. If legacy commands remain visible, their help text must include `legacy`, `deprecated`, `non-canonical`, or equivalent wording.
- Decision: `task` singular remains a legacy generated-artifact compatibility command and must not be described as canonical task truth.
- Decision: `status`, `events`, `approve`, `evaluate`, `chronicler`, and `docs` need conservative help wording if touched: avoid current agent/runtime identity and avoid implying model/provider execution.

## LangGraphRuntime decision

- Decision: **Option B** - keep `LangGraphRuntime` top-level export for compatibility in Phase 25, but mark it legacy/deprecated/non-canonical.
- Rationale: Phase 23 found it importable and public; removing it is a breaking API change and requires a separate owner/API maintainer decision.
- Phase 25 should ensure `LangGraphRuntime` is not presented as canonical current public API.
- Phase 25 should avoid promising LangGraph orchestration, model/provider execution, or AutoGen/CrewAI replacement behavior.

## AgentRuntime / voyage run decision

- Decision: **Option B** - keep `voyage run` for compatibility in Phase 25, but rename/help-text it as legacy/deprecated/non-canonical compatibility.
- Rationale: hiding or removing the command is potentially breaking; keeping it visible without a legacy boundary is unsafe.
- Phase 25 should change top-level help from `Run agent` to a legacy compatibility description.
- Phase 25 should change module docs, examples, status messages, and help text so `voyage run` is not current onboarding and not a canonical workflow.
- If behavior remains unchanged, Phase 25 must still make the command identity explicit as legacy compatibility.

## graph run / LangGraph CLI decision

- Decision: **Option B** - keep `graph` / `graph run` as a legacy/deprecated command group in Phase 25.
- Rationale: moving or removing the namespace is a larger compatibility change; relabeling is the minimum safe implementation.
- Phase 25 should change `graph` help from current LangGraph workflow wording to legacy LangGraph compatibility wording.
- Phase 25 should change `graph run` help from `Run agent via LangGraph` to legacy/deprecated/non-canonical wording.
- Phase 25 must not describe `graph run` as current canonical runtime orchestration or automatic graph execution.

## Optional dependency / extras decision

- Decision: **Option A** - keep the `langgraph` optional extra as legacy compatibility for now.
- Decision: document or classify it as non-canonical compatibility in package/API/CLI-facing surfaces where Phase 25 is authorized to touch them.
- Do not remove `langgraph` from `all` in Phase 25 unless that prompt explicitly authorizes package metadata and breaking extra changes.
- Rationale: removing extras can break install workflows. Phase 24 does not authorize pyproject changes and does not decide release packaging/version semantics.

## Backward compatibility policy

- Preserve existing public imports and visible commands in Phase 25 unless the prompt explicitly authorizes removal.
- Convert unsafe current-runtime identity into explicit legacy/deprecated/non-canonical compatibility language.
- Prefer warnings, help text, docstrings, and compatibility labels over deletion.
- Do not introduce new runtime orchestration, model/provider execution, background agents, or automatic graph execution.
- Do not make generated `TASK.md` or `CONTEXT.json` canonical.

## Deprecation policy

- Deprecation in Phase 25 should be communication-first, not removal-first.
- Minimum deprecation language:
  - `legacy`;
  - `deprecated` or `compatibility`;
  - `non-canonical`;
  - `not part of the v4.1/v4.2 canonical core`;
  - `not current onboarding` for legacy runtime commands.
- If runtime warnings are added, they must not create `.voyage`, root `TASK.md`, or root `CONTEXT.json` and must not change canonical command behavior.
- Any future removal, hiding, namespace move, or breaking extra change requires a separate owner/API/CLI maintainer decision.

## Minimal Phase 25 implementation scope

- Candidate files for Phase 25, only if explicitly authorized:
  - `voyage_framework/__init__.py`;
  - `voyage_framework/cli.py`;
  - focused tests for import and CLI help behavior.
- Required implementation goals:
  - align package docstring with canonical identity;
  - make legacy exports clearly compatibility/deprecated/non-canonical;
  - keep `LangGraphRuntime` available but not canonical;
  - change top-level CLI branding away from `Voyage AI Dev Framework v4.0`;
  - keep `tasks` and `sync` canonical and visible;
  - relabel `run` and `graph` as legacy/deprecated/non-canonical if retained;
  - ensure CLI help does not create runtime state.
- Explicitly not in Phase 25 unless separately authorized:
  - package version bump;
  - pyproject metadata/extras changes;
  - release workflow changes;
  - v4.3 tag;
  - deletion or removal of public APIs;
  - broad cleanup of legacy modules.

## Required tests / smoke checks

- Import smoke:
  - `import voyage_framework` succeeds.
  - `voyage_framework.__doc__` no longer presents AI-native/agent-runtime identity.
  - `LangGraphRuntime` availability matches the compatibility decision.
- Export smoke:
  - `__all__` or public exports preserve compatibility where retained.
  - Canonical exports expected by the implementation prompt are available or explicitly documented.
- CLI smoke:
  - `.venv/Scripts/python.exe -m voyage_framework.cli --help` does not present current AI agent/runtime identity.
  - `.venv/Scripts/python.exe -m voyage_framework.cli tasks --help` remains available.
  - `.venv/Scripts/python.exe -m voyage_framework.cli sync --help` remains available.
  - legacy `run` and `graph` help, if visible, says legacy/deprecated/non-canonical.
  - CLI help creates no `.voyage`, root `TASK.md`, or root `CONTEXT.json`.
- Quality gates:
  - targeted tests for any changed import/help behavior;
  - `git diff --check`;
  - forbidden-file and runtime-pollution checks.

## Out of scope

- Code changes in Phase 24.
- CLI behavior changes in Phase 24.
- `pyproject.toml` changes in Phase 24.
- Test changes in Phase 24.
- README, docs, architecture, tutorial, guide, example, or workflow changes in Phase 24.
- Version bump, package build, release dry-run, release workflow edit, v4.3 tag, or publishing.
- Removing public exports or commands without a separate breaking-change decision.
- Creating `.voyage`, root `TASK.md`, or root `CONTEXT.json`.

## v4.3 impact

- Phase 24 creates a concrete decision plan for Phase 25, but does not make the repository v4.3-ready.
- Current code remains unchanged until Phase 25 implements the decisions.
- A responsible v4.3 proposal remains blocked until:
  - Phase 25 implements package/API/CLI identity decisions;
  - package version/metadata and release workflow decisions are handled in a separate phase;
  - a later readiness audit confirms no UNSAFE/UNKNOWN/BLOCKER release issues remain;
  - no v4.3 tag is created before those gates pass.

## Classification

- SAFE:
  - Package identity decision selects canonical Project Knowledge OS / Development Memory System wording.
  - Legacy exports and commands are preserved only as explicitly legacy/deprecated/non-canonical compatibility.
  - `tasks` and `sync` remain canonical command groups.
  - `LangGraphRuntime`, `AgentRuntime`, `voyage run`, and `graph run` are not treated as current canonical workflow.
  - CLI help must remain non-mutating.
- UNSAFE:
  - None in this decision plan. The plan does not preserve current AI agent/runtime/orchestration identity.
- UNKNOWN:
  - Exact implementation mechanics for deprecation warnings versus help-only labels are left to Phase 25.
  - Package version and release workflow policy remain outside this decision plan.
- BLOCKER:
  - Current repository state remains a v4.3 blocker until Phase 25 implements these decisions and later release-policy phases resolve version/workflow issues.
  - Removing exports/commands or changing extras remains blocked without separate owner/API/CLI maintainer approval.

## Verdict

B. Decision plan complete with safe warnings
