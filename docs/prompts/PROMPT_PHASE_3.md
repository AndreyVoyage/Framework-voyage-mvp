# VOYAGE V4.1 — PROMPT FOR PHASE 3 (CLI tasks)

> Этот промпт предназначен для AI-агента, продолжающего работу над Voyage Framework v4.1.
> Перед началом работы агент должен выполнить все stop-gate проверки.

---

## 1. Мета-информация

- **Проект:** Voyage Framework v4.1
- **Ветка:** `refactor/v4.1-contract`
- **Репозиторий:** `C:\DEV\FRAMEWORK\Framework-voyage-mvp`
- **Фаза:** Phase 3 — CLI tasks (`voyage tasks ...`)
- **Предыдущие фазы:** 0 (Contract), 1 (TaskSpec + TaskParser), 2 (TaskRecord + TaskEngine) — все завершены и запушены

---

## 2. Что такое Voyage v4.1

**Voyage = Development Memory System / Project Knowledge Operating System**

Не "AI Agent Framework". Главная ценность — память проекта, которая переживает агентов.

```text
task.yaml → TaskParser → TaskYamlSpec → TaskEngine → TaskRecord (SQLite)
                                                    ↓
                                            EventEngine (append-only audit log)
                                                    ↓
                                            TaskGenerator → TASK.md + CONTEXT.json
```

### Архитектурные принципы
1. `task.yaml` = source of truth, `TASK.md` = generated artifact
2. EventEngine = append-only audit log, не управляет задачами
3. TaskEngine управляет статусами
4. SQLite sync (не async), не SQLAlchemy ORM
5. Не ломать старые CLI-команды
6. IDE-агенты (Kimi Code) — через prompt, не headless

---

## 3. Stop-gate (выполнить перед любыми изменениями)

```bash
cd /c/DEV/FRAMEWORK/Framework-voyage-mvp
git fetch origin
git status -sb
git status
git log --oneline --decorate -5
git branch --show-current
pytest tests/unit/test_task_parser.py -v
pytest tests/unit/test_task_engine.py -v
pytest tests/ -v
git diff --check
```

### Ожидаемый результат
```text
git status -sb: ## refactor/v4.1-contract...origin/refactor/v4.1-contract (no ahead/behind)
git status: working tree clean, on branch refactor/v4.1-contract
git log: latest commit is Phase 2: implement TaskRecord and TaskEngine
git branch: refactor/v4.1-contract
test_task_parser.py: 48 passed
test_task_engine.py: 55 passed
Full suite: 252 passed, 4 failed (pre-existing integration docs_cli)
git diff --check: passed
```

### Если что-то падает
**Остановиться и дать отчёт.** Не начинать реализацию.

---

## 4. Что уже сделано

### Phase 0: Contract (dbcf51f)
- `docs/VOYAGE_V4_1_CONTRACT.md` — технический контракт, стоп-кран перед новым кодом

### Phase 1: TaskSpec + TaskParser (1908f07 + 8b731c2)
- `voyage_framework/core/task_models.py` — `TaskFiles`, `TaskYamlSpec` (immutable, Pydantic, frozen)
- `voyage_framework/core/task_parser.py` — `TaskParser.parse(path)` / `parse_string(content)`
- `tests/unit/test_task_parser.py` — 48 тестов, все проходят

### Phase 2: TaskRecord + TaskEngine
- `voyage_framework/core/task_models.py` — `TaskRecord` (mutable runtime model)
- `voyage_framework/core/task_engine.py` — `TaskEngine`:
  - `create_from_spec(TaskYamlSpec)` → SQLite
  - `VALID_TRANSITIONS` — 6 статусов, 9 разрешённых переходов
  - `transition()` с валидацией + timestamp rules
  - Shorthands: `start()`, `block()`, `unblock()`, `complete()`, `fail()`, `archive()`
  - EventEngine integration (7 lifecycle events)
  - Custom exceptions: `TaskEngineError`, `TaskNotFoundError`, `TaskAlreadyExistsError`, `TaskTransitionError`
