# Phase 9 — Workflow Policy / Standard Phase Template

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
Branch: docs/phase-9-workflow-policy
Base: main
main contains: 742b3af Phase 8: add adapter contract usage docs and examples
Working tree: clean
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.
Do not start Phase 10.

---

## 1. Mission

Create **Phase 9: Workflow Policy / Standard Phase Template**.

This phase standardizes how all future Voyage Framework phases are planned, executed, audited, and merged.

It is a **meta-phase** — it documents the process itself, not product features.

---

## 2. What Phase 9 Is

Phase 9 creates:

```text
1. Standard phase lifecycle definition
2. Stop-gate template
3. Allowed/forbidden files template
4. Quality gates by task type:
   - code phase
   - docs-only phase
   - audit-only phase
   - release/tag phase
5. Git authority and credentials policy
6. Windows temp path strategy
7. Final report template
8. Phase prompt template (for future phases)
```

All outputs are **Markdown documentation and templates**.
No Python code.
No tests.
No CLI.
No runtime.

---

## 3. What Phase 9 Is NOT

```text
❌ Python code
❌ Tests
❌ CLI commands
❌ Runtime execution
❌ AI model calls
❌ Provider integration
❌ TaskEngine mutations
❌ EventEngine writes
```

---

## 4. Allowed files

You may create:

```text
docs/guides/PHASE_WORKFLOW_POLICY.md
docs/templates/PHASE_PROMPT_TEMPLATE.md
docs/templates/PHASE_FINAL_REPORT_TEMPLATE.md
docs/templates/PHASE_STOP_GATE_TEMPLATE.md
docs/templates/PHASE_QUALITY_GATES_TEMPLATE.md
```

Optional report:

```text
docs/reports/PHASE_9_WORKFLOW_POLICY_REPORT.md
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
docs/reports/*
docs/prompts/*
docs/guides/ADAPTER_CONTRACT_USAGE.md
docs/examples/*
voyage_framework/
tests/
.github/
```

If you think one of these files must change, STOP and report why.

---

## 6. Required content

### 6.1 PHASE_WORKFLOW_POLICY.md

Must define:

```text
1. Standard Phase Lifecycle (8 steps):
   a. Phase 0: Contract / Scope Definition
   b. Phase 1: Prompt Creation (docs/prompts/PROMPT_PHASE_N.md)
   c. Phase 2: Prompt Review and Approval
   d. Phase 3: Implementation (by Codex/Kimi or human)
   e. Phase 4: Self-Audit (tests, gates, diff review)
   f. Phase 5: Human Review (owner approval)
   g. Phase 6: Merge and Tag
   h. Phase 7: Closure Audit and Documentation

2. Branch Naming Convention:
   - code phases: refactor/vX.Y-feature-name
   - docs phases: docs/vX.Y-feature-name
   - audit phases: audit/vX.Y-feature-name
   - release: release/vX.Y.Z

3. Git Authority:
   - AI agents (Codex/Kimi) do NOT push to origin
   - AI agents may create local commits
   - Human owner pushes to origin
   - AI agents report: "Push requires credentials. User must run: git push origin <branch>"
   - No workarounds, no credential guessing, no token exposure

4. Commit Message Convention:
   - "Phase N: description" for implementation
   - "docs: description" for documentation
   - "audit: description" for audit reports
   - "fix: description" for patches

5. Windows ACL Temp Directory Strategy:
   - Use explicit --basetemp paths: .pytest-tmp/phase-name
   - Never rely on system %TEMP% on Windows
   - If ACL dirs appear, report them honestly
   - Do not add .gitignore entries to hide them without explicit approval
   - If removal fails, report: "Windows ACL protected, manual cleanup required"

6. Stop-gate Rules:
   - Every phase must start with environment verification
   - working tree must be clean (except pre-existing ACL dirs)
   - Forbidden files must not be modified
   - Tests must pass before any commit
   - Ruff/mypy must pass before any commit
   - No commit if git diff --check fails

7. Quality Gates by Task Type:

   a. Code Phase:
      - pytest tests/unit/test_new_module.py -v
      - pytest tests/unit -v
      - ruff check .
      - ruff format --check .
      - mypy voyage_framework/core/new_module.py
      - git diff --check
      - git status --short

   b. Docs-Only Phase:
      - git diff --check
      - git status --short
      - Optional: ruff check docs/ (if code snippets)

   c. Audit-Only Phase:
      - git diff --check
      - git status --short
      - Forbidden file diff review
      - No tests needed unless specified

   d. Release/Tag Phase:
      - git tag verification
      - git log --oneline --decorate
      - Working tree clean
      - All previous phases merged

8. Allowed/Forbidden Files Template:
   - Every phase prompt must list explicitly allowed files
   - Every phase prompt must list explicitly forbidden files
   - If a forbidden file changes, the phase must be rejected
   - No "git add ." — only specific files

9. Final Report Template Requirements:
   - Changed files list
   - Implemented features
   - Not implemented features (explicitly)
   - Test results
   - Quality gates results
   - Pollution check
   - Forbidden files check
   - Risks / deviations
   - Verdict: A / B / C

10. Credentials Policy:
    - AI agents never have GitHub credentials
    - AI agents never push automatically
    - Human owner handles all pushes
    - If push fails with "could not read Username", report clearly
    - No credential storage in code, prompts, or logs
```

