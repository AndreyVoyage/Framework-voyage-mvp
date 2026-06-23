# Phase 22 — Published Docs Residual Identity Cleanup

## 0. Stop-gate

Before making any change, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
Branch: docs/phase-22-published-docs-residual-identity-cleanup
Base: main
main contains: 199160c Merge Phase 21 v4.3 release readiness re-audit
Working tree: clean
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit without verifying the diff scope.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 23.

---

## 1. Mission

Perform **Phase 22: Published Docs Residual Identity Cleanup**.

The goal is to close residual published documentation identity blockers identified in `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md` by editing **only**:

```text
docs/index.md
docs/FAQ.md
docs/_config.yml
```

These three files are part of the published GitHub Pages site. They may still contain stale v4.0 identity claims, AI-native/runtime/agent/LangGraph wording, or other misleading current-capability statements. This phase aligns them with the canonical Project Knowledge OS / Development Memory System identity.

This phase must not change code, tests, package metadata, release workflows, or any other documentation pages.

---

## 2. Canonical identity target

Use this exact identity as the target for all three files:

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
2. `docs/reports/VOYAGE_PHASE_21_V4_3_RELEASE_READINESS_REAUDIT.md`;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
5. Current `README.md` and `docs/README.md` (already aligned) as style/identity reference;
6. `AGENTS.md` as operational guidance subordinate to the contract.

Inspect before editing:

```bash
git --no-pager diff -- docs/index.md docs/FAQ.md docs/_config.yml
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|AI agent|agent framework|Trigger deploy" -- docs/index.md docs/FAQ.md docs/_config.yml || true
```

Also inspect `docs/index.md` for suspicious binary/NUL-style content:

```bash
python - <<'PY'
from pathlib import Path
p = Path("docs/index.md")
data = p.read_bytes()
print("docs/index.md bytes:", len(data))
print("contains NUL:", b"\x00" in data)
print("preview:", data[:200])
PY
```

If `python` is not on PATH, use `.venv/Scripts/python.exe`.

All sources except `docs/index.md`, `docs/FAQ.md`, and `docs/_config.yml` are read-only for this phase.

---

## 4. Allowed files

You may modify **only**:

```text
docs/index.md
docs/FAQ.md
docs/_config.yml
```

You may create no other files. You may not edit `README.md`, `docs/README.md`, `AGENTS.md`, `pyproject.toml`, `.gitignore`, `docs/VOYAGE_V4_1_CONTRACT.md`, existing `docs/reports/*`, `docs/guides/`, `docs/examples/`, `docs/tutorial/`, `docs/architecture/`, `docs/prompts/*`, `voyage_framework/`, `tests/`, or `.github/`.

---

## 5. Required changes

### 5.1 `docs/_config.yml`

- Update `title` and `description` fields to match the canonical identity.
- Remove or rephrase any AI-native / AI-agent / runtime orchestration wording.
- Keep `baseurl` and `url` intact unless they are factually wrong.

Example target:

```yaml
theme: minima
title: Voyage Framework
description: Local Project Knowledge OS / Development Memory System
baseurl: /Framework-voyage-mvp
url: https://andreyvoyage.github.io
```

### 5.2 `docs/index.md`

- Open the file as bytes first and verify it does not contain NUL characters or other suspicious binary content.
- If the file contains placeholder text such as “Trigger deploy” or other non-content strings without clear purpose, replace them with meaningful identity-aligned content.
- Replace any stale v4.0 / AI Dev Framework / AI-native identity with the canonical identity.
- Remove or rephrase current claims about LangGraph runtime, AgentRuntime, runtime orchestration, autonomous execution, model/provider execution, or automatic graph/agent execution.
- Preserve historical facts only if explicitly labeled as legacy/historical/non-canonical.
- Keep Jekyll frontmatter (`---`) intact and valid.
- Keep navigation links accurate.

### 5.3 `docs/FAQ.md`

- Review every question and answer for AI-native / agent / runtime / orchestration / provider / model execution claims.
- Rephrase answers that present Voyage as currently executing agents, running graphs, orchestrating workflows, or replacing LangGraph/CrewAI/AutoGen.
- Allowed phrasing:
  - “Voyage does not execute agents or call models.”
  - “Legacy v4.0 runtime modules remain in the repository but are not canonical core.”
  - “Voyage is not a replacement for LangGraph, CrewAI, or AutoGen.”
- Do not delete questions unless they are pure noise; reframe answers.

---

## 6. Identity scan and classification

After editing, run:

```bash
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|AI agent|agent framework" -- docs/index.md docs/FAQ.md docs/_config.yml || true
```

Classify every match:

```text
SAFE    = canonical, negative boundary, historical, legacy, or non-canonical context only
UNSAFE  = published docs still claim current AI agent/runtime/orchestration/provider execution identity
UNKNOWN = ambiguous published docs wording needs human decision
```

Rules:

- A SAFE match must explicitly frame the term as legacy, historical, non-canonical, previous architecture, risk being corrected, or a negative boundary.
- An UNSAFE match is any present-tense claim that Voyage currently is, replaces, executes, orchestrates, or runs agents/models/graphs.
- If you are unsure, classify as UNKNOWN and stop for human decision.

There must be **zero UNSAFE matches** and **zero UNKNOWN matches** in the three allowed files before commit.

---

## 7. What Phase 22 must not do

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
- Do not edit docs/architecture/*.
- Do not edit docs/prompts/*.
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

Expected changed files:

```text
M       docs/_config.yml
M       docs/FAQ.md
M       docs/index.md
```

Forbidden scope check:

```bash
git diff -- README.md docs/README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports docs/guides docs/examples docs/tutorial docs/architecture docs/prompts voyage_framework tests .github
```

Expected: empty output.

Identity scan (repeat after edits):

```bash
git grep -n -E "AI Agent Framework|AI-native|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|LangGraphRuntime|AgentRuntime|runtime orchestration|provider execution|model execution|agent execution|automatic graph execution|AI agent|agent framework" -- docs/index.md docs/FAQ.md docs/_config.yml || true
```

Expected: only SAFE matches; zero UNSAFE; zero UNKNOWN.

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
git add docs/index.md docs/FAQ.md docs/_config.yml
git commit -m "docs: clean residual identity in published docs

- Align docs/_config.yml title/description with canonical identity.
- Remove stale v4.0 / AI-native / runtime / agent claims from docs/index.md.
- Reframe FAQ answers to state non-execution boundaries and legacy context.
- Preserve historical facts only when explicitly labeled legacy/historical.
- No code, tests, metadata, workflows, or other docs changed."
```

Do not push.

---

## 10. Absolute constraints

- Do NOT soften a BLOCKER to WARNING or SAFE.
- Do NOT treat a legacy mention as safe unless it is explicitly framed as legacy/historical/non-canonical.
- Do NOT infer permission to change files outside the allowed three files.
- Do NOT claim v4.3 is released or approved.
- Report failures honestly. Do not mask errors.
