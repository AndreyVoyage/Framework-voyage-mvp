# Voyage v4.1 Development Process Improvement Audit

## 1. Executive Summary

The v4.1 workflow produced a closed MVP with a clear architectural identity: Voyage is a Development Memory System / Project Knowledge Operating System, not an AI Agent Framework. The strongest process controls were the contract-first sequence, phase-specific prompts, explicit file boundaries, stop-gates, tests, and the separation of prompt, implementation, audit, merge, and release commits.

The process nevertheless accumulated avoidable friction. Prompt branches and implementation branches were not consistently distinguished; shell examples mixed Git Bash, PowerShell, and `cmd.exe` conventions; broad repository gates interacted badly with Windows ACL-protected test directories; and legacy `AGENTS.md` content competed with the v4.1 contract until Phase 6.1. Some prompts were also long enough that agents could restate the instructions, ask for Git credentials, or try to complete commit/push steps instead of performing only the requested local work.

Repository history substantiates the phase sequence and resulting artifacts, but it does not preserve Codex/Kimi chat transcripts. Exact instances of repeated instructions, credential requests, or attempted pushes therefore cannot be attributed to a specific agent or commit from repository evidence alone. They should be treated as workflow observations supplied for this audit, not reconstructed facts.

The process needs cleanup before Phase 7. Phase 7 must remain adapter-contract-only until an approved prompt explicitly authorizes it. It must not introduce model inference, runtime agent execution, orchestration, background workers, or changes to the read-only contracts.

## 2. What Worked Well

1. **Contract before implementation.** Phase 0 established `docs/VOYAGE_V4_1_CONTRACT.md` before new v4.1 code. This gave later phases a stable source-of-truth hierarchy and a concrete stop condition for scope disputes.
2. **Small, named phases.** Task parsing, runtime task state, CLI, context building, role profiles, and mode/prompt generation were delivered separately. Phase 1.5 explicitly stabilized the task model instead of allowing uncertainty to propagate.
3. **Prompt-driven scope boundaries.** Phase prompts identified protected APIs, allowed files, forbidden features, expected tests, and final response requirements. The Phase 5 and Phase 6 prompts particularly constrained registries and prompt generation to deterministic, read-only behavior.
4. **Regression awareness.** The workflow preserved the distinction between legacy `voyage task` generation, runtime `voyage tasks`, and Context Builder `voyage sync` commands.
5. **Post-implementation audit.** The Phase 3 audit and MVP closure audit separated verification from feature delivery. This reduced the temptation to repair or extend code while supposedly auditing it.
6. **Controlled closure.** The implementation was closed, merged, tagged `v4.1.0-mvp`, and followed by a documentation-alignment phase rather than silently redefining the completed MVP.
7. **Stop-gates protected architectural boundaries.** They repeatedly prohibited runtime orchestration, LangGraph changes, model execution, unapproved CLI expansion, and mutation from read-only layers.
8. **Explicit no-commit/no-push rules.** These kept repository publication under owner control even when agents performed implementation and validation.

## 3. What Caused Confusion

### Prompt branches versus implementation branches

The history shows several prompt commits immediately followed by implementation commits on the long-lived `refactor/v4.1-contract` branch. Later work used dedicated documentation branches. This produced three concepts that were easy to conflate:

- a branch that contains the approved prompt;
- the branch on which implementation is permitted;
- the commit that is the required stop-gate base.

A prompt commit can legitimately be the current `HEAD` while the expected implementation base is its parent. Conversely, a prompt may describe an implementation branch different from the branch containing the prompt. Prompts should state all three values independently and say whether the agent must remain on the current branch or stop for a branch switch.

### Architecture terminology

Legacy modules and older documentation described agents, LangGraph runtime, agent execution, and graph commands. That vocabulary conflicted with the v4.1 MVP boundary. Before Phase 6.1, an agent reading `AGENTS.md` or legacy paths before the canonical contract could reasonably infer that Voyage v4.1 was continuing an AI Agent Framework. Phase 6.1 corrected the operational guide, but the underlying legacy modules remain a navigation hazard.

