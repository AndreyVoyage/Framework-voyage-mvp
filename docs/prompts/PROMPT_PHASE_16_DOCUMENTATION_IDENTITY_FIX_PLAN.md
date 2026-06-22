# Phase 16 — Documentation Identity Fix Plan

## 0. Stop-gate

Before making any change, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git --no-pager log --oneline --decorate -12
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
Branch: docs/phase-16-documentation-identity-fix-plan
Base: main
main contains: c20a98e Merge Phase 15 v4.3 release readiness audit
Working tree: clean
No v4.3 tag exists
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start implementation of the plan.

---

## 1. Mission

Perform **Phase 16: Documentation Identity Fix Plan**.

Create an evidence-based, planning-only sequence for closing the blockers identified by the Phase 15 v4.3 release readiness audit. Define exact future change packages, dependencies, approvals, rollback strategies, and verification gates without executing any fix.

The only permitted output is:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
```

The plan must state prominently:

```text
No v4.3 tag.
No cleanup execution.
No documentation fixes yet.
No pyproject changes yet.
Planning only.
```

Phase 16 does not make the repository ready for a tag. It produces a controlled path toward a future readiness re-audit.

---

## 2. Canonical identity

Use this exact identity as the target for future public-documentation alignment:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

The plan must preserve these boundaries:

- `task.yaml` is canonical task intent;
- `TaskRecord`, managed by `TaskEngine`, is canonical runtime task state;
- `EventEngine` is append-only audit and not a state controller;
- `AgentRegistry` and `ModeRegistry` are read-only catalogs;
- `ContextBuilder` aggregates context without becoming canonical state;
- `PromptGenerator` creates deterministic packages for manual transfer;
- adapter models and protocols are interface contracts only;
- external AI tools are handoff targets, not Voyage runtime dependencies;
- generated `TASK.md` and `CONTEXT.json` are not canonical truth;
- legacy runtime and LangGraph surfaces remain present but are not canonical v4.1/v4.2 core.

Do not plan new runtime, orchestration, model, provider, credential, webhook, worker, or autonomous-agent behavior.

---

## 3. Authority and required sources

Use this precedence order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. accepted v4.1 and v4.2 closure audits;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md`;
5. `docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md`;
6. accepted Phase 14 root identity alignment;
7. current implementation, packaging, workflow, and Git evidence;
8. `AGENTS.md` as operational guidance subordinate to the contract.

Read at minimum:

```text
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
README.md
docs/README.md
AGENTS.md
docs/guides/
docs/examples/
docs/architecture/components.md
docs/tutorial/
pyproject.toml
voyage_framework/__init__.py
voyage_framework/cli.py
.github/workflows/release.yml
.github/workflows/jekyll-gh-pages.yml
```

All sources outside the new Phase 16 report are read-only. If authorities conflict, record the conflict and the decision owner; do not edit either source.

---

## 4. Phase 15 blockers to cover

The plan must address every Phase 15 blocker:

1. stale published documentation claims;
2. identity drift in `docs/README.md`;
3. legacy API and tutorial pages with unqualified runtime, agent, or LangGraph claims;
4. stale `pyproject.toml` identity, version, extras, and package-metadata risk;
5. tag-triggered release behavior in `.github/workflows/release.yml`;
6. unresolved Phase 13 product, API, CLI, LangGraph, semver, package, Pages, release, and rollback decisions;
7. the need for an approved release dry run and a new release-readiness audit before any tag proposal.

For each blocker record:

```text
- source path and representative lines;
- current claim or behavior;
- conflict with canonical identity or release safety;
- release impact: blocker / warning / follow-up;
- proposed future work package;
- files that package may modify;
- files it must not modify;
- prerequisites and dependencies;
- human decision and approval owner;
- rollback strategy;
- verification evidence required;
- completion/stop criteria.
```

Do not silently downgrade a Phase 15 blocker. If evidence supports reclassification, explain it and require human confirmation.

---

## 5. What Phase 16 must produce

The plan must:

