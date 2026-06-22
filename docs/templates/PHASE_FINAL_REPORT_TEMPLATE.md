# Phase N Implementation Report

## Environment
- branch: `[branch]`
- commit: `[commit or uncommitted]`
- origin sync: `[ahead / behind / synchronized / not checked]`

## Changed files
- `[path]`

## Implemented
- `[implemented outcome]`

## Not implemented
- `[explicit anti-scope item]`

## Tests
- `[module tests]`: `X/Y passed`
- `[unit suite]`: `X/Y passed`
- `[full suite]`: `X/Y passed`
- skipped: `[count and reason]`

## Quality gates
- Ruff check: `passed / failed / not required`
- Ruff format: `passed / failed / not required`
- mypy: `passed / failed / not required`
- `git diff --check`: `passed / failed`

## Pollution check
- `.voyage/tasks.db`: `created / not created / pre-existing unchanged`
- `TASK.md`: `changed / unchanged`
- `CONTEXT.json`: `changed / unchanged`
- untracked files: `[list or none]`
- Windows ACL warnings: `[details or none]`

## Forbidden files check
- `[file or directory]`: `changed / unchanged`

## Risks / deviations
1. `[risk, impact, and mitigation]`
2. `[deviation or none]`

## Verdict
A. Ready for review
B. Ready with warnings
C. Not ready
D. Push required — user must run: `git push origin <branch>`
