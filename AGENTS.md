# AGENTS.md — Voyage Framework v4.0

> Этот файл предназначен для AI-агентов, работающих с проектом. Описывает архитектуру, конвенции, команды и известные особенности.

---

## 1. Обзор проекта

**Voyage Framework v4.0** — AI-Native Engineering Operating System для solo-разработчика.

- **Название пакета:** `voyage-framework`
- **Версия:** `4.0.0`
- **Лицензия:** MIT
- **Автор:** AndreyVoyage
- **Python:** `>=3.11` (поддерживаются 3.11 и 3.12)
- **Статус:** Phase 4 + Chronicler — LangGraph Integration & Process Documentation (MVP runnable)

Фреймворк предоставляет:

- SQLite + JSONL event store (`EventEngine`) для аудита и восстановления контекста.
- Песочницу команд `SecureExecutor` с 5 уровнями безопасности.
- Ролевую модель доступа (`PolicyEnforcer`) и human-in-the-loop approval flow.
- Генератор задач `TaskGenerator`, создающий `TASK.md` + `CONTEXT.json` для агентов.
- Асинхронный runtime агента (`AgentRuntime`) с циклом Plan → Execute → Reflect → Retry.
- CLI `voyage` для инициализации проекта, запуска агентов, просмотра событий и chronicler-команд.

---

## 2. Структура репозитория

```
Framework-voyage-mvp/
├── pyproject.toml              # Конфигурация проекта, зависимостей и инструментов
├── Makefile                    # Стандартные команды разработки
├── README.md                   # Человекочитаемая документация (русский язык)
├── AGENTS.md                   # Этот файл
├── tests/                      # Тесты
│   ├── unit/                   # Модульные тесты
│   └── integration/            # Интеграционные тесты
├── voyage_framework/             # Основной Python-пакет
│   ├── cli.py                  # Точка входа CLI
│   ├── agents/
│   │   └── runtime.py          # AgentRuntime
│   ├── core/
│   │   ├── models.py           # Pydantic-модели
│   │   ├── event_engine.py     # SQLite + JSONL event store
│   │   └── storage.py          # Атомарные записи, frontmatter, journal rotation
│   ├── security/
│   │   ├── sandbox.py          # SecureExecutor + SubprocessBackend/DockerBackend
│   │   ├── policy.py           # RolePolicy + PolicyEnforcer
│   │   ├── approval.py         # ApprovalQueue / human approval flow
│   │   └── audit.py            # JSONL audit logger
│   ├── langgraph_tools/      # Phase 4: LangGraph/SimpleGraph workflow
│   │   ├── graph_builder.py  # VoyageGraphBuilder
│   │   ├── nodes.py          # Ноды plan/execute/reflect/retry/complete
│   │   ├── edges.py          # Conditional edges
│   │   ├── visualizer.py     # Mermaid/Graphviz export
│   │   ├── checkpoint_adapter.py  # Checkpoint → EventEngine
│   │   └── simple_graph.py   # Pure-Python fallback StateGraph
│   ├── chronicler/           # Phase 1 Chronicler — documentation of process
│   │   ├── journal.py        # ProcessJournal
│   │   ├── replay.py         # ReplayGenerator
│   │   ├── decision_log.py   # DecisionLog
│   │   └── tutorial_generator.py  # TutorialDraft
│   └── specs/
│       ├── task_generator.py   # Генератор TASK.md + CONTEXT.json
│       └── tracker.py          # AcceptanceTracker
└── voyage_framework_v4_mvp/    # ⚠️ Полная дублирующая копия всего проекта
    ├── .github/workflows/ci.yml  # CI только внутри этой копии
    ├── .gitignore                # .gitignore только внутри этой копии
    ├── pyproject.toml
    ├── Makefile
    ├── README.md
    ├── tests/
    └── voyage_framework/
```

### Важная особенность: дублирующая копия

Директория `voyage_framework_v4_mvp/` — это **байт-в-байт копия корневого проекта**, включая `voyage_framework/`, `tests/`, `pyproject.toml`, `Makefile` и `README.md`. Она добавлена в Git как самостоятельный снимок (snapshot) MVP.

Последствия:

- В корне репозитория **нет** `.gitignore`.
- CI/GitHub Actions находится **только** внутри `voyage_framework_v4_mvp/.github/workflows/` и не срабатывает для корневого проекта по умолчанию.
- `pyproject.toml` использует `where = ["."]` и `include = ["voyage_framework*"]`, поэтому при установке пакета setuptools найдёт **обе** копии `voyage_framework/`, что может привести к конфликтам импортов.
- Если вы редактируете код, обычно достаточно менять файлы в корневом `voyage_framework/`.

