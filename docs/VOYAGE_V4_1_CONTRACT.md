# VOYAGE V4.1 CONTRACT

> Технический контракт Voyage Framework v4.1.
> Этот документ — **стоп-кран** перед любым новым кодом.
> Ни один компонент v4.1 не реализуется без утверждённого контракта.

---

## 1. Что такое Voyage v4.1

Voyage v4.1 — это **Development Memory System / Project Knowledge Operating System**.

Не "AI Agent Framework". Не замена CrewAI / AutoGen / LangGraph.

**Главная ценность:** память проекта, которая переживает агентов.

```text
Voyage = ADR + Context + Tasks + Events + Decisions + Knowledge
Agents = Kimi, Codex, Claude, Gemini, DeepSeek — заменяемые исполнители
```

---

## 2. Source of Truth иерархия

```text
task.yaml              ← SOURCE OF TRUTH (читаем)
  ↓
TaskYamlSpec (Pydantic) ← immutable YAML model
  ↓
TaskRecord (SQLite)    ← runtime state
  ↓
EventEngine (JSONL)    ← audit log
  ↓
TASK.md                ← GENERATED для человека/агента (письменный)
CONTEXT.json           ← GENERATED для агента (структурированный)
```

### Правила

1. **`task.yaml` — единственный источник истины для задачи.**
2. **`TASK.md` никогда не парсится как source of truth.** Только генерируется.
3. **EventEngine — append-only audit log.** Не управляет задачами. Не хранит текущий статус. Только фиксирует переходы.
4. **TaskEngine управляет статусами.** Только он меняет `TaskRecord.status`.
5. **SQLite sync (не async).** TaskEngine v4.1 использует `sqlite3` напрямую.
   SQLAlchemy ORM для таблицы `tasks` не используется. Примечание ADR-009 про sync
   SQLAlchemy относится к legacy CLI DB usage, а не к TaskEngine v4.1.

---

## 3. Модели

### 3.1 TaskYamlSpec

Описание задачи из `task.yaml`. Иммутабельный, используется при создании `TaskRecord`.

```python
class TaskYamlSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str                    # Уникальный ID задачи (VF-001)
    title: str                 # Краткое название
    description: str           # Подробное описание
    role: str                  # Роль исполнителя (developer, architect, devops...)
    mode: str | None           # Режим: discover, design, solution, plan, implement
    priority: str | None       # high, medium, low
    status: str                # Начальный статус: pending
    acceptance_criteria: list[str]
    files: TaskFiles | None    # Что читать, что менять
    tests: list[str] | None    # Какие тесты запускать
    metadata: dict[str, Any]   # Произвольные метаданные
```

### 3.2 TaskRecord

Runtime-запись в SQLite. Изменяется TaskEngine.

```python
class TaskRecord:
    id: str                    # PK, совпадает с TaskYamlSpec.id
    title: str
    description: str
    role: str
    status: str                # Текущий статус
    priority: str | None
    source_path: str | None    # Путь к task.yaml
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    archived_at: datetime | None
    metadata_json: str          # JSON метаданных
```

### 3.3 Разделение

| Аспект | TaskYamlSpec | TaskRecord |
|---|---|---|
| Источник | `task.yaml` | SQLite |
| Изменяется | Нет (immutable) | Да (TaskEngine) |
| Жизненный цикл | Один раз при создании | На протяжении всей задачи |
| Статус | Начальный | Текущий |
| acceptance_criteria | Есть | Не хранится отдельно (только в metadata) |

`TaskYamlSpec` — описание задачи из `task.yaml`. Legacy `TaskSpec` остаётся в
`core/models.py` для обратной совместимости. Не удалять и не переименовывать legacy-модель
в v4.1 Phase 1.5.

---

## 4. Статусы задачи

```text
pending
  ↓
in_progress
  ↓ ← → blocked
  ↓
completed / failed
  ↓
archived
```

### 4.1 Разрешённые переходы

