---
layout: default
title: Frequently Asked Questions
---

# Frequently Asked Questions

## What is Voyage Framework?

AI-Native Engineering Operating System for solo developers.

## Which Python versions are supported?

Python 3.11 and 3.12.

## How do I run an agent?

Use `voyage run <role> --task "..." --plan "cmd1;cmd2"`.

## Can I run commands in Docker?

Yes, use `--backend docker` with `voyage run` or `voyage graph run`.

## What is Chronicler?

A module that records every development step for replay and tutorials.

## How do I generate a replay script?

Use `voyage chronicler replay <correlation_id>`.

## What is LangGraphRuntime?

A graph-based agent runtime with conditional edges and checkpointing.

## How is the documentation published?

GitHub Pages from the `docs/` directory via `.github/workflows/docs.yml`.

## Can I use Voyage without LangGraph?

Yes, a pure-Python `simple_graph` fallback is included.

## Where are events stored?

In SQLite `.voyage/events.db` and JSONL `.voyage/events.jsonl`.
