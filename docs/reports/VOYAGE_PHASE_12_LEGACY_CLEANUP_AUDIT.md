# Voyage Phase 12 Legacy Cleanup Audit

> Date: 2026-06-22
> Branch: `docs/phase-12-legacy-cleanup-audit`
> Base: `366b43b Merge Phase 11 end-to-end demo scenario`
> Scope: documentation audit only

## 1. Executive summary

### Audit scope

This audit inspected the tracked repository structure, canonical v4.1/v4.2 documents, active package exports, CLI surfaces, tests, documentation, nested snapshot, packaging metadata, and GitHub workflows. It classified material areas without deleting, moving, renaming, or changing them.

### Overall finding

The canonical v4.1 MVP and Phase 7 adapter-contract boundary are identifiable and internally usable: canonical task intent is `task.yaml`; runtime task state is `TaskRecord` managed by `TaskEngine`; `EventEngine` is append-only audit; registry, mode, prompt, context, and adapter-contract layers are read-only or interface-only as documented.

The repository nevertheless exposes two architectural identities at the same time:

1. the accepted Development Memory System / Project Knowledge Operating System described by the v4.1 contract and current guides; and
2. a still-importable, tested, packaged, documented, and CLI-visible v4.0 agent-runtime system.

The second identity is not merely dead text. `voyage_framework/__init__.py`, `voyage_framework/cli.py`, runtime modules, tests, optional dependencies, root documentation, and CI all keep it operationally visible. Cleanup therefore cannot be treated as simple deletion.

### Highest-risk ambiguity

The highest-risk ambiguity is the public entry surface. `README.md:1-10`, `voyage_framework/__init__.py:1-10`, `pyproject.toml:8`, and `voyage_framework/cli.py:876-1017` advertise or expose agent execution and LangGraph behavior, while `AGENTS.md:33-43,149` and the accepted closure reports state that those capabilities are not v4.1 core. A new user or agent can reach the legacy identity before reading the canonical contract.

The contract itself preserves old CLI commands for compatibility (`docs/VOYAGE_V4_1_CONTRACT.md:331-380`), including `voyage run` and `voyage graph run`. This is compatible with “legacy commands remain unbroken,” but it is easily confused with “runtime execution is a current v4.1 capability.” The distinction needs a human-approved public compatibility policy.

### Audit-only confirmation

No cleanup was performed. No code, tests, CLI, dependencies, existing documentation, workflows, generated artifacts, or runtime state were changed. This report is the only Phase 12 output.

## 2. Method and evidence

### Read-only methods

The audit used:

- `rg --files`, `git ls-files`, and directory inventory;
- keyword and import searches for architecture, runtime, orchestration, provider, legacy, and lifecycle terms;
- static inspection of contracts, reports, root documentation, Python exports, CLI parsers, tests, metadata, workflows, tutorials, examples, and drafts;
- relative-path and SHA-256 comparison between the active package and the nested snapshot;
- path-specific Git history;
- tracked-artifact and pollution checks.

No runtime command, `TaskEngine`, `EventEngine`, database creation, provider, model, or network client was invoked.

### Canonical authority order

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md`;
3. `docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`;
4. current root implementation evidence;
5. `AGENTS.md` as operational guidance.

Current Phase 8–11 guides are useful maintained documentation but do not replace the architecture contract.

### Evidence limitations

- No external package-consumer, PyPI download, downstream import, or CLI-usage telemetry was available.
- No remote branches, issues, deployment environment, or private integrations were inspected.
- Static imports and tests prove repository coupling, not external compatibility requirements.
- The audit did not execute the full suite because this phase is documentation-only and runtime creation is prohibited.
- “Candidate for deletion later” means only that repository evidence is weak; it is not proof that no user depends on the item.

## 3. Canonical v4.1/v4.2 core

### Source-of-truth hierarchy

| Concern | Canonical source | Generated or supporting material |
|---|---|---|
| Task intent | `task.yaml` parsed into frozen `TaskYamlSpec` | Legacy `TASK.md` is generated and non-canonical |
| Runtime task state | `TaskRecord` in SQLite, mutated by `TaskEngine` | `CONTEXT.json` may describe state but is non-canonical |
| Audit | Append-only `EventEngine` events | Reports and demo audit trails are documentation |
| Context | `ContextBuilder` aggregates canonical sources | Generated `CONTEXT.json` is replaceable |
| Roles | Read-only `AgentRegistry` | Role descriptions do not execute agents |
| Prompt modes | Read-only `ModeRegistry` | Mode selection does not activate a workflow |
| Prompt preparation | Deterministic `PromptGenerator` / `PromptPackage` | Manual transfer to external tools |
| Adapter boundary | Frozen Phase 7 models and abstract `AdapterProtocol` | No adapter runtime or provider client |

### Contract-backed modules

Keep as canonical:

```text
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

