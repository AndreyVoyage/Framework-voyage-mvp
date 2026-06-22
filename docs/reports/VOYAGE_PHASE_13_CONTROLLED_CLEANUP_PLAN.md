# Voyage Phase 13 Controlled Cleanup Plan

> Date: 2026-06-22
> Branch: `docs/phase-13-controlled-cleanup-plan`
> Base: `5630679 Merge Phase 12 legacy cleanup audit`
> Source audit: `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md`
> Scope: planning only

## 1. Executive summary

### Planning scope

This plan translates the Phase 12 legacy cleanup audit into small, dependency-aware work packages for future human-approved phases. It covers canonical retention, historical retention, later moves, later deletion candidates, blocked human decisions, verification gates, and rollback.

### Recommended sequence

The safe sequence is:

1. clarify public documentation without changing behavior;
2. approve product, API, CLI, and deprecation policy;
3. collect external consumer and deployment evidence;
4. separate canonical and compatibility test reporting without deleting tests;
5. archive the nested snapshot and old documentation only after destination approval;
6. relocate legacy runtime and coupled tests only after compatibility planning;
7. align exports, metadata, dependencies, CI, release, and Pages;
8. delete only owner-approved low-risk candidates;
9. close every destructive package with an audit.

### Highest-risk dependency

`voyage_framework/agents/` and `voyage_framework/langgraph_tools/` cannot be moved independently. They are coupled to root package exports, mixed CLI handlers, `security`, `specs`, core event models, memory/improvement helpers, dedicated tests, optional LangGraph dependencies, full-suite CI, and release packaging. Their public consumer footprint is unknown.

### Planning-only confirmation

**Do not execute cleanup in Phase 13.** No file was deleted, moved, renamed, archived, deprecated, refactored, or edited by this plan. A planned disposition is not approval.

## 2. Inputs, authority, and limitations

### Source audit findings used

The plan carries forward all primary Phase 12 classifications without silent reclassification:

- canonical core and focused tests remain protected;
- historical prompts and process evidence remain retained;
- agent/LangGraph runtime, coupled tests, snapshot, and older generated docs remain move-later candidates;
- obsolete drafts and incomplete example shells remain deletion-later candidates;
- public identity, exports, CLI, packaging, non-core packages, workflows, and shared support remain human decisions.

### Canonical authority order

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. v4.1 MVP closure audit;
3. Phase 7 adapter-contract closure audit;
4. Phase 12 legacy cleanup audit as cleanup evidence;
5. current code/tests as dependency evidence;
6. `AGENTS.md` as subordinate operational guidance.

### Limitations and blocking evidence gaps

The repository provides static dependency evidence but not:

- downstream Python import telemetry;
- CLI usage or automation inventory;
- PyPI/download or release-consumer data;
- private integration information;
- Pages/release/coverage workflow ownership;
- a human-approved product identity and support matrix;
- a destination and retention policy for archived material.

These gaps block API, CLI, package, dependency, workflow, runtime, snapshot, and test removal.

## 3. Cleanup principles

1. **Protect canonical contracts first.** Legacy classification never overrides protected-file rules.
2. **Clarify before moving.** Users must understand current versus legacy behavior before paths change.
3. **Compatibility before deletion.** Public imports, CLI commands, extras, and workflows require policy and evidence.
4. **One concern per package.** Documentation, tests, snapshot, runtime, packaging, and deletions use separate prompts and commits.
5. **Moves before semantic edits.** A relocation package must preserve behavior unless its prompt explicitly authorizes more.
6. **Tests are evidence.** Compatibility tests are separated before they are considered for retirement.
7. **Human authority is mandatory.** Every move or deletion receives an exact path allowlist and owner approval.
8. **Rollback is designed first.** Every package records its base and restoration gates before implementation.
9. **Generated artifacts remain non-canonical.** `.voyage`, root `TASK.md`, and root `CONTEXT.json` are never cleanup shortcuts.
10. **No broad cleanup commit.** The program must remain revertible package by package.

## 4. Candidate register