| From → To | Разрешено | Примечание |
|---|---|---|
| pending → in_progress | ✅ | Начало работы |
| pending → blocked | ✅ | Блокер до старта |
| in_progress → blocked | ✅ | Блокер во время работы |
| blocked → in_progress | ✅ | Разблокировка |
| in_progress → completed | ✅ | Успешное завершение |
| in_progress → failed | ✅ | Неуспешное завершение |
| failed → in_progress | ✅ | Повторная попытка |
| completed → archived | ✅ | Архивация |
| failed → archived | ✅ | Архивация |
| in_progress → archived | ✅ | Принудительная архивация |
| blocked → archived | ✅ | Архивация заблокированной |

### 4.2 Запрещённые переходы

| From → To | Запрещено | Причина |
|---|---|---|
| pending → completed | ❌ | Нельзя завершить без старта |
| pending → failed | ❌ | Нельзя провалить без старта |
| completed → in_progress | ❌ | Завершённая задача не возобновляется |
| completed → failed | ❌ | Конечный статус |
| archived → any | ❌ | Архив — точка невозврата |
| failed → completed | ❌ | Только через in_progress |
| any → pending | ❌ | Только failed → in_progress → ... |

### 4.3 Правила переходов

1. **Каждый переход валидируется TaskEngine.**
2. **Невалидный переход → ValueError.**
3. **Переход пишет событие в EventEngine.**
4. **`updated_at` обновляется при каждом переходе.**
5. **`started_at` заполняется при первом `pending → in_progress`.**
6. **`completed_at` заполняется при `in_progress → completed/failed`.**
7. **`archived_at` заполняется при переходе в archived`.**

---

## 5. События EventEngine

EventEngine — **append-only audit log**. Не управляет задачами.

### 5.1 События жизненного цикла задачи

```text
task_created
task_started
task_blocked
task_unblocked
task_completed
task_failed
task_archived
task_generated          # TaskGenerator создал TASK.md / CONTEXT.json
context_synced          # voyage sync обновил CONTEXT.json
```

### 5.2 Payload событий (обязательные поля)

```python
{
    "task_id": str,           # ID задачи
    "actor": str,             # Кто инициировал (CLI, agent, human)
    "old_status": str | None, # Предыдущий статус (для transition)
    "new_status": str,        # Новый статус
    "reason": str | None,     # Причина (особенно для block/fail)
    "source_path": str | None, # Путь к task.yaml
    "timestamp": str,         # ISO 8601
    "metadata": dict,          # Дополнительные данные
}
```

### 5.3 Правила

1. **Каждый переход статуса = минимум одно событие.**
2. **EventEngine не читает события для определения текущего статуса.**
3. **TaskRecord — единственный источник текущего статуса.**
4. **EventEngine используется для replay, audit, chronicler.**
5. **События не удаляются. Не изменяются. Только append.**

---

## 6. Формат task.yaml

### 6.1 Минимальный формат

```yaml
id: VF-001
title: Implement Task Engine for Voyage
description: >
  Create a runtime lifecycle management system for Voyage tasks
  with SQLite persistence, status transitions, and event logging.

role: developer
mode: solution
priority: high
status: pending

acceptance_criteria:
  - task.yaml can be parsed into TaskYamlSpec
  - TaskRecord can be created in SQLite
  - Status transitions follow the contract
  - EventEngine logs all lifecycle events
  - Existing CLI commands remain unbroken

files:
  read:
    - voyage_framework/cli.py
    - voyage_framework/core/models.py
    - voyage_framework/core/event_engine.py
  modify:
    - voyage_framework/core/task_parser.py
    - voyage_framework/core/task_engine.py
    - tests/test_task_parser.py
    - tests/test_task_engine.py

tests:
  - pytest tests/test_task_parser.py -v
  - pytest tests/test_task_engine.py -v

metadata:
  sprint: 2
  estimated_hours: 4
  dependencies: []
