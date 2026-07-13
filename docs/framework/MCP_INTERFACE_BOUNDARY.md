# MCP Interface Boundary

## Key phrases

> MCP may observe, validate, explain and propose; it may never authorize or apply authoritative state changes.

> Read-only access is still policy-controlled, provenance-aware, and subject to redaction.

## Context

Voyage already has an established core and trust model:

- project memory, context and decision records;
- TaskEngine and EventEngine;
- ContextBuilder and Chronicler;
- report-state and validate-report;
- evidence-oriented validation;
- guarded writes and human approval gates;
- audit trail;
- adapter/interface ownership under D-009;
- risk-based adaptive control under D-012;
- ADR-0001 boundary: Voyage is not an agent runtime.

MCP is therefore not a replacement architecture and does not restart Voyage development from zero. It is an additional standard interface facade over existing capabilities.

The purpose of D-014 is to define the trust boundary before any MCP code, tool schema, transport or pilot integration is planned.

## Decision

Voyage may be exposed as an MCP server through a restricted interface facade beside the CLI.

MCP is:

- an interface and adapter layer;
- additive to the existing CLI;
- a standard way for compatible clients to query selected Voyage capabilities;
- subordinate to the existing Voyage trust, evidence and gate model.

MCP is not:

- the Voyage core;
- a workflow runtime;
- an agent runtime;
- an autonomous control plane;
- a replacement for the CLI;
- a replacement for human authorization;
- a general Git or filesystem execution gateway;
- a reason to rewrite existing deterministic adapters.

D-014 is an interface-boundary decision only. It does not authorize MCP implementation.

## Architectural position

```text
Voyage Core
├── Memory / Context / Decisions
├── TaskEngine / EventEngine
├── Validation / Evidence
├── Trust / Gates / Policy
├── Audit Trail
└── Interfaces
    ├── CLI
    ├── MCP read / validate / explain / propose facade
    └── Human-controlled authorize / apply path
```

The MCP facade must use stable application services exposed by the existing core. It must not bypass those services or directly mutate authoritative storage.

## Voyage as MCP server

The primary supported role is:

```text
Voyage-as-MCP-server: YES
```

A compatible external client may call explicitly published Voyage capabilities such as project status, report validation, decision trace and context construction.

The currently rejected role is:

```text
Voyage-as-general-MCP-client: NO
```

Voyage must not replace existing Git, filesystem, SQLite or local validation adapters with external MCP servers merely for protocol uniformity.

Existing deterministic adapters remain authoritative where they already provide stronger control, reproducibility and testability.

A future, separately approved ingestion adapter may consume external MCP data only as untrusted evidence. Such data must pass normalization, provenance and validation before it can influence Voyage knowledge. It must never write directly into authoritative state.

## Operation classes

MCP-visible capabilities are classified into six operation classes.

### READ

Reads authoritative or derived project information without changing authoritative state.

Examples:

- `project_status`
- `report_state`
- `get_task`
- `list_tasks`
- `get_decision`
- `list_required_evidence`
- `build_context`
- `search_knowledge`

READ is permitted only through capability-scoped tools. Generic file or path reading is forbidden.

### VALIDATE

Runs deterministic, policy-controlled validation against existing state and evidence.

Examples:

- `validate_report`
- `check_gate_evidence`
- `validate_context_sources`
- `check_source_consistency`

VALIDATE may execute only existing read-only allowlisted operations. It may not apply fixes or transition state.

### EXPLAIN

Explains existing evidence, decisions, gate failures or provenance.

Examples:

- `trace_decision`
- `explain_gate_failure`
- `explain_source_precedence`
- `explain_validation_result`

EXPLAIN does not authorize action and must distinguish facts from derived interpretation.

### PROPOSE

Creates a non-authoritative recommendation or draft for later human review.

Examples, in a later phase only:

- `propose_task`
- `propose_task_update`
- `propose_next_task`
- `propose_decision`
- `propose_gate_transition`

PROPOSE is a write operation, but only to a separate non-authoritative proposal store. It must not mutate project state, task status, gate state, decision registry, approved artifacts, active phase or repository content.

### AUTHORIZE

Grants permission for an authoritative action.

Examples:

- approve a gate;
- authorize a phase transition;
- approve a proposal;
- authorize a guarded write;
- authorize deploy, commit, merge or rollback.

AUTHORIZE is forbidden as an autonomous MCP operation.

