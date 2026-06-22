# Adding User Authentication to the API — A Voyage demo

> **Static fictional scenario.** Reading these files does not create a task, write SQLite, append an event, execute an agent, call a model, contact a provider, or perform Git operations. All identities, timestamps, routes, files, and results are examples. No real credentials, secrets, tokens, IP addresses, or passwords are present.

This scenario follows a developer who wants to add JWT-based authentication to a fictional REST API. The developer uses Voyage Framework v4.1 to structure the task, track its imagined runtime lifecycle, prepare context, build a prompt package for manual transfer, review a fictional result, and understand an append-only audit trail.

The demo uses `VF-11001`, not the human-readable label `VF-DEMO-001`, because the current `TaskYamlSpec` requires `VF-` followed by digits. Its task mode is `implement`; the separate prompt mode is `implementation`.

## Artifact map

| File | Meaning | Canonical? |
|---|---|---|
| [`task.yaml`](task.yaml) | Valid fictional `TaskYamlSpec` | Yes, for demo task intent |
| [`CONTEXT.example.json`](CONTEXT.example.json) | Representative `ContextBuilder` output | No, generated example |
| [`TASK.example.md`](TASK.example.md) | Representative legacy task document | No, generated example |
| [`PROMPT_PACKAGE.example.md`](PROMPT_PACKAGE.example.md) | Representative `PromptPackage` | No, generated example |
| [`REVIEW_REPORT.example.md`](REVIEW_REPORT.example.md) | Fictional human review | No, review evidence |
| [`AUDIT_TRAIL.example.md`](AUDIT_TRAIL.example.md) | Illustrative append-only event history | No, not live output |

## The idea

A developer needs login, registration, protected-route enforcement, 24-hour token expiry, bcrypt password hashing, and basic rate limiting. Instead of starting from an informal chat message, the developer writes a canonical task specification with explicit scope and acceptance criteria.

## Step 1: write the task specification

The complete specification is [`task.yaml`](task.yaml):

```yaml
id: VF-11001
title: Add User Authentication to the API
description: Implement JWT-based authentication for the REST API endpoints.
role: developer
priority: high
mode: implement
status: pending
acceptance_criteria:
  - POST /auth/login returns a JWT for valid demo credentials
  - POST /auth/register creates a user with a bcrypt-hashed password
  - GET /api/protected returns 401 without a valid token
  - Tokens expire after 24 hours
  - Passwords use bcrypt with cost factor 12
  - Authentication endpoints are limited to 5 requests per minute
```

- `id` follows the current task identifier contract.
- `role` identifies the task owner profile.
- `mode: implement` is a valid task-specification mode.
- `status: pending` is required for a newly parsed task.
- `acceptance_criteria` makes review observable.
- `files`, `tests`, and `metadata` in the full file narrow scope and mark the data fictional.

No generated `TASK.example.md` or `CONTEXT.example.json` is parsed back into this specification.

## Step 2: represent creation in runtime state

In a real workflow, the user would deliberately invoke `voyage tasks create --file task.yaml`. This demo does not run that command. The resulting `TaskRecord` would look like this after creation:

```json
{
  "id": "VF-11001",
  "title": "Add User Authentication to the API",
  "description": "Implement JWT-based authentication for the REST API endpoints.",
  "role": "developer",
  "status": "pending",
  "priority": "high",
  "mode": "implement",
  "source_path": "docs/examples/e2e-demo/task.yaml",
  "created_at": "2026-06-21T14:00:00+00:00",
  "updated_at": "2026-06-21T14:00:00+00:00",
  "started_at": null,
  "completed_at": null,
  "archived_at": null,
  "metadata": {
    "scenario": "static-e2e-demo",
    "data_classification": "fictional-no-secrets"
  },
  "acceptance_criteria": [
    "POST /auth/login returns a JWT for valid demo credentials",
    "POST /auth/register creates a user with a bcrypt-hashed password",
    "GET /api/protected returns 401 without a valid token",
    "Tokens expire after 24 hours",
    "Passwords use bcrypt with cost factor 12",
    "Authentication endpoints are limited to 5 requests per minute"
  ]
}
```

`pending` means the task exists in runtime state but work has not started. This JSON is narrative display, not a database row created by Phase 11.

## Step 3: represent starting the task

A real owner could use `voyage tasks start VF-11001`. The imagined valid transition is `pending → in_progress`:

```json
{
  "id": "VF-11001",
  "title": "Add User Authentication to the API",
  "description": "Implement JWT-based authentication for the REST API endpoints.",
  "role": "developer",
  "status": "in_progress",
  "priority": "high",
  "mode": "implement",
  "source_path": "docs/examples/e2e-demo/task.yaml",
  "created_at": "2026-06-21T14:00:00+00:00",
  "updated_at": "2026-06-21T14:05:00+00:00",
  "started_at": "2026-06-21T14:05:00+00:00",
  "completed_at": null,
  "archived_at": null,
  "metadata": {
    "scenario": "static-e2e-demo",
    "data_classification": "fictional-no-secrets"
  },
  "acceptance_criteria": [
    "POST /auth/login returns a JWT for valid demo credentials",
    "POST /auth/register creates a user with a bcrypt-hashed password",
    "GET /api/protected returns 401 without a valid token",
    "Tokens expire after 24 hours",
    "Passwords use bcrypt with cost factor 12",
    "Authentication endpoints are limited to 5 requests per minute"
  ]
}
```