| Path / area | Phase 12 class | Proposed disposition | Key dependencies / impact | Risk | Reversibility | Readiness | Human decision |
|---|---|---|---|---|---|---|---|
| v4.1 contract and accepted closure reports | Keep as canonical | Preserve as authority | All planning and architecture interpretation | High if changed | Difficult | Keep | Exact report/contract approval for any errata |
| Canonical core task/parser/engine/event/context/registry/mode/prompt/adapter modules | Keep as canonical | Protect in place | CLI tasks/sync, focused tests, public core imports | High | Difficult | Keep | No cleanup disposition needed |
| Canonical focused tests | Keep as canonical | Preserve; identify as canonical suite | Core regression evidence | High | Moderate | Keep | Test-policy approval before layout changes |
| Current Phase 8–12 guides/templates/static examples | Keep as canonical | Maintain as current documentation | Links, Pages, contributor onboarding | Medium | Easy | Keep | Docs governance for future edits |
| Historical prompts/process evidence | Keep as historical/archive | Retain, later index as historical | Git provenance and phase reconstruction | Low | Easy | Keep | Archive navigation policy |
| `voyage_framework/agents/` | Move later | Relocate behind explicit legacy boundary or separate distribution | Root exports, CLI, security/specs, memory/improvement, integration tests | High | Difficult | Blocked | Public API, CLI, semver, destination, consumer policy |
| `voyage_framework/langgraph_tools/` | Move later | Relocate atomically with graph runtime and tests | `agents/langgraph_runtime.py`, root exports, tests, LangGraph extra | High | Difficult | Blocked | LangGraph support and package decision |
| Legacy runtime/graph compatibility tests | Move later | Separate as compatibility suite; move with implementation later | CI, pre-commit, full-suite counts, runtime modules | High | Moderate | Blocked | Supported behavior and CI policy |
| `voyage_framework_v4_mvp/` | Move later | Archive outside active source tree or externalize | Historical links, provenance, duplicate paths | Medium | Moderate | Blocked | Destination and retention policy |
| `docs/architecture/components.md`, `docs/tutorial/02-05` | Move later | Label/currentize first; archive old variants later | Pages/navigation, generated docs tooling | Medium | Easy | Planning-ready after Package A | Current docs/navigation decision |
| TaskEngine draft text files | Candidate for deletion later | Delete only after reference/provenance proof | No imports; possible historical value | Low | Easy | Planning-ready after approval | Owner confirms no retention need |
| Incomplete `api-endpoint`, `auth-module`, `refactor-legacy` examples | Candidate for deletion later | Regenerate as static examples or delete shells | Docs links/generator expectations | Low | Easy | Blocked | Regenerate-versus-delete decision |
| Sample Jekyll Pages workflow | Candidate for deletion later, conditional | Delete only if Pages is confirmed unused; otherwise align | Deployment environment and permissions | High | Moderate | Blocked | Pages owner/use decision |
| Root `README.md` | Needs human decision | Rewrite current identity; preserve old copy only if approved | Public landing page, package readme, Pages | Medium | Easy | Blocked | Product identity and historical retention |
| `voyage_framework/__init__.py` exports/version | Needs human decision | Define supported API; deprecate before removal | Downstream imports and package version | High | Difficult | Blocked | API/semver/consumer decision |
| `voyage_framework/cli.py` mixed surface | Needs human decision | Define canonical, compatibility, deprecated, hidden, or split commands | Scripts, docs, runtime modules, contract compatibility | High | Difficult | Blocked | CLI support/deprecation window |
| `pyproject.toml` identity, extras, dependencies, version | Needs human decision | Align after product/API/runtime decisions | Installation, releases, optional consumers | High | Difficult | Blocked | Release and compatibility policy |
| `security/`, `memory/`, `improvement/`, `ast_tools/`, `chronicler/`, `specs/` | Needs human decision | Evaluate individually; keep, split, or archive | Public exports, CLI, runtime, tests, canonical shared use | High | Difficult | Blocked | Per-package ownership and consumers |
| `core/models.py`, `core/storage.py` | Needs human decision | Decompose only after dependency mapping; otherwise keep | Canonical EventEngine and legacy subsystems | High | Difficult | Not recommended now | Core architecture approval |
| `.github` CI/release/coverage/Pages workflows | Needs human decision | Align last, after test/package/docs decisions | Publishing, permissions, automated commits | High | Moderate | Blocked | Workflow ownership and release policy |

No candidate is approved for movement or deletion by this register.