### APPLY

Performs authoritative mutation or external side effects.

Examples:

- apply a proposal;
- update authoritative task status;
- transition a phase;
- write project files;
- commit or merge;
- deploy;
- delete;
- rollback;
- mutate approved records.

APPLY is forbidden as an autonomous MCP operation.

## Binding allow / deny boundary

Allowed through the MCP facade:

```text
READ
VALIDATE
EXPLAIN
PROPOSE — only in a later, separately approved restricted phase
```

Forbidden as autonomous LLM-callable MCP tools:

```text
AUTHORIZE
APPROVE
APPLY
DEPLOY
COMMIT
MERGE
DELETE
ROLLBACK
PHASE TRANSITION
AUTHORITATIVE STATUS MUTATION
ARBITRARY FILE WRITE
ARBITRARY COMMAND EXECUTION
```

A human-controlled channel outside the autonomous MCP tool set is required for every authoritative authorization or application.

## Evidence completeness is not authorization

Gate evidence and human authorization are separate concepts.

Do not return ambiguous results such as:

```json
{
  "ready": true
}
```

Use explicit semantics:

```json
{
  "evidence_complete": true,
  "authorization": "human_required"
}
```

`evidence_complete` means only that the required evidence appears complete under the current validator. It does not permit a phase transition, deployment, mutation or guarded write.

## Structural enforcement

The trust boundary must be enforced structurally, not only by tool descriptions or policy prose.

The MCP adapter may depend on:

- `ReadService`;
- `ValidationService`;
- `ExplanationService`;
- a later restricted `ProposalService`.

The MCP adapter must not import or receive direct references to:

- `ApprovalService`;
- `ApplyService`;
- `GuardedWriteService`;
- `PhaseTransitionService`;
- deployment services;
- commit or merge services;
- rollback services;
- arbitrary command executors.

An architecture-boundary test must verify forbidden imports and dependencies.

The target architecture is a separate MCP process that physically does not contain authoritative apply and approval services.

An initial in-process implementation may be considered only if:

- MCP is isolated in a separate package;
- forbidden dependencies are enforced by boundary tests;
- only approved read and validation interfaces are injected;
- the implementation plan explicitly preserves later extraction to a separate process.

## Proposal store

`propose_*` operations are deferred until after the read-only and security phases.

When introduced, proposals must be written only to a non-authoritative proposal store.

A proposal must include:

- immutable proposal ID;
- proposal type;
- caller/client identity where available;
- session identity where available;
- creation time;
- expiry time;
- source and evidence references;
- target authoritative entity;
- exact proposal version or content hash;
- advisory confidence where applicable;
- status such as `pending_review`, `approved`, `rejected`, `expired` or `superseded`.

Required controls:

- per-client and per-session rate limits;
- deduplication of identical proposals;
- TTL and expiry;
- maximum proposal size;
- maximum active proposal count;
- replay protection;
- audit trail;
- explicit binding of human approval to a specific proposal version.

Human approval of one version must never authorize a modified version.

Approval must occur through a separate human-controlled CLI or UI path, not through the autonomous MCP tool set.

## Capability-scoped tools

The MCP facade must not expose generic tools such as:

- `read_file(path)`;
- `write_file(path, content)`;
- `run_command(command)`;
- `run_git(args)`;
- `query_database(sql)`;
- unrestricted repository search outside the declared project scope.

Tools must express semantic Voyage capabilities, for example:

- `build_task_context(task_id)`;
- `trace_decision(decision_id)`;
- `validate_report(report_id)`;
- `project_status()`;
- `list_required_evidence(gate_id)`;
- `check_gate_evidence(gate_id)`.

A semantic tool determines its own permitted sources and applies scope, canonicality, redaction and provenance rules internally.

User-supplied file paths must not become an indirect generic file-reader capability.

## Read security policy

Read-only does not mean unrestricted or safe by default.

Every MCP read or validation operation must apply:

- project-root confinement;
- explicit source allowlists;
- secret and credential deny rules;
- redaction;
- canonical-source selection;
- stale-source detection;
- approved/rejected/draft status awareness;
- provenance;
- response size limits;
- caller/client scope;
- audit logging.

Sensitive or excluded data includes, at minimum:

- `.env` files;
- private keys;
- access tokens;
- passwords and credentials;
- deployment secrets;
- authentication material;
- files outside the approved project root;
- generated outputs that contain secret values;
- rejected or quarantined artifacts unless the specific capability explicitly permits their metadata.

