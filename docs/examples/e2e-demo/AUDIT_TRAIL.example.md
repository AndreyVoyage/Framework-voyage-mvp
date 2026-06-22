# Audit trail example: VF-11001

> **Illustrative append-only log, not real `EventEngine` output.** These rows are static scenario records. Nothing was appended to `.voyage`, SQLite, JSONL, or any live audit store.

## Event log

| Sequence | Timestamp | Event type | Actor | Correlation | Details |
|---:|---|---|---|---|---|
| 1 | 2026-06-21T14:00:00Z | `task_created` | `cli` | `VF-11001` | Task record created from `docs/examples/e2e-demo/task.yaml`; status `pending`. |
| 2 | 2026-06-21T14:05:00Z | `task_started` | `cli` | `VF-11001` | Status changed from `pending` to `in_progress`. |
| 3 | 2026-06-21T14:10:00Z | `process_step` | `demo-user` | `VF-11001` | Context example prepared; no current core event emission is implied. |
| 4 | 2026-06-21T14:15:00Z | `process_step` | `demo-user` | `VF-11001` | Prompt package prepared for manual transfer. |
| 5 | 2026-06-21T14:30:00Z | `process_step` | `demo-user` | `VF-11001` | Fictional external result received and recorded by the scenario narrator. |
| 6 | 2026-06-21T14:45:00Z | `approval_granted` | `human-reviewer` | `VF-11001` | Approved with a minor follow-up after manual review. |
| 7 | 2026-06-21T15:00:00Z | `task_completed` | `cli` | `VF-11001` | Status changed from `in_progress` to `completed`. |
| 8 | 2026-06-21T15:05:00Z | `task_created` | `demo-user` | `VF-11002` | Fictional follow-up recorded for burst-protection coverage. |

## Append-only interpretation

New events are appended with later sequence numbers. Earlier rows are not edited to reflect later decisions. Corrections would be represented by another event, not by rewriting history.

`TaskEngine` remains the state controller for `TaskRecord`. An event row documents an occurrence; it does not independently mutate task status. Only the task lifecycle rows shown here correspond to the normal `TaskEngine` event map. The `process_step` rows explain the demo narrative and are not a claim that `ContextBuilder` or `PromptGenerator` currently writes events.

All timestamps, actors, test evidence, and task activity in this file are fictional. No external agent was executed and no model was called.