### Prompt density

Several phase prompts combine architecture, implementation details, command recipes, Git policy, acceptance criteria, and final response formatting in one long document. Repeated prohibitions help safety but can obscure the single action expected now. A concise execution header should precede supporting detail.

### Inconsistent closure language

The Phase 3 prompt contains both a slogan implying “tests pass — commit — push” and a later explicit prohibition against commit/push without approval. The prohibition is controlling, but contradictory motivational language invites agent mistakes. Every prompt should use one unambiguous Git policy.

## 4. Agent Failure Patterns

### Repeating instructions instead of executing

Codex/Kimi can respond by paraphrasing the prompt, presenting a proposed plan, or reproducing command blocks without running the permitted checks. This is more likely when the prompt is long or written partly as a handoff document. The standard instruction should say: “Execute the task now. Do not return the prompt, a plan, or instructions for another agent.” A report-only task should also require evidence collected from actual command output.

The repository contains no chat transcript that identifies exact occurrences. No agent-specific frequency or blame can be established from Git history.

### Attempting commit/push or asking for credentials

Phase prompts repeatedly prohibit automatic commit and push, indicating this was a material process risk. An agent may interpret a lifecycle description containing “commit,” “push,” “merge,” or “tag” as authorization, then ask for credentials when remote access fails. Lifecycle descriptions must distinguish owner actions from agent actions.

Use an explicit block:

```text
Git authority for this task:
- Agent may inspect local and remote metadata.
- Agent may modify only allowed files.
- Agent must not stage, commit, push, merge, tag, create a PR, or request credentials.
- Owner performs publication steps after reviewing the final report.
```

There is no repository evidence showing who attempted a push or requested credentials, so exact incidents cannot be safely claimed.

### Acting on stale operational documentation

Before Phase 6.1, agents could follow legacy `AGENTS.md` architecture instead of the v4.1 contract and treat runtime agents or LangGraph as current core scope. The fix was correct: make `AGENTS.md` operational, name the canonical documents, label legacy directories, and state that contract conflicts are resolved in favor of the contract.

### Treating environmental warnings as product failures

ACL-protected `.test-tmp-*` directories caused Git and Ruff warnings. Agents could respond by changing `.gitignore`, broadening Ruff exclusions, altering tests, or declaring a dirty tree. Those reactions create scope creep. The warnings must be classified separately from tracked project-file changes.

## 5. Git Workflow Lessons

The successful history broadly follows this lifecycle:

1. **Prompt commit:** adds the approved phase prompt and fixes the execution contract.
2. **Implementation commit:** contains only the phase deliverables and their tests.
3. **Audit commit:** records independent verification without adding features.
4. **Merge commit:** integrates the reviewed phase or release branch without rewriting phase history.
5. **Tag:** marks the exact approved release commit; `v4.1.0-mvp` points to the MVP merge.

Recommended rules:

- Give each phase a unique ID and record prompt commit, required base commit, work branch, and expected deliverable commit separately.
- Never mix prompt authoring and implementation in one commit.
- Never fix findings in an audit commit. Open a corrective phase with its own approved prompt.
- Require an owner-approved merge checklist before merge or tag actions.
- Verify the tag target after creation with `git show --no-patch --decorate <tag>`.
- Treat fetch failure as an inability to verify remote state, not automatically as a product failure. Report it explicitly.
- Do not request credentials in an implementation or audit task. Remote publication is a separate owner-authorized operation.

## 6. Stop-gate Lessons

### Where stop-gates protected the project

- They prevented new code before the v4.1 contract was established.
- They froze core components while later read-only layers were added.
- They prevented Phase 5 and Phase 6 from becoming runtime agent execution or orchestration.
- They preserved canonical state boundaries and kept generated artifacts non-canonical.
- They prevented audit and documentation phases from silently becoming implementation phases.
- They kept commits and pushes under explicit owner control.

### Where stop-gates were too brittle