- map every Phase 15 blocker to one or more future work packages;
- separate docs-only corrections from metadata, packaging, API/CLI, and workflow changes;
- identify exact candidate files for each future package;
- identify protected paths requiring explicit approval;
- define dependencies and a safe execution order;
- define per-package stop-gates, allowed scope, forbidden scope, rollback, and verification;
- preserve historical evidence while correcting current-product claims;
- distinguish safe legacy references from unsafe present-tense claims;
- define human decisions required before package metadata or release automation changes;
- define a final readiness re-audit gate before any v4.3 tag proposal;
- state that a readiness proposal still does not authorize a tag.

Recommendations are not authorization. Future agents must receive separate approved prompts before changing any listed file.

---

## 6. What Phase 16 must not do

Phase 16 must not:

```text
- fix README.md, docs/README.md, guides, examples, architecture pages, or tutorials;
- edit pyproject.toml or package version metadata;
- edit voyage_framework/__init__.py, exports, or version constants;
- edit voyage_framework/cli.py or change CLI behavior;
- edit .github workflows or release triggers;
- delete, move, rename, archive, or deprecate files;
- execute Phase 13 cleanup packages;
- implement compatibility shims or migrations;
- create release notes, manifests, builds, packages, or dry-run artifacts;
- run a publishing workflow;
- create, move, annotate, or delete a tag;
- claim v4.3 is released or approved;
- create TaskRecord state or append EventEngine events;
- create .voyage, root TASK.md, or root CONTEXT.json;
- implement runtime execution, orchestration, model/provider calls, or credentials;
- commit, push, merge, or tag.
```

Do not use planning language that implies a blocker has already been fixed.

---

## 7. Allowed file

