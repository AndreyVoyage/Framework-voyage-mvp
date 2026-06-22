# Phase 11 — End-to-End Demo Scenario

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
```

Expected:

```text
Branch: docs/phase-11-e2e-demo-scenario
Base: main
main contains: 3608a5a Merge Phase 10 user guide
Working tree: clean
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.
Do not start Phase 12.

---

## 1. Mission

Create **Phase 11: End-to-End Demo Scenario**.

This phase builds a **complete walkthrough example** showing how Voyage Framework v4.1 works in practice — from idea to audit trail.

It is **not** a tutorial (that was Phase 10).
It is **not** a reference (that was Phase 8).
It is a **realistic scenario** — a concrete example that a new user can read and understand the full lifecycle.

This is a **documentation-only** phase.

---

## 2. What Phase 11 Is

Phase 11 creates a **demo scenario**:

```text
1. A fictional but realistic task: "Add user authentication to the API"
2. Complete task.yaml specification
3. Complete TaskRecord state after each transition
4. Complete CONTEXT.json after sync build
5. Complete TASK.md (generated artifact)
6. Complete PromptPackage (system_prompt + user_prompt)
7. Complete review report
8. Complete audit trail
```

All files are **static examples** — they illustrate what the system produces, not executable code.

---

## 3. What Phase 11 Is NOT

```text
❌ Python code
❌ Tests
❌ CLI commands
❌ Runtime execution
❌ AI model calls
❌ Provider integration
❌ TaskEngine mutations
❌ EventEngine writes
❌ Real task creation in SQLite
❌ Real git operations
```

---

## 4. Allowed files

You may create:

```text
docs/examples/e2e-demo/README.md
docs/examples/e2e-demo/task.yaml
docs/examples/e2e-demo/CONTEXT.example.json
docs/examples/e2e-demo/TASK.example.md
docs/examples/e2e-demo/PROMPT_PACKAGE.example.md
docs/examples/e2e-demo/REVIEW_REPORT.example.md
docs/examples/e2e-demo/AUDIT_TRAIL.example.md
```

Optional:

```text
docs/reports/PHASE_11_E2E_DEMO_SCENARIO_REPORT.md
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
TASK.md (in root)
CONTEXT.json (in root)
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_V4_1_PROCESS_IMPROVEMENT_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/prompts/*
docs/guides/*
docs/examples/ADAPTER_CONTRACT_EXAMPLE.md
docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md
docs/templates/*
voyage_framework/
tests/
.github/
```

If you think one of these files must change, STOP and report why.

---

## 6. Required content

### 6.1 README.md (the scenario narrative)

Must tell a story:

```text
Title: "Adding User Authentication to the API — A Voyage Demo"

Story structure:
1. The Idea
   - Developer wants to add JWT-based auth to a REST API
   - Decides to use Voyage to track the task

2. Step 1: Writing the Task Specification
   - Show task.yaml content
   - Explain each field

3. Step 2: Creating the Task in Runtime
   - Show what TaskRecord looks like after creation
   - Explain status = pending

4. Step 3: Starting the Task
   - Show status transition to in_progress
   - Show updated TaskRecord

5. Step 4: Building Context
   - Show sync build output
   - Show CONTEXT.json content
   - Explain how context aggregates task + runtime + events

6. Step 5: Generating the Prompt Package
   - Show PromptPackage content
   - Show system_prompt (what the AI agent sees)
   - Show user_prompt (what the developer sees)
   - Explain that this is copied to external tool (Codex/Claude/Gemini)

7. Step 6: External Agent Work
   - Show fictional response from external AI agent
   - Show code changes (as diff, not real files)
   - Show that human reviews changes

8. Step 7: Review and Approval
   - Show REVIEW_REPORT.example.md
   - Explain acceptance criteria check
   - Show approval decision

9. Step 8: Completing the Task
   - Show status transition to completed
   - Show final TaskRecord

10. Step 9: Audit Trail
    - Show AUDIT_TRAIL.example.md
    - Explain append-only log
    - Show all events from task lifecycle

11. Summary
    - What was produced
    - What was NOT produced (no runtime execution, no model calls)
    - How to adapt this to real projects
```

### 6.2 task.yaml

Must be a **complete, valid** TaskYamlSpec:

