# MCP-SEC-01 — MCP Threat Model and Security Gate

- Status: Accepted security design / implementation not started
- Date: 2026-07-14
- Canonical baseline: `4433e4760d9d4a93f5bfbbdcc74683ed956ce009`
- Parent decision: [D-014 — MCP Interface Boundary](MCP_INTERFACE_BOUNDARY.md)
- Implementation authorization: none

## Evidence labels

Every normative or factual statement uses one of these labels:

- **CURRENT VERIFIED** — demonstrated by repository code, tests, or canonical status at the baseline.
- **CANONICAL REQUIREMENT** — binding under D-014 or this accepted security design.
- **FUTURE DESIGN REQUIREMENT** — required before the named future phase; not currently implemented.
- **OPEN FOR MASTER PLAN** — a deferred choice that must not be presented as implemented.

## Purpose and scope

**CANONICAL REQUIREMENT.** MCP-SEC-01 defines the threat model and security gate for Voyage-as-MCP-server. It covers READ, VALIDATE, EXPLAIN, and a future restricted PROPOSE class. Autonomous AUTHORIZE, APPROVE, and APPLY remain excluded. This document does not start implementation.

**CURRENT VERIFIED.** Voyage currently exposes CLI workflows, report validation, repository-state observation, context construction, event recording, read-only repository adapters, edit preview, and guarded-write planning/approval verification. No MCP facade is present at this baseline.

## System model

**FUTURE DESIGN REQUIREMENT.** The permitted information path is:

```text
MCP client
    -> request
MCP facade / adapter
    -> approved service calls
Voyage read / validation / explanation services
    -> canonical project sources, Git metadata, reports and audit
```

**CANONICAL REQUIREMENT.** Authoritative action stays on a separate path:

```text
human operator
    -> explicit approval
CLI / controlled UI
    -> approval / apply / guarded-write services
```

**CANONICAL REQUIREMENT.** The MCP path must not connect directly to, import, receive, or invoke the human authorize/apply path.

## Current implementation evidence

| Classification | Path | Purpose | Current verified capability | Security relevance | Status |
|---|---|---|---|---|---|
| CURRENT VERIFIED | `voyage_framework/core/_git_utils.py` | Shared Git observation | Fixed callers use `status`, `rev-parse`, `branch`, `cat-file`, `diff-tree`, `diff`, and `rev-list`; Git-local environment variables are removed | Starting evidence for a semantic allowlist; not an MCP sandbox | implemented / partial |
| CURRENT VERIFIED | `voyage_framework/core/report_validator.py` | `voyage.report.v1` validation | Compares claims with Git facts, commit/range files, staged/dirty state, and forbidden paths | Deterministic VALIDATE candidate | implemented |
| CURRENT VERIFIED | `voyage_framework/core/_git_utils.py::collect_repo_state` | Repository state | Reports branch, HEAD, origin/main, dirty/staged/untracked files, errors, and warnings | Deterministic READ candidate behind project scope | implemented |
| CURRENT VERIFIED | `voyage_framework/core/context_builder.py` | Context construction | Builds task/event/project context from supplied task files and engines | Context source policy and arbitrary-path prevention are not currently verified for MCP | partial |
| CURRENT VERIFIED | `voyage_framework/core/event_engine.py` | Event audit | Appends events to SQLite and JSONL and supports parameterized queries | Existing audit substrate; MCP caller/session audit is absent | partial |
| CURRENT VERIFIED | `voyage_framework/core/repo_control_adapter.py` | Repository adapter contract | Contract is documented read-only and exposes status/validate/audit/preview results | Supports D-009 separation | implemented |
| CURRENT VERIFIED | `voyage_framework/core/local_repo_adapter.py` | Local repository adapter | Uses fixed `git ls-files` and read-only status/validation surfaces | Useful read surface; MCP confinement/redaction is absent | partial |
| CURRENT VERIFIED | `voyage_framework/core/guarded_write.py` | Guarded-write plan | Emits `writes_supported=false`, `approval_required=true`, and a human gate | Demonstrates separation; it must remain unreachable from MCP | implemented read-only plan |
| CURRENT VERIFIED | `voyage_framework/core/guarded_write_approval.py` | Approval verification | Verifies approval evidence and repository binding but emits `writes_supported=false` | Sensitive service explicitly forbidden to MCP | implemented read-only verification |
| CURRENT VERIFIED | `voyage_framework/core/forbidden_paths.py` | Path policy | Denies `.env` patterns for existing role policies | Useful evidence, not a complete MCP secret/redaction policy | partial |
| CURRENT VERIFIED | `tests/unit/test_architecture_boundaries.py` | Import boundaries | AST tests protect selected current core/CLI boundaries | No MCP forbidden-import test exists | partial |
| CURRENT VERIFIED | `docs/framework/adr/ADR-0001-framework-narrative-separation.md` and D-009…D-014 | Architecture authority | Establish identity, adapter ownership, risk gates, modernization separation, and MCP boundary | Governs future facade | implemented documentation |

**CURRENT VERIFIED.** Dedicated MCP transport identity, response redaction, prompt-injection containment, rate limiting, proposal storage, protocol compatibility, and MCP architecture isolation are absent or not currently verified.

## Protected assets

