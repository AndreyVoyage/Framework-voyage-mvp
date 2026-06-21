# Phase 7 Final Audit and Merge — Self-Contained Execution Prompt

> **STOP-GATE:** Не менять код. Не добавлять новые фичи. Не начинать Phase 8.
> Задача — провести финальный аудит Phase 7 и, если всё чисто, подготовить merge в main.

---

## 0. Environment Verification

Сначала проверь, что ты в правильном проекте и ветке:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
```

Ожидаемо:

```text
/c/DEV/FRAMEWORK/Framework-voyage-mvp
```

Проверь ветку:

```bash
git branch --show-current
git status -sb
git log --oneline --decorate -8
```

Ожидаемо:

```text
refactor/v4.2-adapter-contract
## refactor/v4.2-adapter-contract...origin/refactor/v4.2-adapter-contract
57904da Phase 7: add Adapter Contract Draft
5319af7 docs: add Phase 7 adapter contract prompt
64b49fe (origin/main, origin/HEAD, main) Merge v4.1 process improvement audit
```

Если ветка не `refactor/v4.2-adapter-contract` или есть uncommitted changes — STOP и report.

---

## 1. Forbidden Keywords Audit

Выполни grep по всем файлам Phase 7:

```bash
git grep -nE "TaskEngine|EventEngine|langgraph|crewai|autogen|openai|anthropic|requests|httpx|subprocess|sqlite|webhook|credential|api_key|token|os\.\|Path\(\|open\(" HEAD -- voyage_framework/core/adapter_contract.py voyage_framework/core/adapter_protocols.py tests/unit/test_adapter_contract.py tests/unit/test_adapter_protocols.py
```

Если найдено что-то кроме docstring `AdapterProtocol` (который явно запрещает TaskEngine/EventEngine mutations), это **ошибка**.

Ожидаемый результат:

```text
HEAD:voyage_framework/core/adapter_protocols.py:18:    TaskEngine mutations, or EventEngine writes.
```

Только эта строка — docstring, который защищает, а не нарушает.

Если есть другие совпадения — STOP и report.

---

## 2. Test Gates

### 2.1 Targeted Phase 7 tests

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_adapter_contract.py tests/unit/test_adapter_protocols.py -v --basetemp=".pytest-tmp/adapter-final"
```

Ожидаемо: **36 passed** (0 failed, 0 error)

### 2.2 Full unit suite

```bash
.venv/Scripts/python.exe -m pytest tests/unit -q --basetemp=".pytest-tmp/unit-final"
```

Ожидаемо: **390 passed** (или больше, но не меньше)

### 2.3 Full suite (optional, если unit чистый)

```bash
.venv/Scripts/python.exe -m pytest tests/ -q --basetemp=".pytest-tmp/full-final"
```

Ожидаемо: все тесты проходят

---

## 3. Code Quality Gates

### 3.1 Ruff check

```bash
.venv/Scripts/python.exe -m ruff check voyage_framework tests
```

Ожидаемо: **All checks passed!**

### 3.2 Ruff format

```bash
.venv/Scripts/python.exe -m ruff format --check voyage_framework tests
```

Ожидаемо: **91 files already formatted** (или похожее число)

### 3.3 Mypy

```bash
.venv/Scripts/python.exe -m mypy voyage_framework
```

Ожидаемо: **Success: no issues found in N source files**

---

## 4. Git State Check

### 4.1 Diff статистика

```bash
git diff --stat
git diff --name-status
```

Ожидаемо только эти файлы:

```text
A	tests/unit/test_adapter_contract.py
A	tests/unit/test_adapter_protocols.py
M	voyage_framework/core/__init__.py
A	voyage_framework/core/adapter_contract.py
A	voyage_framework/core/adapter_protocols.py
```

### 4.2 Forbidden files не изменены

```bash
git diff -- AGENTS.md README.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md docs/reports/VOYAGE_V4_1_PROCESS_IMPROVEMENT_AUDIT.md voyage_framework/core/task_engine.py voyage_framework/core/task_parser.py voyage_framework/core/task_models.py voyage_framework/core/event_engine.py voyage_framework/core/context_builder.py voyage_framework/core/agent_registry.py voyage_framework/core/prompt_modes.py voyage_framework/core/prompt_generator.py voyage_framework/cli.py
```

Ожидаемо: **пустой вывод** (no diff for forbidden files)

### 4.3 Git diff --check

```bash
git diff --check
```

Ожидаемо: **no errors**

