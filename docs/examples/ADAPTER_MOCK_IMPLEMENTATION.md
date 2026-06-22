# Illustrative AdapterProtocol mock

> **Non-runnable documentation:** the code below is deliberately incomplete. It must not be copied into the package, imported, registered, or treated as a real adapter. It performs no filesystem, database, network, model, or task operation.

This sketch shows the shape of the six `AdapterProtocol` methods without runtime behavior. See [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md) and [`docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`](../reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md).

## Interface-shaped sketch

```python
# ILLUSTRATION ONLY — intentionally incomplete and non-runnable.
class IllustrativeAdapterShape(AdapterProtocol):
    def validate_request(self, request: AgentRequest) -> ValidationResult:
        ...  # A future boundary would return validation data only.

    def create_task(self, request: AgentRequest) -> AgentResponse:
        ...  # No TaskEngine call is shown or permitted here.

    def get_context(self, task_id: str) -> Mapping[str, Any]:
        ...  # No filesystem or database lookup is implemented.

    def request_prompt(
        self, task_id: str, role_id: str, mode_id: str
    ) -> PromptPackage:
        ...  # No model or provider is contacted.

    def submit_result(
        self, task_id: str, result: Mapping[str, Any]
    ) -> AgentResponse:
        ...  # No task state or EventEngine record is changed.

    def request_approval(self, task_id: str, action: str) -> AgentResponse:
        ...  # No approval service, callback, or timer is started.
```

The ellipses are documentation placeholders, not working method bodies. Imports, construction, persistence, dispatch, and an entry point are intentionally absent, so this cannot serve as a usable implementation.

## Conceptual verification

A future approved phase could test a real mock without external effects by checking that:

- all six abstract signatures are satisfied;
- `validate_request` returns consistent `ValidationResult` values;
- statuses are limited to `pending`, `approved`, `rejected`, and `completed`;
- request and response models remain immutable;
- approval-required actions remain pending until a simulated human decision;
- no file, database, audit, network, provider, or model boundary is touched.

These are test ideas only. This document adds no test module or executable fixture.

## Future replacement boundary

Replacing this sketch with a real adapter is outside Phase 8. It requires a new approved prompt defining ownership, canonical-state access, human approval semantics, failures, security, and `AdapterContract.version` compatibility. A future implementation must preserve the Phase 7 models and must not silently turn `AdapterProtocol` into an executor.

Voyage v4.1 does not run external agents, call AI models, or orchestrate their work. This example provides no provider client, credentials, CLI surface, or runtime execution.