| Classification | Asset | Owner | Confidentiality | Integrity | Availability | Authoritative source |
|---|---|---|---|---|---|---|
| CANONICAL REQUIREMENT | Canonical project state | Project owner | scoped | critical | high | repository contracts and canonical runtime stores |
| CANONICAL REQUIREMENT | Decisions and ADRs | Architecture owner | project-scoped | critical | high | canonical repository documents |
| CANONICAL REQUIREMENT | Task and phase status | Task/control owner | scoped | critical | high | `task.yaml`, TaskRecord, approved progress records |
| CANONICAL REQUIREMENT | Validation evidence | Control owner | scoped | critical | high | validators plus referenced evidence |
| CANONICAL REQUIREMENT | Approval and gate state | Human approver | sensitive | critical | high | human-controlled approval channel |
| CANONICAL REQUIREMENT | Git baseline and repository integrity | Repository owner | scoped | critical | high | Git object/ref/worktree facts |
| CANONICAL REQUIREMENT | Audit and report integrity | Project owner | sensitive | critical | high | EventEngine and validated reports |
| CANONICAL REQUIREMENT | Source provenance | Project owner | scoped | critical | high | canonical source metadata and safe hashes |
| CANONICAL REQUIREMENT | Secrets and credentials | Secret owner | critical | critical | medium | excluded secret stores; never MCP content |
| CANONICAL REQUIREMENT | Personal/private data | Data owner | high | high | medium | approved project sources only |
| CANONICAL REQUIREMENT | Project isolation | Project owner | critical | critical | high | explicitly selected project root |
| FUTURE DESIGN REQUIREMENT | Proposal integrity | Proposal author/reviewer | scoped | critical | medium | non-authoritative versioned proposal store |
| CANONICAL REQUIREMENT | Local workflow availability | Local operator | low | high | high | local Voyage installation and repository |
| CANONICAL REQUIREMENT | Advisory/authoritative distinction | Control owner | low | critical | high | versioned result contract |

## Actors and trust assumptions

| Classification | Actor | Trust | Binding assumption |
|---|---|---|---|
| CANONICAL REQUIREMENT | Human operator | trusted for explicit scoped decisions | Approval must identify a human and exact proposal/version |
| CURRENT VERIFIED | Trusted local Voyage CLI | conditionally trusted | Existing deterministic commands remain first-class |
| CURRENT VERIFIED | Voyage core | trusted within tested contracts | Core is authoritative only for its owned state |
| FUTURE DESIGN REQUIREMENT | MCP facade | conditionally trusted | Least privilege and structural service isolation required |
| CANONICAL REQUIREMENT | MCP client application | untrusted/conditional | Identity and policy determine maximum scope |
| CANONICAL REQUIREMENT | Local or remote LLM | untrusted | Model-generated requests are untrusted input |
| CANONICAL REQUIREMENT | Repository content author | untrusted/conditional | Authorship does not grant instruction authority |
| CANONICAL REQUIREMENT | Malicious repository content | untrusted | Repository content is data, not instructions |
| CANONICAL REQUIREMENT | Git remote | conditional | Refs and content require verification and provenance |
| OPEN FOR MASTER PLAN | MCP transport | conditional | Authentication and channel properties depend on chosen transport |
| CANONICAL REQUIREMENT | Weakly identified client | untrusted | Missing identity reduces scope |
| CANONICAL REQUIREMENT | Compromised client | hostile | Server policy must not rely on client compliance |
| CANONICAL REQUIREMENT | Dependency/plugin supplier | untrusted/conditional | Pinning, review, and supply-chain controls required |

## Trust boundaries

| ID | Classification | Boundary | Allowed data | Denied data | Required validation |
|---|---|---|---|---|---|
| TB-01 | FUTURE DESIGN REQUIREMENT | client ↔ transport | versioned semantic requests/results | secrets, raw commands | authentication, size/schema limits, replay controls |
| TB-02 | FUTURE DESIGN REQUIREMENT | transport ↔ facade | authenticated request context | transport-asserted excess privilege | identity binding, request ID, capability policy |
| TB-03 | CANONICAL REQUIREMENT | facade ↔ Voyage services | approved read/validate/explain interfaces | apply/approval/transition/write services | explicit DI allowlist and forbidden-import test |
| TB-04 | FUTURE DESIGN REQUIREMENT | services ↔ filesystem/Git/database | scoped semantic reads | arbitrary paths/SQL/shell | confinement, allowlists, time/output limits |
| TB-05 | CANONICAL REQUIREMENT | canonical repo ↔ workspace/draft/external | status-labelled evidence | silent authority substitution | source precedence and conflict response |
| TB-06 | CANONICAL REQUIREMENT | proposal store ↔ authoritative state | immutable proposal reference | direct mutation | human approval bound to exact version |
| TB-07 | CANONICAL REQUIREMENT | MCP ↔ authorize/apply path | no direct calls | all autonomous authority | process/package isolation |
| TB-08 | CANONICAL REQUIREMENT | project ↔ project | explicit selected project only | cross-project reads | root identity and deny-by-default isolation |
| TB-09 | OPEN FOR MASTER PLAN | local process ↔ remote resources | approved transport/source calls | arbitrary egress | transport/source allowlist and TLS policy |
| TB-10 | FUTURE DESIGN REQUIREMENT | audit producer ↔ audit storage | bounded structured events | secrets and forgeable raw text | integrity, escaping, retention, quotas |

## Data flows