## 5. Canonical and historical retention

### Keep as canonical

Protected canonical areas include:

```text
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
voyage_framework/core/task_models.py
voyage_framework/core/task_parser.py
voyage_framework/core/task_engine.py
voyage_framework/core/event_engine.py
voyage_framework/core/context_builder.py
voyage_framework/core/agent_registry.py
voyage_framework/core/prompt_modes.py
voyage_framework/core/prompt_generator.py
voyage_framework/core/adapter_contract.py
voyage_framework/core/adapter_protocols.py
```

Focused canonical tests and current user/process documentation remain retained. “Canonical” here means protected current architecture or maintained supporting documentation; the contract still outranks guides and examples.

### Keep as historical/archive

Historical prompts, process reports, and milestone evidence should remain available with clear chronological labels. They should not be rewritten mechanically when terminology evolves. Later navigation may separate them from current guidance without changing their content.

### Protected paths / never touch without approval

In addition to the canonical list, the following require exact prompt approval even when classified legacy or ambiguous:

```text
AGENTS.md
README.md
pyproject.toml
.gitignore
voyage_framework/__init__.py
voyage_framework/cli.py
voyage_framework/core/models.py
voyage_framework/core/storage.py
tests/
.github/
voyage_framework/agents/
voyage_framework/langgraph_tools/
voyage_framework_v4_mvp/
docs/architecture/
docs/tutorial/
docs/drafts/
docs/examples/
```

No wildcard cleanup approval is acceptable. Every future prompt must list exact paths.

## 6. Move-later plan

### Legacy runtime dependency group

Atomic planning group:

```text
voyage_framework/agents/
voyage_framework/langgraph_tools/
legacy runtime/graph tests
related root exports
related CLI handlers
LangGraph optional extras
documentation references
```

Preconditions:

- owner-approved public API and CLI policy;
- external consumer evidence;
- deprecation and semantic-version window;
- selected destination: legacy namespace, separate package, or archive;
- compatibility import/command decision;
- Package C test separation complete;
- package/release migration plan.

Moving only the directories would break root imports, CLI handlers, tests, and consumers. This group remains blocked.

### Snapshot archival group

Candidate: `voyage_framework_v4_mvp/` as one historical unit.

Preconditions:

- choose in-tree archive, external repository, or history-tag strategy;
- verify all documentation/source links;
- preserve authorship and history expectations;
- ensure build/package paths continue excluding the snapshot;
- record old-to-new location mapping.

This group must not be combined with runtime relocation.

### Historical documentation group

Candidates: v4.0 component page and tutorial placeholders identified by Phase 12.

Preconditions:

- Package A defines current navigation;
- Pages ownership is known;
- current replacements exist;
- generated-doc behavior is understood;
- all inbound links are inventoried.

Destination requires owner approval. Labeling can precede movement.

## 7. Delete-later plan

### Superseded drafts

Candidates:

```text
docs/drafts/_draft_task_engine.py.txt
docs/drafts/_draft_test_task_engine.py.txt
```

Required proof:

- no tracked references or generator dependencies;
- Git history preserves the design provenance;
- owner confirms the drafts are not active decision records;
- exact deletion-only prompt and rollback commit are prepared.

### Incomplete example shells

Candidates:

```text
docs/examples/api-endpoint/README.md
docs/examples/auth-module/README.md
docs/examples/refactor-legacy/README.md
```

Required decision: regenerate complete, clearly static examples or delete the empty shells. Reference and Pages checks must precede either option.

### Conditional workflow candidate

`.github/workflows/jekyll-gh-pages.yml` is not deletion-ready. It becomes a candidate only if the owner confirms Pages is unused and no deployment depends on it. Because deletion changes deployment behavior, it belongs in a workflow-specific package, not Package F by default.

### Explicit approval requirement

Every deletion package must include an exact path allowlist, reference-search evidence, owner sign-off, a clean base, a revert plan, and post-deletion verification. No candidate above is approved in Phase 13.

## 8. Human decision register

