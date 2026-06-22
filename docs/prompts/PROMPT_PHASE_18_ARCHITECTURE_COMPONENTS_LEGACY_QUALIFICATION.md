# Phase 18 — Architecture Components Legacy Qualification

## 0. Stop-gate

Before making any change, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git --no-pager log --oneline --decorate -8
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
Branch: docs/phase-18-architecture-components-legacy-qualification
Base: main
main contains: 6b62d0b Merge Phase 17 published docs identity alignment
Working tree: clean
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit without verifying the diff scope.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 19.

---

## 1. Mission

Perform **Phase 18: Architecture Components Legacy Qualification**.

The goal is to close **Blocker 2** from `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md` and `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md` by editing **only** `docs/architecture/components.md`.

`docs/architecture/components.md` currently lists a legacy-heavy public API (including `LangGraphRuntime`, `VoyageGraphBuilder`, `AgentRuntime`, `SecureExecutor`, sandbox/runtime helpers, and v4.0 self-improvement/memory tooling) as the current public API without qualification. This phase must label those surfaces as historical/non-canonical and present the canonical v4.1/v4.2 core as the current supported public surface.

This phase must not change code, tests, metadata, workflows, or any other documentation pages.

---

## 2. Canonical identity target

Use this exact identity as the target for `docs/architecture/components.md`:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

Preserve these boundaries:

- `task.yaml` is canonical task intent;
- `TaskRecord` (managed by `TaskEngine`) is canonical runtime task state;
- `EventEngine` is append-only audit;
- `AgentRegistry` and `ModeRegistry` are read-only catalogs;
- `ContextBuilder` aggregates context without becoming canonical state;
- `PromptGenerator` creates deterministic packages for manual transfer;
- Adapter models and protocols are interface contracts only;
- External AI tools are handoff targets, not Voyage runtime dependencies;
- Generated `TASK.md` and `CONTEXT.json` are not canonical truth;
- Legacy runtime and LangGraph surfaces remain present in the repository but are not canonical v4.1/v4.2 core.

---

## 3. Authority and required sources

Authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. Current `docs/README.md` (already aligned) as style/identity reference;
5. `AGENTS.md` as operational guidance subordinate to the contract.

