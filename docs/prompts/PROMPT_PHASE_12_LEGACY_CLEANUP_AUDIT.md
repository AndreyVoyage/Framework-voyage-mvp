# Phase 12 — Legacy Cleanup Audit

## 0. Stop-gate

Before making any changes, verify the repository and branch:

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
Branch: docs/phase-12-legacy-cleanup-audit
Base: main
main contains: 366b43b Merge Phase 11 end-to-end demo scenario
Working tree: clean
```

If the branch, base, or working tree is unexpected, stop and report. Do not repair unrelated state. Pre-existing Windows ACL warnings may be reported separately, but they do not excuse modified project files.

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start Phase 13.

---

## 1. Mission

Perform **Phase 12: Legacy Cleanup Audit**.

This phase is a documentation audit of legacy, archived, obsolete, historical, deprecated, and experimental repository areas. Its purpose is to identify architectural ambiguity and prepare evidence-based cleanup recommendations for a later human-approved phase.

Phase 12 is **audit-only**. It does not perform cleanup.

The only permitted output is:

```text
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
```

---

## 2. Canonical authority

Use this precedence order:

1. `docs/VOYAGE_V4_1_CONTRACT.md` — canonical v4.1 architecture contract;
2. `docs/reports/VOYAGE_V4_1_MVP_CLOSURE_AUDIT.md` — v4.1 MVP closure evidence;
3. `docs/reports/VOYAGE_PHASE_7_CLOSURE_AUDIT.md` — accepted v4.2 adapter-contract boundary;
4. current root `voyage_framework/`, `tests/`, and `pyproject.toml` — active repository implementation evidence;
5. `AGENTS.md` — operational agent rules, subordinate to the architecture contract.

Generated `TASK.md` and `CONTEXT.json` are not canonical sources. Historical documents and legacy module docstrings must not override the canonical contract.

If sources conflict, record the conflict with file/line evidence and apply the authority order above. Do not silently reconcile or edit either source.

---

## 3. What Phase 12 is

Phase 12 must:

- inventory relevant repository areas;
- identify the v4.1/v4.2 canonical core and its supporting documentation;
- identify legacy, deprecated, historical, archived, experimental, duplicated, or ambiguous areas;
- find files and claims that could mislead contributors about current architecture;
- distinguish code presence from canonical support;
- classify every material finding;
- recommend later actions without performing them;
- identify decisions that require the human owner.

---

## 4. What Phase 12 is not

Phase 12 must not:

```text
- delete, move, rename, archive, or rewrite files;
- modify Python code;
- modify tests;
- modify CLI behavior;
- change dependencies or packaging;
- update README.md or AGENTS.md;
- rewrite contracts, prompts, templates, guides, examples, or existing reports;
- remove legacy modules;
- add compatibility shims;
- implement runtime execution;
- call AI models;
- add provider integrations;
- add LangGraph, CrewAI, or AutoGen orchestration;
- create TaskRecord state or write EventEngine events;
- create .voyage artifacts;
- change .gitignore to hide warnings;
- commit, push, merge, or tag.
```

A recommendation is not authorization. Every destructive or architectural action requires a later explicit prompt and human approval.

---

## 5. Allowed file

You may create only:

```text
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
```

Do not create scratch reports, inventories, scripts, databases, generated context, or temporary project files.

---

## 6. Forbidden files and directories

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
docs/reports/* (except the one allowed Phase 12 report)
voyage_framework/
voyage_framework_v4_mvp/
tests/
.github/
.voyage/
```

If any forbidden path changes during the audit, stop and report the deviation. Do not auto-repair it.

---

## 7. Required repository scan

Inspect repository structure without modifying it. Prefer read-only commands such as:

```bash
rg --files -g "!/.git/"
git ls-files
git status --short
git --no-pager log --oneline --decorate --all -20
```

Review at minimum:

