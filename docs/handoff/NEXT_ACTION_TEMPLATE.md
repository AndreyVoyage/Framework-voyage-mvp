---
schema: voyage.next_action.v1
cycle: 1
task_id: VF-000
mode: bridge_one_shot
baseline_commit: "<full git rev-parse hash>"
checkpoint_tag: "<checkpoint tag or none>"
auto_branch: auto/nightly-20260627
worktree: C:/DEV/FRAMEWORK/Framework-voyage-mvp-auto-night
risk: docs-only
allowed_files:
  - "<exact/path/to/allowed-file>"
forbidden_paths:
  - ".env"
  - ".voyage/**"
  - "tools/**"
  - "tests/**"
  - "voyage_framework/**"
gates:
  - "git status --short --branch"
  - "git diff --check"
acceptance:
  - "Only allowed files are changed."
  - "No push, merge, deploy, scheduler, night run, or bridge execution occurs."
stop_conditions:
  - "turn token is not code"
  - "baseline_commit does not match git rev-parse"
  - "working tree is dirty before the task"
  - "forbidden path would be touched"
  - "secret or .env access would be required"
expires_at: "YYYY-MM-DDTHH:MM:SSZ"
turn: code
---

# NEXT ACTION

## Task

Describe the one plain-language task Code may perform.

## Allowed file scope

Code may read the repo as needed, but may write only the exact files listed in
`allowed_files`.

## Explicit forbidden actions

Do not push, merge, deploy, rebase, delete branches/tags/worktrees, modify global
git config, read `.env`, mutate `.voyage`, run a scheduler, start a night run,
auto-launch AI tools, or continue to another task.

## Expected report path

Write the Code report to:

```text
docs/handoff/LATEST_AGENT_REPORT.md
```
