# Phase 24 - Package/API/CLI Compatibility Decision Plan

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
Branch: docs/phase-24-package-api-cli-compatibility-decision-plan
Base: main
main contains: f3ea751 Merge Phase 23 package API CLI compatibility audit
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
Do not edit package, API, CLI, docs, tests, workflows, or metadata outside the single report authorized below.

---

## 1. Mission

Perform **Phase 24: Package/API/CLI Compatibility Decision Plan**.

This is a decision/report-only phase. Create exactly one new report:

```text
docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md
```

The report must convert the Phase 23 Package/API/CLI Compatibility Audit blockers into a precise decision plan for a future Phase 25 implementation. It must choose and document compatibility/deprecation decisions where the evidence is sufficient, and it must explicitly mark any remaining owner/API/CLI maintainer decisions as `UNKNOWN` or `BLOCKER`.

This phase must not change code, CLI behavior, tests, package metadata, README files, published docs, architecture docs, tutorial docs, release workflows, or tags. Even if the decisions are obvious, record them in the report only.

---

## 2. Canonical identity target

Use this exact identity as the decision target:

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

Non-canonical unless explicitly framed as legacy, deprecated, historical, non-canonical, compatibility-only, or negative-boundary context:

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
graph run as current LangGraph execution command
```

---

## 3. Authority and required sources

Authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md`;
3. `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`;
4. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
5. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
6. Current aligned identity references: `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`;
7. Legacy qualification references: `docs/architecture/components.md`, `docs/tutorial/05-langgraph.md`;
8. `AGENTS.md` as operational guidance subordinate to the contract.

Inspect these files:

```text
docs/reports/VOYAGE_PHASE_23_PACKAGE_API_CLI_COMPATIBILITY_AUDIT.md
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
docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md
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
- package metadata changes;
- release workflow changes.
```

---

## 6. Phase 23 blockers to decide

The decision plan must cover these Phase 23 blockers:

```text
- voyage_framework/__init__.py contains stale v4.0 AI-native identity;
- voyage_framework/__init__.py top-level exports LangGraphRuntime;
- voyage_framework/cli.py top-level help says Voyage AI Dev Framework v4.0;
- voyage run is visible as Run agent;
- graph run is visible as LangGraph agent execution;
- AgentRuntime is used by a legacy command;
- LangGraphRuntime is used by graph CLI;
- backward compatibility / deprecation / removal policy is unknown;
- LangGraph optional dependency / extras policy is unknown;
- API/CLI state blocks v4.3.
```

Do not fix these blockers. Decide or classify them.

---

## 7. Required decisions

Choose exactly one option for each item. If there is not enough authority to choose a concrete implementation path, choose the blocking/owner-decision option and classify it as `UNKNOWN` or `BLOCKER`.

### 7.1 Top-level package identity in `__init__.py`

```text
Option A: rewrite docstring/metadata to canonical identity only.
Option B: keep legacy wording but mark it deprecated/historical.
Option C: block implementation until owner decides.
```

### 7.2 `LangGraphRuntime` top-level export

```text
Option A: remove from top-level public export.
Option B: keep export but mark legacy/deprecated compatibility.
Option C: keep as internal/optional with warning.
Option D: block until owner decides.
```

### 7.3 `AgentRuntime` / `voyage run`

```text
Option A: hide/remove from current CLI help.
Option B: keep command but rename/help as legacy/deprecated compatibility.
Option C: keep but make explicit non-canonical historical compatibility.
Option D: block until owner decides.
```

### 7.4 `graph run` / LangGraph CLI

```text
Option A: hide/remove from current CLI help.
Option B: keep as legacy/deprecated command group.
Option C: move to explicit compatibility/legacy namespace.
Option D: block until owner decides.
```

### 7.5 CLI top-level branding

```text
Option A: replace with canonical Project Knowledge OS identity.
Option B: add negative boundaries.
Option C: block until owner decides.
```

### 7.6 Optional dependency / LangGraph extra

```text
Option A: keep optional extra as legacy compatibility.
Option B: remove from all extra in future breaking release.
Option C: keep but document as non-canonical.
Option D: block until owner decides.
```

