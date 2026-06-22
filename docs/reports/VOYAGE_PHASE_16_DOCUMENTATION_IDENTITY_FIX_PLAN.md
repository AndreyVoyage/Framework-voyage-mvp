# Voyage Phase 16 — Documentation Identity Fix Plan

> **Stop-gate reminder:**
>
> - No v4.3 tag.
> - No cleanup execution.
> - No documentation fixes yet.
> - No pyproject changes yet.
> - Planning only.
>
> This report does not authorize implementation, merge, tag, or release.

---

## Executive Summary

Phase 15 (`docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`) concluded that the repository is **not ready for a v4.3 tag proposal**. The root `README.md` and `AGENTS.md` identity are aligned, but release-facing surfaces still contradict the canonical Voyage v4.1/v4.2 identity:

- `docs/README.md` advertises a v4.0 “AI-Native Engineering Operating System” with runnable LangGraph integration.
- `docs/architecture/components.md` presents legacy runtime and graph exports as the current public API.
- `pyproject.toml` remains at version `4.0.0` with the stale v4.0 description.
- `.github/workflows/release.yml` reacts to every `v*` tag by building distributions and creating a GitHub Release, so a v4.3 tag would publish artifacts whose package identity and version have not been approved.
- Phase 13 left product, API, CLI, LangGraph, semver, package, Pages, release, and rollback decisions as blocked human decisions.

Phase 16 creates a controlled, dependency-aware plan to close those blockers through separately approved future workstreams. It does not change any file.

---

## Scope

- **In scope:** planning report only (`docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`).
- **Out of scope:** code edits, documentation edits, metadata edits, workflow edits, moves, deletions, merges, tags, releases, runtime actions, provider/model calls, credential handling.

---

## Source Baseline

Authority order applied:

1. `docs/VOYAGE_V4_1_CONTRACT.md`
2. `docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md`
3. `docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md`
4. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`
5. `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md`
6. `docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md`
7. Current read-only evidence: `README.md`, `docs/README.md`, `AGENTS.md`, `docs/guides/`, `docs/examples/`, `docs/architecture/components.md`, `docs/tutorial/05-langgraph.md`, `pyproject.toml`, `voyage_framework/__init__.py`, `voyage_framework/cli.py`, `.github/workflows/release.yml`, `.github/workflows/jekyll-gh-pages.yml`.

---

## Phase 15 Blockers Summary

| # | Blocker | Severity | Primary evidence | Phase 15 section |
|---|---|---|---|---|
| 1 | `docs/README.md` makes unqualified current AI/runtime/LangGraph claims. | **BLOCKER** | `docs/README.md:1,8,10,74,221-230` | Canonical Identity Review |
| 2 | `docs/architecture/components.md` lists legacy runtime/graph APIs as current public exports. | **BLOCKER** | `docs/architecture/components.md:6-31` | Canonical Identity Review |
| 3 | Legacy tutorial pages expose live runtime/tutorial-generation wording without historical label. | **BLOCKER** | `docs/tutorial/05-langgraph.md:6-8` | Canonical Identity Review |
| 4 | `pyproject.toml` version and description contradict prospective v4.3 identity. | **BLOCKER** | `pyproject.toml:7-8` | Canonical Identity Review / Release Risks |
| 5 | `.github/workflows/release.yml` triggers on every `v*` tag and creates a public Release. | **BLOCKER** | `.github/workflows/release.yml:5-6,32-39` | Release Risks |
| 6 | Unresolved Phase 13 human decisions block API, CLI, LangGraph, semver, package, Pages, release, and rollback policy. | **BLOCKER** | `docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md` sections 8, 10 | Blocking Issues |
| 7 | Need approved release dry run and new readiness re-audit before any tag proposal. | **BLOCKER** | Phase 15 recommendation | Blocking Issues |

No Phase 15 blocker is reclassified as warning or safe.

---

## Canonical Identity Target

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

Boundaries to preserve in all future fixes:

- `task.yaml` is canonical task intent.
- `TaskRecord` (managed by `TaskEngine`) is canonical runtime task state.
- `EventEngine` is append-only audit; it is not a state controller.
- `AgentRegistry` and `ModeRegistry` are read-only catalogs.
- `ContextBuilder` aggregates context without becoming canonical state.
- `PromptGenerator` creates deterministic packages for manual transfer.
- Adapter models and protocols are interface contracts only.
- External AI tools are handoff targets, not Voyage runtime dependencies.
- Generated `TASK.md` and `CONTEXT.json` are not canonical truth.
- Legacy runtime and LangGraph surfaces remain present but are not canonical v4.1/v4.2 core.

---

## Blocker Register

### Blocker 1 — `docs/README.md` identity drift

- **Source path:** `docs/README.md`
- **Representative lines:** `1, 8, 10, 74, 221-230`
- **Current claim:** “Voyage AI Dev Framework v4.0”, “AI-Native Engineering Operating System”, “LangGraph Integration & Process Documentation (MVP runnable)”, `AgentRuntime` / `LangGraphRuntime` as current capabilities, `voyage run` / `voyage graph run` in quick-start.
- **Conflict:** Contradicts the canonical identity in root `README.md:6` and `AGENTS.md:16-44`.
- **Release impact:** BLOCKER — a published GitHub Pages landing page would present a product identity that the project no longer claims.
- **Proposed work package:** Workstream A — rewrite or archive `docs/README.md`; add legacy/historical labels to retained runtime content; remove live `voyage run` from current onboarding unless explicitly preserved as compatibility docs.
- **Files that package may modify:** `docs/README.md` only (with exact prompt approval).
- **Files it must not modify:** `README.md`, `AGENTS.md`, `pyproject.toml`, code, tests, workflows.
- **Prerequisites:** Product identity decision from Workstream B; Pages/navigation decision.
- **Human decision/approval owner:** Repository owner + docs owner.
- **Rollback strategy:** Revert the single `docs/README.md` commit.
- **Verification evidence required:** Identity scan across `docs/README.md`, link check, Pages preview diff, forbidden-path diff.
- **Completion/stop criteria:** `docs/README.md` no longer makes unqualified current AI/runtime/LangGraph claims; any retained runtime content is labeled legacy/historical.

### Blocker 2 — `docs/architecture/components.md` legacy-heavy API list

- **Source path:** `docs/architecture/components.md`
- **Representative lines:** `6-31`
- **Current claim:** Lists `LangGraphRuntime`, `VoyageGraphBuilder`, and other v4.0 exports as the current public API without legacy qualification.
- **Conflict:** Canonical public API for v4.1/v4.2 is task/context/registry/prompt/adapter core.
- **Release impact:** BLOCKER — published docs misrepresent supported public API.
- **Proposed work package:** Workstream A or B — regenerate the components page from current canonical exports, or label the current page as historical/generated and provide a replacement.
- **Files that package may modify:** `docs/architecture/components.md`; possibly `docs/architecture/index` or navigation files if separately approved.
- **Files it must not modify:** Code, tests, `voyage_framework/__init__.py`, workflows.
- **Prerequisites:** Supported public API decision from Workstream B.
- **Human decision/approval owner:** Docs owner + API maintainer.
- **Rollback strategy:** Revert the documentation commit or restore the original page from history.
- **Verification evidence required:** Claim scan, diff scope check, link check.
- **Completion/stop criteria:** Components page accurately reflects supported public API or clearly marks legacy entries.

### Blocker 3 — Legacy tutorial pages without historical label

- **Source path:** `docs/tutorial/05-langgraph.md` (and adjacent generated tutorial placeholders)
- **Representative lines:** `6-8`
- **Current claim:** “Tutorial placeholder. Run ... `voyage docs tutorial <correlation_id>` to generate live content.”
- **Conflict:** Implies live LangGraph/tutorial generation is a current capability.
- **Release impact:** BLOCKER — published tutorial invites users to invoke a legacy/docs-generation path as if it were current.
- **Proposed work package:** Workstream A — label LangGraph tutorial as historical/legacy placeholder, or remove it from current navigation; inventory other `docs/tutorial/02-05` pages for similar claims.
- **Files that package may modify:** `docs/tutorial/05-langgraph.md`; navigation/index files if approved.
- **Files it must not modify:** Code, CLI, tests.
- **Prerequisites:** Docs/navigation decision from Workstream B/E.
- **Human decision/approval owner:** Docs owner.
- **Rollback strategy:** Revert the tutorial commit.
- **Verification evidence required:** Tutorial directory claim scan, navigation link check.
- **Completion/stop criteria:** No tutorial page presents legacy/runtime generation as a current onboarding step.

### Blocker 4 — `pyproject.toml` version and description mismatch

- **Source path:** `pyproject.toml`
- **Representative lines:** `7-8`
- **Current claim:** `version = "4.0.0"`; `description = "AI-Native Engineering Operating System — Voyage Framework v4.0"`.
- **Conflict:** A prospective v4.3 tag would package version `4.0.0` with a stale identity.
- **Release impact:** BLOCKER — tag semantics and package metadata would be inconsistent and misleading.
- **Proposed work package:** Workstream C — after Workstream B decisions, update version, description, keywords, classifiers, and optional extras (including LangGraph) to match approved identity and compatibility policy.
- **Files that package may modify:** `pyproject.toml`; potentially `voyage_framework/__init__.py` version constants if approved.
- **Files it must not modify:** Code logic, tests, workflows.
- **Prerequisites:** Product identity, semver, public API, LangGraph support, and deprecation decisions from Workstream B.
- **Human decision/approval owner:** Repository owner + release owner.
- **Rollback strategy:** Revert the metadata commit; restore last compatible `pyproject.toml`.
- **Verification evidence required:** Editable install, wheel/sdist metadata inspection, import smoke tests, CLI smoke tests.
- **Completion/stop criteria:** Package version/description/extras match approved v4.3 meaning; no unapproved API/CLI retirement.

### Blocker 5 — Tag-triggered release behavior

- **Source path:** `.github/workflows/release.yml`
- **Representative lines:** `5-6, 32-39`
- **Current behavior:** Any `v*` tag triggers test run, build, and GitHub Release creation.
- **Conflict:** A v4.3 tag would automatically publish release artifacts before identity/metadata are aligned.
- **Release impact:** BLOCKER — tag is not documentation-only; it has immediate publication side effects.
- **Proposed work package:** Workstream D — decide whether every `v*` tag should build a Release; define tag naming, version matching, artifact checks, permissions, failure rollback; perform a non-publishing dry run.
- **Files that package may modify:** `.github/workflows/release.yml`; possibly `.github/workflows/jekyll-gh-pages.yml` if Pages source changes.
- **Files it must not modify:** Code, tests, package metadata unless Workstream C already approved.
- **Prerequisites:** Workstream B product/release decisions; Workstream C metadata alignment (or explicit decision to keep current metadata).
- **Human decision/approval owner:** Release owner + repository owner.
- **Rollback strategy:** Revert workflow commit; disable or narrow trigger if needed.
- **Verification evidence required:** Workflow syntax validation, dry-run artifact inspection, no real tag created.
- **Completion/stop criteria:** Release trigger behavior matches approved release policy; v4.3 tag would produce expected artifacts or be blocked until policy says otherwise.

### Blocker 6 — Unresolved Phase 13 human decisions

- **Source path:** `docs/reports/VOYAGE_PHASE_13_CONTROLLED_CLEANUP_PLAN.md`
- **Representative lines:** sections 8 (Human decision register), 10 (Work package roadmap)
- **Current state:** Decisions for product identity, public API, legacy CLI, LangGraph support, non-core packages, canonical vs compatibility tests, snapshot retention, historical docs destination, CI/release/Pages ownership, report errata policy, and cleanup release/rollback milestone are not recorded.
- **Conflict:** Without decisions, Workstreams A–D cannot be safely authorized.
- **Release impact:** BLOCKER — no responsible packaging or release alignment can proceed.
- **Proposed work package:** Workstream E — convene owners, record decisions in an approved artifact, and unblock downstream workstreams.
- **Files that package may modify:** A new decision-record document (separately approved); not existing canonical reports.
- **Files it must not modify:** Code, tests, metadata, workflows.
- **Prerequisites:** None — this is the first dependency.
- **Human decision/approval owner:** Repository owner.
- **Rollback strategy:** Withdraw or amend the decision record before dependent work begins.
- **Verification evidence required:** Signed-off decision artifact, owner list, blocked-package mapping.
- **Completion/stop criteria:** Each decision in Phase 13 register has a recorded disposition and owner.

### Blocker 7 — Missing release dry run and re-audit

- **Source path:** Process gap
- **Current state:** No approved dry run proves what a v4.3 tag would build/publish; no re-audit verifies fixes.
- **Conflict:** Tag proposal requires evidence that all blockers are closed.
- **Release impact:** BLOCKER — tag cannot be responsibly authorized.
- **Proposed work package:** Workstream F — after A–E complete, run package build, workflow validation, identity scan, and a new release-readiness audit; return a readiness verdict.
- **Files that package may modify:** New audit report only.
- **Files it must not modify:** All production paths remain read-only during audit.
- **Prerequisites:** Workstreams A–E complete.
- **Human decision/approval owner:** Release owner + audit owner.
- **Rollback strategy:** Not applicable — audit is read-only.
- **Verification evidence required:** Exact test counts, metadata inspection, workflow dry-run logs, tag/pollution checks.
- **Completion/stop criteria:** Re-audit supports either a tag proposal or a list of remaining blockers.

---

## Documentation Fix Workstreams

### Workstream A — Public documentation identity correction

**Purpose:** Remove or label unsafe present-tense claims in published docs.

**Candidate files:**

- `docs/README.md`
- `docs/architecture/components.md`
- `docs/tutorial/05-langgraph.md`
- Any navigation/index Markdown that exposes those pages as current.

**Requirements:**

- Replace current AI/runtime identity with the canonical identity.
- Label retained v4.0/runtime/LangGraph material as historical/legacy/compatibility.
- Remove or isolate live execution commands (`voyage run`, `voyage graph run`) from current onboarding.
- Preserve accurate historical facts and links.
- Do not change code, CLI, metadata, tests, workflows, or behavior.

**Anti-scope:** No code, CLI, tests, metadata, exports, workflows, moves, deletions.

**Approval:** Owner + docs owner.

**Risk:** Low-to-medium; public messaging impact.

**Gates:** Identity scan, link check, claim scan, exact diff scope, Pages preview if approved.

**Rollback:** Revert the documentation commit.

**Exit criteria:** New readers see current/legacy distinction before runtime claims.

**Unblocks:** Workstream B (policy) documentation group; parts of Workstream F.

### Workstream B — Legacy API/tutorial qualification and policy

**Purpose:** Define canonical vs compatibility vs deprecated vs historical surfaces.

**Decisions required:**

- Supported product identity and v4.3 meaning.
- Public exports and compatibility window.
- Legacy `voyage run` / `voyage graph` CLI status.
- LangGraph extra/runtime support status.
- Generated docs and Pages ownership.
- Downstream consumer evidence and deprecation policy.
- Release owner and rollback authority.

**Output:** Approved policy/decision artifact.

**Anti-scope:** No relocation, deletion, or behavior changes.

**Approval:** Repository owner + API/CLI maintainers.

**Risk:** Medium; creates support commitments.

**Gates:** Complete surface inventory, consumer evidence, migration review.

**Rollback:** Withdraw policy before implementation.

**Exit criteria:** Every public export/command/package has an approved status and timeline.

**Unblocks:** Workstreams C, D, E, F.

### Workstream C — Package metadata / pyproject identity review

**Purpose:** Align package identity after Workstream B approval.

**Candidate files:**

- `pyproject.toml`
- `voyage_framework/__init__.py` (version constants and exports if approved)
- Package-facing documentation tied to build metadata.

**Requirements:**

- Do not combine with docs-only Workstream A.
- Define exact version/description/extras changes from approved decisions.
- Preserve or deprecate exports through an approved compatibility plan.
- Run editable-install, wheel/sdist, metadata, import, CLI, and required test gates.
- Inspect built artifacts without publishing.
- Define rollback to last compatible metadata and exports.

**Anti-scope:** No unapproved API/CLI retirement; no automatic release.

**Approval:** Owner + release owner.

**Risk:** High; installation and package identity.

**Gates:** Editable install, wheel/sdist metadata inspection, import smoke, CLI smoke, all required suites.

**Rollback:** Revert metadata commit.

**Exit criteria:** Package version/description/extras match approved identity.

### Workstream D — Tag-triggered release workflow review

**Purpose:** Make tag and documentation publication behavior explicit and safe.

**Candidate files:**

- `.github/workflows/release.yml`
- `.github/workflows/jekyll-gh-pages.yml`
- Other directly coupled CI/release workflow files proven by evidence.

**Requirements:**

- Decide whether every `v*` tag should build and create a GitHub Release.
- Define tag naming, package version matching, artifact checks, permissions, failure rollback.
- Verify Pages source/navigation after docs corrections.
- Perform a non-publishing validation or dry run under explicit authority.
- Do not create a real tag during workflow alignment.
- Do not store or expose credentials.

**Anti-scope:** No package-metadata change unless Workstream C approved; no real tag/release.

**Approval:** Release owner + owner.

**Risk:** High; publishing behavior.

**Gates:** Workflow syntax validation, dry-run artifact inspection, no real tag.

**Rollback:** Revert workflow commit.

**Exit criteria:** Tag behavior matches approved release policy.

### Workstream E — Human decisions from Phase 13

**Purpose:** Record all Phase 13 decisions before any implementation package.

**Decisions to close (from Phase 13 section 8):**

| Decision | Options | Owner | Blocks |
|---|---|---|---|
| Product identity | v4.1/v4.2 current; dual product; v4.0 compatibility product | Repository owner | A, B, G |
| Public Python API | keep / deprecate / split / remove legacy exports | Owner/API maintainer | B, E, G |
| Legacy CLI | keep visible / deprecate / hide / split / remove | Owner/CLI maintainer | B, E, G |
| LangGraph support | keep extra / separate package / deprecate / retire | Owner | E, G |
| Non-core packages | keep support / split / archive / retire per package | Owner/maintainers | E, G |
| Canonical vs compatibility tests | mark / move / split CI / retain combined | QA/owner | C, E, G |
| Snapshot retention | in-tree archive / external repo / tag-only / delete later | Owner | D |
| Historical docs destination | currentize / label in place / archive | Docs owner | A, D |
| Draft/example disposition | keep / regenerate / archive / delete | Docs owner | F |
| CI/release/Pages ownership | preserve / narrow / replace / remove selected workflow | Release owner | C, G |
| Historical report errata | immutable reports / add errata / approved amendment | Owner | A |
| Cleanup release/rollback milestone | patch / minor / major / no release | Release owner | E, G |

**Output:** Approved decision-record artifact.

**Anti-scope:** No code, docs, metadata, or workflow edits.

**Approval:** Repository owner.

**Risk:** Medium; gates all downstream work.

**Gates:** Owner sign-off, decision mapping to blocked packages.

**Rollback:** Withdraw/amend decision record before dependent work.

**Exit criteria:** Each Phase 13 decision has a recorded disposition and owner.

### Workstream F — Re-audit before v4.3 tag proposal

**Purpose:** Repeat all Phase 15 gates after approved fixes.

**Requirements:**

- Verify clean `main` and exact merged histories.
- Verify canonical identity across all published surfaces.
- Validate package version/metadata and artifacts.
- Validate release/Pages behavior without publishing.
- Verify no runtime pollution.
- Verify existing milestone tags unchanged and no premature v4.3 tag exists.
- Return a new readiness verdict.

**Anti-scope:** No implementation, tag, release, or merge.

**Approval:** Release owner + audit owner.

**Risk:** Low; read-only.

**Gates:** All Phase 15 gates plus verification that Workstreams A–E completed.

**Exit criteria:** Re-audit returns either a tag proposal recommendation or a list of remaining blockers.

---

## Metadata / Release Risk Workstream

The metadata and release risks are not separate from Workstreams C and D; they are highlighted here because they are release-critical:

- **Version mismatch:** `pyproject.toml:7` reports `4.0.0`. A v4.3 tag without an approved version change would publish a `4.0.0` artifact.
- **Description mismatch:** `pyproject.toml:8` uses “AI-Native Engineering Operating System — Voyage Framework v4.0”, contradicting the canonical identity.
- **LangGraph extra:** `pyproject.toml:56-62` keeps `langgraph` and `all` extras. Whether this remains supported must be a Workstream B decision.
- **Tag trigger:** `.github/workflows/release.yml:5-6` fires on every `v*` tag. A v4.3 tag is therefore a publication event, not a documentation marker.
- **Pages source:** `.github/workflows/jekyll-gh-pages.yml:36` builds from repository root, which includes `docs/README.md` and `docs/architecture/components.md`. Identity fixes must be validated on Pages output.

These risks are addressed by Workstreams B → C → D → F, in that order.

---

## Human Decision Register

| ID | Decision | Status | Owner | Blocks | Proposed resolution path |
|---|---|---|---|---|---|
| E1 | Product identity and v4.3 meaning | BLOCKED | Repository owner | A, B, G | Workstream E |
| E2 | Public Python API compatibility window | BLOCKED | Owner/API maintainer | B, E, G | Workstream E |
| E3 | Legacy CLI disposition | BLOCKED | Owner/CLI maintainer | B, E, G | Workstream E |
| E4 | LangGraph extra/runtime support | BLOCKED | Owner | E, G | Workstream E |
| E5 | Non-core package disposition (security, memory, improvement, ast_tools, chronicler, specs) | BLOCKED | Owner/maintainers | E, G | Workstream E |
| E6 | Canonical vs compatibility test reporting | BLOCKED | QA/owner | C, E, G | Workstream E |
| E7 | `voyage_framework_v4_mvp/` snapshot retention | BLOCKED | Owner | D | Workstream E |
| E8 | Historical docs destination | BLOCKED | Docs owner | A, D | Workstream E |
| E9 | Draft/example shell disposition | BLOCKED | Docs owner | F | Workstream E |
| E10 | CI/release/Pages ownership | BLOCKED | Release owner | C, G | Workstream E |
| E11 | Historical report errata policy | BLOCKED | Owner | A | Workstream E |
| E12 | Cleanup release/rollback milestone | BLOCKED | Release owner | E, G | Workstream E |

All decisions remain BLOCKED until owners record approved dispositions.

---

## Protected Paths

The following paths must not be modified in Phase 16 and require explicit prompt approval in any future phase:

```text
README.md
AGENTS.md
pyproject.toml
.gitignore
.pre-commit-config.yaml
voyage_framework/__init__.py
voyage_framework/cli.py
voyage_framework/core/models.py
voyage_framework/core/storage.py
voyage_framework/agents/
voyage_framework/langgraph_tools/
voyage_framework_v4_mvp/
tests/
.github/
docs/VOYAGE_V4_1_CONTRACT.md
docs/prompts/
docs/guides/
docs/examples/
docs/architecture/
docs/tutorial/
docs/drafts/
docs/templates/
docs/reports/* (except the new Phase 16 report)
```

No wildcard cleanup approval is acceptable.

---

## Recommended Phase Sequence

1. **Phase 16.1 / Workstream E:** Record all Phase 13 human decisions in an approved artifact.
2. **Phase 16.2 / Workstream A:** Correct public docs identity (`docs/README.md`, `docs/architecture/components.md`, `docs/tutorial/05-langgraph.md`).
3. **Phase 16.3 / Workstream B:** Publish legacy/compatibility policy (can run partially in parallel with A once E1 is decided).
4. **Phase 16.4 / Workstream C:** Align `pyproject.toml` and package metadata after B decisions.
5. **Phase 16.5 / Workstream D:** Align release and Pages workflows after C decisions.
6. **Phase 16.6 / Workstream F:** Run release dry-run and re-audit.
7. **Only after F supports readiness:** propose a v4.3 tag in a separately authorized phase.

Do not start Phase 8 (runtime) or any implementation outside these workstreams.

---

## Rollback Strategy

### Per workstream

- **Workstream A:** Revert the single documentation commit. Root `README.md` and `AGENTS.md` remain untouched as fallback identity sources.
- **Workstream B:** Withdraw or amend the policy/decision artifact before dependent implementation begins.
- **Workstream C:** Revert `pyproject.toml` / `__init__.py` metadata commit; restore last compatible version/description/extras.
- **Workstream D:** Revert workflow commit; disable or narrow trigger if needed.
- **Workstream E:** Amend decision record; downstream work must stop until decisions stabilize.
- **Workstream F:** Read-only audit; no rollback needed, but findings must block tag if negative.

### Program-level

- Preserve the last compatible release/tag and cleanup base (`v4.1.0-mvp`, `v4.2.0-adapter-contract`).
- Revert packages in reverse dependency order (C/D before A/B if they were started out of order).
- Each rollback receives its own verification report.

---

## Verification Gates

Before any future workstream is accepted:

- Exact branch/base/tag verification.
- Clean pre-state and explicit changed-file equality.
- Forbidden-path diff and `git diff --check`.
- No `.voyage`, root `TASK.md`, or root `CONTEXT.json` pollution.
- One package per reviewed commit.

For documentation workstreams:

- Identity scan (`AI Agent Framework`, `autonomous agent runtime`, `runtime orchestration`, `LangGraph`, `CrewAI`, `AutoGen`, `automatic agent execution`, `model/provider execution layer`).
- Link check across `docs/`.
- Forbidden-path diff confirms only allowed files changed.

For metadata/package workstream:

- Editable install passes.
- Wheel/sdist metadata inspection matches approved identity.
- Import smoke tests pass.
- CLI smoke tests pass.
- All required test suites pass.

For release workflow workstream:

- Workflow syntax validation.
- Non-publishing dry-run artifact inspection.
- No real tag created during validation.

For re-audit:

- All Phase 15 gates repeated.
- Existing milestone tags unchanged.
- No premature v4.3 tag.

---

## Human Approval Checklist

Before any implementation package after Phase 16:

- [ ] Repository owner approved product identity and v4.3 meaning.
- [ ] API maintainer approved public export compatibility window.
- [ ] CLI maintainer approved legacy command disposition.
- [ ] Release owner approved version/semver, release trigger, and dry-run plan.
- [ ] Docs owner approved `docs/README.md`, `docs/architecture/components.md`, and tutorial disposition.
- [ ] QA/owner approved canonical vs compatibility test reporting plan.
- [ ] Security review completed for any workflow, credential, or permission change.
- [ ] Exact allowed-file list is documented and no wildcards are used.
- [ ] Rollback commit and verification gates are defined.
- [ ] No v4.3 tag exists and no tag will be created without a separate authorized phase.

---

## Do Not Execute in Phase 16

- Do not edit `README.md`, `docs/README.md`, `AGENTS.md`, guides, examples, architecture pages, or tutorials.
- Do not edit `pyproject.toml` or package version metadata.
- Do not edit `voyage_framework/__init__.py`, exports, or version constants.
- Do not edit `voyage_framework/cli.py` or change CLI behavior.
- Do not edit `.github` workflows or release triggers.
- Do not delete, move, rename, archive, or deprecate files.
- Do not execute Phase 13 cleanup packages.
- Do not implement compatibility shims or migrations.
- Do not create release notes, manifests, builds, packages, or dry-run artifacts.
- Do not run a publishing workflow.
- Do not create, move, annotate, or delete a tag.
- Do not claim v4.3 is released or approved.
- Do not create `TaskRecord` state or append `EventEngine` events.
- Do not create `.voyage`, root `TASK.md`, or root `CONTEXT.json`.
- Do not implement runtime execution, orchestration, model/provider calls, or credentials.
- Do not commit, push, merge, or tag.

---

## Recommendation

Do **not** propose or create a v4.3 tag from the current repository state.

Proceed only through the separately approved workstreams above, in order:

1. Close Phase 13 human decisions (Workstream E).
2. Align public documentation identity (Workstream A).
3. Publish compatibility/deprecation policy (Workstream B).
4. Align package metadata (Workstream C).
5. Align release and Pages workflows (Workstream D).
6. Run release dry-run and re-audit (Workstream F).
7. Only if F supports readiness, request a separate authorized tag phase.

Phase 16 is complete when this plan is accepted and the next workstream receives its own approved prompt.

---

## Verdict

**B. Fix plan ready with human-decision warnings**

The plan maps every Phase 15 blocker to a controlled future workstream, preserves protected paths, defines rollback and verification, and does not execute any change. It is ready for controlled implementation after owners close the Phase 13 human-decision register. v4.3 is not ready and is not authorized by this plan.
