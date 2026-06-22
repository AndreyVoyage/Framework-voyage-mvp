# Phase 17 — Published Documentation Identity Alignment

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
Branch: docs/phase-17-published-docs-identity-alignment
Base: main
main contains: a2e7bc1 Merge Phase 16 documentation identity fix plan
Working tree: clean
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit without verifying the diff scope.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 18.

---

## 1. Mission

Perform **Phase 17: Published Documentation Identity Alignment**.

The goal is to close **Blocker 1** from `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md` and `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md` by editing **only** `docs/README.md`.

`docs/README.md` is the published GitHub Pages landing page. It currently presents a stale v4.0 identity:

- “Voyage AI Dev Framework v4.0”
- “AI-Native Engineering Operating System”
- “LangGraph Integration & Process Documentation (MVP runnable)”
- `AgentRuntime` / `LangGraphRuntime` as current capabilities
- `voyage run` / `voyage graph run` in the quick-start

This phase must align `docs/README.md` with the canonical identity without changing code, tests, metadata, workflows, or other documentation pages.

---

## 2. Canonical identity target

Use this exact identity as the target for `docs/README.md`:

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
4. Current root `README.md` (already aligned) as style/identity reference;
5. `AGENTS.md` as operational guidance subordinate to the contract.

Read at minimum:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
README.md
docs/README.md
```

All sources except `docs/README.md` are read-only for this phase.

---

## 4. Allowed file

You may modify **only**:

```text
docs/README.md
```

You may create no other files. You may not edit `README.md`, `AGENTS.md`, `pyproject.toml`, `.gitignore`, `docs/VOYAGE_V4_1_CONTRACT.md`, existing `docs/reports/*`, `docs/guides/`, `docs/examples/`, `docs/tutorial/`, `docs/architecture/`, `voyage_framework/`, `tests/`, or `.github/`.

---

## 5. Required changes to `docs/README.md`

### 5.1 Title and subtitle

- Replace the leading title “Voyage AI Dev Framework v4.0” with a title that matches the canonical identity, e.g. “Voyage Framework”.
- Replace the subtitle “AI-Native Engineering Operating System” with the canonical identity sentence.
- Remove or rephrase the “MVP runnable” LangGraph status line.

### 5.2 Status / version line

- Do not claim version `4.0.0` as the current product identity.
- If a version is mentioned, phrase it as a historical note or omit it.
- Do not claim “Phase 4 + Chronicler — LangGraph Integration ... (MVP runnable)” as current status.

### 5.3 Quick-start / onboarding

- Remove `voyage run` and `voyage graph run` from the current quick-start, or clearly label them as legacy/compatibility commands, not canonical onboarding.
- The canonical quick-start must use `voyage tasks` and `voyage sync` commands.
- If legacy commands are retained for reference, they must be in a clearly labeled “Legacy compatibility” or “Historical commands” section.

### 5.4 Architecture / structure section

- Remove or label as legacy any present-tense claim that `AgentRuntime`, `LangGraphRuntime`, graph builder, or sandbox execution are current core capabilities.
- If the legacy code is mentioned, use phrasing such as:
  - “The repository retains historical v4.0 runtime modules ...”
  - “These surfaces are not the canonical v4.1/v4.2 core.”
- Do not delete accurate historical facts; reframe them as historical context.

### 5.5 Future phases section

- Remove or reframe the “Future Phases” list that presents Semantic Memory, AST Manager, Self-Improving Engine, LangGraph Integration, etc. as upcoming current features.
- If retained, label it as historical roadmap or legacy planning and note that current direction is documented in the v4.1 contract and Phase 16 plan.

### 5.6 Security / runtime sections

- Remove or label as legacy any section that presents `SecureExecutor`, `AgentRuntime`, approval flow, or Docker backend as a current user-facing capability.
- The canonical `docs/README.md` must not teach a new reader how to execute agents or graphs.

### 5.7 Footer / generated-by

- Remove or rephrase “Generated by Voyage Framework v4.0” and similar stale generated text.

---

## 6. Identity scan and classification

After editing, run:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|AI-Native Engineering Operating System" docs/README.md || true
```

Classify every match:

```text
SAFE   = negative boundary / historical / legacy context / risk wording being corrected
UNSAFE = current identity still claims runtime/agent/framework/orchestration
UNKNOWN = insufficient evidence; needs human decision
```

Rules:

- A SAFE match must explicitly frame the term as legacy, historical, non-canonical, previous architecture, risk being corrected, or a negative boundary.
- An UNSAFE match is any present-tense claim that Voyage currently is, replaces, executes, orchestrates, or runs agents/models/graphs.
- If you are unsure, classify as UNKNOWN and stop for human decision.

There must be **zero UNSAFE matches** in `docs/README.md` before commit.

---

## 7. What Phase 17 must not do

```text
- Do not edit README.md (root).
- Do not edit AGENTS.md.
- Do not edit pyproject.toml.
- Do not edit .gitignore.
- Do not edit docs/VOYAGE_V4_1_CONTRACT.md.
- Do not edit existing docs/reports/*.
- Do not edit docs/guides/*.
- Do not edit docs/examples/*.
- Do not edit docs/tutorial/*.
- Do not edit docs/architecture/*.
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
M       docs/README.md
```

Forbidden scope check:

```bash
git diff -- README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports docs/guides docs/examples docs/tutorial docs/architecture voyage_framework tests .github
```

Expected: empty output.

Identity scan:

```bash
grep -RInE "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|AI-Native Engineering Operating System" docs/README.md || true
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
git add docs/README.md
git commit -m "docs: align docs/README.md with canonical v4.1/v4.2 identity

- Replace stale v4.0 AI/runtime identity with canonical Project Knowledge OS identity.
- Label retained runtime/graph content as legacy/historical.
- Remove misleading quick-start commands (voyage run / voyage graph run).
- Keep accurate historical facts; reframe, do not delete.
- No code, tests, metadata, workflows, or other docs changed."
```

Do not push.

---

## 10. Absolute constraints

- Do NOT soften a BLOCKER to WARNING or SAFE.
- Do NOT treat a legacy mention as safe unless it is explicitly framed as legacy/historical/non-canonical.
- Do NOT infer permission to change files outside `docs/README.md`.
- Do NOT claim v4.3 is released or approved.
- Report failures honestly. Do not mask errors.
