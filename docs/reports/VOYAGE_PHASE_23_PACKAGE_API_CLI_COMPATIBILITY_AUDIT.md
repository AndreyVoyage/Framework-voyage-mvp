# Phase 23 Package/API/CLI Compatibility Audit

## Scope

- Audit-only phase on branch `docs/phase-23-package-api-cli-compatibility-audit`.
- Created this report only.
- No code, tests, package metadata, README files, published docs, architecture docs, tutorial docs, release workflows, tags, merge, push, cleanup, provider call, model call, or runtime task creation was performed.
- Audit target identity: Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

## Current main

- Current branch at audit start: `docs/phase-23-package-api-cli-compatibility-audit`.
- Current prompt commit: `4f89c24` - `docs: add Phase 23 package API CLI compatibility audit prompt`.
- Base `main`: `b2900d8` - `Merge Phase 22 published docs residual identity cleanup`.
- `git status --short` before report creation: no output.
- `git tag --list "v4.3*"`: no output.

## Known blockers from Phase 21

- Phase 21 reported package public surface blockers in `voyage_framework/__init__.py`:
  - stale package docstring: `Voyage AI Dev Framework v4.0 - AI-Native Engineering Operating System`;
  - `__version__ = "4.0.0"`;
  - `LangGraphRuntime` import and export.
- Phase 21 reported CLI blockers in `voyage_framework/cli.py`:
  - top-level docs describe `voyage run <role>` as running an agent;
  - argparse description remains `Voyage AI Dev Framework v4.0`;
  - `voyage run` remains visible as `Run agent`;
  - `graph` and `graph run` remain visible as LangGraph workflow and execution commands.
- Phase 21 reported unresolved `pyproject.toml` blockers:
  - `version = "4.0.0"` remains unresolved for a future `v4.3` tag;
  - `langgraph` optional dependency and `all` extra support policy remain unresolved.
- Phase 21 also reported release workflow blockers, but `.github/` was outside Phase 23 scope and was not modified.

## Files inspected