```text
- root documentation and configuration files;
- docs/ contracts, reports, prompts, guides, examples, and templates;
- active voyage_framework/core/ modules;
- voyage_framework/agents/;
- voyage_framework/langgraph_tools/;
- other runtime/orchestration-oriented modules and CLI surfaces;
- nested voyage_framework_v4_mvp/ snapshot;
- tests that exercise legacy or non-core behavior;
- optional dependency groups and project metadata in pyproject.toml;
- .github/ workflows and automation;
- generated or runtime artifacts if tracked;
- duplicate or conflicting architectural descriptions.
```

Do not infer that a path is obsolete from its name alone. Use code references, tests, imports, documentation, Git history, and canonical contracts as evidence.

---

## 8. Claims and terminology audit

Search for architecture claims that may conflict with the accepted v4.1/v4.2 scope:

```bash
rg -n -i "AI Agent Framework|AI-Native|agent runtime|execute agent|run agent|self-running|orchestrat|LangGraph|CrewAI|AutoGen|OpenAI|Anthropic|provider|model inference|background worker|webhook|production deploy" . -g "!/.git/"
```

Also search for lifecycle markers:

```bash
rg -n -i "legacy|deprecated|obsolete|historical|archive|experimental|snapshot|TODO|remove later|backward compatibility" . -g "!/.git/"
```

For each material match, determine whether it is:

- a canonical present-tense capability;
- an explicitly labeled historical statement;
- a safe negative boundary statement;
- an example or future proposal;
- a misleading current claim;
- unclear and requiring human interpretation.

Do not count every keyword occurrence as a finding. Group repeated evidence into coherent issues and cite representative paths and line numbers.

---

## 9. Canonical core identification

Document the accepted v4.1/v4.2 core boundary, including:

```text
- task.yaml / TaskYamlSpec / TaskParser;
- TaskRecord / TaskEngine;
- EventEngine append-only audit;
- ContextBuilder;
- AgentRegistry read-only role catalog;
- ModeRegistry read-only mode catalog;
- PromptGenerator and PromptPackage;
- Phase 7 AdapterContract models and AdapterProtocol signatures only;
- supported tasks and sync CLI surfaces;
- canonical contracts and closure reports.
```

Explicitly distinguish:

- canonical source of truth;
- active support code;
- generated artifacts;
- legacy/historical code still present;
- future work that is documented but not implemented.

Do not promote an imported or tested legacy component into canonical scope without contract evidence.

---

## 10. Required classification

Assign each audited area or material finding exactly one primary classification:

### 1. Keep as canonical

Current, contract-backed architecture or documentation that should remain authoritative.

### 2. Keep as historical/archive

Useful provenance or compatibility evidence that must be clearly labeled and isolated from current architecture.

### 3. Move later

Material that may belong in an archive, legacy namespace, separate package, or historical documentation area in a later approved phase.

### 4. Candidate for deletion later

Apparently obsolete or duplicative material with evidence of low current value. This is a recommendation only; do not delete it.

### 5. Needs human decision

Ambiguous ownership, compatibility impact, release risk, active consumer uncertainty, or contradictory evidence prevents an autonomous recommendation.

For every item record:

```text
- path or area;
- primary classification;
- current role;
- evidence;
- architectural confusion risk: low / medium / high;
- compatibility or deletion risk: low / medium / high;
- recommended later action;
- prerequisites and human decision required.
```

Do not classify the same item into multiple primary categories. Cross-reference related findings where needed.

---

## 11. Required high-risk questions

The audit must answer, with evidence:

