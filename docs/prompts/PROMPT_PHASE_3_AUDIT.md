# Phase 3 Post-Commit Audit — Voyage v4.1

> **STOP-GATE:** Не писать новый функционал. Не начинать Phase 4. Не менять код без отдельного разрешения.
> Задача — проверить, что commit Phase 3 действительно чистый и готов для следующей фазы.

---

## Контекст

- **Проект:** `C:\DEV\FRAMEWORK\Framework-voyage-mvp`
- **Ветка:** `refactor/v4.1-contract`
- **Последний commit:** `939ab8b Phase 3: add tasks CLI commands (voyage tasks) + 31 tests`
- **Предыдущая история:**
  - `939ab8b` Phase 3: add tasks CLI commands (voyage tasks) + 31 tests
  - `3eef381` docs: add Phase 3 implementation prompt
  - `e993d3d` Phase 2: TaskRecord + TaskEngine + tests (55 passing)
  - `8b731c2` Phase 1.5: stabilize TaskYamlSpec and test gates
  - `1908f07` Phase 1: TaskSpec + TaskParser + tests
  - `dbcf51f` Phase 0: VOYAGE V4.1 CONTRACT

---

## Цель аудита

Проверить:

1. Phase 3 запушена на origin.
2. Working tree clean.
3. Новые CLI-команды работают.
4. Старый CLI `voyage task <role> --task "..."` не сломан.
5. Tests не загрязняют реальный проект.
6. `.voyage/tasks.db` не создаётся при тестах.
7. Ruff exclusions не слишком широкие.
8. mypy / ruff / format проходят.
9. Full suite проходит.
10. Phase 3 можно считать завершённой.

---

## 1. Git state

Выполни:

```bash
git fetch origin
git status -sb
git status
git log --oneline --decorate -8
git branch --show-current
```

Ожидаемо:

```text
branch: refactor/v4.1-contract
working tree clean
HEAD == origin/refactor/v4.1-contract
latest commit: Phase 3: add tasks CLI commands
```

Если есть `ahead`, `behind`, untracked или modified files — остановиться и дать отчёт.

---

## 2. Inspect Phase 3 commit

Выполни:

```bash
git show --stat --oneline HEAD
git show --name-status HEAD
git show -- pyproject.toml
git show -- .gitignore
git show -- voyage_framework/cli.py
git show -- tests/unit/test_cli_tasks.py
```

Проверить:

- Нет случайных файлов.
- Нет изменений реального TASK.md / CONTEXT.json.
- Нет .voyage/tasks.db.
- Ruff exclusions не отключают весь `tests/` или весь `voyage_framework/`.
- `.pytest-tmp/` игнорируется.
- Runtime DB файлы `.voyage/*.db`, `.voyage/*.db-shm`, `.voyage/*.db-wal` игнорируются, если добавлены.

Особенно проверить, что в `pyproject.toml` **нет** опасного:

```toml
# ЗАПРЕЩЕНО:
extend-exclude = ["tests"]
extend-exclude = ["voyage_framework"]
extend-exclude = ["voyage_framework/cli.py"]
```

---

## 3. CLI architecture audit

Прочитать:

- `voyage_framework/cli.py`
- `voyage_framework/core/task_engine.py`
- `voyage_framework/core/task_parser.py`
- `voyage_framework/core/task_models.py`
- `tests/unit/test_cli_tasks.py`

Проверить:

1. Старый singular command `voyage task <role> --task "..."` всё ещё вызывает legacy `generate_task`.
2. Новый plural namespace `voyage tasks ...` реализован отдельным subparser.
3. Команды есть:
   - create
   - list
   - show
   - start
   - block
   - unblock
   - complete
   - fail
   - archive
4. Handler-функции возвращают `int` (0/1).
5. Handler-функции **не** вызывают `sys.exit()` внутри.
6. `_dispatch_tasks()` поддерживает dependency injection: `TaskEngine` может передаваться из тестов.
7. Tests не используют реальную `.voyage/tasks.db`.
8. Tests используют `tmp_path` / `monkeypatch.chdir(tmp_path)`.
9. Legacy CLI tests не пишут `TASK.md` / `CONTEXT.json` в реальный root.
10. TaskEngine / TaskParser бизнес-логика не была изменена ради CLI.

---

## 4. Manual CLI smoke tests in temp project

Создать task.yaml во временной папке. Команды запускать **из root проекта**, потому что текущий CLI по умолчанию использует `.voyage/tasks.db` в текущем проекте. Для manual smoke test это допустимо, если после проверки runtime DB удаляется и `git status` остаётся clean.

**Перед smoke test** очистить старую runtime DB и проверить, что проект чистый:

```bash
rm -f .voyage/tasks.db .voyage/tasks.db-shm .voyage/tasks.db-wal
git status --porcelain

mkdir -p .pytest-tmp/manual-cli-audit
```

Создать `task.yaml` через heredoc (из root проекта):