- Exact `HEAD` checks did not always account for a prompt commit sitting above the implementation base.
- “Working tree clean” was ambiguous when known untracked ACL directories were visible but inaccessible.
- Remote verification depended on `git fetch`, which can fail because of credentials, network, sandbox, or `.git/FETCH_HEAD` permissions even when local state is otherwise auditable.
- Shell-specific commands were presented without declaring the required shell.
- Broad gates such as `ruff check .` traversed irrelevant snapshots and protected temporary directories.
- Exact test-count expectations became stale when the suite grew; pass/fail and collected scope are more reliable than a hard-coded total.

### Recommended standard stop-gate

```text
STOP-GATE
Shell: Git Bash on Windows (unless this prompt explicitly says PowerShell).
Current branch: <branch>
Prompt commit: <sha>
Required implementation base: <sha>
Allowed divergence: prompt commit only / none
Required tag or merge-base: <value>

Run read-only checks. Classify results as:
1. tracked project changes — STOP;
2. known ACL temp artifacts — WARN and continue;
3. remote verification unavailable — STOP only if remote freshness is essential;
4. branch/base mismatch — STOP.

Do not modify, stage, commit, push, merge, tag, or request credentials during the stop-gate.
```

## 7. Windows / Git Bash / PowerShell Lessons

### Shell syntax

Prompts should select one shell. For this repository, standardize phase command blocks on Git Bash because they already use POSIX paths and tools. Put PowerShell alternatives in a separate, labeled block only when necessary.

- Git Bash: `.venv/Scripts/python.exe`, `$TEMP`, `rm -rf`, `/c/...` paths.
- PowerShell: `.\.venv\Scripts\python.exe`, `$env:TEMP`, `Remove-Item`, `C:\...` paths.
- `cmd.exe`: `%TEMP%`; this token must not appear in Git Bash or PowerShell command blocks.

Never mix `%TEMP%`, `$TEMP`, and `$env:TEMP` in the same recipe.

### Temporary paths

Use one repository-external, writable base temp directory for pytest, with a phase-specific child:

```bash
PYTEST_TMP="${TEMP:-/tmp}/voyage-v41-phase-<id>"
.venv/Scripts/python.exe -m pytest tests/ -q --basetemp="$PYTEST_TMP" -p no:cacheprovider
```

In PowerShell:

```powershell
$pytestTmp = Join-Path $env:TEMP 'voyage-v41-phase-<id>'
.\.venv\Scripts\python.exe -m pytest tests/ -q --basetemp=$pytestTmp -p no:cacheprovider
```

Do not reuse repository-root `.test-tmp-*` paths. If cleanup is required, resolve and verify the exact path before removal. Do not conceal ACL artifacts through `.gitignore` or broad lint exclusions.

### ACL, pre-commit, and `git.exe`

- Report ACL-protected directories as environmental artifacts and list tracked changes separately.
- Run direct quality commands for evidence; do not make an audit depend only on pre-commit wrappers.
- If a hook invokes a different `git.exe`, Python, or shell than the active environment, record the resolved executable paths before diagnosing product code.
- A pre-commit installation or hook-environment failure is an environment failure, not a failed source gate. Run the equivalent direct checks and report both outcomes.
- Do not repair Git installation, credential helpers, hooks, ACLs, or global config inside a phase unless explicitly authorized.

## 8. Quality Gate Lessons

### `ruff check .` and `ruff format --check .`

Repository-wide checks are valuable for a release but brittle during scoped phases because `.` includes the historical snapshot and inaccessible temp directories. Use task-type gates with explicit active paths:

```bash
.venv/Scripts/python.exe -m ruff check voyage_framework tests
.venv/Scripts/python.exe -m ruff format --check voyage_framework tests
```

For a release, run the configured repository-wide command in addition, while explicitly excluding only documented historical or environmental paths through existing configuration—not ad hoc phase edits.

### Pytest basetemp

Use an external, unique basetemp and disable the cache provider when a clean tree is a gate. Never point basetemp at an ACL-protected directory left by another run. Targeted suites should run first for fast feedback; the full active suite should run once before a code phase is declared ready.

### Standard gates by task type