`voyage_framework/core/models.py` and `storage.py` are active shared support used by both canonical and legacy areas. They cannot be classified as disposable merely because much of their model surface predates v4.1.

### Supported v4.1-oriented CLI surfaces

The unambiguous v4.1 surfaces are:

- `voyage tasks create/list/show/start/block/unblock/complete/fail/archive`;
- `voyage sync build/check/status`;
- legacy singular `voyage task` only as a generated `TASK.md` / `CONTEXT.json` producer, never as canonical task input.

`voyage run`, `voyage graph`, improvement, documentation-generation, and other older commands remain in the parser. Their preservation is contractually acknowledged as backward compatibility, but they are not evidence that agent execution is v4.1 core.

### v4.2 adapter-contract boundary

Phase 7 added interface definitions only. `AdapterProtocol` declares `validate_request`, `create_task`, `get_context`, `request_prompt`, `submit_result`, and `request_approval`; it does not implement them. The Phase 7 closure report incorrectly names `prepare_task_request` at `docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md:27`, while the implementation uses `create_task` at `voyage_framework/core/adapter_protocols.py:24`. This is a documentation defect for a later report-correction phase, not authority to change the interface.

## 4. Repository inventory

| Area | Current role | Evidence | Initial risk |
|---|---|---|---|
| Canonical contract and closure audits | Architecture authority and milestone evidence | Contract plus v4.1/Phase 7 reports | Low |
| Canonical core modules | Task, runtime state, audit, context, catalogs, prompt, adapter contract | Contract and focused unit tests | Low |
| Root `README.md` | Public landing page for v4.0 identity | `README.md:1-10,54,74,221-230` | High |
| Root package exports | Public Python API dominated by v4.0 services | `voyage_framework/__init__.py:1-59` | High |
| Mixed CLI | Canonical task/context commands plus legacy agent/graph/docs behavior | `voyage_framework/cli.py:881-1131` | High |
| `agents/` | Executable `AgentRuntime` and `LangGraphRuntime` | Imports, CLI handlers, integration tests | High |
| `langgraph_tools/` | LangGraph wrapper and pure-Python fallback | Eight tracked modules and unit tests | High |
| `security/` | Policy, sandbox, approval, audit, Docker backend | Used by legacy runtime and tests | Medium |
| `memory/`, `improvement/`, `ast_tools/` | v4.0 semantic/self-improvement/indexing features | Public exports and dedicated tests | Medium |
| `chronicler/` | Process documentation helpers | CLI, docs generation, tests; contract mentions chronicler use | Medium |
| `specs/` | Legacy `TaskGenerator` and acceptance tracking | Singular CLI and regression tests | Medium |
| Root `tests/` | Mixed canonical and legacy regression suites | 38 tracked files | High |
| `pyproject.toml` | Packaging and dependency contract | v4.0 description; `langgraph` extra; `all` extra | High |
| `.github/workflows/` | CI, release, Pages automation | Full mixed suite, package build, auto-commit/deploy | Medium |
| `docs/guides/`, adapter/e2e examples, templates | Current v4.1/v4.2 user/process documentation | Explicit negative runtime boundaries | Low |
| `docs/architecture/`, `docs/tutorial/` | Generated v4.0 public API/tutorial placeholders | LangGraph/runtime names without legacy label | High |
| `docs/drafts/` | Superseded TaskEngine drafts | Stale `TaskManager`, `TaskStatus`, SQLAlchemy wording | Medium |
| Placeholder example directories | READMEs pointing to absent generated files | Three directories contain only README | Medium |
| `voyage_framework_v4_mvp/` | Earlier parallel snapshot | 30 tracked files; 16 duplicate relative paths; compared files diverge | High |
| Historical prompts and process reports | Phase provenance and decision evidence | Chronological, often scoped and negative | Low |
| Local ignored artifacts | `.voyage`, caches, `dist`, egg-info, virtualenv | Ignored; none tracked or changed | Low |

