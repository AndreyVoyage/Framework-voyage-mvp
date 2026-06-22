# Phase N — [Feature Name]

## 0. Stop-gate

Before making any changes, verify the environment:

```bash
cd C:\DEV\FRAMEWORK\Framework-voyage-mvp
pwd
git branch --show-current
git status -sb
git log --oneline --decorate -10
```

Expected:

- Branch: `[branch]`
- Base: `[base commit]`
- Required tags: `[tags or none]`
- Working tree: clean, excluding documented pre-existing Windows ACL directories

If the repository, branch, base, or working tree is unexpected, stop and report. Do not commit or push unless this prompt explicitly authorizes it.

## 1. Mission

[State one concrete outcome for this phase.]

## 2. What Phase N Is

- [In-scope capability or artifact]
- [Task type: code / docs-only / audit-only / release]
- [Acceptance boundary]

## 3. What Phase N Is NOT

- [Explicit anti-scope]
- [Forbidden runtime or integration behavior]
- [Work reserved for later phases]

## 4. Allowed files

Create or modify only:

```text
[path/to/allowed-file]
```

## 5. Forbidden files

Do not modify:

```text
[explicit forbidden paths and directories]
```

If a forbidden file appears necessary, stop and request a revised approved prompt.

## 6. What to implement

### 6.1 [Component or document]

[Detailed specification, inputs, outputs, validation, and acceptance criteria.]

### 6.2 [Additional component]

[Detailed specification.]

## 7. Design requirements

1. [Architectural constraint]
2. [Source-of-truth constraint]
3. [Safety or immutability constraint]
4. [Determinism or compatibility requirement]
5. [No side effects outside the allowed boundary]

## 8. Tests

Required coverage:

1. [Happy path]
2. [Validation failure]
3. [Boundary or regression case]
4. [No-pollution or no-side-effect check]

For documentation or audit phases, state explicitly why code tests are not required and list the content checks instead.

## 9. Quality gates

```bash
[task-type-specific commands from PHASE_QUALITY_GATES_TEMPLATE.md]
```

Report exact results. Do not hide failures or combine commands in a way that masks an earlier exit code.

## 10. Pollution check

```bash
git status --porcelain
git status --porcelain .voyage
```

Verify that no unexpected databases, generated artifacts, temporary files, or forbidden changes were introduced.

## 11. Expected changed files

```text
[path/to/expected-file]
```

Any additional path is a deviation.

## 12. Final report format

```markdown
# Phase N Implementation Report

## Changed files
-

## Implemented
-

## Not implemented
-

## Tests
-

## Quality gates
-

## Pollution check
-

## Forbidden files check
-

## Risks / deviations
-

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
D. Push required — user must run: git push origin <branch>
```

Do not start Phase N+1.