| Task type | Required gates |
|---|---|
| Code phase | Targeted tests; full `tests/`; Ruff check and format on active paths; strict mypy on active package; `git diff --check`; allowed-file and runtime-artifact checks |
| Docs-only phase | Render/readability checks relevant to the document; link or reference checks when available; `git diff --check`; allowed/forbidden-file checks; no code tests unless the prompt explains why |
| Audit-only phase | Read-only inspection; evidence table; `git diff --check`; only the audit report may change; no product fixes |
| Release/tag phase | Full tests; Ruff; format; mypy; clean tracked tree; remote/base verification; merge-commit verification; tag-target verification; owner approval |

Quality reports must record command, exit status, scope, and environmental warning separately. Do not claim a gate passed from an earlier report or commit message.

## 9. Prompt Template Improvements

Every phase prompt should begin with a compact execution contract:

```text
Task type: code | docs | audit | release
Execute now: yes
Shell: Git Bash | PowerShell
Branch: <branch>
Prompt commit: <sha>
Implementation base: <sha>
Allowed files: <exact paths/globs>
Forbidden files: <exact paths/globs>
Git authority: inspect only; no stage/commit/push/merge/tag/credentials
Final response: <exact template>
Stop conditions: <short enumerated list>
```

Then organize the prompt in this order:

1. mission and non-goals;
2. canonical references;
3. stop-gate;
4. allowed and forbidden files;
5. requirements and acceptance criteria;
6. shell-specific command block;
7. quality gates appropriate to task type;
8. final response template.

Additional improvements:

- Use exact file lists where possible and say whether new files are allowed.
- State whether the agent may repair failed gates or must stop and report.
- Assign owner-only operations explicitly.
- Remove contradictory slogans and duplicate Git instructions.
- Avoid hard-coded test totals unless they are themselves contractual.
- Require statements about unavailable evidence so agents do not invent historical incidents.
- For Codex/Kimi, add: “Execute; do not paraphrase this prompt, return a plan, hand work to another agent, request credentials, or publish changes.”

## 10. Recommended Standard Phase Lifecycle

1. **Draft:** Define one bounded outcome and identify canonical contracts.
2. **Approve prompt:** Review and commit the prompt alone.
3. **Open work branch:** Branch from the exact approved base; record branch and SHAs in the prompt.
4. **Stop-gate:** Verify branch, base, tracked cleanliness, toolchain, and allowed environmental warnings.
5. **Implement:** Modify only allowed files; do not publish.
6. **Targeted validation:** Run the smallest relevant tests and static checks.
7. **Full phase validation:** Run the task-type gate set and inspect the diff.
8. **Owner review:** Return a standardized report; owner decides whether to commit.
9. **Implementation commit:** Owner or explicitly authorized agent creates one scoped commit.
10. **Independent audit:** Audit the committed result without feature changes.
11. **Correction loop:** Any finding becomes a separately approved corrective prompt and commit.
12. **Merge:** Complete the merge checklist and create a merge commit where policy requires it.
13. **Release/tag:** Run release gates, verify the exact target, create the tag only with explicit authorization.
14. **Documentation alignment:** Update operational guidance only through an approved docs phase.

## 11. Recommended Command Templates

### Git Bash stop-gate

```bash
git branch --show-current
git status --short --branch
git rev-parse HEAD
git merge-base HEAD <base-branch>
git log --oneline --decorate -12
git tag --list '<expected-tag>'
```

Run `git fetch origin` only when remote freshness is required. If it fails, report the exact failure and do not ask for credentials unless the user explicitly authorized remote authentication.

### Scope and whitespace checks

```bash
git diff --stat
git diff --name-status
git diff --check
git status --short
git diff -- <allowed-file>
git diff -- <forbidden-path-1> <forbidden-path-2>
```

For untracked deliverables, use `git status --short` plus direct file inspection; ordinary `git diff` does not display untracked file contents.

### Code phase

```bash
.venv/Scripts/python.exe -m pytest <targeted-tests> -q --basetemp="${TEMP:-/tmp}/voyage-targeted" -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/ -q --basetemp="${TEMP:-/tmp}/voyage-full" -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check voyage_framework tests
.venv/Scripts/python.exe -m ruff format --check voyage_framework tests
.venv/Scripts/python.exe -m mypy voyage_framework
git diff --check
```