## 5. Classification matrix

| Path / area | Primary classification | Confusion risk | Compatibility risk | Evidence | Recommended later action |
|---|---|---:|---:|---|---|
| `docs/VOYAGE_V4_1_CONTRACT.md`, v4.1 and Phase 7 closure reports | Keep as canonical | Low | High | Accepted authority chain | Preserve; correct factual report defects only through an approved documentation phase. |
| Canonical core modules listed in section 3 | Keep as canonical | Low | High | Contract, tests, CLI task/context integration | Protect as active core. |
| Canonical focused tests (`test_task_*`, CLI tasks/sync, context, registries, prompts, adapters) | Keep as canonical | Low | High | Direct coverage of accepted components | Keep with core; separate from legacy suites only in a planned test-layout phase. |
| Phase 8–11 guides, templates, and explicit static examples | Keep as canonical | Low | Medium | Current negative boundaries and source-of-truth guidance | Maintain as current user/process documentation, subordinate to contract. |
| Historical phase prompts and process audit history | Keep as historical/archive | Low | Low | Useful provenance; dates and phase scope are explicit | Retain; later add archive/index labeling rather than rewrite history. |
| `voyage_framework/agents/`, `voyage_framework/langgraph_tools/` | Move later | High | High | Explicitly legacy in `AGENTS.md`, but imported/exported/tested | After usage study, move behind a `legacy` namespace or separate package with a deprecation window. |
| Legacy runtime/integration tests (`test_langgraph*`, full/memory/self-improvement workflows) | Move later | High | High | Tests make non-core runtime look first-class | Move with legacy implementation; keep running during a compatibility window. |
| `voyage_framework_v4_mvp/` | Move later | High | Medium | Nested installable-looking snapshot; 16 duplicate paths; all sampled pairs diverge | Relocate to a clearly non-package archive or external historical tag after verifying provenance needs. |
| `docs/architecture/components.md` and `docs/tutorial/02-05` | Move later | High | Low | Public v4.0 API list and agent/LangGraph placeholders | Move to a labeled historical docs area or regenerate from current architecture. |
| `docs/drafts/_draft_task_engine.py.txt`, `_draft_test_task_engine.py.txt` | Candidate for deletion later | Medium | Low | Superseded APIs and terminology; not imported | Confirm no decision provenance depends on them, then delete in a dedicated cleanup phase. |
| `docs/examples/api-endpoint/`, `auth-module/`, `refactor-legacy/` | Candidate for deletion later | Medium | Low | README points to `TASK.md`/`CONTEXT.json` files that are absent | Either regenerate as clearly static examples or delete empty placeholders later. |
| Root `README.md` | Needs human decision | High | Medium | v4.0 agent-runtime claims are the public landing page | Decide whether to rewrite as v4.1/v4.2 current docs or preserve a historical README elsewhere. |
| `voyage_framework/__init__.py` public exports and version | Needs human decision | High | High | Imports `LangGraphRuntime`; exports legacy API; reports `4.0.0` | Define supported public API and semver/deprecation policy before changing exports. |
| `voyage_framework/cli.py` mixed command surface | Needs human decision | High | High | Canonical and legacy handlers share one parser; contract says old commands stay unbroken | Define which commands remain supported, hidden, deprecated, or split before editing. |
| `pyproject.toml` metadata and optional extras | Needs human decision | High | High | v4.0 AI-Native description; LangGraph extra; package consumers unknown | Align only after release/API policy and external consumer assessment. |
| `security/`, `memory/`, `improvement/`, `ast_tools/`, `chronicler/`, `specs/` | Needs human decision | Medium | High | Non-core but active imports, CLI surfaces, public exports, tests | Evaluate each as support, legacy, or separate package; do not bulk-delete. |
| `.github/workflows/ci.yml`, `release.yml`, `jekyll-gh-pages.yml` | Needs human decision | Medium | High | CI validates mixed suite; release packages it; Pages publishes root; coverage job auto-commits | Align workflows after package/docs decisions; preserve release controls until replacement exists. |
| `core/models.py` and `core/storage.py` mixed shared support | Needs human decision | Medium | High | Canonical `EventEngine` and legacy subsystems share them | Decompose only after dependency mapping; immediate removal would break core. |