The facade should prefer structural exclusion over post-read redaction. A source that should never be exposed should not be opened merely to redact it later.

## Read-only command allowlist

VALIDATE and selected READ operations may use existing deterministic commands only through a strict allowlist.

For Git, the initial allowlist may include read-only verbs already used by Voyage, such as:

- `rev-parse`;
- `cat-file`;
- `status`;
- `diff`;
- `log`;
- `ls-remote`;
- `show`;
- `merge-base`;
- `rev-list`.

The exact list must be confirmed in MCP-SEC-01 against the existing `_git_utils` and validation implementation.

Forbidden:

- arbitrary shell strings;
- command chaining;
- shell redirection supplied by the caller;
- write-capable Git verbs;
- commands selected directly from model-generated text.

The boundary is an allowlisted semantic operation, not merely the absence of an explicit write flag.

## Caller identity and audit

Every MCP call must be audited with as much caller identity as the transport and client integration can reliably provide.

Audit metadata should include:

- client ID;
- session ID;
- tool name;
- request ID;
- timestamp;
- project scope;
- result classification;
- sources accessed;
- redactions applied;
- validation result;
- proposal ID, if any;
- errors and denied operations.

Missing or weak caller identity must reduce scope, not expand it.

Audit records must not contain raw secrets or unnecessarily duplicate sensitive source content.

## Result classification

MCP responses must identify their epistemic and authority class.

Supported result kinds:

### `deterministic`

Produced entirely from deterministic authoritative sources and deterministic validators.

Examples:

- current Git baseline;
- current project status;
- report validation;
- exact task metadata;
- exact decision record.

### `derived`

Produced from deterministic sources using ranking, aggregation or context selection that may vary with configuration but does not use autonomous judgment to authorize action.

Examples:

- assembled task context;
- source-precedence resolution;
- relevance-ranked knowledge results.

### `advisory`

A recommendation, semantic interpretation or proposal. It is never authoritative.

Examples:

- proposed next task;
- proposed remediation;
- summarized implications;
- proposed gate transition.

An advisory result should include confidence when meaningful.

Example:

```json
{
  "result_kind": "advisory",
  "authoritative": false,
  "confidence": 0.78,
  "authorization": "human_required"
}
```

Clients must not infer authority from tool success.

## Common result metadata

Significant MCP responses should include a versioned result contract with fields equivalent to:

```json
{
  "schema_version": "1.0",
  "tool": "check_gate_evidence",
  "result_kind": "deterministic",
  "authoritative": false,
  "evidence_complete": true,
  "authorization": "human_required",
  "data": {},
  "sources": [
    {
      "path": "docs/framework/FRAMEWORK_PROGRESS.md",
      "content_hash": "sha256:...",
      "canonical": true,
      "status": "approved",
      "stale": false,
      "updated_at": "..."
    }
  ],
  "redactions": [],
  "warnings": [],
  "caller": {
    "client_id": "...",
    "session_id": "..."
  },
  "generated_at": "..."
}
```

The implementation schema is deferred, but provenance, canonicality, staleness, redaction and result classification are binding requirements.

## Source precedence

The MCP facade must follow the same canonical source precedence as Voyage core.

It must not silently choose a newer-looking workspace copy over an authoritative repository document.

When authoritative sources conflict:

1. return the conflict explicitly;
2. identify each source and its canonicality/status;
3. avoid fabricating a merged answer;
4. avoid authoritative recommendations until the conflict is resolved;
5. preserve the human gate.

Source precedence rules must be testable and reused from the core rather than independently reinvented in the MCP adapter.

## Context construction

`build_context` is permitted only as a policy-controlled, provenance-aware context builder.

It must:

- accept semantic identifiers or profiles, not arbitrary file paths;
- select only allowed project sources;
- apply source precedence;
- exclude secrets and denied paths;
- mark stale, draft, rejected and noncanonical material;
- return provenance;
- enforce size and token limits;
- distinguish source facts from summaries;
- remain advisory when semantic ranking or summarization is used.

Possible future profiles include:

- task implementation context;
- review context;
- architecture context;
- incident context;
- documentation context.

Whether these are separate tools or profiles of one tool is deferred to the implementation design.

## Existing interfaces remain first-class

The CLI remains a first-class interface.

The human-controlled authorization and apply path remains a first-class interface.

