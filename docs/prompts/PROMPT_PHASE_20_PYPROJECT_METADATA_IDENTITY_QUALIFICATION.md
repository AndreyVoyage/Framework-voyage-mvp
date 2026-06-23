# Phase 20 - Pyproject Metadata Identity Qualification

## 0. Stop-gate

Before making any change, verify repository state:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git --no-pager log --oneline --decorate -8
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected:

```text
Branch: docs/phase-20-pyproject-metadata-identity-qualification
Base: main
main contains: c54900c Merge Phase 19 LangGraph tutorial legacy qualification
Working tree: clean
No v4.3 tag exists
v4.1.0-mvp and v4.2.0-adapter-contract unchanged
```

If the repository, branch, base, working tree, or tag state is unexpected, stop and report. Do not repair unrelated state or discard another contributor's work.

Do not commit without verifying the exact diff scope.
Do not push.
Do not merge.
Do not tag.
Do not start release preparation, workflow work, dependency work, code work, test work, or cleanup.

---

## 1. Mission

Perform **Phase 20: Pyproject Metadata Identity Qualification**.

The goal is to close or explicitly block the package metadata identity risk from `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md` and `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md` by editing **only**:

```text
pyproject.toml
```

This phase is limited to metadata identity wording. It must not perform release preparation, package restructuring, dependency changes, build-system changes, test configuration changes, workflow changes, code changes, or test changes.

The current known risk is that package metadata may still present Voyage as an AI-native v4.0 runtime product rather than the canonical local Project Knowledge OS / Development Memory System.

---

## 2. Canonical identity target

Use this exact identity as the target for package metadata wording:

> **Voyage Framework is a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.**

Preserve these boundaries:

- `task.yaml` is canonical task intent;
- `TaskRecord` managed by `TaskEngine` is canonical local task lifecycle state;
- `EventEngine` is append-only audit;
- `ContextBuilder` aggregates and compares context;
- `AgentRegistry` and `ModeRegistry` are read-only catalogs;
- `PromptGenerator` creates deterministic prompt packages for manual transfer;
- adapter contracts are interface and documentation boundaries only;
- external AI tools are manual handoff targets, not Voyage runtime dependencies;
- generated `TASK.md` and `CONTEXT.json` are not canonical truth;
- legacy runtime, agent, and LangGraph surfaces may remain present but are not canonical v4.1/v4.2 core and do not define current package identity.

Do not claim or imply that v4.3 is released, tagged, or approved.

---

## 3. Authority and required sources

Authority order:

1. `docs/VOYAGE_V4_1_CONTRACT.md`;
2. `docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md`;
3. `docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md`;
4. Current `README.md`, `docs/README.md`, `docs/architecture/components.md`, and `docs/tutorial/05-langgraph.md` as already-aligned identity references;
5. `AGENTS.md` as operational guidance subordinate to the contract.

Read at minimum:

```text
docs/reports/VOYAGE_PHASE_16_DOCUMENTATION_IDENTITY_FIX_PLAN.md
docs/reports/VOYAGE_PHASE_15_V4_3_RELEASE_READINESS_AUDIT.md
pyproject.toml
README.md
docs/README.md
docs/architecture/components.md
docs/tutorial/05-langgraph.md
```

All sources except `pyproject.toml` are read-only for this phase.

---

## 4. Allowed file and allowed metadata fields

You may modify **only**:

```text
pyproject.toml
```

Within `pyproject.toml`, this phase may modify only package identity metadata wording, such as:

```text
[project].description
[project].keywords
[project].urls or project URL labels if present
[project].classifiers only if they create a wrong current identity impression
```

If no `[project].urls` table exists, do not create one unless it is necessary to remove a wrong identity claim. Prefer the smallest useful diff.

Do not edit:

```text
[build-system]
[project].name
[project].version
[project].readme
[project].requires-python
[project].license
[project].authors
dependencies
[project.optional-dependencies]
[project.scripts]
[tool.setuptools.*]
[tool.pytest.*]
[tool.mypy]
[tool.ruff]
any test, lint, type, package discovery, script, dependency, or build configuration
```

You may create no other files.

---

## 5. Required metadata behavior

### 5.1 Correct stale product identity wording

Inspect package metadata for claims that present Voyage as:

```text
AI Agent Framework
autonomous agent runtime
runtime orchestration framework
LangGraph/CrewAI/AutoGen replacement
automatic agent execution system
model/provider execution layer
AI-Native Engineering Operating System
current v4.0 runtime product
```

Replace unsafe identity wording with the canonical identity. For example, a safe description should describe Voyage as a local Project Knowledge OS / Development Memory System for structured development workflows, task memory, context packaging, audit logs, and external AI tool handoff.

### 5.2 Keep metadata concise

- Prefer a short package description suitable for Python package metadata.
- Keep keywords compact and accurate.
- Do not add long explanatory prose to `pyproject.toml`.
- Do not use metadata wording to make new product, release, API, or compatibility promises.

### 5.3 Do not solve release/version policy

Do **not** change:

```text
version = "..."
```

Do **not** bump to v4.3.
Do **not** create or move tags.
Do **not** change workflow triggers or build behavior.

If the current version value creates an unresolved release or semver ambiguity, classify it as:

```text
UNKNOWN = version/release decision needs a separate human-approved release phase
```

If this UNKNOWN classification is required to answer whether the implementation is ready, stop without commit and report **C. Not ready**.

### 5.4 Do not alter dependencies or extras

Do not remove, rename, add, or edit dependencies, optional dependencies, extras, or dependency groups, including `langgraph` or `all`.

If an optional dependency name or dependency entry appears to create a support-policy ambiguity, classify that ambiguity as UNKNOWN for a separate human decision. Do not resolve it in this phase.

### 5.5 Do not broaden scope