## 6. Misleading architecture claims

### Present-tense AI Agent Framework claims

Verified high-risk claims:

- `README.md:1,8-10` names “Voyage AI Dev Framework v4.0,” calls it AI-Native, and reports LangGraph integration as runnable.
- `README.md:54,74,221-230` presents `AgentRuntime`, `LangGraphRuntime`, and graph tooling as current features.
- `voyage_framework/__init__.py:1-10` repeats the v4.0 AI-Native identity and imports `LangGraphRuntime` at package import time.
- `pyproject.toml:8` publishes the v4.0 AI-Native description.
- `voyage_framework/cli.py:876` identifies the CLI as “Voyage AI Dev Framework v4.0.”
- `docs/architecture/components.md:6-31` lists the old public API, including `LangGraphRuntime` and `VoyageGraphBuilder`, without a legacy label.

These claims are factually connected to code still present. The problem is not that the code is imaginary; it is that readers cannot tell that it is outside the accepted v4.1 core.

### Runtime and orchestration claims

- `voyage_framework/cli.py:888-903` exposes `voyage run` with subprocess/Docker backends.
- `voyage_framework/cli.py:1006-1043` exposes LangGraph visualize/run/state commands.
- `voyage_framework/agents/runtime.py:26` implements `AgentRuntime`.
- `voyage_framework/agents/langgraph_runtime.py:35` implements `LangGraphRuntime`.
- `voyage_framework/langgraph_tools/graph_builder.py:12-20` imports LangGraph when installed and otherwise uses a fallback.
- `tests/integration/test_full_workflow.py`, `test_langgraph_workflow.py`, `test_memory_workflow.py`, and `test_self_improvement.py` exercise those paths as working behavior.

`AGENTS.md` labels `agents/` and `langgraph_tools/` as legacy/historical, but the code directories themselves, public exports, CLI help, and tests do not carry a consistent deprecation boundary. They are therefore not clearly isolated.

### Provider and model claims

No active code import of OpenAI, Anthropic, CrewAI, or AutoGen was found, and no such base or optional dependency was found. Their occurrences are negative boundaries, prompts, reports, or examples. LangGraph is different: it is an actual optional dependency and active import path.

### Safe historical, negative, and future references

Current guides, adapter examples, Phase 11 demo, Phase 5–12 prompts, and process reports usually state explicitly that agents/models/providers are not executed. Those are safe boundary statements. Historical prompts should remain evidence, not be mechanically rewritten to current terminology.

### Documentation defects inside otherwise authoritative reports

- Phase 7 closure audit line 27 says `prepare_task_request`; actual protocol uses `create_task`.
- Phase 7 closure audit lines 273-289 reserve “Phase 8” for runtime work, but completed Phase 8 is documentation-only. The text is stale future planning, not implemented architecture.
- v4.1 closure audit “What Was NOT Added” uses check marks beside forbidden capabilities (`lines 155-179`). In context it means “correctly not added,” but the glyph/text combination can be misread.