| Decision | Options | Impact | Evidence required | Owner | Blocked packages |
|---|---|---|---|---|---|
| Product identity | v4.1/v4.2 current; dual product; or v4.0 compatibility product | README, metadata, docs, release messaging | Roadmap and support statement | Repository owner | A, B, G |
| Public Python API | Keep, deprecate, split, or remove legacy exports | Downstream imports and semver | Consumer/import telemetry | Owner/API maintainer | B, E, G |
| Legacy CLI | Keep visible, deprecate, hide, split, or remove | Scripts and contract compatibility | Usage inventory and support promise | Owner/CLI maintainer | B, E, G |
| LangGraph support | Keep extra, separate package, deprecate, or retire | Dependency and runtime consumers | Installation/release usage | Owner | E, G |
| Non-core packages | Keep support, split, archive, or retire per package | Public exports, tests, shared dependencies | Per-module dependency/consumer map | Owner/maintainers | E, G |
| Canonical vs compatibility tests | Mark, move, split CI, or retain combined | Gate meaning and regression coverage | Supported behavior matrix | QA/owner | C, E, G |
| Snapshot retention | In-tree archive, external repo, tag-only, or delete later | Provenance and navigation | Link/history requirements | Owner | D |
| Historical docs destination | Currentize, label in place, or archive | Pages and onboarding | Navigation and link inventory | Docs owner | A, D |
| Draft/example disposition | Keep, regenerate, archive, or delete | Low-risk docs cleanup | Reference search and owner intent | Docs owner | F |
| CI/release/Pages ownership | Preserve, narrow, replace, or remove selected workflow | Publishing and automation permissions | Deployment and secrets ownership | Release owner | C, G |
| Historical report errata | Immutable reports, add errata, or approved amendment | Accuracy and audit governance | Governance rule | Owner | A |
| Cleanup release/rollback milestone | Patch, minor, major, or no release | Consumer recovery | API/CLI change set | Release owner | E, G |

Until decisions are recorded, blocked packages remain planning-only.

## 9. Work package roadmap

### Package A — Public documentation clarification

- **Objective:** make canonical versus legacy identity explicit in current public docs.
- **Candidate paths:** exact paths must be approved; likely root README and current navigation pages.
- **Prerequisites:** product identity decision; report errata policy.
- **Anti-scope:** no code, CLI, tests, dependencies, exports, workflows, or moves.
- **Approval:** owner and docs owner.
- **Risk:** low-to-medium; public messaging impact.
- **Future prompt:** documentation-only exact allowlist.
- **Gates:** link checks, claim scan, forbidden diff, Pages preview if approved.
- **Rollback:** revert one documentation commit.
- **Exit:** new readers see current/legacy distinction before runtime claims.
- **Unblocks:** B, D documentation group, parts of G.

### Package B — Legacy labeling and deprecation policy

- **Objective:** define canonical, compatibility, deprecated, historical, and unsupported surfaces.
- **Candidate paths:** policy/report outputs first; implementation paths await decisions.
- **Prerequisites:** API, CLI, product, semver decisions.
- **Anti-scope:** no relocation or deletion.
- **Approval:** repository owner and API/CLI maintainers.
- **Risk:** medium; creates support commitments.
- **Future prompt:** policy-only, then separate behavior prompts if selected.
- **Gates:** complete surface inventory, consumer evidence, migration review.
- **Rollback:** retract policy before implementation; preserve prior support statement.
- **Exit:** each public export/command/package has an approved status and timeline.
- **Unblocks:** C, E, G.

### Package C — Test and CI separation

- **Objective:** report canonical-core and legacy-compatibility evidence separately without deleting tests.
- **Candidate paths:** exact test/config/workflow paths selected by QA and owner.
- **Prerequisites:** supported behavior matrix from B.
- **Anti-scope:** no implementation removal and no reduction in total required evidence.
- **Approval:** QA and release owner.
- **Risk:** medium-to-high; gate semantics and automation.
- **Future prompt:** test/config-only exact allowlist.
- **Gates:** old and new suites both pass; counts reconcile; CI matrix validates both.
- **Rollback:** revert suite/config split as one commit.
- **Exit:** canonical and compatibility outcomes are independently visible.
- **Unblocks:** D, E, G.

### Package D — Snapshot and historical documentation archival

