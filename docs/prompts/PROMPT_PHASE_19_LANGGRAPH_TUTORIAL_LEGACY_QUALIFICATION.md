# Phase 19 - LangGraph Tutorial Legacy Qualification

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
Branch: docs/phase-19-langgraph-tutorial-legacy-qualification
Base: main
main contains: df8796f Merge Phase 18 architecture components legacy qualification
Working tree: clean
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit without verifying the diff scope.
Do not push.
Do not merge.
Do not tag.
Do not start package, workflow, API, or cleanup work.

---

## 1. Mission

Perform **Phase 19: LangGraph Tutorial Legacy Qualification**.

The goal is to close the tutorial blocker from `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md` and `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md` by editing **only**:

```text
docs/tutorial/05-langgraph.md
```

The page currently presents LangGraph/tutorial-generation material without sufficient historical, legacy, or non-canonical qualification. This phase must preserve the page as a historical reference while removing any impression that LangGraph runtime, automatic graph execution, tutorial generation, provider execution, or autonomous agent execution is the current canonical Voyage workflow.

This phase must not change code, tests, package metadata, workflows, architecture pages, guides, examples, reports, root documentation, or any other tutorial page.

---

## 2. Canonical identity target

Use this exact identity as the target:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

Preserve these boundaries:

- `task.yaml` is canonical task intent;
- `TaskRecord` managed by `TaskEngine` is canonical local task lifecycle state;
- `EventEngine` is append-only audit;
- `ContextBuilder` aggregates and compares context;
- `AgentRegistry` and `ModeRegistry` are read-only catalogs;
- `PromptGenerator` creates deterministic prompt packages for manual transfer;
- adapter contracts are interface and documentation boundaries only;
- external AI tools are manual handoff targets, not Voyage runtime dependencies;
- generated `TASK.md` and `CONTEXT.json` are not canonical truth;
- legacy runtime and LangGraph surfaces may remain present but are not canonical v4.1/v4.2 core and do not define the current Voyage identity.

Do not claim or imply that v4.3 is released, tagged, or approved.

---

## 3. Authority and required sources

Authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. Current `README.md`, `docs/README.md`, and `docs/architecture/components.md` as already-aligned identity references;
5. `AGENTS.md` as operational guidance subordinate to the contract.

