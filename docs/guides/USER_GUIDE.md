# Voyage Framework v4.1 user guide

Voyage Framework v4.1 is a local **Development Memory System / Project Knowledge Operating System**. It keeps task specifications, runtime task state, audit history, context, role/mode catalogs, and prompt packages organized around a software project.

Voyage v4.1 is **not an AI Agent Framework**. It does not execute external agents, call AI models, orchestrate workflows, or store provider credentials. Legacy modules may remain in the repository, but they are outside the v4.1 MVP core.

For authoritative architecture, read [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md). AI contributors must follow [`AGENTS.md`](../../AGENTS.md). Development phases follow [`PHASE_WORKFLOW_POLICY.md`](PHASE_WORKFLOW_POLICY.md).

## What Voyage does

Voyage provides:

- canonical task specifications in `task.yaml`;
- runtime task tracking through `TaskRecord` and SQLite;
- append-only audit records through `EventEngine`;
- context aggregation and comparison through `ContextBuilder`;
- read-only catalogs of roles and modes;
- deterministic prompt packages for manual use with external tools;
- CLI workflows for task state and context synchronization.

It does not decide what code to write, run an AI assistant, send a prompt to a provider, review a result for you, or merge changes automatically.

## Who it is for

Voyage is useful for:

- solo developers maintaining context across complex or long-running projects;
- teams that use assistants such as Codex, Claude, or Gemini but want project state to remain local and explicit;
- contributors who need structured task tracking, reproducible context, and an audit trail.

## Core concepts

### `task.yaml`: canonical task specification

`task.yaml` describes the intended work: identity, title, description, role, acceptance criteria, and optional priority, mode, files, tests, and metadata. It is immutable input after parsing and remains the source of truth for task intent.

### `TaskRecord`: canonical runtime task state

When a task is created through `voyage tasks create`, `TaskEngine` stores a mutable `TaskRecord` in SQLite. It tracks status and timestamps. Runtime transitions belong to `TaskEngine`; editing generated documents does not change this state.

### `EventEngine`: append-only audit log

`EventEngine` records events. It is an audit log, not a state controller. Task state must not be reconstructed by treating an event write as a status mutation.

### `ContextBuilder`: context aggregation

`ContextBuilder` compares canonical task specifications with runtime records and builds reference context. Generated `CONTEXT.json` is disposable output and is never canonical truth.

### `AgentRegistry` and `ModeRegistry`: read-only catalogs

`AgentRegistry` exposes six role profiles: `architect`, `developer`, `reviewer`, `qa`, `security`, and `devops`. `ModeRegistry` exposes six prompt modes: `analysis`, `implementation`, `review`, `qa`, `security`, and `handoff`. Catalog lookup does not activate or run anything.

A `task.yaml` task mode belongs to the task specification contract and is distinct from a `ModeRegistry` prompt mode. For example, a task may use `mode: implement`, while prompt generation uses `mode_id="implementation"`.

### `PromptGenerator`: deterministic prompt packages

`PromptGenerator` combines a parsed task, a registered role, a prompt mode, and optional project context into a `PromptPackage`. The package contains system and user prompt text for manual transfer to an external AI tool. Generating it makes no model or network call.

## Architecture at a glance

```text
idea
  → task.yaml (canonical specification)
  → TaskParser
  → TaskRecord in SQLite (canonical runtime state)
  → ContextBuilder → CONTEXT.json (generated reference)
  → PromptGenerator → PromptPackage (generated reference)
  → manual transfer to an external tool
  → human review and normal development workflow
```

`TASK.md` and `CONTEXT.json` are generated artifacts. Never parse them back as canonical task or runtime state.

## Common CLI workflows

Use `voyage tasks` for runtime task management:

```bash
voyage tasks create --file task.yaml
voyage tasks list
voyage tasks show VF-001
voyage tasks start VF-001
voyage tasks complete VF-001
```

Use `voyage sync` for context workflows:

```bash
voyage sync build --file task.yaml --output CONTEXT.json
voyage sync check --file task.yaml
voyage sync status
```

The singular `voyage task` command is a legacy generator for `TASK.md` and `CONTEXT.json`; it does not replace canonical `task.yaml`.

## Safe use with an external AI tool

1. Write and validate `task.yaml`.
2. Create and start the runtime task when runtime tracking is wanted.
3. Build context and generate a prompt package locally.
4. Review the package for secrets and scope.
5. Copy the prompt manually into the external tool.
6. Let the external tool propose changes within the approved file scope.
7. Review the complete diff and run tests and quality gates.
8. Commit, push, merge, and audit only under the project's Git authority rules.

Voyage does not perform steps 5–8 automatically. Never place credentials, access tokens, or private secrets in a prompt package.

## Safety boundaries

- Do not modify forbidden files without an approved phase prompt.
- Do not treat generated artifacts as sources of truth.
- Do not add runtime execution or orchestration under the adapter contract.
- Do not store credentials in code, task files, prompts, or logs.
- Do not push or merge merely because an automated report says a gate passed; human review remains required.

Continue with [`INSTALLATION.md`](INSTALLATION.md), [`QUICKSTART.md`](QUICKSTART.md), and [`END_TO_END_WORKFLOW.md`](END_TO_END_WORKFLOW.md). Adapter payloads are documented in [`ADAPTER_CONTRACT_USAGE.md`](ADAPTER_CONTRACT_USAGE.md).
