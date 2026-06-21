# Phase 5 — Agent Registry Draft / Role Profile Registry

> **STOP-GATE:** Не начинать Phase 6. Не добавлять runtime agent orchestration. Не добавлять LangGraph changes. Не менять TaskEngine / TaskParser / TaskModels / EventEngine API без отдельного разрешения.
>
> Задача — добавить lightweight registry ролей/профилей, который будет использоваться будущими prompt generators / modes, но сам не запускает агентов.

---

## Контекст

* **Проект:** `C:\DEV\FRAMEWORK\Framework-voyage-mvp`
* **Ветка:** `refactor/v4.1-contract`
* **Последний стабильный commit:** `2a068a1 Phase 4: add Context Builder Lite and sync CLI`
* **Phase 4 принята:**

  * ContextBuilder implemented
  * `voyage sync build/check/status`
  * Unit suite: 305 passed
  * Full suite: 322 passed
  * Ruff/mypy passed
  * Source of truth preserved

---

## Важная архитектурная формулировка

Voyage Framework v4.1 — это **Development Memory System / Project Knowledge Operating System**, а не AI Agent Framework.

Поэтому **Agent Registry** в Phase 5 означает:

```text
registry of role profiles / capabilities / constraints
```

а не:

```text
runtime agents
agent execution
agent orchestration
multi-agent workflow
LangGraph routing
tool calling
background workers
```

---

## Цель Phase 5

Добавить **Agent Registry Draft** — read-only каталог ролей, который описывает:

```text
1. role id
2. display name
3. purpose
4. responsibilities
5. capabilities
6. boundaries / forbidden actions
7. recommended prompt hints
8. default output expectations
```

Этот registry нужен для будущей Phase 6 Modes Draft / Prompt Generators.

---

## Source of truth rules

Canonical project state remains:

```text
task.yaml   → canonical task specification
TaskRecord  → canonical runtime state
EventEngine → canonical audit trail
```

Agent Registry is **not** source of truth for tasks.

Agent Registry may help validate or describe roles, but Phase 5 must not rewrite task.yaml, TaskRecord, EventEngine, TASK.md, or CONTEXT.json.

---

## Strict constraints

Forbidden:

```text
1. Do not implement agent execution.
2. Do not implement `voyage agents run`.
3. Do not implement orchestration.
4. Do not change LangGraph modules.
5. Do not change TaskEngine.
6. Do not change TaskParser.
7. Do not change TaskYamlSpec or TaskRecord.
8. Do not change EventEngine API.
9. Do not add database tables.
10. Do not add migrations.
11. Do not mutate .voyage runtime files during tests.
12. Do not implement Phase 6 prompt generators yet.
13. Do not commit or push.
```

Allowed:

```text
1. Add voyage_framework/core/agent_registry.py
2. Add tests/unit/test_agent_registry.py
3. Export safe public objects from voyage_framework/core/__init__.py if needed.
4. Add documentation/report file only if useful, preferably under docs/reports/.
```

If exporting from `voyage_framework/core/__init__.py`, export only:

```text
- AgentRegistry
- RoleProfile
- RoleCapability
- RoleBoundary
- default_agent_registry
```

No CLI in Phase 5 unless absolutely necessary. Prefer core-only implementation.

---

## What to implement

### 1. New module

Create:

```text
voyage_framework/core/agent_registry.py
```

Suggested models:

```python
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class RoleCapability(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    description: str


class RoleBoundary(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    description: str


class RoleProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    role_id: str
    display_name: str
    purpose: str
    responsibilities: list[str] = Field(default_factory=list)
    capabilities: list[RoleCapability] = Field(default_factory=list)
    boundaries: list[RoleBoundary] = Field(default_factory=list)
    prompt_hints: list[str] = Field(default_factory=list)
    output_expectations: list[str] = Field(default_factory=list)
```

Registry class:

```python
class AgentRegistry:
    """Read-only registry of role profiles.

    This is not a runtime agent executor.
    It only describes roles and their expected behavior.
    """

    def __init__(self, profiles: list[RoleProfile] | None = None) -> None:
        ...

    def list_roles(self) -> list[str]:
        ...

    def list_profiles(self) -> list[RoleProfile]:
        ...

    def get(self, role_id: str) -> RoleProfile | None:
        ...

    def require(self, role_id: str) -> RoleProfile:
        ...

    def has_role(self, role_id: str) -> bool:
        ...

    def describe(self, role_id: str) -> dict[str, Any]:
        ...
```

Factory:

```python
def default_agent_registry() -> AgentRegistry:
    ...
```

---

## Built-in role profiles

Add built-in profiles for existing Voyage roles only:

```text
architect
developer
reviewer
qa
security
devops
```

Do not invent too many roles.

Each role should include:

```text
- purpose
- 3–6 responsibilities
- 2–5 capabilities
- 2–5 boundaries
- prompt_hints
- output_expectations
```