Create only:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
```

Do not create scratch plans, inventories, generated context, decision files, release notes, scripts, databases, build artifacts, or tag messages.

---

## 8. Forbidden paths

Read-only inspection is allowed, but do not modify:

```text
README.md
docs/README.md
AGENTS.md
pyproject.toml
.gitignore
.pre-commit-config.yaml
TASK.md
CONTEXT.json
docs/VOYAGE_V4_1_CONTRACT.md
docs/prompts/
docs/guides/
docs/examples/
docs/architecture/
docs/tutorial/
docs/templates/
docs/reports/* (except the new Phase 16 report)
voyage_framework/
voyage_framework_v4_mvp/
tests/
.github/
.voyage/
```

Any forbidden change is a Phase 16 scope violation. Stop and report it; do not auto-repair unrelated state.

---

## 9. Required evidence scan

Verify Phase 15 findings with read-only searches:

```bash
rg -n -i "AI Agent Framework|AI-Native|agent runtime|autonomous agent|execute agent|run agent|orchestrat|LangGraph|CrewAI|AutoGen|provider|model inference|automatic agent|v4.0|v4.3" README.md docs/README.md AGENTS.md docs/guides docs/examples docs/architecture docs/tutorial pyproject.toml
```

Inspect release and package behavior:

```bash
rg -n "^version|^description|langgraph|all =|dependencies" pyproject.toml
rg -n "tags:|v\\*|python -m build|Create GitHub Release|Publish to PyPI|dist/" .github/workflows/release.yml
rg -n "pages|jekyll|deploy" .github/workflows/jekyll-gh-pages.yml
rg -n "__version__|LangGraphRuntime|VoyageGraphBuilder" voyage_framework/__init__.py
rg -n "graph|run|agent|runtime" voyage_framework/cli.py
```

Review Phase 13 human-decision and package dependencies:

```bash
rg -n "Needs human decision|Blocked|blocked|Package A|Package B|Package C|Package D|Package E|Package F|Package G|release|tag|version|pyproject|workflow|rollback" docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md
```

Classify claims as:

```text
SAFE-CURRENT     canonical current identity/capability
SAFE-NEGATIVE    explicit non-capability boundary
SAFE-LEGACY      clearly labeled historical/compatibility wording
SAFE-AUDIT       audit or planning risk language
UNSAFE-CURRENT   unqualified current claim contradicting canonical identity
HUMAN-DECISION   disposition depends on owner/release/API/CLI evidence
```

Do not treat every keyword as a defect. Cite representative evidence and preserve safe historical context in the future plan.

---

## 10. Required future workstream separation

The plan must define separate future packages. It may refine names, but it must preserve these authority boundaries.

### Workstream A — Public documentation identity correction

Purpose: documentation-only correction of unsafe present-tense claims.

Candidate files may include:

```text
docs/README.md
docs/architecture/components.md
docs/tutorial/02-*.md through docs/tutorial/05-*.md
exact navigation or index Markdown verified to expose those pages
```

Requirements:

- preserve the corrected root `README.md` unless a verified defect requires a separately approved change;
- replace current AI/runtime identity with canonical identity;
- label retained v4.0/runtime/LangGraph material as historical or legacy;
- remove recommended live execution commands from current onboarding, or isolate them as compatibility documentation;
- preserve accurate historical facts and links;
- do not change code, CLI, metadata, tests, workflows, or behavior;
- verify Markdown links, navigation, claim scans, and exact diff scope.

This is the only workstream that may be proposed as docs-only without metadata/release authority.

### Workstream B — Product and compatibility decision record

Purpose: obtain human decisions before code, CLI, extras, or release metadata changes.

Decisions must include:

- supported product identity and v4.3 meaning;
- package version and semver strategy;
- public exports and compatibility window;
- legacy `voyage run` / `voyage graph` CLI status;
- LangGraph extra/runtime support status;
- generated docs and Pages ownership;
- downstream consumer evidence and deprecation policy;
- release owner and rollback authority.

This workstream must record decisions through a separately approved artifact. It must not infer owner approval from Phase 16.

### Workstream C — Metadata and package alignment

Purpose: align package identity only after Workstream B approval.

Potentially affected files require explicit approval and may include:

```text
pyproject.toml
voyage_framework/__init__.py
package-facing documentation tied to build metadata
```

Requirements:

- do not combine with docs-only Workstream A;
- define exact version/description/extras changes from approved decisions;
- preserve or deprecate exports through an approved compatibility plan;
- run editable-install, wheel/sdist, metadata, import, CLI, and required test gates;
- inspect built artifacts without publishing;
- define rollback to the last compatible metadata and exports.

### Workstream D — Release and Pages workflow alignment

Purpose: make tag and documentation publication behavior explicit and safe.

Potentially affected files require release-owner approval and may include:

```text
.github/workflows/release.yml
.github/workflows/jekyll-gh-pages.yml
other directly coupled CI/release workflow files proven by evidence
```

Requirements:

- decide whether every `v*` tag should build and create a GitHub Release;
- define tag naming, package version matching, artifact checks, permissions, and failure rollback;
- verify Pages source/navigation after docs corrections;
- perform a non-publishing validation or dry run under explicit authority;
- do not create a real tag during workflow alignment;
- do not store or expose credentials.

### Workstream E — Release readiness re-audit

Purpose: repeat all Phase 15 gates after approved fixes.

Requirements:

- verify clean main and exact merged histories;
- verify canonical identity across all published surfaces;
- validate package version/metadata and artifacts;
- validate release/Pages behavior without publishing;
- verify no runtime pollution;
- verify existing milestone tags are unchanged and no premature v4.3 tag exists;
- return a new readiness verdict.

### Workstream F — Separately authorized tag operation

This is not part of Phase 16 and must not be scheduled automatically.

It may occur only after:

- Workstreams A–E are complete;
- the re-audit supports a tag proposal;
- all human decisions and approvals are recorded;
- an explicit release/tag prompt names the exact target commit and tag;
- rollback and post-tag verification are approved.

A readiness verdict does not itself authorize Workstream F.

---

## 11. Files that may be changed later

Create a matrix with columns:

```text
Path / pattern
Current issue
Future workstream
Change type
Docs-only safe: yes/no
Prerequisite
Approval owner
Required verification
Rollback
```

Include every path named by Phase 15 and any directly coupled path proven by inspection. Do not use broad globs as autonomous permission. Every future prompt must list exact allowed files.

Clearly distinguish:

- documentation text that can be corrected without behavior changes;
- generated/public documentation whose navigation or publishing path needs confirmation;
- metadata and version changes that affect built packages;
- API/CLI/export/extras changes that require compatibility and semver decisions;
- workflow changes that require release/deployment ownership;
- cleanup candidates that remain outside this plan's execution authority.

---

## 12. Protected paths and separate approval

The plan must include a “Protected paths — no change without separate approval” section.

At minimum protect:

```text
docs/VOYAGE_V4_1_CONTRACT.md
accepted closure audits and existing reports
voyage_framework/core/ canonical task/event/context/registry/mode/prompt/adapter modules
voyage_framework/cli.py
voyage_framework/__init__.py
voyage_framework/agents/
voyage_framework/langgraph_tools/
tests/
pyproject.toml
.github/
.gitignore
.voyage/
TASK.md
CONTEXT.json
v4.1.0-mvp
v4.2.0-adapter-contract
all future release tags
```

Some paths may be candidates for a later approved workstream, but Phase 16 does not grant that approval.

---

## 13. Dependency and risk map

For every workstream document:

- upstream decisions;
- downstream consumers;
- architecture risk;
- compatibility risk;
- packaging risk;
- release/publishing risk;
- documentation/navigation risk;
- rollback difficulty;
- stop conditions.

Required dependency order:

```text
Phase 16 plan
  -> Workstream A documentation correction
  -> Workstream B human decision record
  -> Workstream C metadata/package alignment
  -> Workstream D release/Pages workflow alignment
  -> Workstream E release readiness re-audit
  -> Workstream F separately authorized tag operation, if approved
```

Workstream A and evidence gathering for B may overlap only if they do not modify the same files or assume undecided product/API behavior. C and D must not start before their approval prerequisites are satisfied.

---

## 14. Rollback strategy

Define rollback before any future work begins.

### Documentation rollback

- preserve the pre-change commit;
- revert only the approved docs commit if links, navigation, or historical labeling regress;
- do not restore unsafe current claims as canonical wording; escalate content conflicts for owner review.

### Metadata/package rollback

- preserve the last installable package state;
- restore version, description, extras, exports, and coupled metadata atomically;
- verify editable install, built metadata, imports, CLI, and tests after rollback;
- do not publish a corrective release without separate approval.

### Workflow rollback

- restore the last approved workflow commit;
- verify permissions, triggers, artifact selection, and Pages source;
- stop further release work after any unexpected publication or permission behavior;
- never move milestone tags as a rollback shortcut.

### Program rollback

- stop dependent workstreams when an upstream gate fails;
- revert in reverse dependency order;
- record restored states and remaining blockers;
- rerun readiness audit after rollback.

No rollback branch, tag, release, or artifact is created in Phase 16.

---

## 15. Verification gates

Define exact gates for each future package.

### Documentation gates

- exact allowed-file diff;
- `git diff --check`;
- canonical identity scan;
- risky current-claim scan with SAFE/UNSAFE classification;
- Markdown relative-link and casing validation;
- navigation/Pages source verification where relevant;
- no code, tests, metadata, workflow, runtime-state, or tag changes.

### Decision gates

- named human owner for every unresolved decision;
- explicit selected option and rejected alternatives;
- consumer/API/CLI/LangGraph evidence;
- approved semver and deprecation window;
- release and Pages ownership;
- signed-off allowed/forbidden files for subsequent workstreams.

### Metadata/package gates

- version and description match approved release identity;
- dependency/extras behavior matches approved support policy;
- editable installation;
- wheel and sdist build without publication;
- artifact metadata/content inspection;
- public import and CLI compatibility checks;
- required Ruff, mypy, unit, integration, and full test suites;
- clean working tree and no runtime pollution after verification.

### Workflow gates

- syntax and trigger review;
- least-privilege permissions review;
- package-version/tag consistency check;
- non-publishing dry run or equivalent approved validation;
- artifact and release-note selection review;
- Pages source/navigation validation;
- credential/secret handling review;
- rollback rehearsal or documented proof.

### Re-audit gates

- all Phase 15 blockers closed with commit evidence;
- no unsafe current identity claims;
- no unresolved release-critical human decisions;
- tags `v4.1.0-mvp` and `v4.2.0-adapter-contract` unchanged;
- no v4.3 tag before approval;
- clean main, clean pollution checks, and synchronized remote state;
- explicit verdict for tag proposal readiness.

---

## 16. Human approval checklist

The plan must provide a checklist covering:

- canonical product identity approved;
- docs-only file list approved;
- historical/legacy retention wording approved;
- public API and export policy approved;
- CLI compatibility/deprecation policy approved;
- LangGraph runtime/extra disposition approved;
- version and semver strategy approved;
- package metadata and artifact expectations approved;
- release workflow owner and trigger policy approved;
- Pages source and navigation owner approved;
- downstream consumer evidence reviewed;
- rollback owners and stop authority assigned;
- readiness re-audit reviewed;
- exact tag name and target commit approved only in a later release operation.

Unchecked items remain blockers. Do not convert missing approval into an assumption.

---

## 17. Required report structure

Create `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md` with:

```markdown
# Voyage Phase 16 — Documentation Identity Fix Plan

## Executive Summary
## Planning-Only Boundary
## Source Baseline
## Canonical Identity Target
## Phase 15 Blocker Register
## Claim and Evidence Classification
## Future File Change Matrix
## Protected Paths — No Change Without Separate Approval
## Workstream A — Public Documentation Identity Correction
## Workstream B — Product and Compatibility Decisions
## Workstream C — Metadata and Package Alignment
## Workstream D — Release and Pages Workflow Alignment
## Workstream E — Release Readiness Re-Audit
## Workstream F — Separately Authorized Tag Operation
## Dependency and Risk Map
## Rollback Strategy
## Verification Gates
## Human Approval Checklist
## Recommended Phase Sequence
## Phase 16 Scope and Pollution Check
## Risks / Evidence Gaps
## Verdict
```

The final verdict must be one of:

```text
A. Plan complete — ready for human approval and sequenced implementation prompts
B. Plan complete with evidence gaps or blocked decisions
C. Plan incomplete or scope violation
```

Use B when the plan is complete but Phase 13 human decisions remain unresolved. Do not label an unresolved release-critical decision as a harmless warning.

---

## 18. Recommended phase sequence requirements

The report must recommend a sequence before any v4.3 tag proposal. Each proposed phase must state:

- objective;
- exact candidate files;
- dependencies;
- required approvals;
- stop-gates;
- verification gates;
- rollback;
- expected output;
- explicit non-goals.

The minimum sequence is:

1. public documentation identity correction;
2. human product/API/CLI/LangGraph/version/release decision record;
3. metadata and package alignment;
4. release and Pages workflow alignment plus non-publishing validation;
5. release readiness re-audit;
6. separately authorized tag operation only if the re-audit and owner approve it.

Do not assign automatic phase numbers beyond Phase 16 unless clearly marked as proposed placeholders subject to owner approval.

---

## 19. Quality gates

After creating the report, run:

```bash
git status --short --untracked-files=all
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

If the new report is untracked and its content is not visible in diff output, use intent-to-add for inspection only:

```bash
git add -N docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected only:

```text
A       docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
```

Forbidden-files check:

```bash
git diff -- README.md docs/README.md AGENTS.md pyproject.toml .gitignore .pre-commit-config.yaml docs/VOYAGE_V4_1_CONTRACT.md docs/prompts docs/guides docs/examples docs/architecture docs/tutorial docs/templates voyage_framework voyage_framework_v4_mvp tests .github
git --no-pager diff --name-status -- docs/reports
```

The reports diff must contain only the new Phase 16 report. Existing reports must remain unchanged.

Runtime pollution check:

```bash
git status --porcelain .voyage
git status --porcelain TASK.md CONTEXT.json
```

Tag check:

```bash
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected: no v4.3 tag and unchanged milestone tags.

Because Phase 16 is planning-only documentation, Python tests, Ruff, mypy, package builds, release dry runs, and runtime commands are not required. Do not execute a future verification package during planning.

---

## 20. Final response format

Return only:

```markdown
# Phase 16 Implementation Report

## Changed files
-

## Planned
-

## Not implemented
-

## Blockers mapped
-

## Workstream sequence
-

## Human decisions
-

## Quality gates
-

## Forbidden files check
-

## Runtime state check
-

## Tag check
-

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
```

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not execute documentation, metadata, package, workflow, cleanup, or release changes.
