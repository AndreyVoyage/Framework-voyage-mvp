# Phase 8 — Adapter Contract Usage Docs and Examples

## 0. Stop-gate

Before making any changes, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
```

Expected:

```text
/c/DEV/FRAMEWORK/Framework-voyage-mvp
```

Check branch and history:

```bash
git branch --show-current
git status -sb
git log --oneline --decorate -10
git tag --list "v4.1.0-mvp"
git tag --list "v4.2.0-adapter-contract"
```

Expected:

```text
Branch: docs/phase-8-adapter-usage-docs
Base: main
main contains: 8d7b268 docs: add Phase 7 closure audit
Tag v4.1.0-mvp exists: yes
Tag v4.2.0-adapter-contract exists: yes
Working tree: clean
```

If the working tree is not clean (excluding pre-existing Windows ACL temp dirs), STOP and report.

Do not commit.
Do not push.
Do not start Phase 9.

---

## 1. Mission

Implement **Phase 8: Adapter Contract Usage Docs and Examples**.

This phase adds **documentation-only** guides and examples showing how to use the Phase 7 Adapter Contract.

Phase 8 is **not** runtime execution.
Phase 8 is **not** agent implementation.
Phase 8 is **not** provider integration.

Phase 8 only writes Markdown documents and Python example snippets (for illustration, not execution).

---

## 2. What Phase 8 Is

Phase 8 creates:

```text
- User guide: how to construct an AgentRequest
- User guide: how to interpret an AgentResponse
- User guide: how to use ApprovalFlow
- Example: mock adapter implementation (for illustration only)
- Example: prompt package generation workflow
- Example: task lifecycle with adapter contract
```

All examples are **static documentation**.
No code runs.
No services start.
No models are called.

---

## 3. What Phase 8 Is NOT

```text
❌ Runtime agent execution
❌ AI model inference
❌ LangGraph workflow orchestration
❌ CrewAI/AutoGen runtime
❌ Background workers
❌ Webhooks or callbacks
❌ Credential storage or auth
❌ TaskEngine mutations
❌ EventEngine writes
❌ Direct task.yaml mutation
❌ CLI commands
❌ Network clients
❌ Provider integration (OpenAI, Anthropic, Google, etc.)
```

---

## 4. Allowed files

You may create:

```text
docs/guides/ADAPTER_CONTRACT_USAGE.md
docs/examples/ADAPTER_CONTRACT_EXAMPLE.md
docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md
```

Optional report:

```text
docs/reports/PHASE_8_ADAPTER_USAGE_DOCS_REPORT.md
```

Do not create the optional report unless useful.

---

## 5. Forbidden files

Do not modify:

```text
AGENTS.md
README.md
pyproject.toml
.gitignore
TASK.md
CONTEXT.json
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_V4_1_PROCESS_IMPROVEMENT_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/prompts/*
voyage_framework/
tests/
.github/
```

If you think one of these files must change, STOP and report why.

---

## 6. Required documentation content

### 6.1 ADAPTER_CONTRACT_USAGE.md

Must cover:

```text
1. What is the Adapter Contract (v4.1.0)
2. Supported roles and modes
3. How to construct a valid AgentRequest
   - Required fields
   - Optional fields
   - Validation rules
4. How to interpret AgentResponse
   - Status values: pending, approved, rejected, completed
   - prompt_package field
   - context_snapshot field
   - next_steps field
5. How to use ApprovalFlow
   - When approval is required
   - Timeout handling
   - Rejection handling
6. How to use ValidationResult
   - valid=true vs valid=false
   - Error tuples
   - Warning tuples
7. Version compatibility
   - AdapterContract.version = "v4.1.0"
   - Future versions
```

### 6.2 ADAPTER_CONTRACT_EXAMPLE.md

Must include:

```text
1. Example: requesting a task for role="developer", mode="implementation"
2. Example: interpreting a completed response
3. Example: handling approval-required action
4. Example: validation failure and recovery
5. Example: full workflow from request to response
```

All examples must use **static Python snippets** (for illustration only).
No executable code.
No imports that trigger runtime.

### 6.3 ADAPTER_MOCK_IMPLEMENTATION.md

Must show:

```text
1. What a mock adapter would look like
2. How each AdapterProtocol method is implemented as a stub
3. How to test the mock adapter (conceptually, not executable tests)
4. How to replace the mock with a real adapter in future phases
```

The mock implementation must be **clearly marked as illustrative** and must not be importable or runnable.

---

## 7. Content constraints

All documentation must:

```text
- Clearly state that examples are for illustration only
- Not claim that Voyage v4.1 executes agents
- Not claim that Voyage v4.1 calls AI models
- Not claim that Voyage v4.1 orchestrates workflows
- Use the exact class names from Phase 7:
  AdapterContract, AgentRequest, AgentResponse, ValidationResult, ApprovalFlow, AdapterProtocol
- Reference canonical source of truth:
  docs/VOYAGE_V4_1_CONTRACT.md
  docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
- Mention that runtime execution requires future Phase 8+ with explicit approved prompt
```

---

## 8. Tone and style

- Direct and practical
- Not marketing-oriented
- Not claiming AI capabilities
- Honest about current limitations
- Future-oriented only where explicitly scoped

---

## 9. Quality gates

### 9.1 File check

```bash
git diff --stat
git diff --name-status
git diff --check
git status --short
```

Expected: only docs/guides/ and docs/examples/ files created.

### 9.2 Forbidden files check

```bash
git diff -- AGENTS.md README.md pyproject.toml .gitignore voyage_framework tests .github
```

Expected: no diff.

### 9.3 Content check (grep keywords)

```bash
grep -nEi "execute.*agent|run.*agent|call.*model|invoke.*model|api.*key|credential|token|webhook|background.*worker|orchestrat|runtime.*execution|self-running|production.*deploy" docs/guides/ADAPTER_CONTRACT_USAGE.md docs/examples/ADAPTER_CONTRACT_EXAMPLE.md docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md
```

Expected: no matches (or only in "what is NOT supported" sections).

### 9.4 Optional: ruff on example snippets

```bash
.venv/Scripts/python.exe -m ruff check docs/examples/ --select=E,W,F
```

Only if example snippets contain Python code blocks. This is optional.

---

## 10. Expected changed files

Expected:

```text
docs/guides/ADAPTER_CONTRACT_USAGE.md
docs/examples/ADAPTER_CONTRACT_EXAMPLE.md
docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md
```

Optional:

```text
docs/reports/PHASE_8_ADAPTER_USAGE_DOCS_REPORT.md
```

No other files should change.

---

## 11. Final report format

Return:

```markdown
# Phase 8 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Quality gates
-

## Forbidden files check
-

## Content check
-

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
```

Do not commit.
Do not push.
Do not start Phase 9.
