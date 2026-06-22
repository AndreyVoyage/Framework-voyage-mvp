# Phase 14 — Root Documentation Identity Alignment

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
Branch: docs/phase-14-root-identity-alignment
Base: main
main contains: 4a980ba Merge Phase 13 controlled cleanup plan
Working tree: clean
```

If the repository, branch, base, or working tree is unexpected, stop and report. Do not repair unrelated changes.

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 15.

---

## 1. Mission

Perform **Phase 14: Root Documentation Identity Alignment**.

This is the first non-destructive documentation package from the Phase 13 controlled cleanup plan. Align the public project identity with the accepted v4.1/v4.2 architecture while preserving accurate historical and compatibility context.

Canonical identity:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

The wording applies to the v4.1/v4.2/v4.3 documentation evolution. Do not infer a new release, tag, package version, or implemented capability from the phase number.

Phase 14 is documentation-only. It changes claims, not behavior.

---

## 2. Source evidence and authority

Read before editing:

```text
docs/VOYAGE_V4_1_CONTRACT.md
docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
AGENTS.md
README.md
```

Use this authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. accepted closure audits;
3. Phase 12 evidence and Phase 13 planning constraints;
4. active implementation evidence for factual compatibility statements;
5. `AGENTS.md` as operational guidance.

Do not rewrite contracts or reports. If an allowed document conflicts with higher authority, align only the allowed document and cite the authoritative source through a link where useful.

---

## 3. What Phase 14 is

Phase 14 may:

- replace misleading root-level product claims;
- state the canonical identity prominently and consistently;
- explain what Voyage v4.1/v4.2 does and does not do;
- distinguish canonical core from preserved legacy/historical modules and commands;
- direct readers to the canonical contract, operational rules, user guides, and cleanup audit/plan;
- clarify that prompt packages and adapter contracts support manual external-tool handoff;
- clarify that generated `TASK.md` and `CONTEXT.json` are non-canonical artifacts;
- retain accurate historical facts when they are explicitly labeled historical or legacy;
- make the smallest documentation diff required by the claim audit.

---

## 4. What Phase 14 is not

Phase 14 must not:

```text
- delete, move, rename, archive, or create project areas;
- perform cleanup Packages D–G;
- change Python code or tests;
- change CLI registration, help behavior, handlers, or compatibility;
- change public exports, package version, dependencies, or extras;
- change GitHub workflows;
- change architecture contracts or existing reports;
- add deprecation behavior or compatibility shims;
- remove legacy code;
- claim legacy code was removed, disabled, unsupported, or deprecated unless approved evidence says so;
- implement runtime execution;
- call models or providers;
- create runtime state;
- commit, push, merge, or tag.
```

Do not use a documentation edit to make a behavior promise that the code and contract do not support.

---

## 5. Allowed files

Inspect all candidates, but modify only files that contain a current identity defect:

```text
README.md
AGENTS.md
docs/guides/*.md
docs/examples/**/*.md
```

Rules:

- `README.md` must be updated if the Phase 12 misleading present-tense claims are still present.
- `AGENTS.md` is already substantially aligned; change it only if a verified identity contradiction remains. Do not churn wording for style.
- Change a guide or example only when it contradicts canonical identity, not merely because it mentions an external AI tool or a legacy term safely.
- Do not create new guide/example files.
- Do not edit every allowed file automatically.
- The final changed-file list must be justified file by file.

Allowed patterns are not permission to modify unrelated Markdown.

---

## 6. Forbidden files and directories

Do not modify:

```text
pyproject.toml
.gitignore
.pre-commit-config.yaml
Makefile
TASK.md
CONTEXT.json
docs/VOYAGE_V4_1_CONTRACT.md
docs/prompts/
docs/reports/
docs/templates/
docs/architecture/
docs/tutorial/
docs/drafts/
voyage_framework/
voyage_framework_v4_mvp/
tests/
.github/
.voyage/
```

No source, test, packaging, workflow, archive, or historical-report cleanup is authorized.

If a necessary change falls outside the allowed files, stop and report it as a future-package recommendation. Do not expand scope.

---

## 7. Required claim audit before editing

Search allowed candidates for identity and capability claims:

```bash
rg -n -i "AI Agent Framework|AI-Native|agent runtime|autonomous agent|execute agent|run agent|orchestrat|LangGraph|CrewAI|AutoGen|OpenAI|Anthropic|provider|model inference|self-running|automatic agent|production deployment" README.md AGENTS.md docs/guides docs/examples
```

Classify each material match as:

```text
CURRENT-MISLEADING  present-tense claim that contradicts canonical identity
SAFE-NEGATIVE       explicit statement that Voyage does not provide the capability
SAFE-LEGACY         clearly labeled historical/legacy compatibility fact
SAFE-EXAMPLE        static example or manual external-tool handoff
UNCLEAR             requires owner interpretation; do not edit by assumption
```

Also inspect:

```bash
rg -n -i "Development Memory System|Project Knowledge OS|Project Knowledge Operating System|task.yaml|TaskRecord|EventEngine|ContextBuilder|PromptGenerator|PromptPackage|AdapterContract|source of truth|canonical" README.md AGENTS.md docs/guides docs/examples
```

Record the classifications in the final response. Do not remove safe negative, legacy, or example wording simply because a keyword matches.

---

## 8. Required canonical identity

The public entry documentation must state, exactly or as a clearly equivalent primary sentence:

> Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

The surrounding content must make these points clear:

- Voyage keeps local development knowledge structured around canonical task specification, runtime task state, context, and audit evidence.
- `task.yaml` is canonical task intent.
- `TaskRecord` managed by `TaskEngine` is canonical runtime task state.
- `EventEngine` is append-only audit, not a state controller.
- `AgentRegistry` and `ModeRegistry` are read-only catalogs.
- `PromptGenerator` produces deterministic packages for manual transfer.
- Phase 7 adapter models/protocols are interface contracts only.
- Generated `TASK.md` and `CONTEXT.json` are not canonical truth.
- Human review and repository authority remain required.

Do not turn the README into a duplicate of the full architecture contract. Link to detailed guides and contracts instead.

---

## 9. Prohibited current-product claims

Do not present Voyage v4.1/v4.2/v4.3 as any of the following:

```text
- AI Agent Framework
- autonomous agent runtime
- runtime orchestration framework
- LangGraph/CrewAI/AutoGen replacement
- automatic agent execution
- model/provider execution layer
```

These terms may remain only when clearly framed as:

- a legacy or historical identity being corrected;
- preserved compatibility code outside canonical core;
- a negative boundary (“Voyage is not ...”);
- an audit risk;
- a fictional/static example that explicitly performs no execution.

Do not claim there is no runtime code in the repository. Phase 12 verified that legacy runtime and graph code remains importable, tested, packaged, and CLI-visible. The accurate distinction is:

```text
Legacy/historical runtime and LangGraph surfaces remain for compatibility and are not the canonical v4.1/v4.2 core. Their disposition requires separate human-approved cleanup packages.
```

Do not describe those surfaces as deprecated unless the owner has approved a deprecation policy.

---

## 10. README requirements

If the known claims remain, update `README.md` so the opening section:

1. uses the canonical identity rather than “AI-Native Engineering Operating System” as the current product definition;
2. distinguishes active canonical v4.1/v4.2 core from preserved v4.0-era legacy surfaces;
3. links to `docs/VOYAGE_V4_1_CONTRACT.md`;
4. links to `AGENTS.md` for contributor/agent rules;
5. links to `docs/guides/USER_GUIDE.md`, `INSTALLATION.md`, and `QUICKSTART.md`;
6. links to the Phase 12 audit and Phase 13 controlled cleanup plan for legacy disposition context;
7. avoids claiming automatic model calls, autonomous work, orchestration, or production deployment;
8. does not remove truthful compatibility information without replacement context.

Review the entire README, not only the title. Present-tense feature matrices, quickstarts, architecture diagrams, examples, and phase/status statements must not contradict the new opening.

A concise legacy compatibility section is preferred over scattering ambiguous runtime claims throughout current-product sections.

---

## 11. AGENTS.md requirements

`AGENTS.md` is operational guidance and already states the v4.1 boundary. Verify:

- canonical source hierarchy remains intact;
- `agents/` and `langgraph_tools/` remain labeled legacy/historical;
- runtime/model/orchestration exclusions remain explicit;
- current Phase 7 adapter contract is not described as runtime;
- future cleanup remains approval-gated.

Modify `AGENTS.md` only for a demonstrated contradiction or genuinely stale phase reference that affects identity. Preserve its operational, non-contract status. Do not use Phase 14 for stylistic rewriting.

---

## 12. Guides and examples requirements

Verify current guides and examples remain consistent:

```text
docs/guides/USER_GUIDE.md
docs/guides/INSTALLATION.md
docs/guides/QUICKSTART.md
docs/guides/END_TO_END_WORKFLOW.md
docs/guides/ADAPTER_CONTRACT_USAGE.md
docs/examples/ADAPTER_CONTRACT_EXAMPLE.md
docs/examples/ADAPTER_MOCK_IMPLEMENTATION.md
docs/examples/e2e-demo/*.md
```

Safe wording includes:

- manual copy/paste or handoff to Codex, Claude, Gemini, or other external tools;
- static `PromptPackage`, `AgentRequest`, and `AgentResponse` examples;
- negative security/runtime boundaries;
- explicit descriptions of legacy CLI visibility;
- fictional examples with no network/model/runtime action.

Only fix an actual contradiction. Do not normalize every document to identical prose.

---

## 13. Version and milestone wording

Distinguish:

- package metadata currently reporting v4.0.0, which Phase 14 cannot change;
- v4.1 MVP architecture and `v4.1.0-mvp` historical tag;
- v4.2 adapter-contract milestone and `v4.2.0-adapter-contract` tag;
- later documentation phases, which do not automatically establish a v4.3 release.

Do not claim a v4.3 tag, release, package version, or runtime implementation exists. If using “v4.1/v4.2/v4.3,” frame it as documentation/roadmap identity continuity, not release evidence.

Do not edit `pyproject.toml` or package version in this phase.

---

## 14. Safety and non-regression requirements

Documentation must remain honest about:

- local-first operation;
- manual external AI tool handoff;
- canonical versus generated state;
- human-in-the-loop review;
- no credential storage or provider execution in canonical core;
- no adapter execution implementation;
- legacy code presence and separate cleanup authority.

Do not provide real credentials, model keys, provider clients, runtime commands as recommended canonical workflows, or automatic deployment instructions.

Do not remove legacy command documentation in a way that breaks the contract's compatibility record. Reframe it as legacy compatibility where necessary.

---

## 15. Expected changed files

Determine expected changes after the claim audit.

Minimum expectation if known root claims remain:

```text
README.md
```

Optional only when a verified contradiction exists:

```text
AGENTS.md
docs/guides/*.md
docs/examples/**/*.md
```

Any other changed file is a scope violation.

The final report must state why each modified optional file was necessary and list allowed candidates inspected but left unchanged.

---

## 16. Quality gates

Run:

```bash
git status --short --untracked-files=all
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Forbidden-files check:

