# AGENTS.md — Voyage Framework v4.1

> Операционное руководство для AI-агентов, работающих с репозиторием. Этот файл не
> является архитектурным контрактом.

## 0. Canonical Source of Truth

Канонические документы архитектуры Voyage v4.1 MVP:

- `docs/VOYAGE_V4_1_CONTRACT.md`
- `docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md`

Если `AGENTS.md` противоречит контракту, действует контракт. Новые фазы можно начинать
только по утверждённому prompt в `docs/prompts/`.

## 1. What Voyage v4.1 MVP Is

Voyage Framework v4.1 MVP — это **Development Memory System / Project Knowledge
Operating System** для локального ведения задач, runtime-состояния, аудита и контекста
разработки.

Основные возможности v4.1 MVP:

- каноническая спецификация задач в `task.yaml`;
- runtime-учёт задач через `TaskRecord` и SQLite;
- append-only аудит через `EventEngine`;
- read-only каталоги ролей и режимов;
- deterministic генерация prompt packages для внешних AI-инструментов;
- Context Builder Lite и CLI для task/context workflows.

## 2. What Voyage v4.1 MVP Is Not

Voyage v4.1 MVP **не является AI Agent Framework** и не реализует:

- выполнение AI-агентов или AI model inference;
- runtime orchestration или multi-agent workflow;
- LangGraph как core runtime;
- CrewAI/AutoGen runtime;
- background workers или self-running agents;
- Web UI или production deployment platform.

В репозитории могут существовать legacy/historical модули `voyage_framework/agents/` и
`voyage_framework/langgraph_tools/`. Они не входят в core-контракт v4.1 MVP и не должны
трактоваться как актуальная архитектура или источник истины.

## 3. Source of Truth Hierarchy

```text
Canonical:
  task.yaml      → canonical task specification (TaskYamlSpec / TaskParser)
  TaskRecord     → canonical runtime task state (SQLite / TaskEngine)
  EventEngine    → append-only audit log

Read-only support:
  AgentRegistry  → role catalog
  ModeRegistry   → mode catalog
  ContextBuilder → context aggregation and comparison
  PromptGenerator → prompt package generation for external tools

Generated artifacts — NOT source of truth:
  TASK.md
  CONTEXT.json

Reports are documentation artifacts. The exception is
`docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md`, which records the final v4.1 MVP closure
verdict.
```

Нельзя парсить `TASK.md` или `CONTEXT.json` обратно как canonical truth. Они генерируются
из канонического состояния и могут быть пересозданы.

## 4. Repository Structure

```text
voyage_framework/
├── core/
│   ├── task_models.py       # TaskYamlSpec и TaskRecord contract models
│   ├── task_parser.py       # task.yaml → TaskYamlSpec
│   ├── task_engine.py       # SQLite runtime task state
│   ├── event_engine.py      # append-only audit log
│   ├── context_builder.py   # Context Builder Lite
│   ├── agent_registry.py    # read-only role catalog (AgentRegistry class + factory)
│   ├── default_roles.py     # static RoleProfile catalog (20 profiles, all_profiles())
│   ├── prompt_modes.py      # read-only mode catalog
│   └── prompt_generator.py  # deterministic prompt packages
├── cli.py                   # существующий CLI surface
├── chronicler/              # process documentation helpers
├── security/                # sandbox, policy, approval, audit helpers
├── agents/                  # legacy/historical, не core v4.1 MVP
└── langgraph_tools/         # legacy/historical, не core v4.1 MVP

tests/
├── unit/
└── integration/

docs/
├── VOYAGE_V4_1_CONTRACT.md
├── prompts/
└── reports/
```

Корневые `voyage_framework/`, `tests/` и `pyproject.toml` относятся к активному проекту.
Вложенная `voyage_framework_v4_mvp/` — более ранний/параллельный snapshot; не изменяйте
его без отдельного указания.

## 5. Core Components

### Task specification and runtime state

- `TaskYamlSpec` — immutable представление canonical `task.yaml`.
- `TaskParser` — валидирует `task.yaml`; не использует generated Markdown/JSON как truth.
- `TaskRecord` — canonical runtime task state в SQLite.
- `TaskEngine` — единственный штатный мутатор runtime-статусов задач.
- `EventEngine` — append-only audit log, а не state controller.

### Read-only knowledge layer

- `AgentRegistry` — deterministic read-only каталог 20 registered role profiles (6 runtime +
  16 methodology; `developer` and `reviewer` shared across both sets). Methodology roles are
  prompt/context roles — they are not autonomous agents, do not execute themselves, and do not
  call models automatically. Он не запускает агентов.
