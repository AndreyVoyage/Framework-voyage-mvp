# Phase 4 — Voyage Sync / Context Builder Lite

> **STOP-GATE:** Не начинать Phase 5. Не менять TaskEngine / TaskParser / TaskModels. Не менять EventEngine API. Не менять существующие команды `voyage task` и `voyage tasks`.
>
> Задача — добавить lightweight context sync layer поверх Phase 1–3.

---

## Контекст

* **Проект:** `C:\DEV\FRAMEWORK\Framework-voyage-mvp`
* **Ветка:** `refactor/v4.1-contract`
* **Фаза 3:** Принята:

  * manual CLI smoke test passed
  * `test_cli_tasks.py`: 31 passed
  * `test_task_parser.py`: 48 passed
  * `test_task_engine.py`: 55 passed
  * unit suite: 270 passed
  * full suite: 287 passed
  * ruff / format / mypy passed
  * git clean
* **Модели:**

  * `TaskYamlSpec` — canonical task spec from `task.yaml`
  * `TaskRecord` — canonical runtime state in SQLite
  * `TaskEngine` — CRUD + transitions
* **CLI Phase 3:** `voyage tasks`
* **EventEngine:** append-only audit log, not the source of truth for task status
* **TASK.md:** generated artifact only, never parsed as source of truth

---

## Цель Phase 4

Добавить **Context Builder Lite** — read-mostly слой, который собирает проектный контекст из:

```text
task.yaml files
TaskRecord SQLite runtime state
EventEngine audit log
```

и умеет:

```text
1. build  — собрать CONTEXT.json
2. check  — показать расхождения между task.yaml и TaskRecord
3. status — показать краткое состояние синхронизации
```

---

## Source of truth rules

Canonical sources:

```text
task.yaml   → canonical task specification
TaskRecord  → canonical runtime state
EventEngine → canonical audit trail
```

Generated / non-canonical artifacts:

```text
TASK.md
CONTEXT.json
docs output
```

Strict rules:

```text
1. Do not parse TASK.md.
2. Do not treat CONTEXT.json as source of truth.
3. Do not update task.yaml.
4. Do not update TaskRecord in Phase 4 Lite.
5. Do not infer runtime status from task.yaml.
6. Do not mutate EventEngine history.
```

---

## Architectural constraints

Allowed:

```text
1. Add voyage_framework/core/context_builder.py
2. Add tests/unit/test_context_builder.py
3. Add tests/unit/test_cli_sync.py if CLI is implemented
4. Add CLI namespace `voyage sync` only
5. Add local Pydantic models inside context_builder.py
```

Forbidden:

```text
1. Do not modify TaskEngine business logic.
2. Do not modify TaskParser.
3. Do not modify TaskYamlSpec / TaskRecord.
4. Do not modify EventEngine API.
5. Do not add Phase 5 features.
6. Do not add AI agent orchestration.
7. Do not add LangGraph changes.
8. Do not add background workers.
9. Do not add web UI.
10. Do not add database migrations beyond what already exists.
```

---

## What to implement

### 1. New module

Create:

```text
voyage_framework/core/context_builder.py
```

Suggested models may live in this file:

```python
from datetime import UTC, datetime
from pathlib import Path
from pydantic import BaseModel, Field

class TaskContext(BaseModel):
    id: str
    title: str
    role: str
    spec_status: str | None = None
    runtime_status: str | None = None
    priority: str | None = None
    mode: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    has_runtime_record: bool = False
    source_path: str | None = None

class EventsSummary(BaseModel):
    total_events: int = 0
    task_events: int = 0
    latest_event_at: datetime | None = None

class TaskDiff(BaseModel):
    task_id: str
    exists_in_yaml: bool
    exists_in_runtime: bool
    changed_fields: dict[str, dict[str, object | None]] = Field(default_factory=dict)

class ProjectContext(BaseModel):
    project_id: str = "default"
    tasks: list[TaskContext] = Field(default_factory=list)
    events_summary: EventsSummary = Field(default_factory=EventsSummary)
    last_sync: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

### 2. ContextBuilder API

Implement a small, explicit API:

```python
class ContextBuilder:
    """Builds project context from task.yaml files, TaskRecord, and EventEngine."""

    def __init__(self, task_engine: TaskEngine, event_engine: EventEngine | None = None) -> None:
        ...

    def build(
        self,
        task_files: list[Path],
        project_id: str = "default",
    ) -> ProjectContext:
        """Build project context from YAML specs + runtime records + events."""
        ...

    def check(
        self,
        task_files: list[Path],
    ) -> list[TaskDiff]:
        """Return diffs between task.yaml specs and TaskRecord runtime data."""
        ...

    def write_context(
        self,
        context: ProjectContext,
        output_path: Path,
    ) -> None:
        """Write CONTEXT.json atomically."""
        ...
```

Important:

```text
- build/check must not mutate TaskRecord.
- build/check must not mutate task.yaml.
- write_context writes only the explicit output path.
- Tests must use tmp_path, never the real project root.
```

### 3. Diff semantics

`check()` should compare only safe spec-derived fields:

```text
id
title
role
priority
mode
acceptance_criteria
source_path
```

Do not compare or overwrite runtime-only fields:

```text
status
created_at
updated_at
started_at
completed_at
archived_at
```

Status may be reported as:

```text
spec_status
runtime_status
```

but Phase 4 Lite must not resolve or mutate status conflicts.

### 4. CLI namespace

Add only this namespace:

```bash
voyage sync
```

Commands:

```bash
voyage sync build --file task.yaml --output CONTEXT.json
voyage sync check --file task.yaml
voyage sync status
```

Optional multi-file support is allowed:

```bash
voyage sync build --file tasks/VF-001.yaml --file tasks/VF-002.yaml --output CONTEXT.json
voyage sync check --file tasks/VF-001.yaml --file tasks/VF-002.yaml
```

Do not implement:

```bash
voyage sync update
```

`update` is deferred to Phase 4.1 because it requires a separate mutation contract.

CLI rules:

```text
1. Return int exit codes.
2. Do not call sys.exit() inside handlers.
3. Support dependency injection for tests if practical.
4. Do not break existing `voyage task`.
5. Do not break existing `voyage tasks`.
6. `sync status` must not fail on an empty project.
```

### 5. CONTEXT.json shape

`voyage sync build` should write JSON similar to:

```json
{
  "project_id": "default",
  "tasks": [
    {
      "id": "VF-001",
      "title": "Example task",
      "role": "developer",
      "spec_status": "pending",
      "runtime_status": "in_progress",
      "priority": "medium",
      "mode": "solution",
      "acceptance_criteria": ["..."],
      "has_runtime_record": true,
      "source_path": "task.yaml"
    }
  ],
  "events_summary": {
    "total_events": 0,
    "task_events": 0,
    "latest_event_at": null
  },
  "last_sync": "2026-06-21T00:00:00Z"
}
```

Exact timestamp value may differ.

---

## Tests

Add:

```text
tests/unit/test_context_builder.py
```

Recommended tests:

```text
1. build returns ProjectContext.
2. build includes YAML-only task.
3. build includes runtime status when TaskRecord exists.
4. build does not mutate TaskRecord.
5. build does not mutate task.yaml.
6. check reports missing runtime record.
7. check reports changed title.
8. check reports changed role.
9. check ignores runtime-only timestamps.
10. write_context creates CONTEXT.json.
11. write_context writes valid JSON.
12. empty task_files returns empty context.
13. missing task file returns controlled error.
14. invalid YAML returns controlled error.
15. EventEngine optional: no event engine does not fail.
```

If CLI is implemented, add:

```text
tests/unit/test_cli_sync.py
```

Recommended CLI tests:

```text
1. sync build writes CONTEXT.json to tmp_path.
2. sync check prints no differences for matching data.
3. sync check prints missing runtime record.
4. sync status works on empty project.
5. sync commands do not write .voyage/tasks.db in real project root during tests.
6. existing voyage task still works.
7. existing voyage tasks still works.
```

All tests must use `tmp_path` and/or `monkeypatch.chdir(tmp_path)`.

---

## Manual smoke test

After implementation, test from project root:

```bash
mkdir -p .pytest-tmp/phase4-smoke