### 7.7 Tests required for Phase 25

Define the minimum tests and smoke checks needed for implementation:

```text
- import voyage_framework should not present runtime identity;
- __all__ or public exports should match the decision;
- CLI --help should not present current agent/runtime identity;
- voyage tasks --help should remain available;
- voyage sync --help should remain available;
- legacy commands, if retained, must say legacy/deprecated/non-canonical;
- CLI help must not create .voyage/TASK.md/CONTEXT.json pollution.
```

---

## 8. Required verification commands

Run:

```bash
git status --short
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Inspect Phase 23 blockers:

```bash
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|voyage run|graph run|Run agent|Voyage AI Dev Framework v4.0" -- voyage_framework/__init__.py voyage_framework/cli.py pyproject.toml || true
```

Inspect public exports and CLI construction:

```bash
git grep -n -E "__all__|__version__|LangGraphRuntime|AgentRuntime|add_parser\\(\"run\"|add_parser\\(\"graph\"|add_parser\\(\"task\"|add_parser\\(\"tasks\"|add_parser\\(\"sync\"|description=|help=" -- voyage_framework/__init__.py voyage_framework/cli.py pyproject.toml || true
```

Check CLI help without intentional runtime state creation:

```bash
.venv/Scripts/python.exe -m voyage_framework.cli --help || true
.venv/Scripts/python.exe -m voyage_framework.cli tasks --help || true
.venv/Scripts/python.exe -m voyage_framework.cli sync --help || true
```

Check runtime pollution:

```bash
git status --short
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

On Windows PowerShell, if `grep` is unavailable, use:

```powershell
git status --short | Select-String -Pattern '^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK\.md|^(\?\?|A|M).*CONTEXT\.json'
```

---

## 9. Classification rules

Classify the decision plan:

```text
SAFE = clear canonical/legacy/deprecated compatibility decision
UNSAFE = plan would preserve current AI agent/runtime/orchestration identity
UNKNOWN = owner/API/CLI maintainer decision still required
BLOCKER = decision gap blocks implementation or v4.3
```

Do not soften `UNSAFE`, `UNKNOWN`, or `BLOCKER`. If a required decision cannot be made from existing authority, record it as `UNKNOWN` and, if it blocks Phase 25 or v4.3, also `BLOCKER`.

---

## 10. Required report structure

Create:

```text
docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md
```

Use this structure:

```markdown
# Phase 24 Package/API/CLI Compatibility Decision Plan

## Scope
-

## Current main
-

## Inputs
-

## Phase 23 blockers
-

## Decision summary
-

## Public API decision
-

## CLI decision
-

## LangGraphRuntime decision
-

## AgentRuntime / voyage run decision
-

## graph run / LangGraph CLI decision
-

## Optional dependency / extras decision
-

## Backward compatibility policy
-

## Deprecation policy
-

## Minimal Phase 25 implementation scope
-

## Required tests / smoke checks
-

## Out of scope
-

## v4.3 impact
-

## Classification
- SAFE:
- UNSAFE:
- UNKNOWN:
- BLOCKER:

## Verdict
A. Decision plan complete, ready for implementation
B. Decision plan complete with safe warnings
C. Decision plan blocked by unresolved owner decisions
```

The report must be clear enough for a future Phase 25 prompt to implement exactly the chosen decisions, or to stop if owner decisions remain unresolved.

---

## 11. Post-change verification

After creating the report, run:

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
A       docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md
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

## 12. Commit policy

If and only if the single report is created, forbidden checks are clean, runtime state is clean, no v4.3 tag exists, and `git diff --check` is clean, make a local commit:

```bash
git add docs/reports/VOYAGE_PHASE_24_PACKAGE_API_CLI_COMPATIBILITY_DECISION_PLAN.md
git commit -m "docs: add Phase 24 package API CLI decision plan"
```

Do not push.
Do not merge.
Do not tag.

---

## 13. Required final response

Return only:

```markdown
# Phase 24 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Decision classification
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
A. Decision plan complete, ready for implementation
B. Decision plan complete with safe warnings
C. Decision plan blocked by unresolved owner decisions
```