---

## 3. Технологический стек

| Категория | Инструмент |
|---|---|
| Язык | Python >=3.11 |
| Сборка / packaging | setuptools + wheel |
| Валидация данных | Pydantic v2 |
| Логирование | structlog |
| ULID | python-ulid |
| Async файловый ввод/вывод | aiofiles |
| YAML | pyyaml |
| Тестирование | pytest, pytest-asyncio, pytest-cov |
| Статический анализ | mypy (strict), ruff |
| Pre-commit | pre-commit |
| CLI | argparse (стандартная библиотека) |

### Опциональные extras

- `semantic`: ChromaDB, sentence-transformers (будущая Phase 2)
- `ast`: tree-sitter, tree-sitter-python, tree-sitter-typescript
- `dev`: pytest, pytest-asyncio, pytest-cov, mypy, ruff, pre-commit
- `all`: устанавливает всё вышеперечисленное

---

## 4. Команды сборки, тестирования и запуска

Все команды выполняются из корня репозитория.

### Установка

```bash
pip install -e ".[dev]"
```

Или через Makefile:

```bash
make install
```

### Тесты

```bash
make test                 # pytest -v
make test-cov             # pytest --cov=voyage_framework --cov-report=html --cov-report=term
pytest                    # все тесты
pytest -m unit            # только unit-тесты
pytest -m integration     # только интеграционные тесты
pytest --cov=voyage_framework --cov-report=html
```

### Линтеры и форматирование

```bash
make lint                 # mypy voyage_framework && ruff check voyage_framework
make format               # ruff format voyage_framework
make fix                  # ruff check --fix voyage_framework
```

### Очистка артефактов

```bash
make clean                # удаляет __pycache__, .pyc, .pytest_cache, htmlcov, .coverage, .voyage/
```

### Запуск CLI

```bash
voyage init                              # инициализировать .voyage/ в текущей директории
voyage status                            # количество событий и последние events
voyage run <role> --task "..." --plan "cmd1;cmd2" [--project id]
voyage task <role> --task "..." [--phase M1] [--project id]
voyage events [--limit N] [--project id]
voyage approve                           # показать pending approval-запросы
voyage chronicler journal                # последние шаги процесса
voyage chronicler replay <correlation_id>  # replay-скрипт
voyage chronicler decisions              # decision log
voyage chronicler tutorial <correlation_id>  # tutorial draft
```

---

## 5. Организация кода

### `voyage_framework/core/` — ядро

- `models.py`: центральные Pydantic-модели (`Event`, `AgentState`, `ToolResult`, `SecurityPolicy`, `ApprovalRequest`, `TaskSpec`, `ProjectContext`) и перечисления (`EventType`, `AgentStatus`, `SecurityLevel`, `ApprovalStatus`).
- `event_engine.py`: `EventEngine` — append-only хранилище событий на SQLite с JSONL-бэкапом, фильтрацией, replay и агрегацией контекста проекта.
- `storage.py`: вспомогательные функции файловой системы — `atomic_write`, frontmatter-журналы, `journal_rotate`, JSONL helpers.

### `voyage_framework/security/` — безопасность

- `sandbox.py`: `SecureExecutor` с 5 уровнями защиты и двумя backend (`SubprocessBackend`, `DockerBackend`).
- `docker_backend.py`: реализация `DockerBackend` через `docker run --rm` с volume mount project root и сетевой изоляцией.
- `policy.py`: `RolePolicy` + `PolicyEnforcer` с 6 ролями (`architect`, `developer`, `reviewer`, `devops`, `security`, `qa`).
- `approval.py`: `ApprovalQueue` / `ApprovalManager` — persistent human approval flow в `.voyage_approval_pending.json`.
- `audit.py`: `AuditLogger` — JSONL audit trail.

### `voyage_framework/agents/` — агенты

- `runtime.py`: `AgentRuntime` — классический асинхронный цикл Plan → Execute → Reflect → Retry.
- `langgraph_runtime.py`: `LangGraphRuntime` — графовый runtime на базе `VoyageGraphBuilder` (LangGraph при доступности, иначе pure-Python fallback). Поддерживает conditional edges, checkpointing в `EventEngine`, визуализацию и resume.

### `voyage_framework/langgraph_tools/` — графовые workflow (Phase 4)