cat > .pytest-tmp/phase4-smoke/task.yaml <<'YAML'
id: VF-004
title: Phase 4 Smoke Task
description: Verify sync build and check
role: developer
acceptance_criteria:
  - sync build creates context
  - sync check reports runtime state
YAML

rm -f .voyage/tasks.db .voyage/tasks.db-shm .voyage/tasks.db-wal

.venv/Scripts/python.exe -m voyage_framework.cli tasks create --file .pytest-tmp/phase4-smoke/task.yaml
.venv/Scripts/python.exe -m voyage_framework.cli tasks start VF-004

.venv/Scripts/python.exe -m voyage_framework.cli sync build --file .pytest-tmp/phase4-smoke/task.yaml --output .pytest-tmp/phase4-smoke/CONTEXT.json
.venv/Scripts/python.exe -m voyage_framework.cli sync check --file .pytest-tmp/phase4-smoke/task.yaml
.venv/Scripts/python.exe -m voyage_framework.cli sync status

cat .pytest-tmp/phase4-smoke/CONTEXT.json

rm -f .voyage/tasks.db .voyage/tasks.db-shm .voyage/tasks.db-wal
git status --porcelain
```

Manual smoke may create `.voyage/tasks.db`; remove it afterward. Unit tests must not create it in the real project root.

---

## Quality gates

Run before reporting completion:

```bash
mkdir -p .pytest-tmp

.venv/Scripts/python.exe -m pytest tests/unit/test_context_builder.py -v --basetemp=".pytest-tmp/context-builder"
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_sync.py -v --basetemp=".pytest-tmp/cli-sync"
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_tasks.py -v --basetemp=".pytest-tmp/cli-tasks"
.venv/Scripts/python.exe -m pytest tests/unit/test_task_parser.py -v --basetemp=".pytest-tmp/task-parser"
.venv/Scripts/python.exe -m pytest tests/unit/test_task_engine.py -v --basetemp=".pytest-tmp/task-engine"
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=".pytest-tmp/unit"
.venv/Scripts/python.exe -m pytest tests/ -v --basetemp=".pytest-tmp/full"

.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/context_builder.py voyage_framework/cli.py

git diff --check
git status
```

If `tests/unit/test_cli_sync.py` is not created, explain why and do not run that specific file.

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
- no untracked .voyage/tasks.db
- no accidental changes to TASK.md
- no accidental changes to CONTEXT.json unless explicitly written to tmp_path
- working tree only contains intentional Phase 4 code/test changes
```

---

## Git workflow

Do not commit or push.

Return only a report with:

```markdown
# Phase 4 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## CLI
-

## Tests
-

## Quality gates
-

## Pollution check
-

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
```

Owner will review diff and decide whether to commit.

---

## Acceptance criteria

1. `ContextBuilder.build()` creates a `ProjectContext`.
2. `ContextBuilder.check()` reports differences between YAML specs and runtime records.
3. `ContextBuilder.write_context()` writes valid JSON.
4. `voyage sync build --file task.yaml --output CONTEXT.json` works.
5. `voyage sync check --file task.yaml` works.
6. `voyage sync status` works on an empty project.
7. Phase 3 CLI remains intact.
8. Phase 3 tests still pass.
9. Full test suite passes.
10. Ruff / format / mypy pass.
11. No real project pollution after tests.
12. No commit or push is performed.

---

## Stop-gate

Do not start Phase 5.

Do not implement `voyage sync update`.

Do not mutate TaskRecord during Phase 4 Lite.

Do not commit or push automatically.
