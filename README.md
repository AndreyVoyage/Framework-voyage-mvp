# Voyage Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

Voyage keeps development intent, task state, context, and audit history organized on the local machine. External AI tools may receive deterministic prompt packages through a manual handoff; Voyage does not call models or providers and does not execute agents.

## Project identity

The canonical architecture is defined by the v4.1 MVP contract. The v4.2 milestone adds an interface-only adapter contract for future external-tool integrations. References to v4.3 describe the current documentation direction, not a published release, tag, or runtime layer.

Voyage is:

- a local Project Knowledge OS and Development Memory System;
- a structured workflow around canonical `task.yaml` specifications;
- a local runtime record for task lifecycle state;
- an append-only audit trail;
- a deterministic context and prompt-packaging layer for manual external AI tool handoff.

Voyage is not:

- an AI Agent Framework or autonomous agent runtime;
- a runtime orchestration framework;
- a LangGraph, CrewAI, or AutoGen replacement;
- an automatic agent execution system;
- a model/provider execution layer;
- a hosted production deployment platform.

## Source of truth

```text
task.yaml      -> canonical task specification (TaskYamlSpec / TaskParser)
TaskRecord     -> canonical runtime task state (SQLite / TaskEngine)
EventEngine    -> append-only audit log

AgentRegistry   -> read-only role catalog
ModeRegistry    -> read-only mode catalog
ContextBuilder  -> context aggregation and comparison
PromptGenerator -> deterministic prompt package generation

TASK.md and CONTEXT.json -> generated artifacts, not canonical truth
```

Generated artifacts must not be parsed back as the authoritative project state.

## Canonical core

- **TaskParser** validates canonical `task.yaml` input.
- **TaskEngine** manages local `TaskRecord` lifecycle state in SQLite.
- **EventEngine** records append-only audit events; it is not a state controller.
- **ContextBuilder** assembles and compares development context.
- **AgentRegistry** and **ModeRegistry** expose deterministic read-only catalogs; they do not launch agents or activate modes.
- **PromptGenerator** produces deterministic prompt packages for external tools; it does not send or execute them.
- **Adapter contracts** define interfaces only. No provider client, network transport, credential storage, or adapter runtime is included.

## Installation and safe quickstart

Voyage requires Python 3.11 or newer.

```bash
pip install -e ".[dev]"
voyage --help
```

Create a canonical `task.yaml`, then use the task and context workflows:

```bash
voyage tasks create --file task.yaml
voyage tasks list
voyage sync build --file task.yaml --output CONTEXT.json
voyage sync check --file task.yaml
```

`CONTEXT.json` is a generated artifact. Review it and any generated prompt package before manually handing it to an external AI tool. Results return through the normal review and Git workflow; Voyage does not execute the external tool or automatically merge its output.

The singular legacy command `voyage task` generates `TASK.md` and `CONTEXT.json`; it does not replace canonical `task.yaml` or the `voyage tasks` runtime-state namespace.

## Legacy compatibility surfaces

The repository still contains historical or compatibility-oriented surfaces such as `voyage_framework/agents/`, `voyage_framework/langgraph_tools/`, and older CLI, Docker, sandbox, memory, improvement, and Chronicler material. Some may remain importable, tested, or visible through legacy commands including `voyage run` and `voyage graph`.

These surfaces are not the canonical v4.1/v4.2 core and must not be interpreted as Voyage's current identity or as a promise of runtime orchestration, model execution, or autonomous behavior. Their disposition requires a separate, explicitly approved cleanup phase. See the [Phase 12 legacy cleanup audit](docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md) and [Phase 13 controlled cleanup plan](docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md).

## Documentation

- [Architecture contract](docs/VOYAGE_V4_1_CONTRACT.md)
- [Agent operating guide](AGENTS.md)
- [User guide](docs/guides/USER_GUIDE.md)
- [Installation](docs/guides/INSTALLATION.md)
- [Quickstart](docs/guides/QUICKSTART.md)
- [End-to-end workflow](docs/guides/END_TO_END_WORKFLOW.md)
- [Adapter contract usage](docs/guides/ADAPTER_CONTRACT_USAGE.md)

## Development checks

Run checks from the repository root:

```bash
pytest tests/
ruff check .
ruff format --check voyage_framework tests
mypy voyage_framework
git diff --check
```

## License

MIT.
