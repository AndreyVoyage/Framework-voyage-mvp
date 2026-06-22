# Voyage phase workflow policy

This policy standardizes planning, implementation, audit, and closure for future Voyage Framework phases. It governs process; it does not authorize product behavior or expand a phase's technical scope.

## Standard phase lifecycle

Every phase follows eight steps:

1. **Phase 0 — Contract / scope definition.** Define the objective, canonical constraints, acceptance criteria, allowed files, forbidden files, anti-scope, and task type.
2. **Phase 1 — Prompt creation.** Add the approved execution prompt as `docs/prompts/PROMPT_PHASE_N.md` or an explicitly named variant.
3. **Phase 2 — Prompt review and approval.** The human owner reviews scope, authority, safety limits, expected files, and gates before implementation begins.
4. **Phase 3 — Implementation.** Codex, Kimi, or a human performs only the approved work on the specified branch.
5. **Phase 4 — Self-audit.** Run the required tests and quality gates, review the complete diff, and check repository pollution.
6. **Phase 5 — Human review.** The owner reviews evidence, deviations, and the final report and decides whether the work may proceed.
7. **Phase 6 — Merge and tag.** Merge and tag only with explicit human authority and only after required gates pass.
8. **Phase 7 — Closure audit and documentation.** Record final scope, evidence, history, residual risks, and milestone state without rewriting earlier contracts.

A later lifecycle step never retroactively broadens an earlier scope. A new feature requires a new approved prompt.

## Branch naming

- Code phases: `refactor/vX.Y-feature-name`
- Documentation phases: `docs/vX.Y-feature-name`
- Audit phases: `audit/vX.Y-feature-name`
- Releases: `release/vX.Y.Z`

Use lowercase kebab-case after the prefix. The phase prompt must state the exact branch and base commit.

## Git authority and credentials

AI agents such as Codex and Kimi do not hold or manage GitHub credentials and never push automatically to `origin`. They may create local commits only when the approved prompt explicitly authorizes committing. The human owner performs all pushes and remote publication.

When publication is required, report exactly:

```text
Push requires credentials. User must run: git push origin <branch>
```

Do not guess credentials, expose tokens, alter credential helpers, rewrite remote URLs, bypass authentication, or use force push unless a separate approved instruction explicitly authorizes the exact operation. GitHub credentials must never be stored in code, prompts, reports, or logs. If Git reports `could not read Username`, stop the push attempt and report it plainly.

## Commit messages

- Implementation: `Phase N: description`
- Documentation: `docs: description`
- Audit report: `audit: description`
- Patch: `fix: description`

Commits must contain only reviewed phase files. Never use `git add .`; stage specific paths only.

A typical history is:

1. prompt commit;
2. implementation or documentation commit;
3. audit commit, when an audit artifact is required;
4. reviewed merge commit;
5. milestone tag, only when explicitly approved.

## Windows shell and ACL policy

Commands must match the active shell. In Git Bash, use POSIX paths and tools. In PowerShell, use native PowerShell syntax and `.venv\Scripts\python.exe`. Do not paste shell-specific operators into the other shell without adapting them.

For pytest on Windows, use an explicit repository-local path:

```text
--basetemp=.pytest-tmp/phase-name
```

Do not rely on system `%TEMP%`. If protected `.test-tmp-*` directories appear, distinguish them from project changes and report them honestly. Do not modify `.gitignore` to conceal them without explicit approval. If cleanup fails, report:

```text
Windows ACL protected, manual cleanup required
```

Never weaken ACLs, ownership, sandboxing, or approval controls merely to make a gate look clean.

## Stop-gate rules

Every phase begins with environment verification before any edit:

- confirm the repository path, branch, base commit, and relevant tags;
- require a clean working tree, except documented pre-existing ACL directories;
- confirm that the approved prompt exists and lists allowed and forbidden files;
- stop if a forbidden file is already modified or the branch/base is wrong;
- run required tests before any authorized commit;
- run Ruff and mypy before a code-phase commit;
- never commit when `git diff --check` fails.

A stop-gate failure is reported, not repaired automatically unless the prompt explicitly authorizes that repair.

## Quality gates by task type

### Code phase

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_new_module.py -v --basetemp=.pytest-tmp/phase-name-targeted
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=.pytest-tmp/phase-name-unit
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/new_module.py
git diff --check
git status --short
```

Add the full test suite when required by risk or by the phase prompt. Report exact pass, fail, error, and skip counts.

### Documentation-only phase

```bash
git diff --check
git status --short
```

Review links, headings, terminology, and risky claims. Optionally run Ruff against documented snippets when the tool can parse them without changing files.

### Audit-only phase

```bash
git diff --check
git status --short
```

Also review forbidden-file diffs and the audited commit range. Tests are unnecessary unless the audit prompt explicitly requires them. An audit is read-only unless its prompt permits a report file.

### Release or tag phase

Verify the working tree is clean, all required phases are merged, the intended commit is checked out, and the proposed tag does not already point elsewhere. Inspect:

```bash
git tag --list
git log --oneline --decorate -10
git status -sb
```

Creating or pushing a tag requires explicit human authority.

## Allowed and forbidden files

Every phase prompt must enumerate exact allowed paths and exact forbidden paths. If a necessary file is absent from the allowed list, stop and request a revised prompt. A forbidden-file change rejects the phase until the owner resolves it. Generated `TASK.md`, `CONTEXT.json`, and `.voyage/` artifacts are not implicit scratch space.

Before handoff, compare `git status --short` and the complete diff with the expected file list. Stage only specific reviewed files; never run `git add .`.

## Final report requirements

Every implementation report includes:

- environment and branch state when relevant;
- changed files;
- implemented behavior or documentation;
- explicitly not implemented items;
- exact test results or a reason tests were not required;
- quality-gate results;
- pollution check;
- forbidden-files check;
- risks and deviations;
- verdict `A`, `B`, or `C`.

Use `D. Push required` only when the workflow specifically needs human publication and all local readiness gates have passed.

## Verdict meanings

- **A — Ready for review:** scope and gates are clean.
- **B — Ready with warnings:** no blocker exists, but material warnings remain.
- **C — Not ready:** a stop-gate, scope, test, quality, or pollution failure blocks review.
- **D — Push required:** local work is ready and the human must run `git push origin <branch>`.
