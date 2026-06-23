# Phase 23 - Package/API/CLI Compatibility Audit

## 0. Stop-gate

Before making any change, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status --short
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
Branch: docs/phase-23-package-api-cli-compatibility-audit
Base: main
main contains: b2900d8 Merge Phase 22 published docs residual identity cleanup
Working tree: clean before changes
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not push.
Do not merge.
Do not tag.
Do not create a v4.3 tag.
Do not run release workflows.
Do not create runtime task state.
Do not call models, providers, or network services.
Do not edit package, API, CLI, docs, tests, or metadata outside the single report authorized below.

---

## 1. Mission

Perform **Phase 23: Package/API/CLI Compatibility Audit**.

This is an audit/report-only phase. Create exactly one new report:

```text
docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
```

The report must audit remaining package/API/CLI blockers after Phase 22. It must determine whether the current public package surface and CLI surface are compatible with the canonical v4.1/v4.2/v4.3 identity, and whether any release-blocking ambiguity remains before a future implementation phase.

This phase must not change code, CLI behavior, tests, package metadata, README files, published docs, or architecture docs. Even if blockers are found, record them in the report only.

---

## 2. Canonical identity target

Use this exact identity as the audit target:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

Canonical current core:

```text
TaskYamlSpec / TaskParser
TaskRecord / TaskEngine
EventEngine append-only audit log
Context Builder Lite / sync
Agent Registry Draft as static role registry
Mode Profiles / Prompt Generator
Adapter Contract Draft as interface/documentation boundary
Documentation, examples, workflow policy, audits, cleanup plans
```

Non-canonical unless explicitly framed as legacy, historical, deprecated, compatibility-only, or negative-boundary context:

```text
AI Agent Framework
AI-native runtime
autonomous agent runtime
runtime orchestration framework
LangGraph/CrewAI/AutoGen replacement
automatic agent execution system
model/provider execution layer
LangGraphRuntime
AgentRuntime
runtime orchestration
provider execution
model execution
agent execution
automatic graph execution
voyage run as current runtime execution command
```

---

## 3. Authority and required sources

Authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
5. `README.md`, `docs/README.md`, `docs/index.md`, and `docs/FAQ.md` as current aligned identity references;
6. `docs/architecture/components.md` and `docs/tutorial/05-langgraph.md` as legacy qualification references;
7. `AGENTS.md` as operational guidance subordinate to the contract.

Inspect these files:

```text
docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
voyage_framework/__init__.py
voyage_framework/cli.py
pyproject.toml
README.md
docs/README.md
docs/index.md
docs/FAQ.md
docs/architecture/components.md
docs/tutorial/05-langgraph.md
```

All inspected sources are read-only for this phase.

---

## 4. Allowed files

You may create **only**:

```text
docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
```

---

## 5. Forbidden changes

Do not modify:

```text
README.md
docs/README.md
AGENTS.md
pyproject.toml
.github/
docs/guides/*
docs/examples/*
docs/tutorial/*
docs/architecture/*
docs/index.md
docs/FAQ.md
docs/_config.yml
voyage_framework/*
tests/*
.gitignore
docs/VOYAGE_V4_1_CONTRACT.md
```

Do not create, delete, move, or rename files except for the single authorized report.

Also forbidden:

```text
- creating .voyage state;
- creating root TASK.md;
- creating root CONTEXT.json;
- creating tags;
- creating a v4.3 tag;
- moving existing tags;
- changing v4.1.0-mvp;
- changing v4.2.0-adapter-contract;
- cleanup;
- merge;
- push;
- code changes;
- test changes;
- pyproject.toml changes;
- CLI behavior changes;
- package metadata changes.
```

---

## 6. Required audit questions

The report must answer:

```text
- Which public API exports look like legacy/current identity conflicts?
- Is there current AI agent/runtime/orchestration/provider execution identity in package code?
- Which CLI commands are canonical?
- Which CLI commands are legacy/historical compatibility surfaces?
- Does voyage run appear as a live/current command claim?
- Are LangGraphRuntime or AgentRuntime exported or referenced?
- Is a backward compatibility layer needed?
- Should legacy CLI/API be deprecated instead of removed?
- Which changes are safe candidates for a future Phase 24 implementation?
- Which changes require human decision?
```

Do not fix any issue found. Classify and report it.

---

## 7. Required commands and scans

Run:

```bash
git status --short
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Scan package/API/CLI identity:

```bash
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|voyage run|run command|agent framework" -- voyage_framework/__init__.py voyage_framework/cli.py pyproject.toml || true
```

Inspect exports/imports and CLI surface:

```bash
git grep -n -E "__all__|import|from voyage_framework|LangGraphRuntime|AgentRuntime|TaskEngine|TaskRecord|TaskYamlSpec|EventEngine|Context|Agent|Runtime|CLI|click|typer|argparse|def main|def run" -- voyage_framework/__init__.py voyage_framework/cli.py || true
```

Check CLI help without intentional runtime state creation:

```bash
.venv/Scripts/python.exe -m voyage_framework.cli --help || true
.venv/Scripts/python.exe -m voyage_framework.cli tasks --help || true
.venv/Scripts/python.exe -m voyage_framework.cli sync --help || true
```

If CLI help creates `.voyage`, root `TASK.md`, root `CONTEXT.json`, or any other runtime state, record it as `BLOCKER` or `UNKNOWN`. Do not fix it.

Check runtime state after CLI help:

```bash
git status --short
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

On Windows PowerShell, if `grep` is unavailable, use:

```powershell
git status --short | Select-String -Pattern '^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK\.md|^(\?\?|A|M).*CONTEXT\.json'
```

---

## 8. Classification rules

Classify every relevant finding:

```text
SAFE = canonical current API/CLI, negative boundary, historical, legacy, deprecated, or compatibility context only
UNSAFE = package/API/CLI still claims current AI agent/runtime/orchestration/provider execution identity
UNKNOWN = public API / CLI compatibility decision needs human decision
BLOCKER = unsafe current behavior or release-risking ambiguity blocks v4.3
```

Do not soften `UNSAFE`, `UNKNOWN`, or `BLOCKER`. If a public API or CLI behavior could mislead users into treating Voyage as a current runtime execution framework, classify it as `UNSAFE` or `BLOCKER`.

---

## 9. Required report structure

Create:

```text
docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
```

Use this structure:

```markdown
# Phase 23 Package/API/CLI Compatibility Audit

## Scope
-

## Current main
-

## Known blockers from Phase 21
-

## Files inspected
-

## Public API surface
-

## CLI surface
-

## LangGraph / runtime compatibility
-

## Canonical vs legacy classification
- SAFE:
- UNSAFE:
- UNKNOWN:
- BLOCKER:

## Runtime pollution check
-

## Tag check
-

## Compatibility decision needed
-

## Recommended Phase 24 implementation scope
-

## v4.3 impact
-

## Verdict
A. API/CLI ready, no compatibility blockers
B. API/CLI ready with safe warnings
C. API/CLI not ready, blockers found
```

The report must include enough command evidence to make the verdict reviewable, but it must not include unrelated cleanup or implementation changes.

---

## 10. Post-change verification

After creating the report, run:

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
A       docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
```

Forbidden check:

```bash
git diff -- README.md
git diff -- docs/README.md
git diff -- AGENTS.md
git diff -- pyproject.toml
git diff -- .gitignore
git diff -- docs/VOYAGE_V4_1_CONTRACT.md
git diff -- docs/guides
git diff -- docs/examples
git diff -- docs/tutorial
git diff -- docs/architecture
git diff -- docs/index.md
git diff -- docs/FAQ.md
git diff -- docs/_config.yml
git diff -- voyage_framework
git diff -- tests
git diff -- .github
```

Expected: no output.

Runtime pollution check:

```bash
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

Expected: no `.voyage`, root `TASK.md`, or root `CONTEXT.json` changes.

Tag check:

```bash
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
- no v4.3 tag exists;
- v4.1.0-mvp unchanged;
- v4.2.0-adapter-contract unchanged.
```

---

## 11. Commit policy

If and only if the single report is created, forbidden checks are clean, runtime state is clean, no v4.3 tag exists, and `git diff --check` is clean, make a local commit:

```bash
git add docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
git commit -m "docs: add Phase 23 package API CLI compatibility audit"
```

Do not push.
Do not merge.
Do not tag.

---

## 12. Required final response

Return only:

```markdown
# Phase 23 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Classification
- SAFE:
- UNSAFE:
- UNKNOWN:
- BLOCKER:

## Runtime pollution check
-

## Tag check
-

## Quality gates
-

## Forbidden files check
-

## Commit
- Created: yes/no
- Commit hash:
- Commit message:

## Push
- Not performed.

## Risks / deviations
-

## Verdict
A. API/CLI ready, no compatibility blockers
B. API/CLI ready with safe warnings
C. API/CLI not ready, blockers found
```