| Flow | Classification | Input/source | Validation/redaction | Result kind/authority | Audit | Failure mode |
|---|---|---|---|---|---|---|
| Project status | CURRENT VERIFIED + FUTURE DESIGN REQUIREMENT | project ID; Git facts | root confinement; path/secret metadata filtering | deterministic; non-authorizing | caller, repo, refs | wrong root or TOCTOU |
| Report validation | CURRENT VERIFIED + FUTURE DESIGN REQUIREMENT | report ID; `voyage.report.v1`; Git facts | schema, hash, file-set, forbidden-path checks | deterministic; non-authorizing | report hash/result | crafted report or stale refs |
| Decision trace | FUTURE DESIGN REQUIREMENT | decision ID; canonical docs | ID grammar, precedence, status labels | deterministic/derived; non-authorizing | sources/hashes | draft shadows accepted decision |
| Context construction | CURRENT VERIFIED + FUTURE DESIGN REQUIREMENT | semantic profile/IDs; allowed sources | no caller paths, precedence, injection labels, redaction, budget | derived/advisory; non-authorizing | selected sources | secret or malicious content inclusion |
| Gate evidence check | FUTURE DESIGN REQUIREMENT | gate ID; evidence references | policy and completeness validation | deterministic; `authorization=human_required` | evidence/result | completeness mistaken for permission |
| Knowledge search | FUTURE DESIGN REQUIREMENT | bounded query; indexed approved sources | scope/status/redaction/ranking labels | derived/advisory | query/source set | cross-project or stale result |
| Proposal creation | FUTURE DESIGN REQUIREMENT | typed proposal; evidence | size, dedup, TTL, hash, identity | advisory; non-authoritative | proposal/version | replay or post-review mutation |
| Audit recording | FUTURE DESIGN REQUIREMENT | structured call/result metadata | escape, redact, quota | deterministic record | mandatory | omission, forgery, secret leakage |
| Denial/error | FUTURE DESIGN REQUIREMENT | rejected request | safe error mapping | deterministic denial; no authority | reason/request ID | over-disclosure or suppressed error |

## Threat register

All likelihood/risk labels are qualitative; no unsupported numeric score is introduced.

| ID | Category | Scenario | Assets/preconditions | Impact | Likelihood / risk | Required controls | Verification | Phase owner | Residual risk |
|---|---|---|---|---|---|---|---|---|---|
| MCP-THR-001 | Identity | Caller/session spoofing or confusion grants another client's scope | identity; weak binding | data leak/action confusion | medium / high | authenticated context, request/session binding | identity negative tests | MCP-SEC-02 | compromised host |
| MCP-THR-002 | Authorization | Tool success or `evidence_complete` is treated as approval | authority semantics | unauthorized action | high / critical | explicit authorization field; no authority tools | contract tests | MCP-READ-01 | client misuse |
| MCP-THR-003 | Identity | Confused deputy reads a project outside caller scope | project isolation | cross-project leak | medium / high | project binding, deny default | isolation tests | MCP-READ-01 | host admin access |
| MCP-THR-004 | Files | Traversal, case/separator, symlink or junction escapes root | filesystem access | secret/private data leak | high / critical | canonical path confinement and handle-time checks | Windows/path tests | MCP-READ-01 | OS race |
| MCP-THR-005 | Files | Semantic parameters become a generic file reader | source confidentiality | arbitrary read | medium / critical | IDs/profiles only; schema bans paths | tool-schema tests | MCP-READ-01 | overly broad service |
| MCP-THR-006 | Files | `.env`, key, token, ignored/untracked or quarantined data is exposed | secrets in/near repo | credential compromise | high / critical | structural deny before read, metadata-only errors | secret denial tests | MCP-READ-01 | secrets in allowed text/history |
| MCP-THR-007 | Injection | Markdown/code/report/commit message instructs client to call forbidden tools | untrusted content | policy bypass | high / high | content-as-data boundary, provenance, no tool recursion | injection fixtures | MCP-READ-01 | persuasive content |
| MCP-THR-008 | Injection | Hidden/encoded or remote metadata injection contaminates context | context integrity | misleading advisory output | medium / high | encoding controls, labels, bounded parsing | adversarial content tests | MCP-READ-02 | novel encodings |
| MCP-THR-009 | Command | Shell metacharacters, raw args, aliases, filters, textconv, pager or hooks execute code | local host/repo | code execution/mutation | medium / critical | no shell, fixed args/env, disable external helpers, allowlist | command/env tests | MCP-READ-01 | Git implementation behavior |
| MCP-THR-010 | Command | Write-capable Git verb or remote URL abuse changes state/contacts attacker | repository/network | mutation/exfiltration | medium / critical | semantic fixed verbs, no caller remote/args | allowlist negative tests | MCP-READ-01 | server-side remote trust |
| MCP-THR-011 | Command | TOCTOU changes source after validation | provenance/integrity | inconsistent result | medium / high | object IDs, safe hashes, recheck state | race tests | MCP-READ-01 | unavoidable concurrent edits |
| MCP-THR-012 | Canonicality | Workspace clone, stale cache, draft, rejected, or future-only source shadows canonical state | decisions/status | false authority | high / high | shared precedence, status preservation, conflict result | precedence tests | MCP-READ-01 | misclassified source |
| MCP-THR-013 | Provenance | Missing/fabricated hash or report claims conflict with Git | evidence | false validation | medium / high | safe content/object hashes and validator facts | report consistency tests | MCP-READ-01 | hash algorithm migration |
| MCP-THR-014 | Semantics | Advisory inference labelled deterministic/authoritative or partial result labelled complete | authority distinction | unsafe downstream action | high / critical | strict result kinds, completeness/authorization split | result-contract tests | MCP-READ-01 | client ignores fields |
| MCP-THR-015 | Semantics | Schema downgrade removes warnings, authority, redaction, or provenance | result integrity | silent weakening | medium / high | explicit versions, reject unsafe downgrade | compatibility tests | MCP-SEC-02 | old clients |
| MCP-THR-016 | Proposal | Flood, duplicates, replay, oversize, expiry bypass, or store exhaustion | proposal availability/integrity | DoS/review bypass | high / high | quotas, dedup, TTL, immutable hash, replay protection | proposal tests | MCP-PROPOSE-01 | coordinated clients |
| MCP-THR-017 | Proposal | Approval binds wrong or modified proposal version; direct-command payload reaches apply | gate state | unauthorized mutation | medium / critical | exact version binding and separate human channel | version-binding tests | MCP-PROPOSE-01 | human error |
| MCP-THR-018 | Audit | Identity/result omitted, logs forged, timestamps misleading, or secrets logged | audit/secrets | repudiation/leak | medium / high | structured events, integrity, redaction, quotas | audit tests | MCP-SEC-02 | local admin tampering |
| MCP-THR-019 | Availability | Oversized context, recursion, binary/generated content, deep Git history, repeated validation | workflow availability | local DoS | high / high | request/source/token/time/concurrency limits | limit tests | MCP-READ-01 | expensive legitimate repo |
| MCP-THR-020 | Supply chain | Compromised SDK/plugin, dependency confusion, unsafe serialization | host/boundary | code execution/tool widening | medium / critical | minimal pinned dependencies, review, SBOM, isolation | supply-chain gate | MASTER PLAN | upstream zero-day |
| MCP-THR-021 | Transport | Insecure binding/authentication or protocol mismatch exposes/widens tools | identity/data | remote compromise | medium / critical | authenticated transport, local default, version negotiation | transport tests | MCP-SEC-02 | endpoint compromise |
| MCP-THR-022 | Architecture | Facade imports/receives apply, approval, guarded-write, transition, service locator, or shared mutable internals | authoritative state | direct boundary bypass | medium / critical | separate package/process and forbidden dependency graph | AST/runtime DI tests | MCP-READ-01 | interpreter compromise |
| MCP-THR-023 | Architecture | Refactor/test bypass silently weakens D-014 | all boundaries | latent authority exposure | medium / critical | mandatory blocking tests/review ownership | CI mutation/negative tests | operations | malicious maintainer |
| MCP-THR-024 | Availability | Audit/proposal/session/transport floods exhaust disk, CPU, handles, or queues | local workflow | denial of service | high / high | quotas, backpressure, retention, circuit breakers | load/abuse tests | MCP-SEC-02 | local resource exhaustion |

