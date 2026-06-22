# Phase quality gates template

Select the gate set matching the phase type. A phase prompt may add stricter gates but must not silently remove applicable ones. Run commands separately or preserve every exit code so an early failure cannot be masked.

## Code phase

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_new_module.py -v --basetemp=.pytest-tmp/phase-name-targeted
.venv/Scripts/python.exe -m pytest tests/unit -v --basetemp=.pytest-tmp/phase-name-unit
.venv/Scripts/python.exe -m pytest tests/ -q --basetemp=.pytest-tmp/phase-name-full
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m mypy voyage_framework/core/new_module.py
git diff --check
git status --short
```

Record exact collected, passed, failed, error, and skipped counts. The full suite may be omitted only when the prompt explicitly permits it; report the omission.

## Documentation-only phase

```bash
git diff --check
git status --short --untracked-files=all
```

Also verify:

- only allowed documentation files changed;
- internal links resolve;
- headings and terminology match canonical documents;
- code snippets are clearly illustrative when they are not executable;
- risky capability claims are absent or explicitly framed as unsupported.

Optionally run Ruff on examples when it can parse them without modifying files.

## Audit-only phase

```bash
git diff --check
git status --short --untracked-files=all
git diff -- [forbidden paths]
```

Inspect the specified commit range and changed-file list. Do not run tests unless the audit prompt requires them. Do not repair findings during a read-only audit.

## Release or tag phase

```bash
git status -sb
git log --oneline --decorate -10
git tag --list
git branch --contains [release-commit]
```

Confirm:

- the working tree is clean;
- all prerequisite phase commits are merged;
- the release commit and version are correct;
- the proposed tag does not conflict with an existing tag;
- release notes and audit evidence are complete when required.

Creating or pushing commits and tags requires explicit human authority.

## Forbidden-files gate

Use explicit paths from the phase prompt:

```bash
git diff -- [forbidden paths]
git status --short --untracked-files=all
```

Any forbidden-file change is a failure. Never hide it with `.gitignore` or stage everything with `git add .`.

## Pollution gate

```bash
git status --porcelain
git status --porcelain .voyage
```

Distinguish pre-existing runtime or ACL artifacts from phase changes. Report every unexpected file. If an ACL-protected temp directory cannot be removed, report `Windows ACL protected, manual cleanup required`.

## Gate result format

For each command record:

- command or gate name;
- exact result and count;
- pass, fail, or not required;
- warning or environmental limitation;
- rerun result, if a failed environmental attempt was repeated safely.