Read at minimum:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
docs/tutorial/05-langgraph.md
README.md
docs/README.md
docs/architecture/components.md
```

All sources except `docs/tutorial/05-langgraph.md` are read-only for this phase.

---

## 4. Allowed file

You may modify **only**:

```text
docs/tutorial/05-langgraph.md
```

You may create no other files. You may not edit:

```text
README.md
docs/README.md
AGENTS.md
pyproject.toml
.gitignore
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/*
docs/guides/*
docs/examples/*
docs/architecture/*
other docs/tutorial/* files
voyage_framework/
tests/
.github/
```

---

## 5. Required changes to `docs/tutorial/05-langgraph.md`

### 5.1 Preserve the page, but qualify it

- Do not delete, move, rename, or archive the file.
- Keep the existing front matter unless a title adjustment is needed to make the legacy status clear.
- Add a prominent legacy/historical notice near the top of the page.
- State that the page is retained as a historical reference for previous LangGraph-related documentation and is not current onboarding.

Suggested framing:

```text
This page is a historical/legacy reference. LangGraph runtime material is not the canonical Voyage v4.1/v4.2 workflow and must not be read as current product identity.
```

### 5.2 Replace live tutorial-generation instruction

The current placeholder says:

```text
Tutorial placeholder. Run the corresponding phase and use `voyage docs tutorial <correlation_id>` to generate live content.
```

Remove or rewrite this instruction so it no longer invites users to run live tutorial-generation commands as a current workflow.

If the command is mentioned at all, it must be explicitly framed as historical, legacy, non-canonical, and not part of current onboarding.

### 5.3 State the current workflow

Add concise current-identity language:

- Voyage's current canonical workflow is local task memory, context packaging, audit logs, and manual external AI handoff.
- Current user-facing workflows are based on `task.yaml`, `voyage tasks`, `voyage sync`, and deterministic prompt packages.
- Voyage does not call models or providers, execute agents, or run LangGraph as the canonical workflow.

### 5.4 Preserve historical value without expanding scope

- The page may remain short.
- Do not add new tutorials, examples, generated artifacts, or command transcripts.
- Do not document or endorse current LangGraph execution.
- Do not invent migration instructions unless they are limited to pointing readers back to canonical docs already present in the repository.
- Do not update navigation or adjacent tutorial pages in this phase.

### 5.5 Remove present-tense runtime/orchestration claims

Ensure the page does not say any of the following in present tense without a legacy qualifier:

- Voyage is an AI Agent Framework.
- Voyage executes agents autonomously.
- Voyage provides a runtime orchestration framework.
- Voyage replaces LangGraph, CrewAI, or AutoGen.
- Voyage performs automatic agent/graph execution.
- Voyage includes a model/provider execution layer.
- LangGraph runtime is a current canonical workflow.
- Tutorial generation via `voyage docs tutorial <correlation_id>` is current onboarding.

If these terms appear, they must be explicitly framed as legacy, historical, non-canonical, or a negative boundary.

---

## 6. Identity scan and classification

After editing, run:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|automatic graph execution|agent execution|provider|runtime|voyage docs tutorial" docs/tutorial/05-langgraph.md || true
```

Classify every match:

```text
SAFE   = negative boundary / historical / legacy / non-canonical context only
UNSAFE = current identity still claims runtime/agent/framework/orchestration
UNKNOWN = insufficient evidence; needs human decision
```

Rules:

- A SAFE match must explicitly frame the term as legacy, historical, non-canonical, previous architecture, or a negative boundary.
- An UNSAFE match is any present-tense claim that runtime, agent, graph, model, provider, orchestration, or live tutorial-generation behavior is current canonical core.
- If you are unsure, classify as UNKNOWN and stop for human decision.

There must be **zero UNSAFE matches** and **zero UNKNOWN matches** before commit.

---

## 7. What Phase 19 must not do

```text
- Do not edit README.md.
- Do not edit docs/README.md.
- Do not edit AGENTS.md.
- Do not edit pyproject.toml.
- Do not edit .gitignore.
- Do not edit docs/VOYAGE_V4_1_CONTRACT.md.
- Do not edit existing docs/reports/*.
- Do not edit docs/guides/*.
- Do not edit docs/examples/*.
- Do not edit docs/architecture/*.
- Do not edit other docs/tutorial/* files.
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
M       docs/tutorial/05-langgraph.md
```

Forbidden scope check:

```bash
git diff -- README.md docs/README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports docs/guides docs/examples docs/architecture voyage_framework tests .github
git diff -- docs/tutorial/01-introduction.md docs/tutorial/02-basic-agent.md docs/tutorial/03-tools.md docs/tutorial/04-memory.md
```

Expected: empty output.

Identity scan:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|automatic graph execution|agent execution|provider|runtime|voyage docs tutorial" docs/tutorial/05-langgraph.md || true
```

Expected: only SAFE matches; zero UNSAFE matches; zero UNKNOWN matches.

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
git add docs/tutorial/05-langgraph.md
git commit -m "docs: qualify LangGraph tutorial as legacy"
```

Do not push.

---

## 10. Absolute constraints

- Do NOT soften a BLOCKER to WARNING or SAFE.
- Do NOT treat a legacy mention as safe unless it is explicitly framed as legacy, historical, or non-canonical.
- Do NOT infer permission to change files outside `docs/tutorial/05-langgraph.md`.
- Do NOT claim v4.3 is released or approved.
- Do NOT create a tag, merge, push, cleanup, package build, provider call, model call, or runtime task state.
- Report failures honestly. Do not mask errors.
