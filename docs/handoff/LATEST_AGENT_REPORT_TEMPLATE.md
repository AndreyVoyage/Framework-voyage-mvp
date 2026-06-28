---
schema: voyage.agent_report.v1
cycle: 1
task_id: VF-000
status: stopped
baseline_commit: "<echo from NEXT_ACTION.md>"
auto_commit: "<full git rev-parse hash or none>"
files_changed: []
gates: []
primary_untouched: true
origin_untouched: true
secrets_untouched: true
voyage_untouched: true
anomalies: []
recommended_next: stop
turn: work
---

# LATEST AGENT REPORT

## Summary of actions

State exactly what Code did and what it did not do.

## Evidence

Include command outputs or concise evidence for branch, HEAD, changed files,
gates, and hash verification. Hashes must come from real `git rev-parse`.
Synthetic hashes are invalid.

## Deviations

List any deviations from `NEXT_ACTION.md`. If none, write `None`.

## Validation results

List each requested gate and its result. Note if any gate was skipped and why.

## Recommended next action

Recommend exactly one next action for Work. In `bridge_one_shot`, the recommended
next action should normally be `stop` or `manual review`.