- `ModeRegistry` — deterministic read-only каталог mode profiles. Он не активирует и не
  исполняет режимы.
- `PromptGenerator` — read-only генератор `PromptPackage` для ручной передачи во внешние
  инструменты (Codex, Claude, Gemini и другие). Он не вызывает модели и не выполняет prompt.
- `ContextBuilder` — собирает и сверяет контекст; generated `CONTEXT.json` не становится
  canonical state.

## 6. CLI Commands

Ключевые различия команд:

```bash
# Legacy singular task generator: создаёт generated TASK.md / CONTEXT.json
voyage task <role> --task "..."

# Runtime task database management
voyage tasks create --file task.yaml
voyage tasks list
voyage tasks show <task_id>
voyage tasks start|block|unblock|complete|fail|archive <task_id>

# Context Builder Lite
voyage sync build --file task.yaml --output CONTEXT.json
voyage sync check --file task.yaml
voyage sync status
```

Команда `voyage task` не заменяет canonical `task.yaml`. Namespace `voyage tasks` управляет
`TaskRecord`, а `voyage sync` относится к Context Builder Lite.

В v4.1 MVP нет CLI-команд для runtime agent execution, orchestration или активации modes.

## 7. Development Commands

Выполняйте команды из корня репозитория:

```bash
pip install -e ".[dev]"
pytest tests/
pytest tests/unit/
ruff check .
ruff format --check voyage_framework tests
mypy voyage_framework
git diff --check
git status --short
```

Проект использует Python 3.11+, Pydantic v2, pytest, Ruff и strict mypy. Работайте с
активным корневым кодом; не дублируйте изменения во вложенном snapshot без указания.

## 8. Safety Rules for AI Agents

- Не начинайте новую фазу без утверждённого prompt в `docs/prompts/`.
- Не меняйте код, если задача documentation-only.
- Не коммитьте и не пушьте без явного указания.
- Не считайте `AGENTS.md` canonical architecture при конфликте с контрактом.
- Не используйте generated `TASK.md` или `CONTEXT.json` как source of truth.
- Не добавляйте runtime orchestration без явного разрешения будущей фазы.
- Не добавляйте CLI-команды без явного разрешения будущей фазы.
- Не изменяйте `.voyage` runtime files.
- Не обходите sandbox, approval flow или ограничения опасных команд.
- Не скрывайте Windows ACL warnings изменением `.gitignore` без явного указания.
- Соблюдайте scope разрешённых файлов и сообщайте об отклонениях вместо догадок.

## 9. Files Agents Must Not Modify Without Explicit Instruction

- `docs/VOYAGE_V4_1_CONTRACT.md` и closure audit;
- `voyage_framework/core/task_models.py`, `task_parser.py`, `task_engine.py`;
- `voyage_framework/core/event_engine.py`, `context_builder.py`;
- `voyage_framework/core/agent_registry.py`, `prompt_modes.py`, `prompt_generator.py`;
- `voyage_framework/cli.py`;
- `voyage_framework/agents/` и `voyage_framework/langgraph_tools/`;
- `.gitignore`, `pyproject.toml`, `.github/`;
- `TASK.md`, `CONTEXT.json` и `.voyage/` runtime artifacts.

Явный approved phase prompt может разрешить конкретное изменение. Без такого разрешения
сохраняйте эти contracts и artifacts неизменными.

## 10. Known Environmental Warnings

На Windows `git status`, Ruff или другие инструменты могут показывать:

```text
warning: could not open directory '.test-tmp-context-p5/': Permission denied
warning: could not open directory '.test-tmp-sync-p5/': Permission denied
warning: could not open directory '.test-tmp-tasks-p5/': Permission denied
warning: could not open directory '.test-tmp-unit-p5/': Permission denied
```

Это pre-existing Windows ACL temp directories от тестового runner, а не ошибки архитектуры
или кода. Не изменяйте `.gitignore` и не добавляйте product code для их сокрытия. При
проверке pollution указывайте их отдельно от project-file changes.

## 11. Future Work / Backlog

- **Phase 7** может определить только будущий adapter contract для внешних AI-инструментов.
- Runtime adapter, agent execution и orchestration пока не реализованы и не должны
  добавляться без отдельной утверждённой фазы.
- Любая будущая интеграция обязана сохранять source-of-truth hierarchy и read-only contracts
  `AgentRegistry`, `ModeRegistry` и `PromptGenerator`.
