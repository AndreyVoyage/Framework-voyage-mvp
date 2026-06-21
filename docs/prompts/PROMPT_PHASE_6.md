# Phase 6 — Mode Profiles / Prompt Generator Draft

## 0. Stop-gate

Before making any code changes, verify repository state:

```bash
git fetch origin
git status -sb
git status
git log --oneline --decorate -7
```

Expected:

```text
HEAD == origin/refactor/v4.1-contract
working tree clean
latest commit: 494c28b Phase 5: add Agent Registry Draft
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.

---

## 1. Mission

Implement **Phase 6: Mode Profiles / Prompt Generator Draft**.

This phase adds a **core-only, deterministic, read-only prompt generation layer**.

Voyage v4.1 is still **not** an AI Agent Framework.

The new layer must prepare prompt packages for external agents such as Codex/Kimi/Claude/Gemini, but it must not execute agents, route agents, orchestrate agents, call LangGraph, create tasks, mutate task state, or touch the filesystem.

Phase 6 should sit logically after:

```text
TaskYamlSpec / TaskParser
TaskRecord / TaskEngine
ContextBuilder Lite
AgentRegistry
```

but it must not change the behavior of those existing components.

---

## 2. Core idea

The system should be able to combine:

```text
TaskYamlSpec
+ RoleProfile from AgentRegistry
+ ModeProfile
+ optional project/context metadata
```

into a deterministic prompt package:

```text
PromptPackage
├── system_prompt
├── user_prompt
├── checklist
├── metadata
└── optional helper representation as messages
```

This package is meant for a human to copy into an external AI tool.

It is not executed by Voyage.

---

## 3. Allowed files

You may add:

```text
voyage_framework/core/prompt_modes.py
voyage_framework/core/prompt_generator.py
tests/unit/test_prompt_modes.py
tests/unit/test_prompt_generator.py
```

You may modify:

```text
voyage_framework/core/__init__.py
```

Only to export safe public symbols.

Optional:

```text
docs/reports/PHASE_6_IMPLEMENTATION_REPORT.md
```

Do not create this report unless useful.

---

## 4. Forbidden files

Do not modify:

```text
AGENTS.md
TASK.md
CONTEXT.json
pyproject.toml
.gitignore
voyage_framework/cli.py
voyage_framework/core/task_engine.py
voyage_framework/core/task_parser.py
voyage_framework/core/task_models.py
voyage_framework/core/event_engine.py
voyage_framework/core/context_builder.py
voyage_framework/core/agent_registry.py
voyage_framework/agents/
voyage_framework/langgraph_tools/
```

If you think one of these files must change, STOP and report why.

---

## 5. Hard constraints

Do not implement:

```text
CLI commands
runtime agents
agent execution
agent orchestration
LangGraph integration
CrewAI/AutoGen integration
database writes
filesystem writes
task status mutations
EventEngine writes
TaskEngine writes
Phase 7 adapter contract
Phase 8 runtime adapter
```

Do not parse `TASK.md` or `CONTEXT.json` as source of truth.

Do not treat generated artifacts as canonical state.

---

## 6. Required concepts

### 6.1 ModeProfile

Add immutable Pydantic v2 model:

```text
ModeProfile
```

Suggested fields:

```text
id: str
display_name: str
purpose: str
instructions: tuple[str, ...]
constraints: tuple[str, ...]
output_expectations: tuple[str, ...]
checklist: tuple[str, ...]
```

Requirements:

```text
- immutable / frozen
- deterministic
- JSON-serializable
- lowercase strict id validation
- no filesystem access
- no database access
```

---

### 6.2 ModeRegistry

Add deterministic read-only registry for mode profiles.

Suggested API:

```python
class ModeRegistry:
    def list_modes(self) -> tuple[str, ...]: ...
    def list_profiles(self) -> tuple[ModeProfile, ...]: ...
    def get(self, mode_id: str) -> ModeProfile | None: ...
    def require(self, mode_id: str) -> ModeProfile: ...
    def has_mode(self, mode_id: str) -> bool: ...
    def describe(self) -> dict[str, Any]: ...
```

Add:

```python
def default_mode_registry() -> ModeRegistry:
    ...
```

Required default modes:

```text
analysis
implementation
review
qa
security
handoff
```

No extra default modes unless justified.

Duplicate mode ids must be rejected.

Unknown mode ids must raise a clear domain error in `require`.

---

### 6.3 PromptPackage

Add immutable Pydantic model:

```text
PromptPackage
```

Suggested fields:

```text
role_id: str
mode_id: str
task_id: str
title: str
system_prompt: str
user_prompt: str
checklist: tuple[str, ...]
metadata: dict[str, Any]
```

Suggested methods:

```python
def as_messages(self) -> list[dict[str, str]]:
    ...