1. Which files present Voyage as an AI Agent Framework rather than a Development Memory System?
2. Which CLI commands appear to offer agent execution or orchestration outside the v4.1 core contract?
3. Which modules import or expose LangGraph or other orchestration behavior?
4. Are `voyage_framework/agents/` and `voyage_framework/langgraph_tools/` clearly isolated as legacy/historical?
5. Does `voyage_framework_v4_mvp/` duplicate active code or create source-of-truth ambiguity?
6. Do tests make legacy behavior look like supported v4.1 core behavior?
7. Do package metadata or optional dependencies communicate obsolete architecture?
8. Do guides, examples, prompts, or reports contain contradictory present-tense claims?
9. Are any generated artifacts or runtime databases tracked and mistaken for canonical state?
10. What could be safely clarified first in a later documentation-only phase?
11. What cleanup would have compatibility, packaging, test, or migration consequences?
12. Which decisions must remain with the human owner?

---

## 12. Report requirements

Create `docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md` with this structure:

```markdown
# Voyage Phase 12 Legacy Cleanup Audit

## 1. Executive summary
- Audit scope
- Overall finding
- Highest-risk ambiguity
- Audit-only confirmation

## 2. Method and evidence
- Commands and sources inspected
- Canonical authority order
- Limitations

## 3. Canonical v4.1/v4.2 core
- Canonical components
- Supported CLI surfaces
- Source-of-truth hierarchy

## 4. Repository inventory
| Area | Current role | Evidence | Initial risk |

## 5. Classification matrix
| Path / area | Classification | Confusion risk | Compatibility risk | Evidence | Recommended later action |

## 6. Misleading architecture claims
- Present-tense AI Agent Framework claims
- Runtime/orchestration claims
- Provider/model claims
- Safe historical, negative, and future references

## 7. Legacy runtime and orchestration surfaces
- Modules
- CLI
- Tests
- Dependencies and packaging

## 8. Duplicate and snapshot analysis
- voyage_framework_v4_mvp/
- Other duplicates or generated artifacts

## 9. Cleanup candidates for later phases
- Documentation-only clarifications
- Move/archive candidates
- Deletion candidates
- Required prerequisites

## 10. Human decisions required
- Decision
- Options
- Impact
- Evidence needed

## 11. Risks and sequencing
- Recommended non-destructive order
- Compatibility and migration risks
- Rollback considerations

## 12. Forbidden-files and pollution check
- Audit report is the only changed file
- .voyage unchanged
- No cleanup performed

## 13. Verdict
A. Audit complete — ready for human cleanup planning
B. Audit complete with evidence gaps
C. Audit incomplete or scope violation
```

Use precise language. Separate verified facts, inferences, and recommendations. Do not describe recommended cleanup as completed work.

---

## 13. Quality gates

Run:

```bash
git status --short --untracked-files=all
git --no-pager diff --stat
git --no-pager diff --name-status
git diff --check
```

Expected changed file:

```text
docs/reports/VOYAGE_PHASE_12_LEGACY_CLEANUP_AUDIT.md
```

Forbidden-files check:

```bash
git diff -- README.md AGENTS.md pyproject.toml .gitignore docs/VOYAGE_V4_1_CONTRACT.md docs/prompts docs/guides docs/examples docs/templates voyage_framework voyage_framework_v4_mvp tests .github
```

Expected: no output.

Pollution check:

```bash
git status --porcelain .voyage
git status --porcelain TASK.md CONTEXT.json
```

Expected: no changes created by Phase 12.

Because this is audit-only documentation, Python tests, Ruff, and mypy are not required unless the audit discovers a reason to run a read-only verification command. If any are run, report exact results without editing failures.

---

## 14. Final report format

Return only:

```markdown
# Phase 12 Implementation Report

## Changed files
-

## Audited
-

## Classifications
- Keep as canonical:
- Keep as historical/archive:
- Move later:
- Candidate for deletion later:
- Needs human decision:

## Not performed
-

## Quality gates
-

## Forbidden files check
-

## Pollution check
-

## Risks / evidence gaps
-

## Verdict
A. Audit complete — ready for human cleanup planning
B. Audit complete with evidence gaps
C. Audit incomplete or scope violation
```

Do not commit.
Do not push.
Do not merge.
Do not tag.
Do not start cleanup.