```

### 6.2 Обязательные поля

| Поле | Тип | Обязательно | Валидация |
|---|---|---|---|
| `id` | str | ✅ | Уникальный, формат `VF-XXX` или `ST-XXX` |
| `title` | str | ✅ | Длина 1–200 |
| `description` | str | ✅ | Длина 1–5000 |
| `role` | str | ✅ | Должна существовать в PolicyEnforcer |
| `status` | str | ✅ | Должна быть `pending` для новых |
| `acceptance_criteria` | list[str] | ✅ | Минимум 1 элемент |

### 6.3 Опциональные поля

| Поле | Тип | По умолчанию |
|---|---|---|
| `mode` | str | `solution` |
| `priority` | str | `medium` |
| `files` | TaskFiles | `None` |
| `tests` | list[str] | `None` |
| `metadata` | dict | `{}` |

### 6.4 Валидация role

```python
from voyage_framework.security.policy import PolicyEnforcer

enforcer = PolicyEnforcer()
assert role in enforcer.DEFAULT_POLICIES
# или enforcer.get_policy(role) не возвращает default пустую
```

### 6.5 Валидация status

```python
assert status in {"pending", "in_progress", "blocked", "completed", "failed", "archived"}
assert status == "pending"  # для новых задач
```

---

## 7. SQLite Schema

### 7.1 Таблица tasks

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT,
    mode TEXT,
    source_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    archived_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    criteria_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_tasks_project
ON tasks(status, role);

CREATE INDEX IF NOT EXISTS idx_tasks_status
ON tasks(status, updated_at);
```

### 7.2 Правила

1. **Одна таблица `tasks` в `events.db` или `tasks.db`.**
2. **Если EventEngine уже использует `events.db`, лучше добавить таблицу туда.**
3. **Или временно `tasks.db` рядом с `events.db`.**
4. **Не создавать отдельную ORM-систему.** Использовать `sqlite3` напрямую (sync).
5. **JSON-поля сериализовать через `json.dumps()`.**

---

## 8. CLI Commands

### 8.1 Старые команды (не ломать)

```bash
voyage init                              # Initialize .voyage/
voyage status                            # Show project status
voyage run <role> --task "..."           # Run agent
voyage task <role> --task "..."          # Generate TASK.md + CONTEXT.json
voyage task <role> --task "..." --phase M2
voyage events [--limit N]                # Show events
voyage approve                           # Show pending approvals
voyage graph visualize                   # Visualize workflow graph
voyage graph run <role> --task "..."     # Run via LangGraph
voyage graph state <correlation_id>      # Show graph state
voyage chronicler journal                # Show process journal
voyage chronicler replay <id>            # Generate replay
voyage chronicler decisions              # Show decision log
voyage chronicler tutorial <id>          # Generate tutorial draft
voyage evaluate                          # Show improvement summary
voyage docs build                        # Build documentation
voyage docs serve                        # Serve docs locally
```

### 8.2 Новые команды (runtime lifecycle)

Используем **plural `tasks`**, чтобы не конфликтовать с `voyage task <role>`.

```bash
voyage tasks create --file .voyage/TASKS/VF-001/task.yaml
voyage tasks list
voyage tasks list --role developer
voyage tasks list --status in_progress
voyage tasks list --limit 20
voyage tasks show VF-001
voyage tasks start VF-001
voyage tasks block VF-001 --reason "Need clarification"
  # → status: blocked, reason сохраняется
voyage tasks unblock VF-001
  # → status: in_progress
voyage tasks complete VF-001
voyage tasks fail VF-001 --reason "Tests failed"
voyage tasks archive VF-001
```

### 8.3 Правила CLI

1. **`voyage task <role>` (singular) — остаётся генератором TASK.md.**
2. **`voyage tasks ...` (plural) — runtime управление задачами.**
3. **Никаких breaking changes для существующих команд.**
4. **Позже можно добавить alias `voyage task create` через отдельный subparser, но только если парсер отличит `create` от роли.**
5. **Все новые команды — sync, не async.**

---

## 9. TaskParser

### 9.1 Интерфейс

```python
class TaskParser:
    """Читает task.yaml и возвращает TaskYamlSpec."""

    def parse(self, path: Path | str) -> TaskYamlSpec:
        """Прочитать и валидировать task.yaml.
        
        Raises:
            TaskValidationError: если YAML невалиден или обязательные поля отсутствуют.
            RoleValidationError: если роль не существует в PolicyEnforcer.
        """
        ...

    def parse_string(self, yaml_content: str) -> TaskYamlSpec:
        """Парсить task.yaml из строки (для тестов)."""
        ...
```