Do not edit code, tests, CLI behavior, workflows, docs, reports, examples, guides, architecture pages, tutorial pages, generated artifacts, or runtime state.

---

## 6. Metadata scan and classification

After editing, run:

```bash
git grep -n -E "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|AI-Native Engineering Operating System|agent runtime|provider execution|runtime orchestration|v4\.3" -- pyproject.toml || true
```

Also inspect these fields manually:

```text
[project].version
[project].description
[project].keywords
[project].classifiers
[project.optional-dependencies]
```

Classify every relevant result:

```text
SAFE   = package metadata now matches canonical Project Knowledge OS / Development Memory System identity
UNSAFE = package metadata still claims current AI agent/runtime/orchestration/provider execution identity
UNKNOWN = version/release decision, dependency/support policy, or metadata ambiguity needs human decision
```

Rules:

- A SAFE result must align with the canonical identity and avoid current runtime/provider/agent execution claims.
- An UNSAFE result is any package metadata claim that Voyage is currently an AI agent framework, autonomous runtime, orchestration framework, provider execution layer, or LangGraph/CrewAI/AutoGen replacement.
- An UNKNOWN result includes unresolved version/release policy, semver ambiguity, package support policy ambiguity, or anything that cannot be corrected by metadata wording alone.
- If you classify any result as UNKNOWN, stop and report. Do not commit unless the requested final verdict explicitly permits a warning-only commit.

Implementation is ready only if:

```text
UNSAFE = None
UNKNOWN = None
```

---

## 7. What Phase 20 must not do

```text
- Do not edit README.md.
- Do not edit docs/README.md.
- Do not edit AGENTS.md.
- Do not edit .gitignore.
- Do not edit docs/VOYAGE_V4_1_CONTRACT.md.
- Do not edit existing docs/reports/*.
- Do not edit docs/guides/*.
- Do not edit docs/examples/*.
- Do not edit docs/tutorial/*.
- Do not edit docs/architecture/*.
- Do not edit voyage_framework/ code.
- Do not edit tests/.
- Do not edit .github/ workflows.
- Do not edit build-system configuration.
- Do not edit dependencies or optional dependencies.
- Do not edit package discovery.
- Do not edit pytest, mypy, ruff, or pre-commit configuration.
- Do not change CLI behavior.
- Do not change public exports.
- Do not delete, move, rename, or archive files.
- Do not create .voyage, root TASK.md, or root CONTEXT.json.
- Do not create, move, or delete tags.
- Do not create a v4.3 tag.
- Do not merge.
- Do not push.
```

---

## 8. Verification gates

Before committing, verify:

```bash
git status --short
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
M       pyproject.toml
```

Forbidden scope check:

```bash
git diff -- README.md docs/README.md AGENTS.md .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/reports docs/guides docs/examples docs/tutorial docs/architecture voyage_framework tests .github
```

Expected: empty output.

Configuration boundary check:

```bash
git --no-pager diff -- pyproject.toml
```

Confirm manually that the diff changes only allowed metadata wording and does not modify:

```text
version
dependencies
optional dependencies
build-system
package discovery
project scripts
pytest/mypy/ruff configuration
```

Metadata identity scan:

```bash
git grep -n -E "AI Agent Framework|autonomous agent runtime|runtime orchestration framework|LangGraph|CrewAI|AutoGen|automatic agent execution|model/provider execution layer|AI-Native Engineering Operating System|agent runtime|provider execution|runtime orchestration|v4\.3" -- pyproject.toml || true
```

Expected: only SAFE matches; zero UNSAFE matches; zero UNKNOWN matches.

Runtime pollution check:

```bash
git status --short | grep -E "^(\?\?|A|M).*\.voyage|^(\?\?|A|M).*TASK.md|^(\?\?|A|M).*CONTEXT.json" || true
```

Expected: no output.

Tag check:

```bash
git tag --list "v4.3*"
git show-ref --tags v4.1.0-mvp
git show-ref --tags v4.2.0-adapter-contract
```

Expected: no v4.3 tag; existing milestone tags unchanged.

Optional metadata smoke check, if local tooling is available without network access:

```bash
python -m build --sdist --wheel --outdir .test-tmp-phase20-dist
```

This smoke check is optional and must not be run if it would require network access or create non-ignored artifacts that cannot be safely removed. Do not modify `.gitignore` to hide artifacts.

---

## 9. Commit

If and only if all required gates pass and `UNSAFE = None`, `UNKNOWN = None`:

```bash
git add pyproject.toml
git commit -m "docs: align pyproject metadata identity"
```

Do not push.

If a version/release, dependency/support, or metadata-policy ambiguity remains, do not commit. Report **C. Not ready** and list the UNKNOWN item.

---

## 10. Required final report

Return:

```markdown
# Phase 20 Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Metadata scan
- SAFE:
- UNSAFE:
- UNKNOWN:

## Version / release boundary
-

## Quality gates
-

## Forbidden files check
-

## Runtime state check
-

## Tag check
-

## Commit
- Created: yes/no
- Commit hash:
- Commit message:

## Push
- Not performed.

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with safe warnings
C. Not ready
```

---

## 11. Absolute constraints

- Do NOT soften a BLOCKER to WARNING or SAFE.
- Do NOT treat a metadata mention as safe unless it clearly matches the canonical identity or is outside package identity wording.
- Do NOT infer permission to change fields outside the allowed metadata wording.
- Do NOT change `version`.
- Do NOT change dependencies, optional dependencies, extras, build system, test config, lint config, type-check config, scripts, package discovery, code, tests, workflows, or docs.
- Do NOT claim v4.3 is released or approved.
- Do NOT create a tag, merge, push, cleanup, package release, provider call, model call, or runtime task state.
- Report failures honestly. Do not mask errors.