```bash
git diff -- pyproject.toml .gitignore .pre-commit-config.yaml Makefile docs/VOYAGE_V4_1_CONTRACT.md docs/prompts docs/reports docs/templates docs/architecture docs/tutorial docs/drafts voyage_framework voyage_framework_v4_mvp tests .github
```

Expected: no output.

Runtime pollution check:

```bash
git status --porcelain .voyage
git status --porcelain TASK.md CONTEXT.json
```

Expected: no changes.

Post-edit identity scan:

```bash
rg -n -i "AI Agent Framework|AI-Native|agent runtime|autonomous agent|execute agent|run agent|orchestrat|LangGraph|CrewAI|AutoGen|OpenAI|Anthropic|provider|model inference|self-running|automatic agent|production deployment" README.md AGENTS.md docs/guides docs/examples
```

Classify every remaining material match. Fail the phase for an unqualified current-product claim. Safe negative, legacy, audit, and static-example matches may remain.

Required identity check:

```bash
rg -n -i "local Project Knowledge OS|Development Memory System|external AI tool handoff" README.md AGENTS.md docs/guides
```

At least the public entry documentation must contain the required identity.

Link checks:

- verify every new or changed relative link resolves;
- verify casing matches tracked paths;
- verify no link points to an uncreated cleanup artifact.

Markdown-only changes do not require Python tests, Ruff, or mypy unless the approved prompt is expanded by the human owner. Do not run runtime commands to validate wording.

---

## 17. Final report format

Return only:

```markdown
# Phase 14 Implementation Report

## Changed files
-

## Identity aligned
-

## Claims corrected
-

## Allowed candidates inspected but unchanged
-

## Not implemented
-

## Quality gates
-

## Forbidden files check
-

## Runtime state check
-

## Remaining safe legacy references
-

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with safe warnings
C. Not ready
```

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start cleanup Packages D–G.