### 9.2 Требования

1. **Использовать `pyyaml` для чтения YAML.**
2. **Валидировать через Pydantic `TaskYamlSpec`.**
3. **Проверять `role` через `PolicyEnforcer`.**
4. **Проверять `status == "pending"` для новых задач.**
5. **Не читать `TASK.md` как source of truth.**
6. **Не генерировать `TASK.md` — это работа TaskGenerator.**
7. **TaskParser MAY писать `task_parsed`, если EventEngine явно передан.** До Phase 4
   emission события опционален; обязательное event logging начинается в Phase 4.

---

## 10. TaskEngine

### 10.1 Интерфейс

```python
class TaskEngine:
    """Управляет жизненным циклом задач."""

    def __init__(self, db_path: Path, event_engine: EventEngine | None = None) -> None:
        ...

    def create_from_spec(self, spec: TaskYamlSpec) -> TaskRecord:
        """Создать TaskRecord из TaskYamlSpec."""
        ...

    def get(self, task_id: str) -> TaskRecord | None:
        ...

    def list(
        self,
        status: str | None = None,
        role: str | None = None,
        limit: int = 100,
    ) -> list[TaskRecord]:
        ...

    def transition(
        self,
        task_id: str,
        new_status: str,
        reason: str | None = None,
        actor: str = "cli",
    ) -> TaskRecord:
        """Перевести задачу в новый статус.
        
        Validates transition against VALID_TRANSITIONS.
        Logs event to EventEngine.
        Updates updated_at.
        """
        ...

    # Shorthand methods
    def start(self, task_id: str, actor: str = "cli") -> TaskRecord: ...
    def block(self, task_id: str, reason: str, actor: str = "cli") -> TaskRecord: ...
    def unblock(self, task_id: str, actor: str = "cli") -> TaskRecord: ...
    def complete(self, task_id: str, actor: str = "cli") -> TaskRecord: ...
    def fail(self, task_id: str, reason: str, actor: str = "cli") -> TaskRecord: ...
    def archive(self, task_id: str, actor: str = "cli") -> TaskRecord: ...
```

### 10.2 Требования

1. **Только TaskEngine меняет статус TaskRecord.**
2. **Каждый переход валидируется по `VALID_TRANSITIONS`.**
3. **Каждый переход пишет событие в EventEngine.**
4. **`updated_at` обновляется при любом изменении.**
5. **`started_at` устанавливается при первом `pending → in_progress`.**
6. **`completed_at` устанавливается при `in_progress → completed/failed`.**
7. **`archived_at` устанавливается при `→ archived`.**
8. **Не генерировать TASK.md.** Это работа TaskGenerator.
9. **Не парсить YAML.** Это работа TaskParser.

---

## 11. TaskGenerator

### 11.1 Правила

1. **TaskGenerator не заменяет TaskParser.**
2. **Legacy TaskGenerator принимает legacy `TaskSpec` и генерирует `TASK.md` +
   `CONTEXT.json`.** Этот flow сохраняется для обратной совместимости.
3. **TaskGenerator не управляет статусами.**
4. **Правильная цепочка:**
   ```text
   task.yaml → TaskParser → TaskYamlSpec → TaskEngine → TaskRecord
                                                ↓
                                         TaskGenerator → TASK.md + CONTEXT.json
   ```
5. **`voyage task <role> --task "..."` — это TaskGenerator.** Он не создаёт TaskRecord.

---

## 12. Архитектурная цепочка v4.1

