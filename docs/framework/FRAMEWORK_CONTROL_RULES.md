# Framework Control Rules

> Binding operating rules for Voyage Framework. Target path in repo: `docs/framework/FRAMEWORK_CONTROL_RULES.md`.
> If these rules conflict with a phase prompt, these rules win. Changes require a decision entry in `FRAMEWORK_DECISIONS.md`.

## 1. Separation & scope
1. Framework and Narrative are separate projects (see `adr/ADR-0001`). Framework controls/validates; Narrative owns story/runtime/product.
2. Framework never writes directly to Narrative-`main`. Narrative edits go through the Narrative repo's own worktree + its own gates + human approval.
3. No product-repo domain logic in Framework core; integration via adapters/specs only.

## 2. Read-only by default
4. All Framework commands are read-only by default.
5. A `write-authorized` mode requires explicit enablement and must pass `validate-report`.
6. Autonomy ends at `auto branch + report`. It never reaches `main`, `origin/main`, deploy, or any product runtime.

## 3. Forbidden under automation (without separate human approval)
7. `git push`, `git merge` to main, `git reset`/`git clean` in a primary repo, deploy, Docker, SSH, Certbot.
8. Reading `.env`/secrets; mutating `.voyage` runtime (`events.db`, `events.jsonl`, `tasks.db`).
9. Deleting branch/tag/worktree; modifying global git config; `--no-verify`.
10. Unlimited task loops; automatic merge/push to origin.

## 4. Closeout / dogfood ritual (effective from F0-B onward)
11. Every significant step produces two report layers: a human-readable report and a structured `voyage.report.v1` JSON.
12. `voyage validate-report` must validate the JSON against real git state.
13. If `validate-report` fails, the closeout is NOT closed. No "done" without a passing report.
14. Every significant step also updates `FRAMEWORK_PROGRESS.md` (and `FRAMEWORK_DECISIONS.md` if a decision changed).
15. Reports verify full 40-char hashes against `git rev-parse`/`git cat-file`; short/synthetic hashes are rejected (this is what F0-E asserts negatively).

## 5. Verifiable vs unverifiable claims
16. `validate-report` is a consistency check, not an adversarial security boundary. It verifies git-observable claims (HEAD/origin/main, branch, clean, changed/staged files, forbidden paths).
17. Behavioral negatives (`bridge_executed`, `auto_launch_executed`, `env_file_read`, `claude_memory_modified`, `--no-verify`, etc.) are listed under `unverifiable_safety_claims` and are not asserted from repo state.

## 6. Definition of Done per slice (template)
- Scope declared up front (read-only or write-authorized); only allowed files changed; forbidden-touch clean.
- Gates: ruff (changed files), ruff format, mypy strict, targeted + regression pytest, `git diff --check`.
- A `voyage.report.v1` JSON produced and PASSing `validate-report`.
- One commit on the auto branch; push/merge only via a separate, human-approved closeout.
- `FRAMEWORK_PROGRESS.md` updated. No rule in this document violated.