---

## 5. Pollution Check

```bash
git status --porcelain
git status --porcelain .voyage
find .voyage -maxdepth 2 -type f 2>/dev/null || true
```

Ожидаемо:

```text
- нет новых .voyage/tasks.db
- нет изменений в .voyage runtime files
- нет untracked project files (только .test-tmp-* ACL dirs acceptable)
```

---

## 6. Merge Readiness Check

Если ВСЕ проверки выше пройдены (tests, ruff, mypy, forbidden keywords, git diff), тогда:

### 6.1 Проверь, что origin ветка существует

```bash
git fetch origin
git branch -r | grep refactor/v4.2-adapter-contract
```

Если нет — push сначала:

```bash
git push origin refactor/v4.2-adapter-contract
```

Если push требует credentials и падает с `fatal: could not read Username for 'https://github.com'`, **не пытайся обойти**. Сообщи пользователю:

```text
Push требует credentials. Пользователь должен сделать вручную:
git push origin refactor/v4.2-adapter-contract
```

### 6.2 Если ветка уже на origin — подготовь merge

```bash
git switch main
git pull --ff-only origin main
```

Ожидаемо:

```text
Already up to date.
```

или fast-forward merge без конфликтов.

### 6.3 Сделай merge

```bash
git merge --no-ff refactor/v4.2-adapter-contract -m "Merge Phase 7 adapter contract draft

- AdapterContract: immutable interface contract for external AI agents
- AgentRequest / AgentResponse: immutable request/response models
- ValidationResult: immutable validation with error/warning tuples
- ApprovalFlow: immutable human-in-the-loop approval gate
- AdapterProtocol: abstract ABC defining adapter interface signatures
- Mapping instead of dict for read-only signal
- 36 tests (30 adapter_contract + 6 adapter_protocols)
- All models frozen, no filesystem, no database, no mutations
- No runtime execution, no AI model calls, no orchestration
- No CLI, no network clients, no credentials, no webhooks"
```

Если merge вызывает конфликт — STOP и report.

### 6.4 Проверь merge result

```bash
git log --oneline --decorate -5
```

Ожидаемо:

```text
XXXXXXX (HEAD -> main) Merge Phase 7 adapter contract draft
57904da (refactor/v4.2-adapter-contract) Phase 7: add Adapter Contract Draft
5319af7 docs: add Phase 7 adapter contract prompt
64b49fe (origin/main) Merge v4.1 process improvement audit
```

### 6.5 Push main

```bash
git push origin main
```

Если push требует credentials и падает — **не пытайся обойти**. Сообщи пользователю:

```text
Push main требует credentials. Пользователь должен сделать вручную:
git push origin main
```

---

## 7. Final Report Format

После выполнения ВСЕХ проверок (или после любой ошибки) верни отчёт:

```markdown
# Phase 7 Final Audit Report

## Environment
- branch: ...
- commit: ...
- origin sync: ...

## Forbidden Keywords Audit
- TaskEngine: found only in docstring / found elsewhere / not found
- EventEngine: found only in docstring / found elsewhere / not found
- langgraph: found / not found
- crewai: found / not found
- autogen: found / not found
- openai: found / not found
- requests: found / not found
- httpx: found / not found
- subprocess: found / not found
- sqlite: found / not found
- webhook: found / not found
- credential: found / not found
- Path/open: found / not found

## Test Results
- adapter tests: 36/36 passed
- unit suite: N/N passed
- full suite: N/N passed

## Quality Gates
- ruff check: passed / failed
- ruff format: passed / failed
- mypy: passed / failed
- git diff --check: passed / failed

## Git State
- changed files: only allowed / unexpected files found
- forbidden files diff: clean / dirty
- .voyage pollution: clean / dirty

## Merge Status
- pushed to origin: yes / no (credentials required)
- merged to main: yes / no
- merge conflicts: none / present

## Verdict
A. Ready — all checks passed, merge completed
B. Ready with warnings — minor issues, merge completed
C. Not ready — tests failed / forbidden keywords found / git dirty
D. Push required — user must run: git push origin refactor/v4.2-adapter-contract && git push origin main
```

---

## 8. Absolute Constraints

- Do NOT modify code during audit.
- Do NOT add new features.
- Do NOT start Phase 8.
- Do NOT push if credentials are required and unavailable.
- Do NOT create `.gitignore` changes to hide Windows ACL warnings.
- Do NOT modify forbidden files.
- Report failures honestly. Do not mask errors.