```text
Phase 0: Contract Freeze
    ├── Read existing code
    ├── Create VOYAGE_V4_1_CONTRACT.md
    └── Approve contract

Phase 1: TaskYamlSpec + TaskParser
    ├── Define TaskYamlSpec Pydantic model
    ├── Implement TaskParser
    ├── Write tests
    └── Approve: tests pass

Phase 2: TaskRecord + TaskEngine
    ├── Define SQLite schema
    ├── Implement TaskEngine
    ├── Implement VALID_TRANSITIONS
    ├── Integrate EventEngine logging
    ├── Write tests
    └── Approve: tests pass

Phase 3: CLI tasks (plural)
    ├── Add voyage tasks create
    ├── Add voyage tasks list/show
    ├── Add voyage tasks start/block/unblock/complete/fail/archive
    ├── Integrate TaskParser + TaskEngine
    ├── Write tests
    └── Approve: tests pass + old CLI not broken

Phase 4: Event Logging
    ├── Ensure all transitions write events
    ├── Add task_parsed event
    ├── Add context_synced event
    ├── Write tests
    └── Approve: events appear in EventEngine

Phase 5: voyage sync / Context Builder Lite
    ├── Implement voyage sync command
    ├── Collect ADR, TASKS, PROJECT_STATE, ROADMAP, ARCHITECTURE
    ├── Update CONTEXT.json
    ├── Write tests
    └── Approve: CONTEXT.json updated correctly

Phase 6: Agent Registry Draft
    ├── Define registry schema
    ├── Implement voyage agent list/show/suggest
    ├── Write tests
    └── Approve: minimal registry works

Phase 7: Modes Draft
    ├── Implement voyage discover/design/solution/plan
    ├── Generate prompt files (not workflows)
    ├── Write tests
    └── Approve: prompt files generated
```

---

## 13. Definition of Done for v4.1

Готово только если **все** пункты выполнены:

1. `pytest tests/` проходит (все тесты, включая новые).
2. `voyage task developer --task "..."` работает как раньше (не сломан).
3. `voyage tasks create --file ...` создаёт задачу из task.yaml.
4. `voyage tasks list` показывает задачи.
5. `voyage tasks start <id>` меняет статус на `in_progress`.
6. `voyage tasks block <id> --reason "..."` меняет статус на `blocked`.
7. `voyage tasks complete <id>` меняет статус на `completed`.
8. `voyage tasks fail <id> --reason "..."` меняет статус на `failed`.
9. `voyage tasks archive <id>` меняет статус на `archived`.
10. EventEngine пишет `task_created`, `task_started`, `task_completed`, `task_failed`, `task_blocked`, `task_archived`.
11. `voyage sync` обновляет `CONTEXT.json`.
12. Старые CLI-команды не сломаны.
13. Документ `docs/VOYAGE_V4_1_CONTRACT.md` создан и актуален.
14. Тесты покрывают TaskParser, TaskEngine, CLI tasks, Event logging.
15. **Coverage ≥ 80% для новых модулей.**

---

## 14. Архитектурные принципы v4.1

1. **Context Before Automation** — сначала знание, потом код.
2. **Decisions Before Code** — сначала ADR/контракт, потом имплементация.
3. **Local First** — SQLite, файловая система, git. Не PostgreSQL для Voyage.
4. **Human Approval Required** — не auto-deploy без подтверждения.
5. **Sequential Before Parallel** — работает один агент, потом несколько.
6. **Headless First** — CLI, потом GUI. IDE-агенты через prompt.
7. **Knowledge > Agents** — агентов можно менять, знания остаются.
8. **task.yaml = Source of Truth** — не TASK.md, не YAML-файлы.
9. **EventEngine = Audit Log** — не контроллер, не state machine.
10. **Sync sqlite3 for TaskEngine v4.1** — без async и без SQLAlchemy ORM для `tasks`.
    ADR-009 про sync SQLAlchemy применяется только к legacy CLI DB usage.

---

## 15. Изменения в контракте

| Версия | Дата | Автор | Изменения |
|---|---|---|---|
| 1.1 | 2026-06-20 | Phase 1.5 | Clarified TaskYamlSpec, sqlite3 usage, task_parsed optional, ID validation, immutable model |
| 1.0 | 2026-06-20 | Phase 0 | Начальный контракт v4.1 |

---

## 16. Утверждение

Этот контракт утверждён и является **стоп-краном**.

Любое изменение требует:
1. Обновление этого документа.
2. Пометку версии в таблице "Изменения".
3. Обновление Definition of Done.

**Без утверждённого контракта — никакого нового кода.**