## Binding security invariants

| ID | Classification | Invariant |
|---|---|---|
| MCP-SEC-INV-001 | CANONICAL REQUIREMENT | MCP cannot authorize or apply authoritative mutation. |
| MCP-SEC-INV-002 | CANONICAL REQUIREMENT | MCP cannot import or receive approval, apply, guarded-write, or phase-transition services. |
| MCP-SEC-INV-003 | CANONICAL REQUIREMENT | No generic path/file read tool exists. |
| MCP-SEC-INV-004 | CANONICAL REQUIREMENT | No arbitrary shell/command tool exists. |
| MCP-SEC-INV-005 | CANONICAL REQUIREMENT | Git operations are semantic, fixed, and allowlisted. |
| MCP-SEC-INV-006 | FUTURE DESIGN REQUIREMENT | Root confinement handles Windows case, separators, symlinks, and junctions. |
| MCP-SEC-INV-007 | CANONICAL REQUIREMENT | Secret sources are excluded before loading where possible. |
| MCP-SEC-INV-008 | CANONICAL REQUIREMENT | Significant results include provenance and result classification. |
| MCP-SEC-INV-009 | CANONICAL REQUIREMENT | Evidence completeness is separate from authorization. |
| MCP-SEC-INV-010 | CANONICAL REQUIREMENT | Advisory output is never authoritative. |
| MCP-SEC-INV-011 | CANONICAL REQUIREMENT | Missing or weak identity reduces scope. |
| MCP-SEC-INV-012 | FUTURE DESIGN REQUIREMENT | Calls are auditable without recording secrets. |
| MCP-SEC-INV-013 | CANONICAL REQUIREMENT | Source precedence is shared with core and testable. |
| MCP-SEC-INV-014 | CANONICAL REQUIREMENT | Draft, rejected, stale, quarantined, and future-only status is preserved. |
| MCP-SEC-INV-015 | CANONICAL REQUIREMENT | Proposal data is non-authoritative, immutable/version-bound, and expiring. |
| MCP-SEC-INV-016 | CANONICAL REQUIREMENT | CLI and human approval remain first-class. |
| MCP-SEC-INV-017 | CANONICAL REQUIREMENT | Cross-project access is denied by default. |
| MCP-SEC-INV-018 | FUTURE DESIGN REQUIREMENT | Bounded request, response, source, time, concurrency, audit, and proposal workloads are enforced. |
| MCP-SEC-INV-019 | FUTURE DESIGN REQUIREMENT | Protocol and result-schema versions are explicit; unsafe downgrade is rejected. |
| MCP-SEC-INV-020 | CANONICAL REQUIREMENT | MCP code cannot start before MCP-SEC-01, an approved Master Plan, and read-only preflight pass. |

## Security requirements

Every row is blocking unless explicitly marked otherwise.

