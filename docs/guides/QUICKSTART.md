# Quickstart

This quickstart creates one canonical task, adds its runtime record, builds generated context, and prepares a prompt package for manual use. Voyage v4.1 does not execute an AI agent or call an AI model.

Complete [`INSTALLATION.md`](INSTALLATION.md) first. The canonical architecture is [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md); AI-tool rules are in [`AGENTS.md`](../../AGENTS.md), and development rules are in [`PHASE_WORKFLOW_POLICY.md`](PHASE_WORKFLOW_POLICY.md).

## 1. Initialize a working project

After installing Voyage as a dependency or from an editable checkout:

```bash
mkdir my-project
cd my-project
```

PowerShell:

```powershell
New-Item -ItemType Directory my-project
Set-Location my-project
```

Voyage stores local runtime artifacts under the current project's `.voyage/` directory. Do not commit those artifacts unless the project explicitly requires it.

## 2. Create your first `task.yaml`

Git Bash, Linux, or macOS:

```bash
cat > task.yaml <<'YAML'
id: VF-001
title: My first task
description: Learn the canonical Voyage task and context workflow.
role: developer
mode: implement
priority: medium
status: pending
acceptance_criteria:
  - Install Voyage
  - Validate the task specification
  - Build project context
YAML
```

PowerShell users can create the same UTF-8 file in an editor or write these lines with `Set-Content`:

```powershell
$taskYaml = @(
    'id: VF-001'
    'title: My first task'
    'description: Learn the canonical Voyage task and context workflow.'
    'role: developer'
    'mode: implement'
    'priority: medium'
    'status: pending'
    'acceptance_criteria:'
    '  - Install Voyage'
    '  - Validate the task specification'
    '  - Build project context'
)
$taskYaml | Set-Content -Encoding utf8 task.yaml
```

`task.yaml` is canonical. A new task starts with `status: pending`, has an ID such as `VF-001`, uses a known role, and contains at least one acceptance criterion.

Validate it without creating runtime state:

```bash
python -c "from voyage_framework.core.task_parser import TaskParser; print(TaskParser().parse('task.yaml'))"
```

## 3. Add the task to runtime state

```bash
python -m voyage_framework.cli tasks create --file task.yaml
python -m voyage_framework.cli tasks show VF-001
```

This creates a `TaskRecord` in local SQLite. The record is canonical runtime state; it does not replace `task.yaml`.

## 4. Start the task

```bash
python -m voyage_framework.cli tasks start VF-001
python -m voyage_framework.cli tasks show VF-001
```

Use `tasks block`, `unblock`, `complete`, `fail`, and `archive` only for valid state transitions.

## 5. Build and compare context

```bash
python -m voyage_framework.cli sync build --file task.yaml --output CONTEXT.json
python -m voyage_framework.cli sync check --file task.yaml
python -m voyage_framework.cli sync status
```

`CONTEXT.json` is generated reference material. It can be rebuilt and must never be parsed back as canonical truth.

## 6. Generate a prompt package

```python
# Run manually from a Python session in the project directory.
from voyage_framework.core.prompt_generator import default_prompt_generator
from voyage_framework.core.task_parser import TaskParser

parser = TaskParser()
task = parser.parse("task.yaml")

generator = default_prompt_generator()
package = generator.generate(
    task=task,
    role_id="developer",
    mode_id="implementation",
)

print(package.system_prompt)
print(package.user_prompt)
```

The task specification uses `mode: implement`; the prompt catalog uses `mode_id="implementation"`. These are separate contracts. Generation is local and deterministic. Copy reviewed prompts manually to an external tool; Voyage sends nothing over the network.

## 7. List roles and prompt modes

```python
from voyage_framework.core.agent_registry import default_agent_registry
from voyage_framework.core.prompt_modes import default_mode_registry

roles = default_agent_registry()
print(roles.list_roles())

modes = default_mode_registry()
print(modes.list_modes())
```

The registries are read-only. Listing a role or mode does not activate an agent or workflow.

## 8. Review and finish

After an external tool returns a proposal:

1. inspect every changed file;
2. confirm it stayed within approved scope;
3. run tests and quality gates;
4. update runtime state through `voyage tasks`, not generated files;
5. let the human owner decide whether to commit, push, and merge.

Never include credentials or secrets in task context or prompt text.

## Where to go next

- [`USER_GUIDE.md`](USER_GUIDE.md) — concepts and safety;
- [`END_TO_END_WORKFLOW.md`](END_TO_END_WORKFLOW.md) — idea-to-audit workflow;
- [`ADAPTER_CONTRACT_USAGE.md`](ADAPTER_CONTRACT_USAGE.md) — external-tool contract payloads;
- [`PHASE_WORKFLOW_POLICY.md`](PHASE_WORKFLOW_POLICY.md) — branch, gate, Git authority, and audit process.