- `graph_builder.py`: `VoyageGraphBuilder` — единый API поверх LangGraph/SimpleGraph.
- `nodes.py`: ноды `plan`, `execute`, `reflect`, `retry`, `complete`, `error`, `policy_check`, `parallel_validation`.
- `edges.py`: функции маршрутизации по score/retry_count.
- `visualizer.py`: экспорт графа в Mermaid и DOT.
- `checkpoint_adapter.py`: `EventEngineCheckpoint` — сохранение state transitions в `EventEngine`.
- `simple_graph.py`: минимальная реализация `StateGraph` без внешних зависимостей.

### `voyage_framework/chronicler/` — документирование процесса (Phase 1 Chronicler)

- `journal.py`: `ProcessJournal` — запись шагов разработки в `EventEngine`.
- `replay.py`: `ReplayGenerator` — bash/markdown replay из журнала.
- `decision_log.py`: `DecisionLog` — "почему так решили" + ADR drafts.
- `tutorial_generator.py`: `TutorialDraft` — черновик tutorial из шагов.

### `voyage_framework/specs/` — спецификации

- `task_generator.py`: `TaskGenerator` — собирает `TaskSpec` из контекста проекта, правил, ADR, критериев и инструкций; атомарно пишет `TASK.md` и `CONTEXT.json`.
- `tracker.py`: `AcceptanceTracker` — проверяет acceptance criteria и логирует `TASK_COMPLETED` / `ERROR_LOGGED`.

### `voyage_framework/cli.py` — интерфейс командной строки

Реализует команды `voyage init | status | run | task | events | approve` на чистом `argparse`.

### Публичный API

`voyage_framework/__init__.py` экспортирует:

```python
Event, AgentState, ToolResult, ProjectContext, EventEngine,
SecureExecutor, SecurityPolicy, TaskGenerator
```

---

## 6. Стиль кода и конвенции

### Язык документации

- **Кодовые идентификаторы** — английский (`snake_case` для функций/модулей, `PascalCase` для классов, `UPPER_CASE` для констант).
- **Docstrings и комментарии** — русский язык. README полностью на русском.
- Файл `AGENTS.md` также ведётся на русском, так как это основной язык проектной документации.

### Типизация

- В каждом файле первой строкой импортируется `from __future__ import annotations`.
- Используется современный синтаксис: `Path | str`, `dict[str, Any]`, `list[str]`.
- Возвращаемые типы указываются явно: `-> None`, `-> int`, `-> TaskSpec`.
- mypy настроен в strict-режиме (`[tool.mypy]`).

### Форматирование

- Максимальная длина строки: **100 символов** (`ruff line-length = 100`).
- Целевая версия Python: **py311**.
- Ruff линтит правила: `E`, `F`, `I`, `N`, `W`, `UP`, `B`, `C4`, `SIM`.

### Модели

- Повсеместно используются Pydantic v2 `BaseModel` + `Field(...)` с описаниями и default-фабриками.
- Идентификаторы — ULID через `python-ulid`.
- Перечисления — `class Foo(str, Enum)`.

### Асинхронность

- `AgentRuntime` и `SecureExecutor` используют `asyncio.create_subprocess_exec`.
- CLI оборачивает async-обработчики в `asyncio.run(...)`.
- В тестах активен `asyncio_mode = "auto"`.

---

## 7. Инструкции по тестированию

### Маркеры

В `pyproject.toml` зарегистрированы маркеры:

- `unit`: быстрые изолированные тесты.
- `integration`: интеграционные тесты, могут использовать БД/сервисы.

### Структура тестов

```
tests/
├── unit/
│   ├── test_event_engine.py
│   ├── test_models.py
│   ├── test_sandbox.py
│   ├── test_storage.py
│   └── test_task_generator.py
└── integration/
    └── test_full_workflow.py
```

### Что покрывают тесты

- `test_event_engine.py`: инициализация SQLite store, append/get, фильтрация по типу, порядок replay, project context, счётчики, JSONL backup.
- `test_models.py`: валидация Pydantic-моделей.
- `test_sandbox.py`: 5 уровней защиты `SecureExecutor` и `SubprocessBackend`.
- `test_storage.py`: atomic writes, frontmatter journal, rotation, JSONL append/load.
- `test_task_generator.py`: создание `TaskSpec`, запись `TASK.md` + `CONTEXT.json`, логирование `plan_created`.
- `test_full_workflow.py`: сквозной сценарий `EventEngine → TaskGenerator → AgentRuntime → SecureExecutor` с retry и блокировкой опасных команд.

---

## 8. Безопасность

### 5 уровней защиты SecureExecutor