### 6.2 PHASE_PROMPT_TEMPLATE.md

Must provide a template for future phase prompts:

```markdown
# Phase N — [Feature Name]

## 0. Stop-gate

[Environment verification commands and expected output]

## 1. Mission

[What this phase implements]

## 2. What Phase N Is

[Clear scope]

## 3. What Phase N Is NOT

[Explicit anti-scope]

## 4. Allowed files

[List explicitly]

## 5. Forbidden files

[List explicitly]

## 6. What to implement

[Detailed specification]

## 7. Design requirements

[Constraints]

## 8. Tests

[Required test coverage]

## 9. Quality gates

[Commands to run]

## 10. Pollution check

[How to verify no project pollution]

## 11. Expected changed files

[List]

## 12. Final report format

[Template]
```

### 6.3 PHASE_FINAL_REPORT_TEMPLATE.md

Must provide a reusable final report template:

```markdown
# Phase N Implementation Report

## Environment
- branch: ...
- commit: ...
- origin sync: ...

## Changed files
-

## Implemented
-

## Not implemented
-

## Tests
- [module tests]: X/Y passed
- [unit suite]: X/Y passed
- [full suite]: X/Y passed

## Quality gates
- ruff check: passed / failed
- ruff format: passed / failed
- mypy: passed / failed
- git diff --check: passed / failed

## Pollution check
- .voyage/tasks.db: created / not created
- TASK.md: changed / unchanged
- CONTEXT.json: changed / unchanged
- untracked files: ...

## Forbidden files check
- [file]: changed / unchanged

## Risks / deviations
1. ...
2. ...

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
D. Push required (user must run: git push origin <branch>)
```

### 6.4 PHASE_STOP_GATE_TEMPLATE.md

Must provide a reusable stop-gate block:

```markdown
## 0. Stop-gate

Before making any changes, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
```

Expected: `/c/DEV/FRAMEWORK/Framework-voyage-mvp`

```bash
git branch --show-current
git status -sb
git log --oneline --decorate -10
```

Expected:
- Branch: [specified branch]
- Base: [specified base]
- Working tree: clean

Known Windows warnings (acceptable):
```text
warning: could not open directory '.test-tmp-*/': Permission denied
```

If working tree is not clean (excluding pre-existing ACL dirs), STOP and report.

Do not commit.
Do not push.
```

---

## 7. Tone and constraints

- Direct and practical
- Not marketing-oriented
- Honest about limitations
- Future-oriented only where scoped
- No fluff

---

## 8. Quality gates

```bash
git diff --stat
git diff --name-status
git diff --check
git status --short
```

Expected: only docs/guides/, docs/templates/, docs/reports/ files created.

Forbidden files check:

```bash
git diff -- AGENTS.md README.md pyproject.toml .gitignore voyage_framework tests .github docs/VOYAGE_V4_1_CONTRACT.md docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md docs/guides/ADAPTER_CONTRACT_USAGE.md docs/examples/
```

Expected: no diff.

---

## 9. Expected changed files

Expected:

```text
docs/guides/PHASE_WORKFLOW_POLICY.md
docs/templates/PHASE_PROMPT_TEMPLATE.md
docs/templates/PHASE_FINAL_REPORT_TEMPLATE.md
docs/templates/PHASE_STOP_GATE_TEMPLATE.md
docs/templates/PHASE_QUALITY_GATES_TEMPLATE.md
```

Optional:

```text
docs/reports/PHASE_9_WORKFLOW_POLICY_REPORT.md
```

No other files should change.

---

## 10. Final report format

Return:

```markdown
# Phase 9 Implementation Report

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
Do not start Phase 10.