Read at minimum:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
docs/architecture/components.md
docs/README.md
```

All sources except `docs/architecture/components.md` are read-only for this phase.

---

## 4. Allowed file

You may modify **only**:

```text
docs/architecture/components.md
```

You may create no other files. You may not edit `README.md`, `docs/README.md`, `AGENTS.md`, `pyproject.toml`, `.gitignore`, `docs/VOYAGE_V4_1_CONTRACT.md`, existing `docs/reports/*`, `docs/guides/`, `docs/examples/`, `docs/tutorial/`, `voyage_framework/`, `tests/`, or `.github/`.

---

## 5. Required changes to `docs/architecture/components.md`

### 5.1 Page title and introduction

- Keep the page title as “Components” or equivalent.
- Add an introductory paragraph that states the canonical identity and explains that the page lists both canonical current components and historical legacy surfaces.
- Example framing: “This page documents the supported public API of Voyage v4.1/v4.2, followed by historical v4.0 surfaces that remain in the repository for compatibility but are not canonical core.”

### 5.2 Canonical current components section

Create a clearly labeled section such as:

```text
## Canonical v4.1/v4.2 core
```

List only components that belong to the canonical current core. Candidate items:

- `TaskYamlSpec`
- `TaskParser`
- `TaskRecord`
- `TaskEngine`
- `EventEngine`
- `ContextBuilder`
- `AgentRegistry`
- `ModeRegistry`
- `PromptGenerator`
- `PromptPackage`
- `AdapterContract`
- `AdapterProtocol`
- `AgentRequest`
- `AgentResponse`
- `ValidationResult`
- `ApprovalFlow`

For each item, include a one-line description that emphasizes its read-only, deterministic, or interface-only nature where applicable.

### 5.3 Legacy / historical surfaces section

Create a clearly labeled section such as:

```text
## Legacy and historical v4.0 surfaces
```

Move the following exports into this section and label them as historical/non-canonical:

- `LangGraphRuntime`
- `AgentRuntime`
- `VoyageGraphBuilder`
- `MermaidExporter`
- `SecureExecutor`
- `SecurityPolicy`
- `AgentState`
- `ToolResult`
- `SemanticStore`
- `CodeSearch`
- `ASTParser`
- `CodeIndexer`
- `GoldenDataset`
- `GoldenSolution`
- `RuleEngine`
- `Evaluator`
- `FeedbackLoop`
- `TaskGenerator`
- `ProcessJournal`
- `ReplayGenerator`
- `DecisionLog`
- `TutorialDraft`
- `TutorialGenerator`
- `DocsBuilder`
- `ProjectContext`

For each legacy item, use phrasing such as:

- “Historical v4.0 runtime/graph module; not canonical v4.1/v4.2 core.”
- “Legacy compatibility surface; disposition planned in Phase 13 controlled cleanup plan.”
- “Retained for compatibility; does not define current Voyage identity.”

Do not delete items; qualify them.

### 5.4 Remove present-tense runtime/orchestration claims

Ensure the page does not say any of the following in present tense without a legacy qualifier:

- Voyage is an AI Agent Framework.
- Voyage executes agents autonomously.
- Voyage provides a runtime orchestration framework.
- Voyage replaces LangGraph, CrewAI, or AutoGen.
- Voyage performs automatic agent/graph execution.
- Voyage includes a model/provider execution layer.
- `LangGraphRuntime` or `AgentRuntime` are current canonical runtime components.

If these terms appear, they must be explicitly framed as legacy, historical, non-canonical, or risk wording being corrected.

### 5.5 Preserve links and navigation

- Do not change file paths.
- Do not break relative links.
- If the page links to `docs/tutorial/` or other historical pages, ensure the link text frames them as legacy where appropriate.

---

## 6. Identity scan and classification

After editing, run:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|Phase 4.*LangGraph|Visualizer API" docs/architecture/components.md || true
```

Classify every match:

```text
SAFE   = negative boundary / historical / legacy context / risk wording being corrected
UNSAFE = current identity still claims runtime/agent/framework/orchestration
UNKNOWN = insufficient evidence; needs human decision
```

Rules:

- A SAFE match must explicitly frame the term as legacy, historical, non-canonical, previous architecture, risk being corrected, or a negative boundary.
- An UNSAFE match is any present-tense claim that a runtime/agent/graph/model/orchestration capability is current canonical core.
- If you are unsure, classify as UNKNOWN and stop for human decision.

There must be **zero UNSAFE matches** in `docs/architecture/components.md` before commit.

---

## 7. What Phase 18 must not do

```text
- Do not edit README.md (root).
- Do not edit docs/README.md.
- Do not edit AGENTS.md.
- Do not edit pyproject.toml.
- Do not edit .gitignore.
- Do not edit docs/VOYAGE_V4_1_CONTRACT.md.
- Do not edit existing docs/reports/*.
- Do not edit docs/guides/*.
- Do not edit docs/examples/*.
- Do not edit docs/tutorial/*.
- Do not edit voyage_framework/ code.
- Do not edit tests/.
- Do not edit .github/ workflows.
- Do not delete, move, rename, or archive files.
- Do not change CLI behavior.
- Do not change package metadata or version.
- Do not change public exports.
- Do not create .voyage, root TASK.md, or root CONTEXT.json.
- Do not create, move, or delete tags.
- Do not create a v4.3 tag.
- Do not merge.
- Do not push.
```

---

## 8. Verification gates

Before committing, verify:

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
M       docs/architecture/components.md
```

Forbidden scope check:

```bash
git diff -- README.md docs/README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports docs/guides docs/examples docs/tutorial voyage_framework tests .github
```

Expected: empty output.

Identity scan:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|Phase 4.*LangGraph|Visualizer API" docs/architecture/components.md || true
```

Expected: only SAFE matches; zero UNSAFE matches.

Runtime pollution check:

```bash
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

Expected: no output.

Tag check:

```bash
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected: no v4.3 tag; existing milestone tags unchanged.

---

## 9. Commit

If and only if all gates pass:

```bash
git add docs/architecture/components.md
git commit -m "docs: qualify legacy components in architecture page

- Separate canonical v4.1/v4.2 core from historical v4.0 surfaces.
- Label LangGraphRuntime, AgentRuntime, graph builder, sandbox, memory,
  improvement, and chronicler exports as legacy/historical/non-canonical.
- Preserve all items; do not delete or move files.
- No code, tests, metadata, workflows, or other docs changed."
```

Do not push.

---

## 10. Absolute constraints

- Do NOT soften a BLOCKER to WARNING or SAFE.
- Do NOT treat a legacy mention as safe unless it is explicitly framed as legacy/historical/non-canonical.
- Do NOT infer permission to change files outside `docs/architecture/components.md`.
- Do NOT claim v4.3 is released or approved.
- Report failures honestly. Do not mask errors.