- `voyage_framework/core/models.py` — `EventType` extended: `TASK_CREATED`, `TASK_STARTED`, `TASK_BLOCKED`, `TASK_UNBLOCKED`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_ARCHIVED`
- `tests/unit/test_task_engine.py` — 55 тестов, все проходят

---

## 5. Critical Additions Before Phase 3 Implementation

### 5.1. No automatic commit or push

Do **not** commit or push automatically.

At the end of implementation, provide a report and wait for **explicit user approval** before running:

```bash
git commit ...
git push ...
```

The user controls Git checkpoints manually.

---

### 5.2. Phase 2 must be clean and pushed before Phase 3

Before starting Phase 3, verify:

```bash
git status
git log --oneline -5
git branch --show-current
git remote -v
```

Expected:

```text
branch: refactor/v4.1-contract
working tree clean
latest commit includes Phase 2
```

If Phase 2 is not pushed or working tree is not clean, **stop and report**.

Do not start Phase 3 on top of dirty Phase 2 changes.

---

### 5.3. Environment rule for CLI tests

If CLI integration tests fail with:

```text
ModuleNotFoundError: No module named 'voyage_framework'
```

do not treat this as an application logic failure immediately.

First check environment:

```bash
which python
python --version
python -m pip show voyage-framework
python -m pip show ruff mypy pytest
```

If package is not installed in editable mode, run:

```bash
python -m pip install -e ".[dev]"
```

Then rerun tests.

For direct CLI execution in tests or manual checks, prefer:

```bash
python -m voyage_framework.cli ...
```

over relying on a globally installed `voyage` command.

---

### 5.4. Phase 3 scope is CLI only

Allowed:

```text
- modify voyage_framework/cli.py
- add CLI tests
- add small helper functions only if needed for CLI wiring
```

Forbidden unless absolutely necessary:

```text
- changing TaskParser behavior
- changing TaskEngine lifecycle logic
- changing TaskYamlSpec validation
- changing EventEngine behavior
- changing TaskGenerator
- changing old singular `voyage task <role> --task "..."`
```

If a TaskEngine issue is discovered, **stop and report**. Do not silently rewrite Phase 2.

---

### 5.5. Singular vs plural command rule

Existing command must remain working:

```bash
voyage task <role> --task "..."
```

New runtime commands must use plural namespace only:

```bash
voyage tasks create --file <task.yaml>
voyage tasks list
voyage tasks show <task_id>
voyage tasks start <task_id>
voyage tasks block <task_id> --reason "..."
voyage tasks unblock <task_id>
voyage tasks complete <task_id>
voyage tasks fail <task_id> --reason "..."
voyage tasks archive <task_id>
```

Do not overload `voyage task`.

Do not replace the old `task` command with the new runtime commands.

---

### 5.6. CLI handler return codes

CLI handler functions should return integer exit codes:

```python
return 0  # success
return 1  # user-facing failure
```

Avoid calling `sys.exit()` inside handler functions.

The main entrypoint may convert the returned code to process exit status.

This makes handlers testable.

---

### 5.7. Test database isolation

CLI tests must **not** write to the real project `.voyage/tasks.db`.

Use `tmp_path` and pass/monkeypatch project root or database path.

Each CLI test should use isolated temporary state.

No test should depend on previous test execution order.

---

### 5.8. Output format

Human-readable CLI output is enough for Phase 3.

Do not add JSON output unless already specified in contract.

Suggested output:

```text
Created task VF-001: Implement TaskEngine
Started task VF-001
Blocked task VF-001: waiting for review
Completed task VF-001
Archived task VF-001
```

For errors:

```text
Error: task VF-999 not found
Error: invalid transition pending -> completed
Error: invalid task.yaml: missing acceptance_criteria
```

Errors should return non-zero exit code.

---

## 6. Цель Phase 3

Реализовать CLI-команды для runtime-управления задачами через **plural namespace** `voyage tasks ...`.

### Запрещено
- Не ломать `voyage task <role> --task "..."` (singular, генератор TASK.md)
- Не добавлять async
- Не менять TaskGenerator
- Не менять TaskParser
- Не добавлять SQLAlchemy ORM

### Разрешено
- Добавить `voyage tasks` subparser в `cli.py`
- Добавить runtime-команды управления задачами
- Интегрировать `TaskParser` + `TaskEngine` в CLI

---

## 7. CLI Commands (Phase 3)

### Старые команды (не ломать)
```bash
voyage task <role> --task "..."          # Generate TASK.md + CONTEXT.json
voyage task <role> --task "..." --phase M2
voyage init
voyage status
voyage run <role> --task "..."
voyage events [--limit N]
voyage approve
voyage graph visualize
voyage chronicler journal
voyage evaluate
voyage docs build
```

### Новые команды (добавить)
```bash
# Создание задачи из task.yaml
voyage tasks create --file .voyage/TASKS/VF-001/task.yaml