1. **L1 — Dangerous Patterns:** regex-блокировка (`rm -rf /`, `eval(`, `sudo`, `curl | sh` и др.).
2. **L2 — Whitelist / Denylist:** неизвестные команды блокируются.
3. **L3 — Path Traversal:** каждый файловый аргумент резолвится и должен находиться внутри `project_root`.
4. **L4 — Network Guard:** флаги `http://`, `--url`, `--host` блокируются, если `allow_network=False`.
5. **L5 — Dangerous Tier:** команды `systemctl`, `ssh`, `rm`, `curl`, `wget` и т.п. требуют human approval (`approval_required=True`).

### Ролевая модель

- `PolicyEnforcer` предоставляет 6 встроенных ролей.
- Каждая роль имеет набор булевых флагов (`can_write_code`, `can_deploy`, `can_access_dangerous`, ...).
- Роли могут ограничивать пути (например, `developer` разрешён в `backend/`, `frontend/`, `tests/`, но запрещён в `ADR/`).

### Approval flow

- `ApprovalQueue` сохраняет запросы в `.voyage_approval_pending.json`.
- Поддерживаются `approve()`, `reject()` и `cleanup_expired()`.
- У запроса есть `ttl_hours` (по умолчанию 24 часа).

### Audit trail

- `AuditLogger` записывает timestamped JSONL-записи в `.voyage/audit.jsonl`.

---

## 9. Известные проблемы и важные замечания

### 1. Синтаксическая ошибка в `voyage_framework/specs/task_generator.py`

В строке ~86 не закрыта кавычка:

```python
default_instructions = [
    "Напиши код согласно критериям.",
    "Запусти mypy и pytest перед финализацией.
    "Не меняй файлы вне указанных relevant_files.",
]
```

Это приводит к `SyntaxError` при импорте модуля.

### 2. Неверный импорт в том же файле

```python
from voyage_framework.core.models import EventEngine, Event, EventType, TaskSpec, ProjectContext
```

`EventEngine` находится в `voyage_framework.core.event_engine`, а не в `voyage_framework.core.models`.

### 3. Дублирование проекта

`voyage_framework_v4_mvp/` — полная копия. При правках учитывайте, что та же ошибка существует и внутри копии. См. раздел 2.

### 5. Отсутствие корневого `.gitignore`

В корне нет `.gitignore`. Единственный `.gitignore` находится в `voyage_framework_v4_mvp/.gitignore`.

### 6. CI скрыт внутри копии

`.github/workflows/ci.yml` существует только в `voyage_framework_v4_mvp/.github/workflows/`.

### 7. Правила по умолчанию в `TaskGenerator`

`TaskGenerator.DEFAULT_RULES` требуют:

- async функции с type hints;
- использование `async_sessionmaker` и `AsyncSession`;
- отказ от `eval()`, `exec()`, `compile()` с user input;
- секреты через `pydantic-settings` + `.env`;
- каждая новая функция длиной >10 строк должна иметь >=1 тест.

---

## 10. CI/CD

### GitHub Actions

Файлы:

- `.github/workflows/ci.yml` — основной CI для корневого репозитория.
- `.github/workflows/release.yml` — релиз по git tag `v*`.

Триггеры CI:

- `push` в `main` или `develop`;
- `pull_request` в `main`.

Matrix: Python 3.11 и 3.12 на `ubuntu-latest` и `windows-latest`.

Шаги CI:

1. `pip install -e ".[dev]"`
2. `ruff check voyage_framework`
3. `mypy voyage_framework`
4. `pytest tests/ --cov=voyage_framework --cov-report=xml --cov-report=html`
5. Генерация `coverage.svg` и `coverage.json` через `coverage-badge`.
6. Автоматический commit badge-файлов в `main` при изменении.

Release pipeline собирает `dist/*`, публикует GitHub Release и (после настройки `PYPI_API_TOKEN`) может публиковать пакет в PyPI.

---

## 11. Связанные репозитории

Документация и архитектурные решения:

- [Framework-voyage-v2](https://github.com/AndreyVoyage/Framework-voyage-v2) — ADR, ROLE, TECH, TEST_STRATEGY

---

## 12. Быстрый старт для агента

```bash
# 1. Установка
pip install -e ".[dev]"

# 2. Линтеры
make lint

# 3. Тесты
make test

# 4. Инициализация проекта и проверка статуса
voyage init
voyage status
```

Если при запуске тестов или CLI возникают ошибки импорта, первым делом проверьте `voyage_framework/specs/task_generator.py` на синтаксическую ошибку и неверный импорт `EventEngine`.