- `docs/prompts/PROMPT_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`
- `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`
- `voyage_framework/__init__.py`
- `voyage_framework/cli.py`
- `pyproject.toml`
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/FAQ.md`
- `docs/architecture/components.md`
- `docs/tutorial/05-langgraph.md`

## Public API surface

- `pyproject.toml` package description and keywords are now aligned with the canonical Project Knowledge OS / Development Memory System identity.
- `pyproject.toml` exposes the CLI entry point `voyage = "voyage_framework.cli:main"`, so CLI identity is package-facing.
- `pyproject.toml` still has `version = "4.0.0"`; this is an UNKNOWN/BLOCKER for any future `v4.3` release because version semantics require an explicit release decision.
- `pyproject.toml` still includes the `langgraph` optional dependency and includes it in `all`; this is UNKNOWN/BLOCKER because LangGraph support policy is unresolved.
- `voyage_framework/__init__.py` remains unsafe as a package public surface:
  - the module docstring still claims `Voyage AI Dev Framework v4.0 - AI-Native Engineering Operating System`;
  - `__version__ = "4.0.0"` remains package-visible;
  - `from voyage_framework.agents.langgraph_runtime import LangGraphRuntime` imports a legacy runtime at top level;
  - `__all__` exports `LangGraphRuntime`.
- `voyage_framework/__init__.py` also exports many legacy v4.0 compatibility surfaces as public names, including `AgentState`, `ProjectContext`, `ToolResult`, `SecurityPolicy`, `SecureExecutor`, `TaskGenerator`, `SemanticStore`, `CodeSearch`, `ASTParser`, `CodeIndexer`, improvement helpers, graph helpers, and Chronicler helpers. Documentation now classifies these as historical/non-canonical, but the package surface itself does not.
- Canonical current core names expected by the v4.1/v4.2 identity are not clearly represented as the public package surface in `__all__`; for example `TaskYamlSpec`, `TaskRecord`, `TaskEngine`, `TaskParser`, `ContextBuilder`, role/mode registries, and prompt generator are not the top-level identity of the package.

## CLI surface

- SAFE canonical commands:
  - `voyage tasks create|list|show|start|block|unblock|complete|fail|archive` - runtime task database management around `TaskEngine` / `TaskRecord`;
  - `voyage sync build|check|status` - Context Builder Lite and task/context comparison workflow;
  - `voyage task` is safe only as a documented legacy generated-artifact command when framed as generating `TASK.md` and `CONTEXT.json`, not as canonical task truth.
- UNSAFE current CLI identity:
  - top-level CLI help says `Voyage AI Dev Framework v4.0`;
  - top-level command list exposes `run` as `Run agent`;
  - `voyage_framework/cli.py` module docs say `voyage run <role>` runs an agent;
  - `run_agent()` constructs `AgentRuntime` and prints agent execution status;
  - `show_status()` tells users to run `voyage run` to start when there are no events.
- UNSAFE LangGraph CLI identity:
  - top-level CLI help exposes `graph` as `LangGraph workflow commands`;
  - `graph run` help says `Run agent via LangGraph`;
  - `graph_run()` constructs `LangGraphRuntime`;
  - `graph visualize` and `graph state` construct or reference `LangGraphRuntime`.
- UNKNOWN compatibility decisions:
  - whether `voyage run` should remain visible, be deprecated, be hidden, be split into a legacy namespace, or be removed;
  - whether `voyage graph` should remain visible, be deprecated, be hidden, be split into a legacy namespace, or be removed;
  - whether CLI help should label legacy commands directly rather than presenting them as current commands.

## LangGraph / runtime compatibility

- `LangGraphRuntime` is exported from `voyage_framework/__init__.py` and is used by CLI graph commands. This is UNSAFE as current package/API/CLI identity.
- `AgentRuntime` is imported at CLI module scope and used by `voyage run`. This is UNSAFE as current CLI identity.
- The repository documentation has been corrected to state that runtime and LangGraph surfaces are historical, legacy, non-canonical, or compatibility-only. The package and CLI surfaces do not yet carry equivalent boundaries.
- A backward compatibility layer is needed if these imports and commands must remain available for existing consumers. Removing them directly would require explicit owner/API/CLI maintainer approval and compatibility/deprecation policy.

## Canonical vs legacy classification

- SAFE:
  - `pyproject.toml` description and keywords align with Project Knowledge OS / Development Memory System identity.
  - `voyage tasks` command group is canonical runtime task-state management.
  - `voyage sync` command group is canonical Context Builder Lite workflow.
  - `voyage task` is safe only as legacy generated-artifact compatibility when explicitly framed that way.
  - `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/architecture/components.md`, and `docs/tutorial/05-langgraph.md` classify runtime/LangGraph content as negative boundary, legacy, historical, or non-canonical.
- UNSAFE:
  - `voyage_framework/__init__.py` docstring still claims stale v4.0 AI-native package identity.
  - `voyage_framework/__init__.py` imports and exports `LangGraphRuntime` as top-level public API.
  - `voyage_framework/cli.py` exposes `voyage run` as current `Run agent` CLI.
  - `voyage_framework/cli.py` exposes `voyage graph` and `voyage graph run` as current LangGraph workflow/agent execution CLI.
  - CLI help presents current runtime wording without legacy/deprecation boundaries.
- UNKNOWN:
  - Public Python API compatibility window for legacy exports.
  - Legacy CLI disposition for `voyage run`, `voyage graph`, `status`, `events`, `approve`, `evaluate`, `chronicler`, and `docs` commands.
  - LangGraph optional extra support policy in `pyproject.toml`.
  - Version semantics for any future `v4.3` package/tag while package version remains `4.0.0`.
  - Whether backward compatibility should be implemented via deprecation warnings, legacy namespaces, hidden commands, split packages, or removal.
- BLOCKER:
  - Current package and CLI surfaces still expose AI agent/runtime/orchestration/LangGraph execution identity as current behavior.
  - No approved public API / legacy CLI / LangGraph compatibility decision exists.
  - A future `v4.3` tag remains blocked until package/API/CLI identity, version semantics, and release workflow policy are resolved.

## Runtime pollution check

- Commands run:
  - `.venv/Scripts/python.exe -m voyage_framework.cli --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli tasks --help`
  - `.venv/Scripts/python.exe -m voyage_framework.cli sync --help`
  - `git status --short`
  - runtime pollution scan for `.voyage`, root `TASK.md`, and root `CONTEXT.json`
- Result: no runtime state pollution was created by CLI help.
- `git status --short` after CLI help, before report creation: no output.

## Tag check

- `git tag --list "v4.3*"`: no output.
- `v4.1.0-mvp` tag object: `43e051219ade3f965de85a69110bf3bd93f1d4fe`.
- `v4.1.0-mvp` target commit: `086fefc8cbb0e6dfa57a6ff8f1236fc70a56c98a`.
- `v4.2.0-adapter-contract` tag object: `6f6e38093a439eddefde1e1e8b272ffdafa88a13`.
- `v4.2.0-adapter-contract` target commit: `8d7b268ef46a0e8b8a5634d749fcc5eff3094f50`.
- No tag was created, moved, or deleted.

## Compatibility decision needed

- Decide whether top-level package exports should represent only canonical v4.1/v4.2 core, or preserve legacy v4.0 exports under an explicit compatibility contract.
- Decide whether `LangGraphRuntime` remains exported, moves behind a legacy namespace, emits deprecation warnings, or is removed from top-level public API.
- Decide whether `voyage run` remains visible, becomes deprecated, moves to a legacy namespace, is hidden from help, or is removed.
- Decide whether `voyage graph` and LangGraph commands remain visible, become deprecated, move to a legacy namespace, are hidden from help, or are removed.
- Decide how `pyproject.toml` version `4.0.0`, optional `langgraph` extra, and `all` extra should behave before any future `v4.3` tag.
- Decide whether legacy runtime modules are package-supported compatibility surfaces, separately packaged components, historical code only, or cleanup targets.

## Recommended Phase 24 implementation scope

- Scope Phase 24 as a package/API/CLI identity and compatibility implementation only, after owner/API/CLI maintainer decisions are recorded.
- Candidate files for Phase 24, only if explicitly authorized:
  - `voyage_framework/__init__.py`;
  - `voyage_framework/cli.py`;
  - focused tests for import and CLI smoke behavior;
  - possibly a new compatibility/deprecation decision document if decisions are not already recorded.
- Safe implementation direction after approval:
  - align package docstring with Project Knowledge OS / Development Memory System identity;
  - make canonical public exports explicit;
  - preserve legacy exports only behind clear compatibility/deprecation boundaries;
  - update CLI help so canonical commands are clearly current and legacy runtime commands are not presented as current onboarding;
  - add import and CLI smoke tests proving canonical commands work and help does not create runtime state.
- Do not combine Phase 24 with version bump, release workflow changes, tag creation, package build/release, or broad cleanup. Those remain separate release-policy phases.

## v4.3 impact

- Current API/CLI state blocks a responsible `v4.3` release proposal.
- Published docs blockers from Phase 21 were substantially reduced by Phase 22, but package and CLI surfaces still contradict the canonical identity.
- A `v4.3` tag should not be created until:
  - public API compatibility policy is approved and implemented;
  - legacy CLI disposition is approved and implemented;
  - LangGraph support policy is approved and implemented;
  - package version/metadata policy is approved and implemented;
  - release workflow behavior is validated in a non-publishing dry run;
  - a later readiness audit verifies no UNSAFE/UNKNOWN/BLOCKER release issues remain.

## Verdict

C. API/CLI not ready, blockers found
