# Phase 10 — User Guide / Installation Guide / Quickstart

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
Branch: docs/phase-10-user-guide
Base: main
main contains: e671b28 Merge Phase 9 workflow policy
Working tree: clean
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.
Do not start Phase 11.

---

## 1. Mission

Create **Phase 10: User Guide, Installation Guide, and Quickstart**.

This phase makes the Voyage Framework v4.1 understandable for:
- New users joining the project
- Future you (revisiting after a month)
- External AI agents (Codex, Claude, Gemini) working with the repository
- Contributors who need to understand the workflow

This is a **documentation-only** phase.

---

## 2. What Phase 10 Is

Phase 10 creates user-facing documentation:

```text
- What Voyage Framework is and what it does
- What Voyage Framework is NOT
- How to install and set up
- How to run checks and tests
- How to create a task
- How to build context
- How to use roles and modes
- How to generate prompt packages
- Safe workflow with Kimi/Codex
- Minimum end-to-end workflow from idea to merge
```

---

## 3. What Phase 10 Is NOT

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
docs/guides/USER_GUIDE.md
docs/guides/INSTALLATION.md
docs/guides/QUICKSTART.md
docs/guides/END_TO_END_WORKFLOW.md
```

Optional:

```text
docs/reports/PHASE_10_USER_GUIDE_REPORT.md
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
docs/guides/PHASE_WORKFLOW_POLICY.md
docs/guides/ADAPTER_CONTRACT_USAGE.md
docs/examples/*
docs/templates/*
voyage_framework/
tests/
.github/
```

If you think one of these files must change, STOP and report why.

---

## 6. Required documentation content

### 6.1 USER_GUIDE.md

Must cover:

```text
1. What is Voyage Framework v4.1
   - Development Memory System / Project Knowledge Operating System
   - NOT an AI Agent Framework
   - What it does: task tracking, context building, role/mode catalog, prompt generation
   - What it does NOT do: execute agents, call models, orchestrate workflows

2. Core concepts (brief)
   - task.yaml = canonical task specification
   - TaskRecord = runtime task state in SQLite
   - EventEngine = append-only audit log
   - AgentRegistry = read-only role catalog
   - ModeRegistry = read-only mode catalog
   - ContextBuilder = context aggregation
   - PromptGenerator = prompt package generation

3. Who is this for
   - Solo developers managing complex projects
   - Teams using AI assistants (Codex, Claude, Gemini)
   - Anyone who needs structured task tracking with context

4. Architecture overview (high level)
   - Reference VOYAGE_V4_1_CONTRACT.md for details
   - Reference AGENTS.md for agent rules
   - Reference PHASE_WORKFLOW_POLICY.md for development process

5. Safety and boundaries
   - Voyage does not execute AI agents
   - Voyage does not call AI models
   - Voyage does not store credentials
   - Prompt packages are for manual copy-paste to external tools
```

### 6.2 INSTALLATION.md

Must cover:

```text
1. Prerequisites
   - Python 3.11 or higher
   - Git
   - Virtual environment (recommended)

2. Clone the repository
   ```bash
   git clone https://github.com/AndreyVoyage/Framework-voyage-mvp.git
   cd Framework-voyage-mvp
   ```

3. Create virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/macOS
   ```

4. Install in development mode
   ```bash
   pip install -e ".[dev]"
   ```

5. Verify installation
   ```bash
   python -c "import voyage_framework; print('OK')"
   voyage --version  # or python -m voyage_framework.cli --help
   ```

6. Run tests
   ```bash
   pytest tests/unit -v
   ```

7. Run linters
   ```bash
   ruff check .
   ruff format --check .
   mypy voyage_framework
   ```

8. Windows-specific notes
   - Use Git Bash for consistent behavior
   - Python executable: .venv\Scripts\python.exe
   - pytest executable: .venv\Scripts\pytest.exe
   - If ruff shows "Access is denied" for temp dirs, use:
     ruff check voyage_framework tests
   - If pytest creates ACL-protected temp dirs, use:
     pytest --basetemp=.pytest-tmp/xxx
```

### 6.3 QUICKSTART.md

Must cover:

```text
1. Initialize project
   ```bash
   mkdir my-project
   cd my-project
   # Copy voyage_framework or use as dependency
   ```

2. Create your first task
   ```bash
   cat > task.yaml <<'YAML'
   id: VF-001
   title: My first task
   description: Learn Voyage Framework
   role: developer
   acceptance_criteria:
     - Install Voyage
     - Run tests
     - Create a task
   YAML
   ```

3. Add task to runtime
   ```bash
   python -m voyage_framework.cli tasks create --file task.yaml
   ```

4. Start the task
   ```bash
   python -m voyage_framework.cli tasks start VF-001
   ```

5. Build context
   ```bash
   python -m voyage_framework.cli sync build --file task.yaml --output CONTEXT.json
   ```

6. Check status
   ```bash
   python -m voyage_framework.cli sync status
   ```

7. Generate prompt package (Python example)
   ```python
   from voyage_framework.core.prompt_generator import default_prompt_generator
   from voyage_framework.core.task_parser import TaskParser
   
   parser = TaskParser()
   task = parser.parse("task.yaml")
   
   generator = default_prompt_generator()
   package = generator.generate(
       task=task,
       role_id="developer",
       mode_id="implementation",
   )
   
   print(package.system_prompt)
   print(package.user_prompt)
   ```

8. List roles and modes
   ```python
   from voyage_framework.core.agent_registry import default_agent_registry
   from voyage_framework.core.prompt_modes import default_mode_registry
   
   registry = default_agent_registry()
   print(registry.list_roles())
   
   modes = default_mode_registry()
   print(modes.list_modes())
   ```

9. Where to go next
   - USER_GUIDE.md for full concepts
   - ADAPTER_CONTRACT_USAGE.md for external agent integration
   - PHASE_WORKFLOW_POLICY.md for development process
```

### 6.4 END_TO_END_WORKFLOW.md

Must cover the complete workflow from idea to merge:

```text
1. Idea → task.yaml
   - Write task specification
   - Validate with TaskParser
   - Save as task.yaml

2. task.yaml → TaskRecord
   - Create task in runtime: voyage tasks create --file task.yaml
   - Start task: voyage tasks start <id>

3. TaskRecord → Context
   - Build context: voyage sync build --file task.yaml --output CONTEXT.json
   - Check status: voyage sync check --file task.yaml

4. Context → Prompt Package
   - Generate prompt: via PromptGenerator
   - Copy to external AI tool (Codex, Claude, Gemini)
   - External agent works on task

5. External Agent → Result
   - External agent returns code/docs/changes
   - Human reviews changes
   - Run tests: pytest tests/unit -v
   - Run gates: ruff check .; mypy voyage_framework

6. Result → Merge
   - Commit changes: git add <files>; git commit -m "..."
   - Push to origin: git push origin <branch>
   - Create PR / merge to main
   - Tag if needed: git tag -a vX.Y.Z -m "..."

7. Audit → Closure
   - Run full test suite
   - Verify git status clean
   - Write closure audit if needed
   - Document in reports/

Safety checkpoints at each step:
   - Never modify forbidden files without explicit approval
   - Never treat generated TASK.md/CONTEXT.json as source of truth
   - Never add runtime execution without approved phase prompt
   - Never store credentials in code or prompts
```

---

## 7. Content constraints

All documentation must:

```text
- Clearly state that Voyage v4.1 does NOT execute AI agents
- Clearly state that Voyage v4.1 does NOT call AI models
- Reference canonical source of truth: docs/VOYAGE_V4_1_CONTRACT.md
- Reference AGENTS.md for AI agent rules
- Reference PHASE_WORKFLOW_POLICY.md for development process
- Include Windows-specific notes where relevant
- Be honest about current limitations
- Use concrete examples, not abstract descriptions
- Be written for a user who is not the project author
```

---

## 8. Tone and style

- Friendly but direct
- Practical, not theoretical
- Step-by-step where possible
- Include both CLI and Python API examples
- Include troubleshooting notes
- No marketing fluff
- No claims about AI capabilities that don't exist

---

## 9. Quality gates

```bash
git diff --stat
git diff --name-status
git diff --check
git status --short
```

Expected: only docs/guides/ and docs/reports/ files created.

Forbidden files check:

```bash
git diff -- AGENTS.md README.md pyproject.toml .gitignore voyage_framework tests .github docs/VOYAGE_V4_1_CONTRACT.md docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md docs/reports/VOYAGE_V4_1_PROCESS_IMPROVEMENT_AUDIT.md docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md docs/prompts/* docs/guides/PHASE_WORKFLOW_POLICY.md docs/guides/ADAPTER_CONTRACT_USAGE.md docs/examples/* docs/templates/*
```

Expected: no diff.

---

## 10. Expected changed files

Expected:

```text
docs/guides/USER_GUIDE.md
docs/guides/INSTALLATION.md
docs/guides/QUICKSTART.md
docs/guides/END_TO_END_WORKFLOW.md
```

Optional:

```text
docs/reports/PHASE_10_USER_GUIDE_REPORT.md
```

No other files should change.

---

## 11. Final report format

Return:

```markdown
# Phase 10 Implementation Report

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
Do not start Phase 11.
