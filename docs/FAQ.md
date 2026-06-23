---
layout: default
title: Frequently Asked Questions
---

# Frequently Asked Questions

## What is Voyage Framework?

Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

Voyage does not execute agents, call AI models or providers, or orchestrate workflows. External AI tools receive deterministic prompt packages through a manual handoff.

## Which Python versions are supported?

Python 3.11 and 3.12.

## How do I run an agent?

Voyage v4.1/v4.2 does not run agents. The older `voyage run <role>` command is a legacy v4.0 compatibility surface and is not part of the canonical current workflow. Use the canonical task and context workflows instead:

```bash
voyage tasks create --file task.yaml
voyage sync build --file task.yaml --output CONTEXT.json
```

## Can I run commands in Docker?

The Docker backend was part of the legacy v4.0 `voyage run` sandbox. It is not a canonical v4.1/v4.2 capability and remains only as a historical compatibility surface.

## What is Chronicler?

A module that records development process steps for replay and documentation generation. It does not execute agents or models.

## How do I generate a replay script?

Use `voyage chronicler replay <correlation_id>`. This produces a bash replay script from recorded process steps; it does not execute the script automatically.

## What is LangGraphRuntime?

A historical v4.0 graph-based runtime module. It is **not** part of the canonical v4.1/v4.2 core. Voyage does not use LangGraph as its runtime and is not a replacement for LangGraph, CrewAI, or AutoGen.

## How is the documentation published?

GitHub Pages from the `docs/` directory via `.github/workflows/docs.yml`.

## Can I use Voyage without LangGraph?

Yes. LangGraph is not a dependency of the canonical v4.1/v4.2 core. The repository retains a legacy v4.0 `langgraph_tools` module and a pure-Python fallback, but these are historical compatibility surfaces, not current architecture.

## Where are events stored?

In SQLite `.voyage/events.db` and JSONL `.voyage/events.jsonl`.