These should be corrected or annotated later without rewriting historical verdicts.

## 7. Legacy runtime and orchestration surfaces

### Modules

`agents/` and `langgraph_tools/` are the clearest legacy runtime cluster. They also depend on `security`, `specs`, core event models, and improvement/memory helpers. Removing only the two named directories would leave imports and public exports broken.

The root package imports the graph runtime eagerly. Consequently, the legacy boundary is part of the current Python public surface even when LangGraph itself is absent (the fallback keeps portions importable).

### CLI

The CLI combines at least four layers:

1. canonical task/runtime state (`tasks`);
2. canonical-derived context (`sync`);
3. preserved legacy generators and process tools (`task`, `events`, chronicler/docs/evaluate);
4. executable legacy agent/graph surfaces (`run`, `graph run`).

The v4.1 contract explicitly says old commands must not break. A cleanup phase must therefore choose between compatibility, deprecation, hiding, extraction, or removal; it cannot infer permission to delete commands from their non-core status.

### Tests

The full test suite includes legacy runtime, graph, Docker, semantic memory, self-improvement, and generated-doc workflows. Passing the full suite demonstrates repository behavior, not v4.1 core membership. Current test organization gives new contributors no immediate way to distinguish canonical contract tests from compatibility tests.

A later phase should introduce test markers or directory separation before removing implementation. Until then, deleting legacy tests would remove compatibility evidence and could mask consumer breakage.

### Dependencies and packaging

- Root package metadata remains version `4.0.0` and uses an AI-Native description.
- The optional `langgraph` group installs `langgraph>=0.2` and `langchain>=0.3`.
- The `all` extra includes the LangGraph group.
- The package finder excludes `voyage_framework_v4_mvp`, which reduces accidental wheel duplication, but the snapshot remains visible in source checkouts.
- Release workflow packages the complete active root module surface on `v*` tags.

External usage is unknown. Public export or dependency removal requires a release and migration decision.

## 8. Duplicate and snapshot analysis

### `voyage_framework_v4_mvp/`

The nested snapshot contains 30 tracked files, including its own README, metadata, workflow, tests, and package tree. Sixteen paths duplicate active package-relative names. Sampled duplicate files (`__init__.py`, CLI, runtime, EventEngine, models, storage, policy, and TaskGenerator) all have different SHA-256 hashes from the active versions.

This creates three hazards:

- agents can edit the wrong copy;
- searches return conflicting v4.0 claims and APIs;
- the directory looks independently installable despite being excluded by root packaging.

The snapshot may still be valuable provenance. Move it later to a clearly labeled archive, external repository, or historical tag only after the owner decides how much in-tree history is required.

### Other duplicates and generated artifacts

- Root tracked files do not include `.voyage`, `TASK.md`, `CONTEXT.json`, caches, `dist`, or egg-info.
- Those artifacts exist locally in ignored form but were unchanged and are not repository truth.
- `docs/examples/e2e-demo/CONTEXT.example.json` and `TASK.example.md` are explicitly marked static/non-canonical and are safe.
- Three older example directories reference missing generated artifacts, making them incomplete rather than canonical examples.
- TaskEngine draft text duplicates obsolete design concepts and names that differ from current code.

## 9. Cleanup candidates for later phases

### Documentation-only clarifications first

Recommended lowest-risk next step:

1. Add a prominent current-vs-legacy boundary to root `README.md`.
2. Label `docs/architecture/components.md` and tutorials 02–05 as historical/generated placeholders or remove them from current navigation.
3. Add deprecation banners to legacy CLI help/docs and module docstrings without changing behavior.
4. Correct `create_task` naming and stale Phase 8 future wording through a dedicated report errata document or approved report edit.
5. Document that full-suite legacy tests are compatibility tests, not canonical-core definition.

These changes require a separate documentation prompt because Phase 12 authorizes only this report.

### Move/archive candidates

After documentation clarity and usage discovery:

