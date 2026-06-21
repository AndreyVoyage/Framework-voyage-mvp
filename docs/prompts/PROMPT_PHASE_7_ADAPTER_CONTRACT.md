# Phase 7 — Adapter Contract Draft

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
Branch: refactor/v4.2-adapter-contract
Base: main
main contains: 64b49fe Merge v4.1 process improvement audit
MVP tag exists: v4.1.0-mvp
Working tree: clean
```

If the working tree is not clean, STOP and report.

Do not commit.
Do not push.

---

## 1. Mission

Implement **Phase 7: Adapter Contract Draft**.

This phase defines the **interface contract** between Voyage v4.1 and external AI agents (Codex, Claude, Gemini, etc.).

**Phase 7 is NOT runtime execution.**

It only defines:
- How an external agent creates a task in Voyage
- How an external agent retrieves context
- How an external agent updates task status
- How an external agent requests a prompt package
- Human-in-the-loop approval flow

No agent is executed by Voyage.

No AI model is called by Voyage.

No orchestration is implemented.

---

## 2. What Phase 7 Is

Phase 7 defines a **contract** — interfaces, protocols, and validation rules.

It does not implement:

```text
- Runtime agent execution
- AI model inference
- LangGraph workflow orchestration
- Background workers or daemons
- Webhooks or callbacks
- Credential storage or auth
- Production deployment automation
```

---

## 3. Allowed files

You may add:

```text
voyage_framework/core/adapter_contract.py
voyage_framework/core/adapter_protocols.py
tests/unit/test_adapter_contract.py
tests/unit/test_adapter_protocols.py
```

You may modify:

```text
voyage_framework/core/__init__.py
```

Only to export safe public symbols.

Optional:

```text
docs/reports/PHASE_7_ADAPTER_CONTRACT_REPORT.md
```

Do not create the optional report unless useful.

---

## 4. Forbidden files

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
docs/prompts/*
voyage_framework/core/task_engine.py
voyage_framework/core/task_parser.py
voyage_framework/core/task_models.py
voyage_framework/core/event_engine.py
voyage_framework/core/context_builder.py
voyage_framework/core/agent_registry.py
voyage_framework/core/prompt_modes.py
voyage_framework/core/prompt_generator.py
voyage_framework/cli.py
voyage_framework/agents/
voyage_framework/langgraph_tools/
tests/unit/test_task_*.py
tests/unit/test_cli_*.py
tests/unit/test_context_builder.py
tests/unit/test_agent_registry.py
tests/unit/test_prompt_*.py
.github/
```

If you think one of these files must change, STOP and report why.

---

## 5. Hard constraints

Do not implement:

```text
- Agent runtime
- AI model calls
- LangGraph orchestration
- Background workers
- CLI execution commands
- Credentials / auth storage
- Webhooks
- TaskEngine mutations from adapter layer
- EventEngine writes from adapter layer
- Direct task.yaml mutation
```

Do not parse `TASK.md` or `CONTEXT.json` as source of truth.

Do not treat generated artifacts as canonical state.

---

## 6. What to implement

### 6.1 AdapterContract

Add immutable Pydantic v2 model:

```python
class AdapterContract(BaseModel):
    """Defines the interface contract for external AI agents."""

    version: str = "v4.1.0"
    supported_roles: tuple[str, ...]
    supported_modes: tuple[str, ...]
    required_context_fields: tuple[str, ...]
    optional_context_fields: tuple[str, ...]
    max_task_length: int
    max_prompt_length: int
    approval_required_for: tuple[str, ...]
```

### 6.2 AgentRequest

Add immutable Pydantic model:

```python
class AgentRequest(BaseModel):
    """Request from external agent to Voyage."""

    request_id: str
    agent_id: str
    role_id: str
    mode_id: str
    task_hint: str | None
    project_context: dict[str, Any] | None
```

### 6.3 AgentResponse

Add immutable Pydantic model:

```python
class AgentResponse(BaseModel):
    """Response from Voyage to external agent."""

    request_id: str
    status: str  # "pending", "approved", "rejected", "completed"
    task_id: str | None
    prompt_package: PromptPackage | None
    context_snapshot: dict[str, Any] | None
    next_steps: tuple[str, ...]
```

### 6.4 AdapterProtocol

Add abstract protocol / interface class:

```python
class AdapterProtocol(ABC):
    """Abstract protocol for Voyage ↔ external agent adapter."""

    @abstractmethod
    def validate_request(self, request: AgentRequest) -> ValidationResult: ...

    @abstractmethod
    def create_task(self, request: AgentRequest) -> AgentResponse: ...

    @abstractmethod
    def get_context(self, task_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def request_prompt(self, task_id: str, role_id: str, mode_id: str) -> PromptPackage: ...

    @abstractmethod
    def submit_result(self, task_id: str, result: dict[str, Any]) -> AgentResponse: ...

    @abstractmethod
    def request_approval(self, task_id: str, action: str) -> AgentResponse: ...
```

### 6.5 DefaultAdapterContract

Add factory:

```python
default_adapter_contract() -> AdapterContract
```

Must include:

```text
- all 6 roles from AgentRegistry
- all 6 modes from ModeRegistry
- approval_required_for: "mutate_task", "delete_task", "change_status", "deploy"
- max_task_length: 10000
- max_prompt_length: 15000
```

### 6.6 ValidationResult

Add immutable model:

```python
class ValidationResult(BaseModel):
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
```

### 6.7 ApprovalFlow

Add abstract model for human-in-the-loop:

```python
class ApprovalFlow(BaseModel):
    """Defines when human approval is required."""

    action: str
    required: bool
    reason: str | None
    timeout_hours: int
```

---

## 7. Design requirements

1. All models immutable (frozen Pydantic v2).
2. No filesystem access.
3. No database access.
4. No EventEngine usage.
5. No TaskEngine mutations.
6. No CLI required.
7. JSON-serializable.
8. Deterministic.

---

## 8. Tests

Add at least 20 tests:

```text
1. default_adapter_contract returns valid contract.
2. contract includes all 6 roles.
3. contract includes all 6 modes.
4. contract has approval_required_for.
5. AgentRequest validates required fields.
6. AgentRequest rejects unknown role.
7. AgentRequest rejects unknown mode.
8. AgentRequest accepts known role and mode.
9. AgentResponse has correct status enum.
10. AgentResponse can include prompt_package.
11. AdapterProtocol is abstract (cannot instantiate).
12. ValidationResult valid=true has no errors.
13. ValidationResult valid=false has errors.
14. ApprovalFlow required=true needs human.
15. ApprovalFlow timeout is positive.
16. AdapterContract version is v4.1.0.
17. max_task_length > 0.
18. max_prompt_length > 0.
19. contract is JSON-serializable.
20. contract does not touch filesystem.
21. contract does not create .voyage files.
22. existing Phase 6 tests still pass.
```

---

## 9. Quality gates

Run:

```bash
mkdir -p .pytest-tmp

.venv/Scripts/python.exe -m pytest tests/unit/test_adapter_contract.py -v --basetemp=".pytest-tmp/adapter-contract"
.venv/Scripts/python.exe -m pytest tests/unit/test_adapter_protocols.py -v --basetemp=".pytest-tmp/adapter-protocols"
.venv/Scripts/python.exe -m pytest tests/unit/test_prompt_generator.py -v --basetemp=".pytest-tmp/prompt-generator"
.venv/Scripts/python.exe -m pytest tests/unit/test_agent_registry.py -v --basetemp=".pytest-tmp/agent-registry"
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=".pytest-tmp/unit"
.venv/Scripts/python.exe -m pytest tests/ -v --basetemp=".pytest-tmp/full"

.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/adapter_contract.py voyage_framework/core/adapter_protocols.py

git diff --check
git status --short
```

---

## 10. Pollution check

After tests:

```bash
git status --porcelain
git status --porcelain .voyage
find .voyage -maxdepth 2 -type f 2>/dev/null || true
```

Expected:

```text
- no .voyage/tasks.db created by Phase 7
- no .voyage files changed by Phase 7
- no unrelated temp files tracked
```

---

## 11. Expected changed files

Expected:

```text
voyage_framework/core/adapter_contract.py
voyage_framework/core/adapter_protocols.py
tests/unit/test_adapter_contract.py
tests/unit/test_adapter_protocols.py
voyage_framework/core/__init__.py
```

Optional:

```text
docs/reports/PHASE_7_ADAPTER_CONTRACT_REPORT.md
```

No other files should change.

---

## 12. Final report format

Return:

```markdown
# Phase 7 Implementation Report

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
Do not start Phase 8.
