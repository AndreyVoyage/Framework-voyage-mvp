# End-to-end workflow

This guide follows one task from an idea to closure. Voyage supplies structured local memory and generated prompt material. Voyage v4.1 does not execute external agents, call AI models, orchestrate work, push branches, or merge changes.

Follow [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md), [`AGENTS.md`](../../AGENTS.md), and [`PHASE_WORKFLOW_POLICY.md`](PHASE_WORKFLOW_POLICY.md).

## 1. Idea → `task.yaml`

Turn the idea into a narrow task with acceptance criteria and file scope:

```yaml
id: VF-010
title: Document configuration validation
description: Explain how invalid configuration is reported to a user.
role: developer
mode: implement
priority: medium
status: pending
acceptance_criteria:
  - The supported configuration fields are documented
  - Invalid input behavior is explained
files:
  read:
    - voyage_framework/core/config.py
  modify:
    - docs/guides/CONFIGURATION.md
tests:
  - python -m pytest tests/unit/test_config.py -v
```

Validate it before creating runtime state:

```bash
python -c "from voyage_framework.core.task_parser import TaskParser; TaskParser().parse('task.yaml'); print('valid')"
```

`task.yaml` is canonical task intent. Generated Markdown and JSON do not replace it.

## 2. `task.yaml` → `TaskRecord`

```bash
voyage tasks create --file task.yaml
voyage tasks show VF-010
voyage tasks start VF-010
```

`TaskRecord` in SQLite is canonical runtime state. Use supported `voyage tasks` transitions; do not edit the database directly.

## 3. `TaskRecord` → context

```bash
voyage sync build --file task.yaml --output CONTEXT.json
voyage sync check --file task.yaml
voyage sync status
```

`CONTEXT.json` is generated and replaceable. If it differs from canonical sources, fix the source or rebuild it; do not use the JSON as authoritative input.

## 4. Context → `PromptPackage`

```python
from voyage_framework.core.prompt_generator import default_prompt_generator
from voyage_framework.core.task_parser import TaskParser

spec = TaskParser().parse("task.yaml")
package = default_prompt_generator().generate(
    task=spec,
    role_id="developer",
    mode_id="implementation",
    project_context={"review_required": True},
)

print(package.system_prompt)
print(package.user_prompt)
print(package.checklist)
```

Review the package for scope, secrets, and stale information. Copy it manually to Codex, Claude, Gemini, or another external tool. Prompt generation contacts no provider.

## 5. External tool → proposed result

The external tool works outside Voyage and returns suggested code, documentation, or a patch. The human or authorized development agent must:

1. inspect `git status --short` and the complete diff;
2. reject files outside the approved list;
3. verify generated artifacts were not used as canonical truth;
4. run targeted tests;
5. run broader gates in proportion to risk.

Typical code-phase checks are:

```bash
python -m pytest tests/unit -v --basetemp=.pytest-tmp/vf-010-unit
python -m ruff check .
python -m ruff format --check .
python -m mypy voyage_framework
git diff --check
git status --short
```

For documentation-only work, use the content, link, whitespace, scope, and forbidden-file gates in its prompt. Voyage implements no automated retry loop.

## 6. Result → runtime completion and merge

After acceptance criteria and gates pass:

```bash
voyage tasks complete VF-010
voyage tasks show VF-010
```

Commit only explicitly reviewed files:

```bash
git add docs/guides/CONFIGURATION.md
git commit -m "docs: explain configuration validation"
```

Never use `git add .` in a scoped phase. Under the Git authority policy, the human owner publishes remotely:

```bash
git push origin <branch>
```

The owner reviews and merges the pull request. Tag only under an explicitly approved release prompt:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

Do not expose or work around Git credentials. Passing local gates does not itself authorize a commit, push, merge, or tag.

## 7. Audit → closure

After merge:

1. run the required full test suite on merged state;
2. verify `git status -sb` is clean;
3. inspect merge and tag history;
4. confirm forbidden files and runtime artifacts are clean;
5. write a closure audit only when an approved prompt permits it;
6. record exact results, deviations, and residual risks.

```bash
python -m pytest tests/ -q --basetemp=.pytest-tmp/vf-010-full
git diff --check
git status -sb
git log --oneline --decorate -10
```

## Safety checkpoints

At every step:

- never modify forbidden files without explicit approval;
- never parse `TASK.md` or `CONTEXT.json` as canonical truth;
- never add agent runtime or model invocation without a separately approved phase;
- never store credentials in code, task files, prompts, context, or logs;
- never confuse `EventEngine` audit entries with `TaskEngine` transitions;
- stop and report unexpected branch, scope, tests, or repository state.

```text
idea → task.yaml → TaskRecord → context → PromptPackage
     → manual external-tool work → proposed result → human review
     → tests and gates → authorized merge → closure audit
```