- **Objective:** remove duplicate navigation hazards from active source/docs layout while preserving history.
- **Candidate paths:** snapshot and selected historical docs; exact destination awaits approval.
- **Prerequisites:** retention/destination decisions, A, link inventory, C for snapshot tests if relevant.
- **Anti-scope:** no runtime relocation, semantic edits, or deletion.
- **Approval:** owner and docs/history owner.
- **Risk:** medium; provenance and links.
- **Future prompt:** move-only with explicit source/destination map.
- **Gates:** Git rename verification, link checks, package-content check, unchanged canonical tests.
- **Rollback:** inverse path map or revert the move-only commit.
- **Exit:** archive is clearly labeled and active paths contain no duplicate package tree.
- **Unblocks:** later optional archive pruning.

### Package E — Legacy runtime relocation

- **Objective:** isolate agent/LangGraph runtime and coupled tests behind an approved compatibility boundary.
- **Candidate paths:** exact dependency group selected after B/C; never directories alone.
- **Prerequisites:** A, B, C, consumer evidence, destination, deprecation window, semver/release plan.
- **Anti-scope:** no behavior rewrite and no deletion unless separately approved.
- **Approval:** owner, API/CLI, QA, security, release maintainers.
- **Risk:** high; imports, CLI, packaging, tests, shared events/security.
- **Future prompt:** move/import-migration scope with explicit compatibility behavior.
- **Gates:** canonical and compatibility suites, import/CLI smoke, packaging, optional extras, security review.
- **Rollback:** revert relocation and restore exports/handlers in reverse dependency order.
- **Exit:** canonical package no longer exposes runtime accidentally; approved compatibility path works.
- **Unblocks:** G and future retirement planning.

### Package F — Low-risk deletion candidates

- **Objective:** remove only owner-approved drafts or incomplete placeholders with proven zero active references.
- **Candidate paths:** exact files from section 7; no wildcard directories.
- **Prerequisites:** reference proof, owner decision, archive/provenance decision.
- **Anti-scope:** no code, tests, runtime, package, workflow, or unrelated docs.
- **Approval:** owner and docs owner.
- **Risk:** low per file; irreversible without Git history.
- **Future prompt:** deletion-only exact allowlist.
- **Gates:** reference search before/after, docs links, changed-file equality, diff check.
- **Rollback:** revert the single deletion commit.
- **Exit:** only approved paths are absent and documentation remains coherent.
- **Unblocks:** none; optional hygiene package.

### Package G — Packaging and workflow alignment

- **Objective:** align root exports/version, metadata/extras, CI, release, coverage, and Pages with approved product/runtime policy.
- **Candidate paths:** exact files selected after earlier packages.
- **Prerequisites:** A–C decisions; E if runtime moves; release and deployment ownership.
- **Anti-scope:** no unapproved API/CLI retirement and no automatic release/tag.
- **Approval:** owner, release owner, API/CLI maintainers, security reviewer.
- **Risk:** high; installation and publishing behavior.
- **Future prompt:** split metadata/export and workflow changes when possible.
- **Gates:** editable install, wheel/sdist inspection, imports, CLI, all required suites, workflow validation, release dry-run.
- **Rollback:** restore last compatible package metadata/workflows; publish corrective release only with approval.
- **Exit:** packaged and published identity matches the approved architecture and compatibility promise.
- **Unblocks:** closure audit and any future legacy retirement.

## 10. Safe execution order

1. **A:** clarify documentation after owner selects product identity.
2. **B:** approve and publish API/CLI/deprecation policy.
3. Gather external imports, CLI usage, release, Pages, and deployment evidence.
4. **C:** separate test/CI reporting without deletion.
5. **D:** archive snapshot and historical docs after destination approval.
6. **E:** relocate legacy runtime as one dependency-aware program.
7. **G:** align public packaging and automation after runtime/API outcomes are known.
8. **F:** delete only explicit low-risk paths; F may occur after A when its own evidence is complete, but never as part of E/G.
9. Run a closure audit after D, E, F, and G.

### Stop conditions

Stop a future package when:

- branch/base or working tree differs from its prompt;
- a changed file is outside the allowlist;
- a dependency or external consumer is newly discovered;
- human decisions are missing;
- tests, imports, CLI, packaging, docs links, or workflows fail;
- generated/runtime artifacts appear;
- the change requires semantic work outside the approved package;
- rollback cannot be demonstrated.

## 11. Verification gates

### Scope and repository

