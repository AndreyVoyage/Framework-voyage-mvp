# Phase 25 — Package/API/CLI Compatibility Implementation

## Goal

Implement the conservative compatibility decisions from `docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md`. Align the package public identity, top-level exports, and CLI help wording with the canonical Project Knowledge OS identity, while preserving legacy runtime/graph surfaces only as deprecated/non-canonical compatibility. Do not break existing users.

## Canonical identity target

> Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

## Scope

### Allowed files

Only these files may be changed:

- `voyage_framework/__init__.py`
- `voyage_framework/cli.py`
- `tests/unit/test_package_api_cli_identity.py`

If the existing test layout makes a different focused test file clearly necessary, stop and mark the issue `UNKNOWN`; do not spread changes across `tests/`.

### Forbidden files

Do not modify:

- `pyproject.toml`
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `docs/FAQ.md`
- `docs/_config.yml`
- `docs/reports/*`
- `docs/prompts/*`
- `docs/guides/*`
- `docs/examples/*`
- `docs/tutorial/*`
- `docs/architecture/*`
- `.github/*`
- `AGENTS.md`
- `.gitignore`
- `docs/VOYAGE_V4_1_CONTRACT.md`

### Forbidden actions

- Do not create `.voyage/`.
- Do not create root `TASK.md`.
- Do not create root `CONTEXT.json`.
- Do not create any tag.
- Do not create a `v4.3*` tag.
- Do not modify `v4.1.0-mvp` or `v4.2.0-adapter-contract`.
- Do not change `pyproject.toml`.
- Do not bump `__version__` or package version.
- Do not make a release.
- Do not merge.
- Do not push.
- Do not remove public exports or CLI commands without separate explicit approval.

## Primary sources

Before editing, read:

- `docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md`
- `docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md`
- `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`
- `voyage_framework/__init__.py`
- `voyage_framework/cli.py`
- `pyproject.toml` (read-only)
- `README.md` (read-only)
- `docs/README.md` (read-only)
- `docs/index.md` (read-only)
- `docs/FAQ.md` (read-only)

## Required implementation

### `voyage_framework/__init__.py`

1. Replace stale v4.0 / AI-native / runtime-orchestration identity in the package docstring/branding with the canonical Project Knowledge OS identity.
2. Keep `__version__ = "4.0.0"` unchanged.
3. Keep `LangGraphRuntime`, `AgentRuntime`, and other legacy top-level exports present in `__all__`, but ensure the surrounding documentation/comments/frame them as `legacy/deprecated/non-canonical compatibility`.
4. Keep canonical exports such as `tasks` and `sync` paths current and un-deprecated.

### `voyage_framework/cli.py`

1. Change the top-level CLI help/branding away from `Voyage AI Dev Framework v4.0` to the canonical identity or neutral local development memory wording.
2. Keep `voyage tasks` and `voyage sync` as canonical/current commands.
3. Keep `voyage run` and `voyage graph [run]` available, but change their help text to explicitly state they are `legacy/deprecated/non-canonical compatibility` surfaces.
4. Ensure that invoking `--help` on any command does not create runtime artifacts (`.voyage/`, root `TASK.md`, root `CONTEXT.json`).

## Non-canonical terms that must not appear as current identity

- AI Agent Framework
- AI-native runtime
- autonomous agent runtime
- runtime orchestration framework
- LangGraph/CrewAI/AutoGen replacement
- automatic agent execution system
- model/provider execution layer
- runtime orchestration
- provider execution
- model execution
- agent execution
- automatic graph execution
- Voyage AI Dev Framework v4.0
- `Run agent` as a current canonical command description

These terms are allowed only inside an explicit `legacy/deprecated/non-canonical compatibility` context.

## Pre-change checks

Run and record the output:

```bash
git status --short
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Identity/API/CLI scan before changes:

```bash
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|voyage run|run command|agent framework|Voyage AI Dev Framework v4.0|Run agent" -- voyage_framework/__init__.py voyage_framework/cli.py pyproject.toml || true
```

API/export scan:

```bash
git grep -n -E "__all__|LangGraphRuntime|AgentRuntime|TaskEngine|TaskRecord|TaskYamlSpec|EventEngine|__version__|__description__|__doc__|def main|def run|graph|tasks|sync" -- voyage_framework/__init__.py voyage_framework/cli.py || true
```

## CLI help checks

Use the isolated virtual environment:

```bash
.venv/Scripts/python.exe -m voyage_framework.cli --help || true
.venv/Scripts/python.exe -m voyage_framework.cli tasks --help || true
.venv/Scripts/python.exe -m voyage_framework.cli sync --help || true
.venv/Scripts/python.exe -m voyage_framework.cli run --help || true
.venv/Scripts/python.exe -m voyage_framework.cli graph --help || true
.venv/Scripts/python.exe -m voyage_framework.cli graph run --help || true
```

## Runtime pollution check

After every CLI help invocation, run:

```bash
git status --short
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

Expected: no `.voyage/`, no root `TASK.md`, no root `CONTEXT.json`.

## Tests

Add focused smoke tests to `tests/unit/test_package_api_cli_identity.py` covering:

- `import voyage_framework` succeeds.
- Package public identity does not contain `AI-native`, `AI Agent Framework`, `runtime orchestration framework`, or `Voyage AI Dev Framework v4.0` as current identity.
- `LangGraphRuntime` / `AgentRuntime` compatibility wording is `legacy/deprecated/non-canonical` if exposed in metadata/help.
- `voyage --help` does not contain `Voyage AI Dev Framework v4.0`.
- `voyage --help` does not present `Run agent` as a current canonical command.
- `voyage tasks --help` and `voyage sync --help` succeed or remain available.
- `voyage run --help` and `voyage graph run --help`, if available, contain `legacy/deprecated/non-canonical compatibility` wording.
- CLI help tests do not create `.voyage/`, root `TASK.md`, or root `CONTEXT.json`.

If the CLI structure makes these tests impossible, stop and report `C. Implementation blocked`; do not silently skip tests.

Run tests:

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_package_api_cli_identity.py -v || true
```

## Classification of scan results

Classify each finding as:

- `SAFE` — canonical current wording or explicit `legacy/deprecated/non-canonical compatibility` context.
- `UNSAFE` — current AI agent/runtime/orchestration identity remains.
- `UNKNOWN` — ambiguous API/CLI compatibility or test coverage gap needs human decision.
- `BLOCKER` — issue blocks Phase 25 completion or the v4.3 readiness path.

## Acceptance criteria

All of the following must pass:

- `voyage_framework/__init__.py` no longer claims AI-native / AI Agent Framework / runtime orchestration as current identity.
- Package description/docstring uses the canonical Project Knowledge OS / Development Memory System identity.
- `LangGraphRuntime` export, if present, is explicitly `legacy/deprecated/non-canonical compatibility`.
- `AgentRuntime` reference, if present, is explicitly `legacy/deprecated/non-canonical compatibility`.
- CLI top-level help no longer says `Voyage AI Dev Framework v4.0`.
- CLI top-level help uses canonical identity or neutral local development memory wording.
- `voyage run --help` no longer says current `Run agent`; it must say `legacy/deprecated/non-canonical compatibility`.
- `voyage graph run --help` no longer presents a current canonical LangGraph execution workflow; it must say `legacy/deprecated compatibility`.
- `tasks` and `sync` remain available as canonical/current commands.
- CLI help creates no runtime pollution.
- No `pyproject.toml` changes.
- No tag created.
- No `v4.3*` tag created.
- No version bump.

## Final report template

Return exactly:

```markdown
# Phase 25 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Public API changes
-

## CLI changes
-

## Legacy compatibility retained
-

## Tests added / updated
-

## Identity scan
- SAFE:
- UNSAFE:
- UNKNOWN:
- BLOCKER:

## CLI help checks
-

## Runtime pollution check
-

## Tag check
-

## Quality gates
-

## Forbidden files check
-

## v4.3 impact
-

## Risks / deviations
-

## Verdict
A. Implementation ready for review
B. Implementation ready with safe warnings
C. Implementation blocked
```

Do not commit. Commit only after human review.