| ID | Group / classification | Requirement | Rationale | Applies to | Verification | Blocking |
|---|---|---|---|---|---|---|
| MCP-SEC-REQ-001 | architecture / CANONICAL REQUIREMENT | Separate MCP package/process exposes only read/validate/explain interfaces | prevent authority reachability | MCP-READ-01 | dependency graph test | yes |
| MCP-SEC-REQ-002 | architecture / FUTURE DESIGN REQUIREMENT | DI allowlist rejects service locators and write-capable services | prevent confused deputy | MCP-READ-01 | runtime injection test | yes |
| MCP-SEC-REQ-003 | identity / FUTURE DESIGN REQUIREMENT | Bind request, client, session, project, and capability scope | prevent spoofing | MCP-READ-01 | identity tests | yes |
| MCP-SEC-REQ-004 | identity / CANONICAL REQUIREMENT | Weak/unidentified clients receive the minimum read-only scope or denial | fail closed | all | scope matrix tests | yes |
| MCP-SEC-REQ-005 | input / FUTURE DESIGN REQUIREMENT | Validate schemas, identifiers, encodings, sizes, and enums before service calls | reject injection/malformed input | all | fuzz/negative tests | yes |
| MCP-SEC-REQ-006 | path / FUTURE DESIGN REQUIREMENT | Resolve and recheck canonical paths beneath one bound project root | stop traversal/races | MCP-READ-01 | Windows/symlink tests | yes |
| MCP-SEC-REQ-007 | Git / CANONICAL REQUIREMENT | Expose semantic fixed operations, never raw Git args or shell | stop command injection | MCP-READ-01 | allowlist tests | yes |
| MCP-SEC-REQ-008 | Git / FUTURE DESIGN REQUIREMENT | Sanitize Git environment and disable aliases, pager, hooks where relevant, filters/textconv, and caller remotes | stop external execution | MCP-READ-01 | environment tests | yes |
| MCP-SEC-REQ-009 | precedence / CANONICAL REQUIREMENT | Reuse one canonical source-precedence service and return explicit conflicts | prevent shadow authority | MCP-READ-01 | conflict tests | yes |
| MCP-SEC-REQ-010 | provenance / CANONICAL REQUIREMENT | Return source, safe hash, canonicality, status, staleness, and update metadata | make claims traceable | all | contract tests | yes |
| MCP-SEC-REQ-011 | secrets / CANONICAL REQUIREMENT | Structurally deny secret path/classes before content load | minimize exposure | all | denial tests | yes |
| MCP-SEC-REQ-012 | secrets / FUTURE DESIGN REQUIREMENT | Apply typed redaction markers and fail closed on uncertain sensitive content | safe output | all | redaction tests | yes |
| MCP-SEC-REQ-013 | result / CANONICAL REQUIREMENT | Versioned contract separates result kind, authority, evidence completeness, and authorization | prevent semantic escalation | all | schema tests | yes |
| MCP-SEC-REQ-014 | result / FUTURE DESIGN REQUIREMENT | Reject incompatible or authority-weakening schema downgrade | preserve controls | MCP-SEC-02 | compatibility tests | yes |
| MCP-SEC-REQ-015 | audit / FUTURE DESIGN REQUIREMENT | Record request/result identity, scope, sources, denials, redactions, and timings without secrets | accountability | all | audit tests | yes |
| MCP-SEC-REQ-016 | limits / FUTURE DESIGN REQUIREMENT | Enforce request/response/source/token/history/time/concurrency/rate limits | availability | MCP-READ-01 | limit/load tests | yes |
| MCP-SEC-REQ-017 | transport / OPEN FOR MASTER PLAN | Choose authenticated transport with local-only default unless remote risk is accepted | protect channel | MCP-SEC-02 | threat review/test | yes |
| MCP-SEC-REQ-018 | dependencies / OPEN FOR MASTER PLAN | Minimize, pin, review, scan, and lifecycle-manage SDK/dependencies | supply-chain safety | before code | dependency gate | yes |
| MCP-SEC-REQ-019 | proposal / CANONICAL REQUIREMENT | Store proposals separately with immutable ID/version/hash, TTL, quota, dedup, replay protection | non-authority integrity | MCP-PROPOSE-01 | proposal tests | yes |
| MCP-SEC-REQ-020 | proposal / CANONICAL REQUIREMENT | Human approval channel binds identity and exact proposal version | stop review bypass | MCP-PROPOSE-01 | end-to-end negative tests | yes |
| MCP-SEC-REQ-021 | testing / CANONICAL REQUIREMENT | All blocking security tests run in required CI/preflight gates | prevent regression | each phase | CI evidence | yes |
| MCP-SEC-REQ-022 | operations / FUTURE DESIGN REQUIREMENT | Define retention, incident response, revocation, rotation, backup, and safe shutdown | operational resilience | pilot | operational review | yes |
| MCP-SEC-REQ-023 | content / CANONICAL REQUIREMENT | Treat repository and remote content as data, never executable instructions | prompt-injection containment | all | adversarial fixtures | yes |
| MCP-SEC-REQ-024 | non-mutation / CANONICAL REQUIREMENT | Prove every READ/VALIDATE/EXPLAIN operation leaves repo/runtime authoritative state unchanged | D-014 boundary | MCP-READ-01 | before/after state tests | yes |

## Initial tool classification