The complete record preserves specification-derived fields while updating runtime status and timestamps. Only `TaskEngine` is the normal runtime state mutator; the demo does not instantiate it.

## Step 4: build context

At `14:10Z`, the fictional user builds context from the task specification, runtime record, and available event summary. The full representative output is [`CONTEXT.example.json`](CONTEXT.example.json).

The output keeps both `spec_status: pending` and `runtime_status: in_progress`, making the source-of-truth distinction visible. Its two summarized events are the task creation and start events that existed at sync time. `last_sync` is a snapshot timestamp, not canonical state.

`CONTEXT.example.json` is generated reference material. It may be deleted and rebuilt and must not be treated as task or runtime truth.

## Step 5: generate the prompt package

The developer selects the `developer` role and the `implementation` prompt mode. [`PROMPT_PACKAGE.example.md`](PROMPT_PACKAGE.example.md) shows the resulting role boundaries, instructions, task description, acceptance criteria, files, tests, and safety reminders.

The package is copied manually into Codex, Claude, Gemini, or another external tool. Voyage generates text only: it does not send the package, authenticate with a provider, execute the tool, or receive a response automatically.

## Step 6: external tool work

The following fictional response is manually returned by an external tool:

```text
Proposed result:
- Add login and registration route handlers.
- Add JWT issue/verify helpers with an injected signing configuration.
- Add protected-route middleware.
- Add bcrypt cost-factor checks and basic rate-limit tests.
- Report six focused tests passing.
```

A compact illustrative diff summary follows. It is not a patch and cannot be applied:

```diff
+ src/auth/jwt_handler.py: issue and verify expiring JWTs through injected configuration
+ src/api/routes.py: add /auth/login, /auth/register, and protected middleware
+ tests/test_auth.py: add login, registration, expiry, bcrypt, 401, and rate-limit cases
```

No signing value or user password is shown. A fictional identity, if needed by a test description, is `demo-user@example.invalid`; it is not a real account.

## Step 7: review and approval

The human reads the proposed diff, checks file scope, and compares each criterion with evidence. [`REVIEW_REPORT.example.md`](REVIEW_REPORT.example.md) records five passes and one partial result: basic rate limiting works, but burst protection lacks a dedicated test.

The human chooses **Approved with a minor follow-up** and records `VF-11002` as fictional follow-up work. Voyage does not make this decision. A different project could keep the original task open until the partial item is resolved.

## Step 8: represent completion

After the fictional approval, a real owner could invoke `voyage tasks complete VF-11001`. The final imagined `TaskRecord` state is:

```json
{
  "id": "VF-11001",
  "title": "Add User Authentication to the API",
  "description": "Implement JWT-based authentication for the REST API endpoints.",
  "role": "developer",
  "status": "completed",
  "priority": "high",
  "mode": "implement",
  "source_path": "docs/examples/e2e-demo/task.yaml",
  "created_at": "2026-06-21T14:00:00+00:00",
  "updated_at": "2026-06-21T15:00:00+00:00",
  "started_at": "2026-06-21T14:05:00+00:00",
  "completed_at": "2026-06-21T15:00:00+00:00",
  "archived_at": null,
  "metadata": {
    "scenario": "static-e2e-demo",
    "data_classification": "fictional-no-secrets"
  },
  "acceptance_criteria": [
    "POST /auth/login returns a JWT for valid demo credentials",
    "POST /auth/register creates a user with a bcrypt-hashed password",
    "GET /api/protected returns 401 without a valid token",
    "Tokens expire after 24 hours",
    "Passwords use bcrypt with cost factor 12",
    "Authentication endpoints are limited to 5 requests per minute"
  ]
}
```

Again, this is documentation, not a mutation performed by the demo.

## Step 9: inspect the audit trail

[`AUDIT_TRAIL.example.md`](AUDIT_TRAIL.example.md) presents eight append-only fictional records. It distinguishes normal task lifecycle event types from narrative `process_step` rows. Earlier rows never change when later decisions occur.

An audit record documents an occurrence; it does not control `TaskRecord`. `EventEngine` is append-only, while `TaskEngine` owns task status transitions. No event was written while creating this scenario.

## Summary

The scenario produced seven static files:

1. one valid canonical demo `task.yaml`;
2. three explicitly non-canonical generated examples;
3. one review report;
4. one illustrative audit trail;
5. this narrative.

It produced no Python code, database, real task, network request, provider integration, model call, agent execution, credential, secret, token, commit, or push.

To adapt the scenario, copy the structure rather than its fictional data: choose a valid numeric task ID, write project-specific acceptance criteria and file scope, build context locally, review the prompt package before manual transfer, require human approval, and preserve the distinction between canonical state and generated artifacts.