```bash
cat > .pytest-tmp/manual-cli-audit/task.yaml <<'YAML'
id: VF-001
title: Manual CLI Audit Task
description: Verify voyage tasks CLI manually
role: developer
acceptance_criteria:
  - CLI can create task
  - CLI can transition task
YAML
```

Проверить, что CLI модуль запускается:

```bash
.venv/Scripts/python.exe -m voyage_framework.cli --help
.venv/Scripts/python.exe -m voyage_framework.cli tasks --help
```

Запустить smoke test (все команды из root проекта):

```bash
.venv/Scripts/python.exe -m voyage_framework.cli tasks create --file .pytest-tmp/manual-cli-audit/task.yaml
.venv/Scripts/python.exe -m voyage_framework.cli tasks list
.venv/Scripts/python.exe -m voyage_framework.cli tasks show VF-001
.venv/Scripts/python.exe -m voyage_framework.cli tasks start VF-001
.venv/Scripts/python.exe -m voyage_framework.cli tasks block VF-001 --reason "audit check"
.venv/Scripts/python.exe -m voyage_framework.cli tasks unblock VF-001
.venv/Scripts/python.exe -m voyage_framework.cli tasks complete VF-001
.venv/Scripts/python.exe -m voyage_framework.cli tasks archive VF-001
```

Если smoke test создаёт `.voyage/tasks.db` в root проекта — это допустимо для ручного runtime smoke test, но после теста нужно удалить runtime DB и проверить, что Git clean:

```bash
rm -f .voyage/tasks.db .voyage/tasks.db-shm .voyage/tasks.db-wal
git status --porcelain
```

Если `.voyage/tasks.db` создаётся **во время unit tests** — это ошибка. Unit tests должны использовать injected `TaskEngine(tmp_path / "tasks.db")`.

---

## 5. Test gates

Использовать venv Python явно, с `--basetemp` для избежания Windows setup errors:

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_tasks.py -v --basetemp=".pytest-tmp/cli-audit"
.venv/Scripts/python.exe -m pytest tests/unit/test_task_parser.py -v --basetemp=".pytest-tmp/parser-audit"
.venv/Scripts/python.exe -m pytest tests/unit/test_task_engine.py -v --basetemp=".pytest-tmp/engine-audit"
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=".pytest-tmp/unit-audit"
.venv/Scripts/python.exe -m pytest tests/ -v --basetemp=".pytest-tmp/full-audit"
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/cli.py voyage_framework/core/task_engine.py voyage_framework/core/task_models.py
git diff --check
git status
```

Ожидаемо:

```text
test_cli_tasks.py: 31 passed
test_task_parser.py: 48 passed
test_task_engine.py: 55 passed
unit suite: passed
full suite: passed
ruff: passed
ruff format: passed
mypy selected targets: passed
git diff --check: passed
working tree clean
```

---

## 6. Pollution check

После **всех** тестов (unit + manual smoke test) выполнить:

```bash
git status --porcelain
git status --porcelain .voyage
find .voyage -maxdepth 2 -type f 2>/dev/null || true
```

Проверить:

- **Unit tests не создали** `.voyage/tasks.db` в реальном root.
- `TASK.md` не изменён.
- `CONTEXT.json` не изменён.
- Нет untracked runtime файлов.

Если manual smoke test создал runtime DB, удалить его:

```bash
rm -f .voyage/tasks.db .voyage/tasks.db-shm .voyage/tasks.db-wal
```

Потом снова:

```bash
git status --porcelain
```

Если после удаления runtime DB `working tree clean` — manual smoke test считается безопасным.

Если **unit tests** создали `.voyage/tasks.db` — **Phase 3 audit failed**. Unit tests обязаны использовать injected `TaskEngine(tmp_path / "tasks.db")`.

---

## 7. Final report

Вернуть отчёт:

```markdown
# Phase 3 Post-Commit Audit Report

## Git state
- branch:
- HEAD:
- origin sync:
- working tree:

## Commit review
- files changed:
- risky exclusions:
- unexpected files:

## CLI architecture
- singular `voyage task`: passed/failed
- plural `voyage tasks`: passed/failed
- dependency injection: passed/failed
- handler return codes: passed/failed
- no sys.exit inside handlers: passed/failed

## Test results
- test_cli_tasks.py:
- test_task_parser.py:
- test_task_engine.py:
- unit suite:
- full suite:
- ruff:
- ruff format:
- mypy:
- git diff --check:

## Pollution check
- .voyage/tasks.db:
- TASK.md:
- CONTEXT.json:
- untracked files:

## Findings
1.
2.
3.

## Verdict
A. Phase 3 accepted, ready for Phase 4
B. Phase 3 accepted with warnings
C. Phase 3 not accepted
```

**Do not commit or push anything.**

Если аудит даст **A** или честное **B без архитектурных проблем**, тогда следующим шагом будет промпт на **Phase 4**, но не раньше.