### Docs-only or audit-only phase

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

Add document-specific validation only. Do not run or claim source tests merely for ceremony.

### Standard merge/tag checklist

```text
- Approved prompt and implementation commits identified
- Independent audit verdict accepted
- Full release gates passed on exact merge candidate
- No forbidden or runtime artifacts present
- Canonical contract unchanged unless explicitly approved
- Merge target and source verified
- Owner explicitly authorized merge
- Tag name and target SHA verified
- Owner explicitly authorized tag and push
- Post-operation local and remote refs verified
```

## 12. Recommended Final Report Template

```markdown
# <Phase> Report

## Repository state
- Branch:
- HEAD:
- Required base:
- Stop-gate result:

## Changed files
- <path>: <purpose>

## Implemented
- <requirement and evidence>

## Not implemented
- <explicit non-goal>

## Quality gates
- `<exact command>`: PASS | FAIL | NOT RUN — <scope/result>

## Forbidden files check
- PASS | FAIL — <evidence>

## Environmental warnings
- <warning classified separately>

## Risks / deviations
- <fact, impact, next action>

## Git actions
- Staged: no
- Committed: no
- Pushed: no

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
```

The report should distinguish observed results, inferences, and unavailable evidence. It should never carry forward a historical test result as if the current agent ran it.

## 13. Risks Before Phase 7

1. **Scope expansion:** “Adapter” can be misread as runtime execution. Phase 7 must define interfaces, data contracts, error semantics, and approval boundaries only.
2. **Legacy gravity:** Existing `agents/` and `langgraph_tools/` code can pull design toward historical runtime architecture. They are reference/legacy areas, not Phase 7 implementation targets.
3. **Canonical-state leakage:** An adapter contract must not make `TASK.md`, `CONTEXT.json`, role profiles, mode profiles, or prompt packages writable canonical state.
4. **Mutation ambiguity:** External-tool adapters must not mutate `TaskRecord` except through the existing authorized task-state contract; read-only components must stay read-only.
5. **Security ambiguity:** Credential storage, remote authentication, model invocation, and tool execution are outside an adapter-contract-only phase.
6. **CLI creep:** No adapter CLI should be added unless a separately approved prompt explicitly authorizes commands.
7. **Platform assumptions:** The contract must define paths and transport semantics without embedding Git Bash, PowerShell, or local credential behavior into product architecture.
8. **Premature implementation:** No SDK, provider integration, network client, background process, or orchestration should be added in Phase 7.

Minimum Phase 7 prerequisites:

- an approved Phase 7 prompt committed separately;
- an exact list of contract documents/files allowed to change;
- explicit non-goals covering execution, inference, orchestration, credentials, CLI, and persistence;
- compatibility rules for `TaskYamlSpec`, `TaskRecord`, `EventEngine`, `AgentRegistry`, `ModeRegistry`, `ContextBuilder`, and `PromptGenerator`;
- contract review and audit before any runtime-adapter implementation phase is considered.

## 14. Recommended Next Steps

1. Review this audit and choose which recommendations become repository policy.
2. Create a concise reusable phase-prompt template with one declared Windows shell.
3. Define task-type quality-gate matrices and external pytest temp paths.
4. Standardize the no-credentials/no-publication instruction for Codex and Kimi.
5. Add branch, prompt SHA, base SHA, and Git authority as mandatory prompt metadata.
6. Keep Phase 7 blocked until its adapter-contract-only prompt is separately approved.
7. Audit the Phase 7 contract before authorizing any implementation beyond documentation/contracts.

## 15. Verdict

**B. Process needs cleanup before Phase 7**

The v4.1 process achieved its MVP boundary and preserved the core source-of-truth model. The remaining weaknesses are procedural rather than architectural, but they are concentrated exactly where Phase 7 could accidentally become runtime integration. Standardizing branch metadata, shell syntax, stop-gate classification, agent authority, task-specific quality gates, and final reports should precede Phase 7 approval.
