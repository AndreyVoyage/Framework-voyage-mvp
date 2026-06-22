# Adapter Contract usage guide

> Documentation only. Every snippet is illustrative; none is an executable adapter, provider client, or integration.

The Phase 7 Adapter Contract is a versioned interface for exchanging request, response, validation, and approval payloads with external tools. Voyage v4.1 does not execute agents, call AI models, or orchestrate workflows. The architectural source of truth is [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md); Phase 7 acceptance is recorded in [`docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`](../reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md).

## Contract, roles, and modes

`default_adapter_contract()` returns immutable `AdapterContract` version `v4.1.0`. Supported roles are `architect`, `developer`, `reviewer`, `qa`, `security`, and `devops`. Supported modes are `analysis`, `implementation`, `review`, `qa`, `security`, and `handoff`.

The default task and prompt limits are 10,000 and 15,000 characters. `approval_required_for` contains `mutate_task`, `delete_task`, `change_status`, and `deploy`. These values describe a boundary; they perform no action.

## Constructing AgentRequest

Required fields are non-empty `request_id` and `agent_id`, plus known `role_id` and `mode_id`. Optional fields are `task_hint` and `project_context`. Unknown fields are rejected. The frozen model validates role and mode through the read-only registries.

```python
# Illustration only; this does not submit or execute anything.
from voyage_framework.core import AgentRequest

request = AgentRequest(
    request_id="request-008",
    agent_id="external-tool-example",
    role_id="developer",
    mode_id="implementation",
    task_hint="Document the adapter boundary.",
    project_context={"repository": "voyage", "phase": 8},
)
```

Construction validates a payload. It does not create `TaskRecord`, modify `task.yaml`, or write an event.

## Interpreting AgentResponse

`AgentResponse.status` is one of:

- `pending`: processing or a human decision remains outstanding;
- `approved`: the requested boundary action was approved;
- `rejected`: the request or approval was declined;
- `completed`: the contract interaction has a completed result.

`task_id` identifies an associated task when present. `prompt_package` may contain a read-only `PromptPackage` prepared for manual transfer. `context_snapshot` is canonical-derived reference data, not canonical state. `next_steps` is an ordered tuple for the caller. The response is a payload, not runtime task state.

## Human approval with ApprovalFlow

`ApprovalFlow` records an action, whether human approval is required, an optional reason, and a positive `timeout_hours`.

```python
# Illustration only; no timer or approval service is started.
from voyage_framework.core import ApprovalFlow

approval = ApprovalFlow(
    action="change_status",
    required=True,
    reason="A human must authorize the state transition.",
    timeout_hours=24,
)
```

A future approved integration should keep the request `pending` while a decision is outstanding. On timeout it should report an explicit timeout outcome at its own boundary; the model runs no timer. On rejection it should return a `rejected` response and perform no action.

## ValidationResult

A valid result must have an empty `errors` tuple. An invalid result must contain at least one error. `warnings` may accompany either result and represent non-blocking concerns.

```python
# Illustrative payloads only.
from voyage_framework.core import ValidationResult

accepted = ValidationResult(valid=True, warnings=("Optional context omitted.",))
rejected = ValidationResult(valid=False, errors=("Unknown role: operator",))
```

On `valid=False`, correct the reported data and construct a new immutable request. Warnings do not make an otherwise valid result invalid.

## Version compatibility

Consumers should compare `AdapterContract.version` before exchanging payloads. This guide documents `v4.1.0`; unchanged class names do not guarantee future compatibility. A future version needs an approved phase and explicit compatibility rules. Runtime execution after Phase 8, if ever approved, requires its own explicit prompt and is outside this contract.
