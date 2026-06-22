# Phase 13 — Controlled Cleanup Plan

## 0. Stop-gate

Before making any changes, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git --no-pager log --oneline --decorate -10
git tag --list "v4.1.0-mvp"
git tag --list "v4.2.0-adapter-contract"
```

Expected:

```text
Branch: docs/phase-13-controlled-cleanup-plan
Base: main
main contains: 5630679 Merge Phase 12 legacy cleanup audit
Working tree: clean
```

If the repository, branch, base, or working tree is unexpected, stop and report. Do not repair unrelated changes.

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 14.

---

## 1. Mission

Create **Phase 13: Controlled Cleanup Plan**.

Phase 13 converts the evidence and classifications in:

```text
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
```

into a safe, staged, reversible cleanup plan for later human-approved phases.

Phase 13 is **planning-only**. It must not execute any cleanup action.

The only permitted output is:

```text
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

---

## 2. Canonical authority and inputs

Use this authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md`;
3. `docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`;
4. `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md` as the cleanup evidence source;
5. current tracked implementation and tests as dependency evidence;
6. `AGENTS.md` as subordinate operational guidance.

The Phase 12 report is an audit, not deletion authority. Preserve its distinctions between facts, inferences, recommendations, and evidence gaps. If current repository evidence conflicts with Phase 12, record the conflict in the plan; do not edit either source.

Generated `TASK.md` and `CONTEXT.json` are not canonical truth.

---

## 3. What Phase 13 is

Phase 13 must create a plan that:

- lists every material Phase 12 cleanup candidate;
- states what should remain canonical;
- states what should remain historical/archive;
- identifies what may be moved later;
- identifies what may be deleted later;
- preserves all items that still need a human decision;
- maps dependencies, public interfaces, tests, packaging, CI, docs, and compatibility risks;
- breaks future cleanup into small, separately approved work packages;
- orders work packages from least destructive to most destructive;
- defines stop-gates, rollback strategies, and verification evidence for each package;
- lists protected paths that no future cleanup package may touch without explicit approval;
- names evidence gaps that block destructive work.

---

## 4. Do not execute cleanup in this phase

**Do not execute cleanup in this phase.**

Phase 13 must not:

```text
- delete files or directories;
- move, rename, archive, or copy files;
- edit Python code;
- edit tests;
- refactor imports or public exports;
- hide, remove, deprecate, or add CLI commands;
- change package metadata, dependencies, extras, or versions;
- change GitHub workflows;
- rewrite README.md, AGENTS.md, contracts, existing reports, guides, examples, prompts, or templates;
- create compatibility shims;
- create migration scripts;
- modify runtime state;
- instantiate TaskEngine or EventEngine;
- call models or providers;
- run deployment or release operations;
- commit, push, merge, or tag.
```

Do not include executable cleanup commands such as recursive delete or move commands in the report. Future commands belong only in a separately approved implementation prompt after the owner selects a work package.

A planned disposition is not approval. “Move later” and “Candidate for deletion later” remain recommendations until a human explicitly authorizes exact paths and acceptance criteria.

---

## 5. Allowed file

You may create only:

```text
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

Do not create scratch files, generated context, task records, databases, scripts, manifests, inventories, or migration artifacts.

---

## 6. Forbidden files and paths

Read-only inspection is allowed, but do not modify:

```text
AGENTS.md
README.md
pyproject.toml
.gitignore
TASK.md
CONTEXT.json
docs/VOYAGE_V4_1_CONTRACT.md
docs/prompts/
docs/guides/
docs/examples/
docs/templates/
docs/reports/* (except the single allowed Phase 13 report)
voyage_framework/
voyage_framework_v4_mvp/
tests/
.github/
.voyage/
```

If any forbidden path changes, stop and report. Do not auto-repair it.

---

## 7. Required read-only verification

Confirm the Phase 12 source and current repository relationship without mutating state:

```bash
git status --short --untracked-files=all
git --no-pager log --oneline --decorate -10
git ls-files
rg --files -g "!/.git/"
```

Review at minimum:

```text
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
AGENTS.md
README.md
pyproject.toml
voyage_framework/__init__.py
voyage_framework/cli.py
voyage_framework/core/
voyage_framework/agents/
voyage_framework/langgraph_tools/
voyage_framework/security/
voyage_framework/memory/
voyage_framework/improvement/
voyage_framework/ast_tools/
voyage_framework/chronicler/
voyage_framework/specs/
tests/
voyage_framework_v4_mvp/
docs/architecture/
docs/tutorial/
docs/drafts/
docs/examples/
.github/workflows/
```

Use static imports, public exports, CLI parsers, tests, packaging extras, workflows, documentation links, and Git history as dependency evidence. Do not infer safety from names alone.

---

## 8. Candidate register

The plan must carry forward every material Phase 12 classification. At minimum include:

### Keep as canonical

- canonical architecture contracts and accepted closure records;
- task/parser/runtime/audit/context/registry/mode/prompt/adapter core;
- canonical focused tests;
- current v4.1/v4.2 user, process, adapter, and static demo documentation.

### Keep as historical/archive

- historical phase prompts and process evidence;
- milestone provenance that remains useful but must not override current contracts.

### Move later

- `voyage_framework/agents/`;
- `voyage_framework/langgraph_tools/`;
- their runtime/graph compatibility tests;
- `voyage_framework_v4_mvp/` snapshot;
- legacy/generated architecture and tutorial material identified by Phase 12.

### Candidate for deletion later

- superseded TaskEngine draft text files;
- incomplete example shells that reference absent generated artifacts;
- any workflow or placeholder that the human owner confirms is unused.

### Needs human decision

- root product identity in `README.md`;
- public exports and version in `voyage_framework/__init__.py`;
- mixed CLI compatibility policy;
- `pyproject.toml` identity, dependencies, extras, and versioning;
- non-core support packages with active imports/tests;
- mixed shared core support such as `core/models.py` and `core/storage.py`;
- CI, release, coverage auto-commit, and Pages workflows;
- external consumer compatibility and historical retention requirements.

For every candidate create a row with:

```text
- exact path or area;
- Phase 12 classification;
- proposed long-term disposition;
- current dependencies and dependents;
- public API / CLI / packaging / docs / test impact;
- risk: low / medium / high;
- reversibility: easy / moderate / difficult;
- evidence gaps;
- required human decision;
- prerequisite work packages;
- future verification gates;
- rollback unit;
- readiness: planning-ready / blocked / keep / not recommended.
```

Do not silently change a Phase 12 classification. Any proposed reclassification must be labeled, justified with new evidence, and left for human approval.

---

## 9. Dependency and blast-radius analysis

For each move or deletion candidate, map:

- internal imports and public exports;
- CLI registration and handler references;
- unit and integration tests;
- optional and base dependencies;
- build and release packaging;
- documentation links and generated pages;
- CI, pre-commit, coverage, release, and Pages workflows;
- canonical components that share models or storage;
- external-use evidence or the absence of it;
- tag, branch, and rollback implications.

Explicitly answer:

1. What breaks if the item is removed alone?
2. What must move with it as one atomic future change?
3. What compatibility period or deprecation notice is required?
4. Which verification proves canonical v4.1/v4.2 behavior remains intact?
5. What evidence is missing before destructive work is allowed?

A candidate with unknown external consumers, public exports, CLI commands, packaging effects, or shared canonical dependencies must remain blocked pending human decision.

---

## 10. Required future work packages

Design future work as separate, narrow packages. Do not combine all cleanup into one phase. The plan must define at least these package types:

### Package A — Public documentation clarification

Planning goal: distinguish current canonical architecture from preserved legacy behavior in root and generated/public documentation.

Constraints: documentation-only; no code, CLI, dependency, or test behavior changes.

### Package B — Legacy labeling and deprecation policy

Planning goal: define supported, compatibility, deprecated, and historical surfaces before relocation.

Constraints: human approval required for API/CLI commitments.

### Package C — Test and CI separation

Planning goal: distinguish canonical-core gates from legacy compatibility gates without reducing total evidence prematurely.

Constraints: do not delete tests in the separation step.

### Package D — Snapshot archival

