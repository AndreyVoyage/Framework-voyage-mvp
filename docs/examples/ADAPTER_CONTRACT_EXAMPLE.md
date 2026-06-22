# Adapter Contract examples

> All snippets are static illustrations. They are not an executable program and do not start services, contact providers, execute agents, or mutate Voyage state.

These examples follow [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md) and the accepted Phase 7 boundary in [`docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`](../reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md).

## Requesting developer/implementation work

```python
# Illustration only.
from voyage_framework.core import AgentRequest

request = AgentRequest(
    request_id="example-request-1",
    agent_id="manual-external-tool",
    role_id="developer",
    mode_id="implementation",
    task_hint="Prepare a narrow, tested change proposal.",
    project_context={"task_id": "VF-800", "source": "canonical-derived"},
)
```

This constructs an immutable payload. It does not create a task or dispatch work.

## Interpreting a completed response

```python
# Illustration only. prepared_package represents a previously supplied value.
from voyage_framework.core import AgentResponse

response = AgentResponse(
    request_id="example-request-1",
    status="completed",
    task_id="VF-800",
    prompt_package=prepared_package,
    context_snapshot={"task_id": "VF-800", "status": "pending"},
    next_steps=("Transfer the package manually.", "Review the external result."),
)
```

The snapshot does not replace `task.yaml` or `TaskRecord`. A completed response says the contract interaction completed; it does not claim an external agent ran.

## Handling an approval-required action

```python
# Illustration only; no approval service or timeout worker exists here.
from voyage_framework.core import AgentResponse, ApprovalFlow

gate = ApprovalFlow(
    action="change_status",
    required=True,
    reason="Runtime state changes require human authorization.",
    timeout_hours=12,
)
pending = AgentResponse(
    request_id="example-request-2",
    status="pending",
    task_id="VF-800",
    next_steps=("Request a human decision.", "Do not change task state."),
)
```

On rejection, represent the outcome with `status="rejected"` and take no action. Timeout behavior belongs to a future separately approved boundary.

## Validation failure and recovery

```python
# Illustrative outcomes; no automatic retry occurs.
from voyage_framework.core import AgentRequest, ValidationResult

failure = ValidationResult(valid=False, errors=("Unknown mode: coding",))
corrected_request = AgentRequest(
    request_id="example-request-3",
    agent_id="manual-external-tool",
    role_id="developer",
    mode_id="implementation",
    task_hint="Use a registered mode.",
)
rechecked = ValidationResult(valid=True)
```

Recovery means constructing a new valid immutable payload, not mutating the rejected request.

## Full illustrative workflow

```python
# Static outline only; no protocol implementation is supplied.
contract = default_adapter_contract()       # inspect version and supported ids
request = AgentRequest(...)                 # construct an immutable payload
validation = ValidationResult(valid=True)   # represent validation outcome
approval = ApprovalFlow(...)                # describe a human gate if required
response = AgentResponse(...)               # represent the resulting payload
```

The conceptual sequence is: inspect `AdapterContract`, construct `AgentRequest`, represent validation, obtain a human decision when required, and interpret `AgentResponse`. `AdapterProtocol` defines signatures only. Voyage v4.1 performs none of these integration steps automatically. Any runtime behavior after Phase 8 requires a separate approved prompt.
