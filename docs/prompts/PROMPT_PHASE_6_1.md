# Phase 6.1 — Documentation Alignment / AGENTS.md v4.1 Cleanup

## 0. Stop-gate

Before making any changes, verify repository state:

```bash
git fetch origin
git status -sb
git status
git log --oneline --decorate -10
git tag --list "v4.1.0-mvp"
```

Expected:

```text
Branch: docs/v4.1-documentation-alignment
Base: main
main contains: 086fefc Merge Voyage v4.1 MVP
Tag exists: v4.1.0-mvp
Working tree: clean
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.

---

## 1. Mission

Perform **Phase 6.1 Documentation Alignment**.

The goal is to align `AGENTS.md` with the completed **Voyage Framework v4.1 MVP** architecture.

This is a **documentation-only phase**.

Voyage v4.1 MVP is:

```text
Development Memory System / Project Knowledge Operating System
```

Voyage v4.1 MVP is **not**:

```text
AI Agent Framework
Runtime agent orchestrator
LangGraph workflow runtime
CrewAI/AutoGen runtime
Background worker system
Web UI
Production deployment platform
```

---

## 2. Source of truth

Canonical architecture documents:

```text
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
```

`AGENTS.md` is **not** canonical source of truth.

`AGENTS.md` is only an operational guide for AI agents working with the repository.

If `AGENTS.md` conflicts with `docs/VOYAGE_V4_1_CONTRACT.md`, the contract wins.

---

## 3. Allowed files

You may modify only:

```text
AGENTS.md
```

Optional report:

```text
docs/reports/PHASE_6_1_DOCUMENTATION_ALIGNMENT_REPORT.md
```

Do not create the optional report unless useful.

---

## 4. Forbidden files

Do not modify:

```text
README.md
pyproject.toml
.gitignore
TASK.md
CONTEXT.json
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
voyage_framework/
tests/
.github/
```

If you think one of these files must change, STOP and report why.

---

## 5. Required AGENTS.md changes

Rewrite or patch `AGENTS.md` so it clearly states:

```text
1. Voyage Framework v4.1 MVP is a Development Memory System / Project Knowledge Operating System.
2. It is not an AI Agent Framework.
3. It does not execute AI agents.
4. It does not orchestrate agents.
5. It does not use LangGraph as core runtime in v4.1 MVP.
6. AgentRegistry is a read-only role catalog.
7. ModeRegistry is a read-only mode catalog.
8. PromptGenerator only generates prompt packages for external tools.
9. task.yaml is the canonical task specification.
10. TaskRecord in SQLite is canonical runtime task state.
11. EventEngine is append-only audit log.
12. TASK.md and CONTEXT.json are generated artifacts and must not be parsed as canonical truth.
13. Old singular `voyage task <role> --task "..."` remains legacy task generator.
14. Plural `voyage tasks ...` is runtime task database management.
15. `voyage sync ...` is Context Builder Lite.
16. Future Phase 7 may define an adapter contract, but no runtime adapter is implemented yet.
```

---

## 6. Remove or correct legacy wording

Search and correct misleading wording such as:

```text
AI-Native Engineering Operating System
AI Agent Framework
agent runtime
multi-agent orchestrator
LangGraph core runtime
CrewAI runtime
AutoGen runtime
self-running agents
background workers
production deployment runtime
```

Important nuance:

It is acceptable to mention legacy modules if they exist in the repository, but they must be described as **legacy / historical / not v4.1 MVP source of truth** when appropriate.

Do not claim that v4.1 MVP implements runtime orchestration.

Do not claim that v4.1 MVP implements AI model inference.

Do not claim that v4.1 MVP implements production agent execution.

---

## 7. Required AGENTS.md structure

Prefer this structure:

```markdown
# AGENTS.md — Voyage Framework v4.1

## 0. Canonical Source of Truth

## 1. What Voyage v4.1 MVP Is

## 2. What Voyage v4.1 MVP Is Not

## 3. Source of Truth Hierarchy

## 4. Repository Structure

## 5. Core Components

## 6. CLI Commands

## 7. Development Commands

## 8. Safety Rules for AI Agents

## 9. Files Agents Must Not Modify Without Explicit Instruction

## 10. Known Environmental Warnings

## 11. Future Work / Backlog
```

---

## 8. Safety rules for AI agents

`AGENTS.md` must explicitly instruct future agents:

```text
- Do not start new phases without an approved prompt in docs/prompts/.
- Do not modify code when the task is documentation-only.
- Do not commit or push unless explicitly instructed.
- Do not treat AGENTS.md as canonical architecture if it conflicts with the contract.
- Do not use generated TASK.md / CONTEXT.json as source of truth.
- Do not add runtime orchestration unless a future phase explicitly approves it.
- Do not add CLI commands unless a future phase explicitly approves them.
- Do not modify .voyage runtime files.
- Do not hide Windows ACL temp directory warnings by changing .gitignore unless explicitly instructed.
```

---

## 9. Known environmental warnings

Document the current known Windows warning:

```text
warning: could not open directory '.test-tmp-context-p5/': Permission denied
warning: could not open directory '.test-tmp-sync-p5/': Permission denied
warning: could not open directory '.test-tmp-tasks-p5/': Permission denied
warning: could not open directory '.test-tmp-unit-p5/': Permission denied
```

State that these are pre-existing Windows ACL temp directories and are not architecture/code failures.

---

## 10. Quality gates

Run:

```bash
git diff -- AGENTS.md
grep -nEi "AI Agent Framework|runtime orchestration|LangGraph.*core|Development Memory System|Project Knowledge Operating System|source of truth|TASK.md|CONTEXT.json" AGENTS.md
git diff --check
git status --short
```

Optional, to ensure no accidental code breakage:

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_agent_registry.py -v
.venv/Scripts/python.exe -m pytest tests/unit/test_prompt_generator.py -v
.venv/Scripts/python.exe -m ruff format --check AGENTS.md
```

Do not run full test suite unless necessary. This is a documentation-only phase.

---

## 11. Expected changed files

Expected:

```text
AGENTS.md
```

Optional:

```text
docs/reports/PHASE_6_1_DOCUMENTATION_ALIGNMENT_REPORT.md
```

No other files should change.

---

## 12. Final report format

Return:

```markdown
# Phase 6.1 Documentation Alignment Report

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

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
```