Planning goal: relocate or externalize `voyage_framework_v4_mvp/` only after provenance and link review.

Constraints: exact destination, history preservation, and rollback required.

### Package E — Legacy runtime relocation

Planning goal: isolate agent/LangGraph runtime code and coupled tests behind an explicit legacy boundary or separate package.

Constraints: dependency graph, import migration, CLI policy, semver, and consumer evidence required.

### Package F — Low-risk deletion candidates

Planning goal: remove only owner-approved obsolete drafts or empty placeholders.

Constraints: exact path allowlist and proof of no references required.

### Package G — Packaging and workflow alignment

Planning goal: align public exports, metadata, extras, release, CI, and Pages only after the product/API decision.

Constraints: release plan and rollback release required.

For each package specify:

```text
- objective;
- exact candidate paths, or state that exact paths await human selection;
- prerequisites;
- explicit anti-scope;
- required approval;
- risk and blast radius;
- future implementation prompt boundaries;
- verification gates;
- rollback strategy;
- exit criteria;
- downstream packages unblocked.
```

---

## 11. Safe execution order

The plan must propose a dependency-aware sequence. Default ordering:

1. clarify documentation and product identity;
2. approve API/CLI/deprecation policy;
3. gather external consumer and deployment evidence;
4. separate canonical and compatibility test reporting without deleting tests;
5. archive low-coupling documentation/snapshot areas;
6. relocate legacy runtime and coupled tests with compatibility support;
7. align package exports, metadata, extras, workflows, and release behavior;
8. delete only explicitly approved low-risk candidates;
9. run closure audit after every destructive package.

If evidence supports a different order, explain the dependency change. No package may depend on work that has not been approved and completed.

---

## 12. Rollback strategy requirements

Define rollback at both package and program levels:

- record the exact pre-change commit and branch;
- require one narrow commit per reversible concern;
- avoid mixing moves with semantic edits;
- preserve path mapping for relocated files;
- retain compatibility aliases only when explicitly approved;
- define revert order for dependent packages;
- preserve the last compatible release/tag;
- specify how tests, CLI, imports, docs, packaging, and workflows are restored;
- stop on conflicts, unexpected files, test failures, or scope expansion;
- require a post-rollback verification report.

Do not create tags or rollback branches in Phase 13. Describe future requirements only.

---

## 13. Verification gates for future cleanup phases

The plan must tailor gates per work package. Include, when applicable:

### Repository and scope

```text
- exact branch/base verification;
- clean working tree;
- explicit allowed and forbidden paths;
- git diff --check;
- changed-file list equals approved scope;
- no .voyage, root TASK.md, or root CONTEXT.json pollution.
```

### Canonical behavior

```text
- targeted tests for affected canonical modules;
- full canonical unit suite;
- full suite or explicitly separated compatibility suite;
- TaskParser/TaskEngine/EventEngine/ContextBuilder regressions;
- AgentRegistry/ModeRegistry/PromptGenerator/AdapterContract regressions.
```

### Public API and CLI

```text
- import smoke tests for supported exports;
- CLI help snapshot and supported command checks;
- deprecated-command behavior when compatibility is promised;
- migration documentation and version-policy review.
```

### Packaging and dependencies

```text
- editable install;
- wheel and sdist build;
- package-content inspection;
- optional extras installation where supported;
- dependency and import checks;
- release workflow dry-run or equivalent approved verification.
```

### Documentation and workflows

```text
- internal link and navigation checks;
- legacy/current labeling review;
- GitHub workflow syntax and permission review;
- Pages source/output review;
- no automatic publication without explicit authority.
```

### Quality

```text
- Ruff check and format check for code phases;
- strict mypy for affected code;
- exact pytest pass/fail/error/skip counts;
- forbidden-claim scan;
- human review and cleanup closure audit.
```

These are future gate requirements, not commands to execute during Phase 13.

---

## 14. Protected paths requiring separate approval

The plan must include a protected-path register. At minimum, no future cleanup phase may touch these without an exact approved prompt:

```text
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
AGENTS.md
README.md
pyproject.toml
.gitignore
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
voyage_framework/core/models.py
voyage_framework/core/storage.py
voyage_framework/cli.py
voyage_framework/__init__.py
tests/
.github/
```