```yaml
id: VF-DEMO-001
title: Add User Authentication to the API
description: Implement JWT-based authentication for the REST API endpoints
role: developer
priority: high
mode: implementation
acceptance_criteria:
  - "POST /auth/login returns JWT token for valid credentials"
  - "POST /auth/register creates new user with hashed password"
  - "GET /api/protected returns 401 without valid token"
  - "Token expires after 24 hours"
  - "Passwords are hashed with bcrypt (cost factor 12)"
  - "All endpoints have rate limiting (5 req/min for auth)"
tests:
  - "test_login_valid_credentials_returns_token"
  - "test_login_invalid_credentials_returns_401"
  - "test_protected_endpoint_without_token_returns_401"
  - "test_token_expiration_after_24h"
  - "test_password_hashing_uses_bcrypt"
```

### 6.3 CONTEXT.example.json

Must show realistic output from ContextBuilder:

```json
{
  "project_id": "default",
  "tasks": [
    {
      "id": "VF-DEMO-001",
      "title": "Add User Authentication to the API",
      "role": "developer",
      "spec_status": "pending",
      "runtime_status": "in_progress",
      "priority": "high",
      "mode": "implementation",
      "acceptance_criteria": [...],
      "has_runtime_record": true,
      "source_path": "task.yaml"
    }
  ],
  "events_summary": {
    "total_events": 3,
    "task_events": 3,
    "latest_event_at": "2026-06-21T14:30:00Z"
  },
  "last_sync": "2026-06-21T14:30:00Z"
}
```

### 6.4 TASK.example.md

Must show what the legacy `voyage task` generator would produce:

```markdown
# Task: Add User Authentication to the API

## Role: developer
## Mode: implementation
## Priority: high

## Description
Implement JWT-based authentication for the REST API endpoints

## Acceptance Criteria
- [ ] POST /auth/login returns JWT token for valid credentials
- [ ] POST /auth/register creates new user with hashed password
- [ ] GET /api/protected returns 401 without valid token
- [ ] Token expires after 24 hours
- [ ] Passwords are hashed with bcrypt (cost factor 12)
- [ ] All endpoints have rate limiting (5 req/min for auth)

## Tests
- test_login_valid_credentials_returns_token
- test_login_invalid_credentials_returns_401
- test_protected_endpoint_without_token_returns_401
- test_token_expiration_after_24h
- test_password_hashing_uses_bcrypt

## Rules
- [ ] ... (from TaskGenerator.DEFAULT_RULES)
```

### 6.5 PROMPT_PACKAGE.example.md

Must show what PromptGenerator produces:

```markdown
# Prompt Package for VF-DEMO-001

## Role: developer
## Mode: implementation
## Task: Add User Authentication to the API

---

## System Prompt

You are a developer working on the Voyage Framework project.
Your task is to implement JWT-based authentication for REST API endpoints.

### Your Responsibilities
- Write clean, tested code
- Follow existing project conventions
- Run tests before submitting

### Your Boundaries
- Do not modify files outside task scope
- Do not change database schema without approval
- Do not expose secrets in code

### Mode Instructions
- implementation mode: write code, add tests, verify with pytest
- constraints: do not rewrite existing auth logic
- output: code + tests + brief documentation

---

## User Prompt

Task: Add User Authentication to the API

Description: Implement JWT-based authentication for the REST API endpoints

Acceptance Criteria:
1. POST /auth/login returns JWT token for valid credentials
2. POST /auth/register creates new user with hashed password
3. GET /api/protected returns 401 without valid token
4. Token expires after 24 hours
5. Passwords are hashed with bcrypt (cost factor 12)
6. All endpoints have rate limiting (5 req/min for auth)

Relevant Files:
- src/api/routes.py
- src/auth/jwt_handler.py
- tests/test_auth.py

---

## Safety Reminders

- Do not commit or push unless explicitly instructed
- Do not modify files outside the listed relevant files
- Report deviations instead of guessing
- Run tests (pytest) before finalizing
```

### 6.6 REVIEW_REPORT.example.md

Must show what a human review looks like:

```markdown
# Review Report: VF-DEMO-001

## Reviewer: (human or AI reviewer role)
## Date: 2026-06-21

## Acceptance Criteria Check

| Criterion | Status | Notes |
|---|---|---|
| POST /auth/login returns JWT token | ✅ Pass | Token valid, 24h expiration correct |
| POST /auth/register creates user | ✅ Pass | Password hashed with bcrypt cost 12 |
| GET /api/protected returns 401 | ✅ Pass | Middleware correctly rejects missing token |
| Token expires after 24h | ✅ Pass | Expiration tested with clock manipulation |
| Passwords hashed with bcrypt | ✅ Pass | Cost factor verified |
| Rate limiting 5 req/min | ⚠️ Partial | Rate limit works but no burst protection |

## Regression Check
- [ ] Existing API endpoints still work
- [ ] No breaking changes to public API
- [ ] Tests pass: pytest tests/ -v

## Decision
- **Status: Approved with minor note**
- Note: Add burst protection in follow-up task
- Action: Create VF-DEMO-002 for rate limit improvement
```

### 6.7 AUDIT_TRAIL.example.md

Must show append-only EventEngine log:

```markdown
# Audit Trail: VF-DEMO-001

## Event Log (append-only)

| # | Timestamp | Event Type | Actor | Details |
|---|---|---|---|---|
| 1 | 2026-06-21T14:00:00Z | TASK_CREATED | developer | Task VF-DEMO-001 created from task.yaml |
| 2 | 2026-06-21T14:05:00Z | TASK_STARTED | developer | Status: pending → in_progress |
| 3 | 2026-06-21T14:10:00Z | CONTEXT_BUILT | developer | ContextBuilder.build() called |
| 4 | 2026-06-21T14:15:00Z | PROMPT_GENERATED | developer | PromptPackage for role=developer, mode=implementation |
| 5 | 2026-06-21T14:30:00Z | AGENT_RESPONSE | external | Codex/Kimi returned code changes |
| 6 | 2026-06-21T14:45:00Z | REVIEW_APPROVED | reviewer | All criteria pass, minor note |
| 7 | 2026-06-21T15:00:00Z | TASK_COMPLETED | developer | Status: in_progress → completed |
| 8 | 2026-06-21T15:05:00Z | FOLLOW_UP_CREATED | developer | VF-DEMO-002 created for rate limit improvement |
```

---

## 7. Content constraints

All examples must:

```text
- Be realistic but fictional (no real API, no real credentials)
- Show complete content, not placeholders
- Include timestamps and realistic data
- Reference actual Voyage classes and concepts
- Clearly mark generated artifacts (TASK.md, CONTEXT.json) as non-canonical
- Include safety reminders in PROMPT_PACKAGE
- Show human-in-the-loop approval
- Show that Voyage does not execute agents or call models
```

---

## 8. Tone and style

- Story-like but technical
- Concrete, not abstract
- Show, don't just tell
- Include both successes and realistic minor issues (rate limit partial pass)
- Honest about limitations
- No marketing

---

## 9. Quality gates

```bash
git diff --stat
git diff --name-status
git diff --check
git status --short
```

Expected: only docs/examples/e2e-demo/ and docs/reports/ files created.

Forbidden files check:

```bash
git diff -- AGENTS.md README.md pyproject.toml .gitignore voyage_framework tests .github docs/VOYAGE_V4_1_CONTRACT.md docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md docs/reports/VOYAGE_V4_1_PROCESS_IMPROVEMENT_AUDIT.md docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md docs/prompts/* docs/guides/* docs/examples/ADAPTER_CONTRACT_EXAMPLE.md docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md docs/templates/*
```

Expected: no diff.

---

## 10. Expected changed files

Expected:

```text
docs/examples/e2e-demo/README.md
docs/examples/e2e-demo/task.yaml
docs/examples/e2e-demo/CONTEXT.example.json
docs/examples/e2e-demo/TASK.example.md
docs/examples/e2e-demo/PROMPT_PACKAGE.example.md
docs/examples/e2e-demo/REVIEW_REPORT.example.md
docs/examples/e2e-demo/AUDIT_TRAIL.example.md
```

Optional:

```text
docs/reports/PHASE_11_E2E_DEMO_SCENARIO_REPORT.md
```

No other files should change.

---

## 11. Final report format

Return:

```markdown
# Phase 11 Implementation Report

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

Do not commit.
Do not push.
Do not start Phase 12.