# Список задач
voyage tasks list
voyage tasks list --role developer
voyage tasks list --status in_progress
voyage tasks list --limit 20

# Детали задачи
voyage tasks show VF-001

# Управление статусами
voyage tasks start VF-001
voyage tasks block VF-001 --reason "Need clarification"
voyage tasks unblock VF-001
voyage tasks complete VF-001
voyage tasks fail VF-001 --reason "Tests failed"
voyage tasks archive VF-001
```

---

## 8. Архитектура CLI

### Файлы для чтения (перед кодом)
```text
voyage_framework/cli.py                    # Текущий CLI, его нельзя ломать
voyage_framework/core/task_engine.py       # TaskEngine API
voyage_framework/core/task_parser.py       # TaskParser API
voyage_framework/core/task_models.py       # TaskYamlSpec, TaskRecord
voyage_framework/core/event_engine.py      # EventEngine (append-only)
```

### План изменений
```text
voyage_framework/cli.py
  ├── Добавить subparser "tasks" (plural)
  ├── Команды: create, list, show, start, block, unblock, complete, fail, archive
  ├── create читает task.yaml через TaskParser → TaskEngine.create_from_spec
  ├── list/show/start/... используют TaskEngine напрямую
  └── Все команды — sync, не async
```

### Правила парсинга
```text
"voyage task <role>"  (singular) → старая команда, generate TASK.md
"voyage tasks <cmd>"  (plural)  → новые runtime-команды
```

### Важно: не ломать старую команду
Старый парсер `voyage task <role> --task "..."` должен продолжать работать как раньше. Новые команды — через отдельный subparser `tasks`.

---

## 9. Поведение команд

### `voyage tasks create --file <path>`
```python
parser = TaskParser()
spec = parser.parse(path)
engine = TaskEngine()
record = engine.create_from_spec(spec)
print(f"✅ Created: {record.id} {record.title}")
return 0
```

### `voyage tasks list`
```python
engine = TaskEngine()
records = engine.list(limit=args.limit or 20)
# Таблица: ID | Status | Role | Title | Updated
return 0
```

### `voyage tasks show <id>`
```python
engine = TaskEngine()
record = engine.get(id)
# Показать все поля TaskRecord
return 0
```

### `voyage tasks start <id>`
```python
engine = TaskEngine()
record = engine.start(id)
print(f"🚀 Started: {record.id} → {record.status}")
return 0
```

### `voyage tasks block <id> --reason "..."`
```python
engine = TaskEngine()
record = engine.block(id, reason=args.reason)
print(f"⏸️  Blocked: {record.id} → {record.status}")
return 0
```

### `voyage tasks complete <id>`
```python
engine = TaskEngine()
record = engine.complete(id)
print(f"✅ Completed: {record.id} → {record.status}")
return 0
```

### `voyage tasks fail <id> --reason "..."`
```python
engine = TaskEngine()
record = engine.fail(id, reason=args.reason)
print(f"❌ Failed: {record.id} → {record.status}")
return 0
```

### `voyage tasks archive <id>`
```python
engine = TaskEngine()
record = engine.archive(id)
print(f"📦 Archived: {record.id} → {record.status}")
return 0
```

---

## 10. Definition of Done для Phase 3

Готово только если:

```text
1. voyage tasks create --file ... работает
2. voyage tasks list показывает задачи
3. voyage tasks show <id> показывает детали
4. voyage tasks start <id> меняет статус на in_progress
5. voyage tasks block <id> --reason меняет статус на blocked
6. voyage tasks unblock <id> меняет статус на in_progress
7. voyage tasks complete <id> меняет статус на completed
8. voyage tasks fail <id> --reason меняет статус на failed
9. voyage tasks archive <id> меняет статус на archived
10. Старые команды не сломаны (voyage task <role> --task "...")
11. pytest tests/unit/test_task_parser.py: 48 passed
12. pytest tests/unit/test_task_engine.py: 55 passed
13. pytest tests/unit/test_cli_tasks.py: all passed
14. pytest tests/ -v: 252 passed, 4 failed (pre-existing integration docs_cli environment failures only)
    - If new failures appear outside docs_cli → stop and report
    - Final readiness: B. Yes with warnings (not A. Yes) while docs_cli failures persist