| Tool | Class | Result kind | Authoritative | Sources | Side effects | Audit/main threats/controls | Phase | Status |
|---|---|---|---|---|---|---|---|---|
| `project_status` | READ | deterministic | false | scoped Git facts | none | root/ref audit; THR-003/011; fixed Git | MCP-READ-01 | candidate |
| `report_state` | READ | deterministic | false | scoped Git facts | none | repo/result audit; THR-011/013 | MCP-READ-01 | candidate |
| `get_decision` | READ | deterministic | false | canonical decision docs | none | source/hash audit; precedence/redaction | MCP-READ-01 | candidate |
| `get_task` | READ | deterministic | false | canonical task/runtime state | none | task/project audit; scope/status | MCP-READ-01 | candidate |
| `list_tasks` | READ | deterministic | false | canonical task/runtime state | none | bounded list; project scope | MCP-READ-01 | candidate |
| `list_required_evidence` | READ | deterministic | false | canonical gate policy | none | gate audit; no authorization inference | MCP-READ-01 | candidate |
| `validate_report` | VALIDATE | deterministic | false | report plus Git facts | none | report hash/result; fixed validator | MCP-READ-02 | candidate |
| `check_gate_evidence` | VALIDATE | deterministic | false | evidence/policy | none | completeness distinct from permission | MCP-READ-02 | candidate |
| `trace_decision` | EXPLAIN | deterministic/derived | false | canonical sources | none | provenance; conflict/status labels | MCP-READ-02 | candidate |
| `explain_gate_failure` | EXPLAIN | derived | false | validator evidence | none | facts vs interpretation | MCP-READ-02 | candidate |
| `build_context` | READ/EXPLAIN | derived/advisory | false | profile-scoped sources | none | injection/redaction/budget controls | MCP-READ-02 | candidate |
| `search_knowledge` | READ | derived | false | approved indexed sources | none | project/status/budget audit | MCP-READ-02 | candidate |
| `propose_task` / `propose_task_update` / `propose_next_task` | PROPOSE | advisory | false | evidence + proposal store | non-authoritative proposal | identity, TTL, version, rate controls | MCP-PROPOSE-01 | deferred |
| `propose_decision` / `propose_gate_transition` | PROPOSE | advisory | false | evidence + proposal store | non-authoritative proposal | no authority; exact human review | MCP-PROPOSE-01 | deferred |
| approve/authorize/apply | AUTHORIZE/APPLY | n/a | forbidden | n/a | authoritative | structurally absent | never autonomous MCP | forbidden |
| commit/merge/deploy/delete/rollback/phase transition/status mutation | APPLY | n/a | forbidden | n/a | external/authoritative | structurally absent | never autonomous MCP | forbidden |
| arbitrary file read/write | READ/APPLY | n/a | forbidden | arbitrary | leak/mutation | no generic schema | never | forbidden |
| arbitrary command execution | APPLY | n/a | forbidden | arbitrary | host effects | no shell/raw args | never | forbidden |

**OPEN FOR MASTER PLAN.** The final tool list and exact schemas remain subject to the approved Master Plan and read-only preflight.

## Git read-only allowlist

### Verified currently used read-only operations

**CURRENT VERIFIED.** Repository code uses fixed call sites for `status --porcelain=v1 -uall`, `rev-parse`, `branch --show-current`, `cat-file -t`, `diff-tree --no-commit-id --name-only -r --root`, `diff --name-only`, `rev-list --parents -n 1`, and `ls-files`. These are evidence, not a ready-made MCP command gateway. `_git_utils` removes Git-local environment variables, but comprehensive MCP controls for aliases, pagers, filters, hooks, and output/time limits are not currently verified.

### Proposed initial MCP allowlist

| Operation | Classification | Purpose | Allowed arguments | Forbidden arguments | Environment/CWD/output | Side-effect risk | Verification |
|---|---|---|---|---|---|---|---|
| `rev-parse` | FUTURE DESIGN REQUIREMENT | fixed refs/root fact | predefined `HEAD`, `origin/main`, `--is-inside-work-tree` | caller refs/options | sanitized env; bound root; small output | config/replacement refs | positive/negative fixed-arg tests |
| `branch --show-current` | FUTURE DESIGN REQUIREMENT | branch fact | exact flag only | all caller options | sanitized env; bound root; one line | low | exact invocation test |
| `status --porcelain=v1 -uall` | FUTURE DESIGN REQUIREMENT | worktree fact | exact flags only | caller pathspec/config | sanitized env; bounded output/time | large/untracked enumeration | size/non-mutation tests |
| `cat-file -t` | FUTURE DESIGN REQUIREMENT | object type | validated full object ID only | batch/content modes | sanitized env; bound repo; one line | object lookup cost | hash grammar tests |
| `diff-tree` | FUTURE DESIGN REQUIREMENT | commit file set | fixed name-only flags plus verified object ID | patches, external diff, textconv | disable external diff; bounded output | history cost | flag/environment tests |
| `diff --name-only` | FUTURE DESIGN REQUIREMENT | verified commit range files | two verified object IDs | worktree patch, caller path/options | disable external diff/textconv; bounded output | range cost | range/limit tests |
| `rev-list --parents -n 1` | FUTURE DESIGN REQUIREMENT | parent verification | exact flags plus verified object ID | arbitrary traversal/options | bounded output/time | history lookup | fixed-arg tests |
| `ls-files` | FUTURE DESIGN REQUIREMENT | tracked inventory | no caller pathspec/options | ignored/others/submodules flags | bound root; bounded output | large repo | scope/limit tests |

**CANONICAL REQUIREMENT.** Never expose `git <caller args>`. Git aliases must not select operations; shell execution and command chaining are forbidden. External diff, textconv, pager, filters, hooks, replacement/config environment, remote selection, working directory, time, and output behavior must be explicitly controlled or proven irrelevant for each semantic operation.