Legacy classification does not waive protection. Exact approval is still required for `voyage_framework/agents/`, `voyage_framework/langgraph_tools/`, `voyage_framework_v4_mvp/`, documentation moves, drafts, and examples.

Never treat generated artifacts or ignored runtime directories as permission for broad deletion.

---

## 15. Human decision register

The plan must state the owner decision required for each blocked area, including:

- current product identity and supported architecture;
- public Python API and semantic-version policy;
- legacy CLI support/deprecation window;
- external consumers and integrations;
- LangGraph and other optional extras;
- ownership of security, memory, improvement, AST, chronicler, and specs packages;
- snapshot retention location;
- canonical versus compatibility test policy;
- CI/release/Pages ownership and automation permissions;
- whether historical reports may receive errata;
- release and rollback milestones.

For each decision provide options, consequences, required evidence, decision owner, and which work packages remain blocked.

---

## 16. Required report structure

Create `docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md` with:

```markdown
# Voyage Phase 13 Controlled Cleanup Plan

## 1. Executive summary
- Planning scope
- Recommended sequence
- Highest-risk dependency
- Planning-only confirmation

## 2. Inputs, authority, and limitations
- Phase 12 findings used
- Canonical authority order
- Evidence gaps

## 3. Cleanup principles
- Contract protection
- Compatibility before deletion
- Small reversible packages
- Human authority

## 4. Candidate register
| Path / area | Phase 12 class | Proposed disposition | Dependencies | Risk | Reversibility | Readiness | Human decision |

## 5. Canonical and historical retention
- Keep as canonical
- Keep as historical/archive
- Protected paths

## 6. Move-later plan
- Candidates
- Required dependency groups
- Preconditions
- Destination decision

## 7. Delete-later plan
- Candidates
- Reference proof
- Preconditions
- Explicit approval requirement

## 8. Human decision register
| Decision | Options | Impact | Evidence required | Blocked packages |

## 9. Work package roadmap
- Package A through G
- Dependencies
- Entry and exit criteria

## 10. Safe execution order
- Ordered phases
- Stop conditions

## 11. Verification gates
- Scope
- Tests
- API/CLI
- Packaging
- Documentation/workflows
- Pollution

## 12. Rollback strategy
- Package rollback
- Program rollback
- Compatibility restoration

## 13. Future prompt boundaries
- Exact allowed files per package
- Explicit anti-scope
- Required approvals

## 14. Do not execute cleanup in this phase
- No deletion, movement, refactor, or mutation performed

## 15. Forbidden-files and pollution check
- Plan is the only changed file
- Runtime artifacts unchanged

## 16. Verdict
A. Plan complete — ready for human package selection
B. Plan complete with blocked decisions/evidence gaps
C. Plan incomplete or scope violation
```

Use precise future tense. Do not say files were removed, moved, deprecated, or fixed. Distinguish recommendations from approved actions.

---

## 17. Quality gates

Run:

```bash
git status --short --untracked-files=all
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

Forbidden-files check:

```bash
git diff -- README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/prompts docs/guides docs/examples docs/templates voyage_framework voyage_framework_v4_mvp tests .github
```

Expected: no output.

Existing reports check:

```bash
git --no-pager diff --name-status -- docs/reports
```

Expected only:

```text
A       docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

Pollution check:

```bash
git status --porcelain .voyage
git status --porcelain TASK.md CONTEXT.json
```

Expected: no changes.

Python tests, Ruff, and mypy are not required for this planning-only documentation phase. Do not run cleanup behavior to validate the plan.

---

## 18. Final report format

Return only:

```markdown
# Phase 13 Implementation Report

## Changed files
-

## Planned
-

## Work packages
-

## Human decisions / blockers
-

## Not performed
-

## Quality gates
-

## Forbidden files check
-

## Pollution check
-

## Risks / deviations
-

## Verdict
A. Plan complete — ready for human package selection
B. Plan complete with blocked decisions/evidence gaps
C. Plan incomplete or scope violation
```

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not execute cleanup.