15. git diff --check: passed
16. git status: working tree clean
17. Нет автоматических commit/push без explicit approval
```

---

## 11. Тесты для Phase 3

Создать: `tests/unit/test_cli_tasks.py`

Минимальные тесты:

### New plural CLI tests
```text
test_tasks_create_from_yaml
test_tasks_list_shows_created_task
test_tasks_show_existing_task
test_tasks_show_missing_task_returns_error
test_tasks_start_task
test_tasks_block_task_with_reason
test_tasks_unblock_task
test_tasks_complete_task
test_tasks_fail_task_with_reason
test_tasks_archive_task
test_tasks_invalid_transition_returns_error
test_tasks_create_invalid_yaml_returns_error
test_tasks_list_by_role
test_tasks_list_by_status
test_tasks_list_limit
test_tasks_list_empty
```

### Regression tests (старое не сломано)
```text
test_legacy_task_command_still_works
test_legacy_task_command_does_not_route_to_tasks_runtime
test_legacy_task_command_with_phase_still_works
```

### Implementation notes
- Использовать `tmp_path` для изоляции БД
- Тестировать handler-функции напрямую (не subprocess)
- Проверять возвращаемый exit code (0/1)
- Проверять stdout output
- Каждый тест создаёт новый TaskEngine с tmp_path

---

## 12. Файлы, которые НЕ менять

```text
voyage_framework/core/task_models.py      # TaskYamlSpec, TaskRecord — не менять
voyage_framework/core/task_parser.py      # TaskParser — не менять
voyage_framework/core/task_engine.py      # TaskEngine — не менять API
voyage_framework/core/event_engine.py     # EventEngine — не менять
voyage_framework/core/models.py           # EventType — не менять
```

---

## 13. Контактные данные

Если что-то неясно — проверять `docs/VOYAGE_V4_1_CONTRACT.md`.

Если контракт противоречит реальному коду — остановиться и дать отчёт.
Не менять контракт без explicit user approval.
Не менять контракт в Phase 3, если это не было отдельно разрешено пользователем.

---

## 14. Пример task.yaml для теста create

```yaml
id: VF-001
title: CLI Test Task
description: Test task for CLI create command
role: developer
acceptance_criteria:
  - CLI creates task from YAML
  - Task appears in list
```

---

## 15. Главное правило

**Не ломать старое. Не писать лишнего. Тесты проходят — commit — push.**

But: **Do not commit or push without explicit user approval.**

---

## 16. Final Report Format

At the end, provide:

```markdown
# Phase 3 Report

## Changed files
...

## Implemented commands
- voyage tasks create
- voyage tasks list
- voyage tasks show
- voyage tasks start
- voyage tasks block
- voyage tasks unblock
- voyage tasks complete
- voyage tasks fail
- voyage tasks archive

## Backward compatibility
- voyage task <role> --task "...": passed/failed

## Test results
- test_task_parser.py: 48 passed
- test_task_engine.py: 55 passed
- test_cli_tasks.py: X passed, Y failed
- Full suite: X passed, Y failed
- git diff --check: passed
- git status: working tree clean

## Remaining risks
...

## Ready to commit Phase 3?
B. Yes with warnings (4 known pre-existing integration docs_cli environment failures are acceptable only if no new failures appear)
C. No
```

Do not commit or push automatically. Wait for explicit approval.