- exact branch/base/tag verification;
- clean pre-state and explicit changed-file equality;
- forbidden-path diff and `git diff --check`;
- no `.voyage`, root `TASK.md`, or root `CONTEXT.json` pollution;
- one package per reviewed commit.

### Tests and canonical behavior

- targeted tests for affected modules;
- TaskParser, TaskEngine, EventEngine, ContextBuilder regressions;
- AgentRegistry, ModeRegistry, PromptGenerator, AdapterContract regressions;
- canonical unit suite;
- compatibility suite where promised;
- full suite or an approved explanation of separated suites with exact counts.

### Public API and CLI

- supported root import smoke tests;
- direct canonical core imports;
- CLI help snapshot;
- supported `tasks` and `sync` command checks;
- legacy command behavior during any promised window;
- migration/deprecation documentation review.

### Packaging and dependencies

- editable install;
- wheel and sdist builds;
- archive content inspection to exclude unintended paths;
- base and approved optional-extra import checks;
- dependency resolution and package version review;
- approved release workflow dry-run.

### Documentation and workflows

- internal links/navigation;
- canonical/legacy claim scan;
- Pages source/output review;
- workflow syntax, triggers, permissions, secrets, and auto-commit review;
- no publication, tag, or deployment without explicit authority.

### Quality and closure

- Ruff check/format and strict mypy for code packages;
- exact pytest outcomes;
- security review for runtime, subprocess, Docker, approvals, or workflow changes;
- human diff review;
- package-specific closure audit.

## 12. Rollback strategy

### Package-level rollback

Each future prompt must record the exact pre-change commit and use one narrow commit per concern. Move-only packages keep an old-to-new path map and avoid semantic edits. Rollback reverts packages in reverse dependency order and re-runs the same gates used for acceptance.

- **A/B:** revert documentation/policy commits before dependent implementation begins.
- **C:** restore prior test/config grouping and verify original full suite.
- **D:** restore paths through the inverse map and recheck links/package exclusions.
- **E:** restore runtime paths, imports, exports, handlers, tests, and extras as one coordinated rollback.
- **F:** revert the exact deletion commit; do not reconstruct content manually.
- **G:** restore metadata/workflows and the last compatible package behavior; corrective publication needs separate approval.

### Program-level rollback

Preserve the last compatible release/tag and cleanup base. If a dependent package fails, stop later work and revert back through dependency order. Record which API, CLI, package, test, docs, and workflow states are restored. A rollback receives its own verification report.

No rollback branch, tag, release, or compatibility shim is created in Phase 13.

## 13. Future prompt boundaries

Every future implementation prompt must include:

- one work package only;
- exact allowed files and explicit forbidden files;
- approved human decisions and evidence prerequisites;
- exact branch/base and rollback commit;
- behavior-preserving or behavior-changing designation;
- explicit anti-scope;
- package-specific tests and gates;
- expected changed files;
- pollution and forbidden checks;
- commit/push/merge authority;
- closure report format.

Broad permissions such as “cleanup legacy code” or directory wildcards are insufficient. Destructive commands must never be inferred from this plan.

## 14. Do not execute cleanup in this phase

Phase 13 performed planning only.

- No file or directory was deleted.
- No file or directory was moved, renamed, copied, or archived.
- No code, tests, CLI, dependencies, exports, workflows, or existing documentation were changed.
- No deprecation policy was activated.
- No compatibility shim or migration was created.
- No runtime state, model call, provider call, deployment, release, commit, push, merge, or tag was performed.

All dispositions and work packages remain proposals pending explicit human selection and future prompts.

## 15. Forbidden-files and pollution check

At plan creation time, the only intended change is:

```text
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

Final gates must confirm:

- all existing reports are unchanged;
- contracts, root docs, code, tests, metadata, snapshot, and workflows are unchanged;
- `.voyage`, root `TASK.md`, and root `CONTEXT.json` are unchanged;
- no cleanup action occurred.

## 16. Verdict

**B. Plan complete with blocked decisions/evidence gaps.**

The plan is complete enough for the human owner to select Package A or to resolve the product/API/CLI decisions that unlock later packages. Packages D–G remain blocked until their specified evidence and approvals exist. Nothing in this plan authorizes cleanup execution.