Role meanings:

### architect

Focus:

```text
architecture, boundaries, design consistency, source-of-truth protection
```

Forbidden:

```text
large implementation without tests, changing runtime behavior without contract
```

### developer

Focus:

```text
implementation, small patches, tests, existing contracts
```

Forbidden:

```text
broad rewrites, changing architecture silently
```

### reviewer

Focus:

```text
diff review, regression risks, acceptance criteria
```

Forbidden:

```text
writing large new features during review
```

### qa

Focus:

```text
test plans, edge cases, reproducibility, quality gates
```

Forbidden:

```text
approving without evidence
```

### security

Focus:

```text
secrets, unsafe commands, injections, filesystem/network safety
```

Forbidden:

```text
weakening sandbox or approval constraints
```

### devops

Focus:

```text
CI, scripts, environment, deployment, reproducibility
```

Forbidden:

```text
changing production/deploy behavior without explicit approval
```

---

## Design requirements

1. Registry is deterministic.
2. Registry is read-only by default.
3. Returned profiles should not be mutated accidentally.
4. Unknown role handling must be explicit.
5. Built-in role IDs should be stable lowercase strings.
6. No file IO required for Phase 5.
7. No database IO.
8. No EventEngine usage.
9. No TaskEngine usage.
10. No CLI required.
11. RoleProfile, RoleCapability, and RoleBoundary should be immutable.
12. Prefer Pydantic `ConfigDict(frozen=True)` for registry models.
13. Registry methods should not expose mutable internal state directly.

---

## Tests

Add:

```text
tests/unit/test_agent_registry.py
```

Required test coverage:

```text
1. default registry contains expected roles.
2. list_roles returns stable role ids.
3. get returns RoleProfile for known role.
4. get returns None for unknown role.
5. require returns RoleProfile for known role.
6. require raises clear error for unknown role.
7. has_role true for known role.
8. has_role false for unknown role.
9. describe returns serializable dict.
10. profiles contain responsibilities.
11. profiles contain capabilities.
12. profiles contain boundaries.
13. profiles contain prompt_hints.
14. profiles contain output_expectations.
15. registry can be constructed with custom profiles.
16. duplicate role ids are rejected.
17. role ids are normalized or validated consistently.
18. registry does not touch filesystem.
19. registry does not create .voyage files.
20. existing Phase 4 tests still pass.
```

---

## Quality gates

Run before reporting:

```bash
mkdir -p .pytest-tmp

.venv/Scripts/python.exe -m pytest tests/unit/test_agent_registry.py -v --basetemp=".pytest-tmp/agent-registry"
.venv/Scripts/python.exe -m pytest tests/unit/test_context_builder.py -v --basetemp=".pytest-tmp/context-builder"
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_sync.py -v --basetemp=".pytest-tmp/cli-sync"
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_tasks.py -v --basetemp=".pytest-tmp/cli-tasks"
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=".pytest-tmp/unit"
.venv/Scripts/python.exe -m pytest tests/ -v --basetemp=".pytest-tmp/full"

.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/agent_registry.py

git diff --check
git status --short
```

---

## Pollution check

After tests:

```bash
git status --porcelain
git status --porcelain .voyage
find .voyage -maxdepth 2 -type f 2>/dev/null || true
```

Expected:

```text
- no new .voyage/tasks.db
- no new .voyage runtime files caused by Phase 5
- no changes to TASK.md
- no changes to CONTEXT.json
- working tree contains only intentional Phase 5 files
```

---

## Files expected to change

Expected:

```text
voyage_framework/core/agent_registry.py
tests/unit/test_agent_registry.py
voyage_framework/core/__init__.py   # only if exporting registry symbols
```

Optional:

```text
docs/reports/PHASE_5_IMPLEMENTATION_REPORT.md
```

Unexpected / forbidden:

```text
voyage_framework/core/task_engine.py
voyage_framework/core/task_parser.py
voyage_framework/core/task_models.py
voyage_framework/core/event_engine.py
voyage_framework/core/context_builder.py
voyage_framework/cli.py
TASK.md
CONTEXT.json
.voyage/tasks.db
```

If any forbidden file changes, stop and report.

---

## Manual smoke check

Use a Python one-liner:

```bash
.venv/Scripts/python.exe - <<'PY'
from voyage_framework.core.agent_registry import default_agent_registry

registry = default_agent_registry()

print("roles:", registry.list_roles())

profile = registry.require("developer")
print("developer:", profile.display_name)
print("capabilities:", len(profile.capabilities))
print("boundaries:", len(profile.boundaries))
PY
```

Expected:

```text
roles: includes architect, developer, reviewer, qa, security, devops
developer: Developer
capabilities: > 0
boundaries: > 0
```

---

## Final report format

Return:

```markdown
# Phase 5 Implementation Report

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

Do not commit.

Do not push.

Do not start Phase 6.