## Source precedence and canonicality

**CURRENT VERIFIED.** The repository hierarchy identifies canonical architecture documents and runtime truth; generated `TASK.md` and `CONTEXT.json` are not canonical truth. D-014 is canonical in the repository. External handoff reports are evidence, workspace drafts are noncanonical, legacy documents are stale-risk, and CONTROL-LOOP-2…10 documents are future-only.

**CANONICAL REQUIREMENT.** MCP must prefer canonical repository contracts/decisions and owned runtime state, preserve accepted/draft/rejected/quarantined/stale/future-only labels, and never silently elevate a workspace copy, report, generated artifact, or newer-looking draft. Conflicts return all relevant provenance and no fabricated merged authority; authoritative resolution remains human-controlled.

**OPEN FOR MASTER PLAN.** The exact reusable core source-precedence service and representation for rejected/quarantined artifacts are not currently verified.

## Redaction and secret policy

**CANONICAL REQUIREMENT.** Structurally deny `.env` variants, private keys, credentials, tokens, passwords, authentication/deployment material, files outside the project root, secret-bearing generated output, and raw rejected/quarantined content unless a narrowly approved metadata capability exists. Prefer exclusion before loading. Do not enumerate ignored/untracked contents merely to redact them.

**FUTURE DESIGN REQUIREMENT.** Define safe metadata-only responses, stable redaction markers containing category but no value, binary/generated-file rejection, Git-history policy, bounded scanning, fail-closed behavior, audit redaction, and false-positive human review. False negatives are a blocking security defect; false positives may deny access and require explicit review. Tests must use synthetic secrets only.

**CURRENT VERIFIED.** Existing forbidden-path policy includes `.env`, but comprehensive MCP redaction, Git-history secret handling, key classification, and response scanning are not currently verified.

## Caller identity and session model

| Class | Classification | Maximum capability before further approval |
|---|---|---|
| Strongly identified local client | FUTURE DESIGN REQUIREMENT | explicitly granted project-scoped READ/VALIDATE/EXPLAIN candidates |
| Weakly identified local client | CANONICAL REQUIREMENT | minimal non-sensitive project status or denial; no context/search/proposal |
| Remote authenticated client | OPEN FOR MASTER PLAN | denied until transport threat model and explicit policy; never broader than strong local scope |
| Unidentified client | CANONICAL REQUIREMENT | denial or minimal health metadata with no project content |

**CANONICAL REQUIREMENT.** Missing or weak identity reduces scope; it never expands scope. Identity must bind client, session, request, project, capability, and audit record. Transport choice is deferred.

## Result contract requirements

**CANONICAL REQUIREMENT.** Significant results carry: schema version, tool, request ID, result kind, authoritative flag, evidence completeness, authorization status, data, sources/provenance, canonicality/status/staleness, safe hashes, redactions, warnings, caller/client/session when available, generated time, and errors/denials.

**FUTURE DESIGN REQUIREMENT.** Unknown major versions and authority-weakening downgrades fail closed. Clients cannot negotiate away provenance, redaction, warnings, result kind, or authorization. Partial results explicitly name omissions. Tool success never implies authority.

## Resource and rate limits

**FUTURE DESIGN REQUIREMENT.** Mandatory independently configurable categories are request bytes, response bytes, source count, context/token budget, Git history depth/object count, validation duration, concurrency, per-client/session/project rate, audit growth/retention, and future proposal count/bytes/TTL. Exact values are OPEN FOR MASTER PLAN; absence of any category blocks its applicable phase.

## Required future security tests