```

`as_messages()` should return:

```python
[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
]
```

The package must be JSON-serializable.

---

### 6.4 PromptGenerator

Add deterministic read-only generator.

Suggested API:

```python
class PromptGenerator:
    def __init__(
        self,
        *,
        agent_registry: AgentRegistry | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        ...

    def generate(
        self,
        *,
        task: TaskYamlSpec,
        role_id: str,
        mode_id: str,
        project_context: Mapping[str, Any] | None = None,
    ) -> PromptPackage:
        ...
```

Requirements:

```text
- validates role via AgentRegistry.require()
- validates mode via ModeRegistry.require()
- does not mutate task
- does not mutate registry
- does not touch filesystem
- does not touch .voyage
- does not use TaskEngine
- does not use EventEngine
- does not call CLI
- deterministic output for same input
```

Add:

```python
def default_prompt_generator() -> PromptGenerator:
    ...
```

---

## 7. Prompt content requirements

Generated prompt must include:

```text
- role identity
- mode identity
- task id
- task title
- task description
- acceptance criteria
- allowed read/modify file hints if available in TaskYamlSpec
- tests if available in TaskYamlSpec
- role responsibilities from RoleProfile
- role capabilities from RoleProfile
- role boundaries from RoleProfile
- mode instructions
- mode constraints
- output expectations
- explicit "do not commit / do not push unless instructed"
- explicit "do not modify files outside task scope"
- explicit "report deviations instead of guessing"
```

For review/security/qa/handoff modes, the prompt should prefer read-only behavior unless the mode explicitly requires otherwise.

---

## 8. Error handling

Add clear domain errors, for example:

```text
PromptModeNotFoundError
DuplicateModeError
PromptGenerationError
```

Do not use vague bare `ValueError` for main domain failures unless existing project style requires it.

---

## 9. Public exports

If modifying `voyage_framework/core/__init__.py`, export only safe symbols, for example:

```python
ModeProfile
ModeRegistry
PromptPackage
PromptGenerator
default_mode_registry
default_prompt_generator
```

Also export domain errors if appropriate.

Do not break existing imports.

---

## 10. Required tests

Add at least 20 meaningful tests across prompt modes and prompt generator.

Required coverage:

```text
default mode registry contains exactly expected modes
mode ids are stable
get known mode
get unknown mode returns None
require known mode
require unknown mode raises clear error
has_mode true/false
describe returns JSON-serializable copy
mode profiles are immutable
mode registry rejects duplicate ids
mode ids are normalized/validated
default prompt generator can be constructed
generator validates role id
generator validates mode id
generator returns PromptPackage
PromptPackage is JSON-serializable
PromptPackage.as_messages() returns system/user messages
generated prompt includes task id/title/description
generated prompt includes acceptance criteria
generated prompt includes role boundaries
generated prompt includes mode constraints
generated prompt includes "do not commit / do not push"
same input produces same output
generator does not touch filesystem or create .voyage
existing AgentRegistry tests still pass
existing TaskParser tests still pass
existing ContextBuilder tests still pass
```

---

## 11. Quality gates

Run:

```bash
mkdir -p .pytest-tmp

.venv/Scripts/python.exe -m pytest tests/unit/test_prompt_modes.py -v --basetemp=".pytest-tmp/prompt-modes"
.venv/Scripts/python.exe -m pytest tests/unit/test_prompt_generator.py -v --basetemp=".pytest-tmp/prompt-generator"
.venv/Scripts/python.exe -m pytest tests/unit/test_agent_registry.py -v --basetemp=".pytest-tmp/agent-registry"
.venv/Scripts/python.exe -m pytest tests/unit/test_task_parser.py -v --basetemp=".pytest-tmp/task-parser"
.venv/Scripts/python.exe -m pytest tests/unit/test_context_builder.py -v --basetemp=".pytest-tmp/context-builder"
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=".pytest-tmp/unit"
.venv/Scripts/python.exe -m pytest tests/ -v --basetemp=".pytest-tmp/full"

.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/prompt_modes.py voyage_framework/core/prompt_generator.py

git diff --check
git status --short
```

If Windows creates ACL-protected temporary directories, report them clearly. Do not hide them by changing `.gitignore` unless explicitly instructed.

---

## 12. Pollution check

Run:

```bash
git status --porcelain
git status --porcelain .voyage
find .voyage -maxdepth 2 -type f 2>/dev/null || true
```

Expected:

```text
No .voyage/tasks.db created by Phase 6
No .voyage files changed by Phase 6
No unrelated temp files tracked
```

---

## 13. Expected changed files

Expected:

```text
voyage_framework/core/prompt_modes.py
voyage_framework/core/prompt_generator.py
tests/unit/test_prompt_modes.py
tests/unit/test_prompt_generator.py
voyage_framework/core/__init__.py
```

Optional:

```text
docs/reports/PHASE_6_IMPLEMENTATION_REPORT.md
```

No other files should change.

---

## 14. Final report format

Return:

```markdown
# Phase 6 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Tests
-

## Quality gates
-

## Pollution check
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