MCP does not become the only mental model or only entry point for Voyage.

Existing deterministic CLI workflows, report validation, report-state, guarded write and gate operations remain authoritative according to their current contracts.

An MCP client may request evidence or prepare a proposal, but it cannot replace the human approval channel.

## Compliance with existing decisions

### ADR-0001

D-014 does not make Voyage an agent runtime. External LLM clients call a restricted tool facade; Voyage does not autonomously invoke or orchestrate models as part of this decision.

### D-009 — Project Adapter Ownership

MCP is an additional interface/adapter layer. It must call stable core services and must not take ownership of repository-specific logic that belongs to existing adapters.

### D-010 — Role Versioning

MCP tools must use canonical role and policy versions from the core. They must not create an independent role-version interpretation.

### D-011 — LangGraph Reserved

D-014 does not authorize LangGraph implementation or make MCP dependent on LangGraph.

### D-012 — Risk-Based Adaptive Control

MCP does not weaken risk-based gates. Evidence and validation may be exposed, but authorization and application remain human-gated and outside the autonomous MCP tool set.

### D-013 — Application Modernization

MCP may become a future interface over modernized stable services. D-014 does not begin D-013 implementation and does not require modernization to be completed during documentation.

## Consequences

Positive consequences:

- Voyage capabilities become accessible to compatible MCP clients without changing the core identity;
- clients receive semantically meaningful project knowledge rather than generic file access;
- trust and gate boundaries remain explicit;
- MCP can be added incrementally;
- existing CLI and adapters remain usable;
- the first implementation slice can be read-only and low risk.

Costs and constraints:

- every tool requires explicit scope and result semantics;
- provenance and redaction are mandatory;
- proposal storage requires abuse controls;
- separate-process isolation adds packaging and deployment complexity;
- client identity may vary by MCP transport;
- architecture-boundary tests are required;
- a threat model is required before implementation.

## Non-goals

D-014 does not:

- implement an MCP server;
- select an MCP Python SDK;
- select stdio, HTTP or another transport;
- define every final tool schema;
- expose generic filesystem access;
- expose arbitrary Git access;
- expose arbitrary command execution;
- authorize autonomous writes;
- authorize autonomous approvals;
- authorize deployment, commit, merge, rollback or phase transitions;
- replace the CLI;
- replace existing Git or filesystem adapters;
- start LangGraph work;
- start control-loop work;
- start F7-D or another implementation phase;
- make Voyage a general MCP client.

## Deferred implementation sequence

The recommended future sequence is:

```text
D-014 canonical documentation
        ↓
MCP-SEC-01 threat model and boundary analysis
        ↓
new approved Master Development Plan
        ↓
MCP-READ-01 deterministic read facade
        ↓
MCP-READ-02 validation / explanation tools
        ↓
MCP-SEC-02 provenance / redaction / identity hardening
        ↓
MCP-PILOT-01 one-client pilot
        ↓
MCP-PROPOSE-01 non-authoritative proposal layer
        ↓
MCP-PROC-01 separate-process hardening
```

No implementation phase begins automatically after D-014 documentation.

## Open (for MCP-SEC-01 and implementation design)

The following questions remain open without changing the D-014 boundary decision:

1. Which MCP SDK and protocol version should the first implementation use?
2. Which transport should be used for the first pilot?
3. Should the first implementation be a separate process immediately, or a boundary-tested package first?
4. How is caller identity established for each supported client?
5. What exact result schema and version-negotiation policy is required?
6. What exact Git read-only verb allowlist matches the current core?
7. What canonical source-precedence implementation can be reused directly?
8. What redaction patterns and secret scanners are required?
9. What response size and context token limits apply per tool?
10. Which deterministic tools enter MCP-READ-01?
11. Is `build_context` one profile-based tool or several capability-specific tools?
12. What proposal rate limits, TTL, quotas and replay protections are required?
13. Where is the non-authoritative proposal store located?
14. How is a human approval cryptographically or structurally bound to one proposal version?
15. Which single MCP client should be used for the pilot?
16. What compatibility policy applies when the Voyage core or tool schema changes?
17. How are prompt-injection attempts inside repository documents detected or contained?
18. How are rejected, quarantined and stale artifacts represented without exposing unsafe content?
19. Which audit fields are mandatory when the MCP client cannot provide strong identity?
20. What architecture tests prove that MCP cannot import or invoke apply/approval services?