- move `agents/` and `langgraph_tools/` behind an explicit legacy namespace or separate distribution;
- move their integration/unit tests with them;
- move `voyage_framework_v4_mvp/` out of the active source tree;
- move generated v4.0 architecture/tutorial pages to a historical documentation section.

### Deletion candidates

Low-evidence candidates for a later cleanup phase:

- obsolete TaskEngine draft text files;
- empty legacy example shells that reference absent outputs;
- sample Jekyll workflow if the owner confirms Pages is not used.

No deletion should occur until `git log`, external links, release use, and human ownership are checked.

### Required prerequisites

- supported public API list;
- CLI compatibility and deprecation policy;
- external consumer/import evidence;
- package versioning and migration plan;
- CI split between canonical and legacy compatibility suites;
- documentation navigation plan;
- rollback commit or release branch for every destructive phase.

## 10. Human decisions required

| Decision | Options | Impact | Evidence still needed |
|---|---|---|---|
| Public product identity | Rewrite root surfaces to v4.1/v4.2; preserve v4.0 under history; or maintain dual products | User and contributor expectations | Owner product roadmap |
| Legacy Python API | Keep, deprecate, split package, or remove | Import compatibility and semver | Downstream import telemetry |
| Agent/graph CLI | Keep visible, hide, deprecate, split, or remove | Scripts and user workflows | CLI usage and support promise |
| LangGraph extra | Retain compatibility extra or remove in major release | Dependency footprint | Consumer and release data |
| Non-core support modules | Keep support libraries, archive, or split | Tests, CLI, public exports | Per-module ownership and consumers |
| Nested snapshot | In-tree archive, history tag, separate repo, or deletion | Provenance and navigation | Human retention requirement |
| Legacy tests | Keep full suite, mark compatibility, move, or retire | Regression signal and CI cost | Supported behavior matrix |
| CI/release/Pages | Preserve, narrow, or replace workflows | Publishing and automation | Deployment ownership and secrets configuration |
| Historical report errata | Add errata, amend reports, or leave immutable | Accuracy versus audit immutability | Documentation governance decision |

## 11. Risks and sequencing

### Recommended non-destructive order

1. Approve a public architecture/compatibility policy.
2. Clarify root documentation and legacy labels without changing behavior.
3. Inventory external imports, CLI use, releases, and deployments.
4. Split CI/test reporting into canonical and compatibility groups.
5. Deprecate public exports and commands with a stated window.
6. Move legacy code/tests/snapshot while retaining a rollback reference.
7. Remove only evidence-backed candidates in a separate cleanup phase.
8. Re-run full tests, package builds, docs checks, and release verification after each step.

### Compatibility and migration risks

- Removing eager root exports can break `from voyage_framework import ...` consumers.
- Removing CLI commands can break scripts even though commands are non-core.
- Moving shared `core/models.py` or `storage.py` can break canonical EventEngine behavior.
- Deleting legacy tests before implementation removal can conceal regressions.
- Removing optional extras is a packaging and semver change.
- Moving the snapshot can break documentation links or external source references.
- Narrowing CI or release workflows can reduce coverage or alter published artifacts.

### Rollback considerations

Every later cleanup phase should use narrow commits by category, preserve the last compatible tag/branch, document path mappings, and avoid combining documentation clarification with code deletion. A failed migration should be revertible without reconstructing files from this audit.

## 12. Forbidden-files and pollution check

At report creation time:

- the only intended change is `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md`;
- no Python, tests, root docs, metadata, workflows, existing reports, or snapshot files were changed;
- `.voyage`, root `TASK.md`, and root `CONTEXT.json` were unchanged;
- no cleanup, runtime creation, model/provider call, commit, push, merge, or tag was performed.

Final Git checks must confirm these statements before handoff.

## 13. Verdict

**B. Audit complete with evidence gaps.**

The repository is ready for human cleanup planning, beginning with a documentation-only clarification phase. External consumer, CLI usage, release, and deployment evidence is missing, so no code, API, CLI, dependency, workflow, snapshot, or test deletion is safe to authorize from this audit alone.