| ID | Classification | Threats covered / fixture | Expected result | Required phase | Blocking gate |
|---|---|---|---|---|---|
| MCP-SEC-TEST-001 | FUTURE DESIGN REQUIREMENT | THR-022; AST dependency fixture | forbidden imports fail | MCP-READ-01 | yes |
| MCP-SEC-TEST-002 | FUTURE DESIGN REQUIREMENT | THR-022; DI/service-locator fixture | write service injection rejected | MCP-READ-01 | yes |
| MCP-SEC-TEST-003 | FUTURE DESIGN REQUIREMENT | THR-005; tool schemas | no generic path parameter/tool | MCP-READ-01 | yes |
| MCP-SEC-TEST-004 | FUTURE DESIGN REQUIREMENT | THR-004; `..`, absolute, UNC, drive-relative paths | root escape denied | MCP-READ-01 | yes |
| MCP-SEC-TEST-005 | FUTURE DESIGN REQUIREMENT | THR-004; Windows case/separator variants | bypass denied | MCP-READ-01 | yes |
| MCP-SEC-TEST-006 | FUTURE DESIGN REQUIREMENT | THR-004; symlink/junction fixtures | escape denied before read | MCP-READ-01 | yes |
| MCP-SEC-TEST-007 | FUTURE DESIGN REQUIREMENT | THR-006; synthetic `.env`/key/token paths | content never loaded/returned | MCP-READ-01 | yes |
| MCP-SEC-TEST-008 | FUTURE DESIGN REQUIREMENT | THR-006/018; synthetic secrets in allowed text/log inputs | typed redaction; logs secret-free | MCP-READ-01 | yes |
| MCP-SEC-TEST-009 | FUTURE DESIGN REQUIREMENT | THR-007/008; malicious Markdown/encoded instructions | treated as data; no tool escalation | MCP-READ-01 | yes |
| MCP-SEC-TEST-010 | FUTURE DESIGN REQUIREMENT | THR-012; canonical/workspace conflict | canonical selected or conflict explicit | MCP-READ-01 | yes |
| MCP-SEC-TEST-011 | FUTURE DESIGN REQUIREMENT | THR-012; draft/rejected/future-only fixtures | status preserved, no implementation claim | MCP-READ-01 | yes |
| MCP-SEC-TEST-012 | FUTURE DESIGN REQUIREMENT | THR-009/010; Git allowlist positive/negative matrix | only fixed semantic calls accepted | MCP-READ-01 | yes |
| MCP-SEC-TEST-013 | FUTURE DESIGN REQUIREMENT | THR-009; metacharacter/argument injection | no shell/external process | MCP-READ-01 | yes |
| MCP-SEC-TEST-014 | FUTURE DESIGN REQUIREMENT | THR-009; aliases/filter/textconv/pager/config env | external helpers disabled | MCP-READ-01 | yes |
| MCP-SEC-TEST-015 | FUTURE DESIGN REQUIREMENT | THR-014; deterministic/advisory fixtures | correct kind/authority flags | MCP-READ-01 | yes |
| MCP-SEC-TEST-016 | FUTURE DESIGN REQUIREMENT | THR-002/014; complete evidence fixture | `human_required`, no permission | MCP-READ-01 | yes |
| MCP-SEC-TEST-017 | FUTURE DESIGN REQUIREMENT | THR-001/003; missing/weak identity | scope reduced or denied | MCP-READ-01 | yes |
| MCP-SEC-TEST-018 | FUTURE DESIGN REQUIREMENT | THR-018; success/deny/error calls | complete structured secret-free audit | MCP-SEC-02 | yes |
| MCP-SEC-TEST-019 | FUTURE DESIGN REQUIREMENT | THR-019/024; oversized request/response/context | bounded denial, stable service | MCP-READ-01 | yes |
| MCP-SEC-TEST-020 | FUTURE DESIGN REQUIREMENT | THR-019/024; expensive repeats/concurrency | rate/time limit enforced | MCP-READ-01 | yes |
| MCP-SEC-TEST-021 | FUTURE DESIGN REQUIREMENT | THR-015/021; version/downgrade fixtures | unsafe version rejected | MCP-SEC-02 | yes |
| MCP-SEC-TEST-022 | FUTURE DESIGN REQUIREMENT | THR-016/017; duplicate/expired/replayed/modified proposals | dedup/TTL/version binding enforced | MCP-PROPOSE-01 | yes |
| MCP-SEC-TEST-023 | FUTURE DESIGN REQUIREMENT | THR-003; two project roots/sessions | cross-project reads denied | MCP-READ-01 | yes |
| MCP-SEC-TEST-024 | FUTURE DESIGN REQUIREMENT | THR-010/011; before/after repo/runtime snapshots | every read operation non-mutating | MCP-READ-01 | yes |
| MCP-SEC-TEST-025 | FUTURE DESIGN REQUIREMENT | THR-013/014; report-state vs validate-report facts | consistent deterministic facts | MCP-READ-01 | yes |

## MCP-SEC-01 gate

**CANONICAL REQUIREMENT.** This document satisfies the documentation gate by defining assets, actors, boundaries, flows, critical/high threat controls, candidate and forbidden tools, Git policy, precedence, identity classes, result metadata, redaction policy, limits, and the security-test matrix. MCP implementation remains not started.

| Unresolved item | Classification |
|---|---|
| SDK/protocol, transport, process model, identity mechanism, exact schemas/limits, redaction implementation, dependency policy | BLOCKS MASTER PLAN |
| Exact tool list, reusable precedence service, Git execution hardening, root confinement, blocking MCP-READ tests | BLOCKS MCP-READ-01 |
| Remote/local exposure policy, pilot client, operational monitoring/incident plan | BLOCKS MCP-PILOT-01 |
| Proposal store location, quotas, TTL, dedup, replay and approval binding | BLOCKS MCP-PROPOSE-01 |
| Portfolio/fleet integration and later semantic tools | NON-BLOCKING FUTURE |

**CANONICAL REQUIREMENT.** Before MCP-READ-01 can be authorized: the threat model must remain accepted; all critical/high threats need implemented and verified controls; no unresolved issue may change D-014; the Master Plan and read-only preflight must pass; and no MCP code may have started early.

## Residual risk

**CANONICAL REQUIREMENT.** A compromised client/host, malicious LLM output, secrets already present in Git history, weak client identity, prompt injection in legitimate content, dependency/transport compromise, human approval mistakes, and local denial of service cannot be eliminated by the facade alone. Endpoint hardening, secret rotation/history remediation, authenticated transport, dependency governance, human review training, backups, monitoring, quotas, and incident response are operational controls outside MCP.

## Deferred decisions for Master Plan

**OPEN FOR MASTER PLAN.** Select MCP SDK/protocol and transport; local-only versus remote exposure; initial in-process versus separate-process deployment; exact request/result schemas; numeric limits; identity mechanism; redaction implementation; pilot client; packaging/lifecycle; compatibility policy; and ordering relative to F7-D1 and D-013 modernization.

## Final security verdict

```text
MCP implementation status: NOT STARTED.
D-014 boundary status: unchanged.
MCP-SEC-01 result: threat model and security requirements documented.
Next permitted activity after acceptance: create the new Master Development Plan.
No MCP code may start until that plan and a read-only preflight are separately accepted.
```
