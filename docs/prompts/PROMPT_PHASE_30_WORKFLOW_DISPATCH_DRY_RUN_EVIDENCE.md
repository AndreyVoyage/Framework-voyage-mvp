# PROMPT: Phase 30 — Workflow Dispatch Dry-Run Evidence

## Role

You are an execution and evidence collection agent.
You trigger a safe `workflow_dispatch` dry-run of the release workflow, watch the run, collect evidence, and create a report.
You do NOT create tags. You do NOT create a GitHub Release. You do NOT publish to PyPI. You do NOT edit source files or the release workflow.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 30 — Workflow Dispatch Dry-Run Evidence

---

## Background

Phase 27 (`docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`) required:
- A successful `workflow_dispatch` dry-run must be completed and documented before `v4.3.0` tag authorization.
- The dry-run must produce `dist/voyage_framework-4.3.0-*.whl` and `dist/voyage_framework-4.3.0.tar.gz` without creating a GitHub Release.

Phase 28 (`docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md`) implemented:
- `workflow_dispatch` trigger with `dry_run: boolean, default: true`
- `environment: release` on the release job
- `Create GitHub Release` step gated on `github.event_name == 'push' && github.ref_type == 'tag'`
- PyPI publish step remains commented out

Phase 29 merged to `main` at `0ac0238`:
- `pyproject.toml`: `version = "4.3.0"`
- `voyage_framework/__init__.py`: `__version__ = "4.3.0"`
- Build: `voyage_framework-4.3.0-py3-none-any.whl` + `voyage_framework-4.3.0.tar.gz`, twine check PASSED

The `v4.3.0` tag remains NOT authorized. Phase 30 produces the dry-run evidence required for Phase 31 re-audit.

---

## Required input files

Read and analyze all of the following before running the dry-run:

- `docs/reports/VOYAGE_PHASE_27_VERSION_RELEASE_POLICY_DECISION_PLAN.md`
- `docs/reports/VOYAGE_PHASE_28_RELEASE_WORKFLOW_IMPLEMENTATION_REPORT.md`
- `docs/reports/VOYAGE_PHASE_29_VERSION_BUMP_4_3_0_REPORT.md`
- `.github/workflows/release.yml`
- `pyproject.toml`
- `voyage_framework/__init__.py`
- `docs/handoff/README.md`
- `tools/copy_latest_report.ps1`
- `tools/copy_report_to_clipboard.ps1`

---

## FORBIDDEN — do NOT do any of the following

- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py` or any package source file
- Edit `.github/workflows/*`
- Edit test files
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`, or any documentation page other than the Phase 30 report
- Create any git tag
- Create the `v4.3` or `v4.3.0` tag
- Push any tag to the remote
- Create a GitHub Release (`gh release create`, `gh release upload`, etc.)
- Publish to PyPI (`twine upload`, `pypa/gh-action-pypi-publish`, etc.)
- Run `twine upload` (read-only `twine check` is allowed)
- Run release, deploy, or publish commands
- Merge any branch
- Force-push

---

## Pre-run checks

Run all of the following before triggering the dry-run:

```bash
git fetch origin --tags
git switch main
git pull --ff-only origin main
git status --short
git --no-pager log --oneline --decorate -15
git rev-parse HEAD
git rev-parse origin/main
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
```

Expected:
- HEAD and `origin/main` are at `0ac0238` or a later approved `main` commit.
- No local or remote `v4.3*` tag exists.
- Working tree has no tracked changes.

If `v4.3*` tag exists locally or remotely, stop and report `C. Dry-run blocked — unauthorized tag found`.

### Version check

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0" -- pyproject.toml voyage_framework/__init__.py || true
```

Expected:
- `pyproject.toml` contains `version = "4.3.0"`
- `voyage_framework/__init__.py` contains `__version__ = "4.3.0"`
- No `4.0.0` remains in those two files.

### Workflow check

```bash
git grep -n -E "workflow_dispatch|dry_run|environment: release|github\.event_name|gh release|create-release|twine|publish|pypi|upload-artifact|download-artifact" -- .github/workflows/release.yml || true
```

Expected:
- `workflow_dispatch` present
- `dry_run` input with `default: true` present
- `environment: release` present
- `Create GitHub Release` step has `if: github.event_name == 'push' && github.ref_type == 'tag'`
- PyPI publish step remains commented out

### GitHub CLI authentication check

```bash
gh auth status
```

If this fails or shows not authenticated, stop immediately and report:

```
C. Dry-run blocked — GitHub CLI not authenticated
```

Do NOT attempt `gh auth login` unless the user explicitly instructs you to.

### Workflow view check

```bash
gh workflow view release.yml --ref main --yaml
```

If the workflow cannot be found by filename, list workflows and identify the release workflow:

```bash
gh workflow list
```

Then use the exact workflow name or id discovered by `gh workflow list` for all subsequent `gh workflow` and `gh run` commands.

---

## GitHub environment `release` protection

Before triggering, check whether the `release` environment is configured with required reviewers.

Document one of the following:
1. **Configured** — environment was manually configured in GitHub Settings → Environments → `release` → Required reviewers. The workflow run will enter a waiting/approval state before the job executes. Classification: **SAFE** (human gate operational).
2. **Not configured** — the `release` environment exists in YAML but protection rules have not been configured in GitHub Settings. The workflow will execute without approval. Classification: **WARNING** (human gate not yet operational; evidence still valid for dry-run purposes, but must be resolved before Phase 32 tag push).
3. **Unknown** — cannot determine from CLI. Document as **UNKNOWN** and proceed.

---

## Dry-run execution

### Trigger

```bash
gh workflow run release.yml --ref main -f dry_run=true
```

If the workflow requires the name/id from `gh workflow list`, use that exact name/id. Keep `--ref main -f dry_run=true` unchanged.

Capture any returned run URL or confirmation message.

### Find the run

```bash
gh run list --workflow release.yml --event workflow_dispatch --branch main --limit 10 --json databaseId,displayTitle,workflowName,headBranch,headSha,event,status,conclusion,url,createdAt,updatedAt
```

Identify the most recent `workflow_dispatch` run on `main`. Record its `databaseId` as `<RUN_ID>`.

### Watch the run

```bash
gh run watch <RUN_ID> --exit-status --interval 10
```

If the run enters a waiting/pending/action_required state due to environment protection:
- Stop the watch.
- Tell the user: "The workflow run is waiting for environment approval. Please go to GitHub Actions UI and approve the deployment in the `release` environment. Confirm here when approved."
- Resume the watch only after the user confirms approval.

---

## Evidence collection

After the run completes, collect all of the following:

### Run summary

```bash
gh run view <RUN_ID> --json databaseId,displayTitle,workflowName,headBranch,headSha,event,status,conclusion,url,createdAt,updatedAt,jobs
```

### Run log

```bash
gh run view <RUN_ID> --log
```

From the log, extract and document:
- The `Run tests` step result (`pytest tests/ -q` exit code and summary line, e.g., `N passed`)
- The `Build distribution packages` step result (`python -m build` output, specifically lines showing the wheel and sdist filenames, e.g., `Successfully built voyage_framework-4.3.0.tar.gz and voyage_framework-4.3.0-py3-none-any.whl`)
- The `Create GitHub Release` step — confirm it was **skipped** (not run). The condition `github.event_name == 'push' && github.ref_type == 'tag'` is false for `workflow_dispatch`, so it must not appear as executed.
- The PyPI publish step — confirm it is commented out and does not appear in the log.

### Artifact download (if available)

```bash
mkdir -p docs/handoff/phase30/artifacts
gh run download <RUN_ID> --dir docs/handoff/phase30/artifacts
```

List downloaded files:

```bash
ls docs/handoff/phase30/artifacts/
```

If artifact download fails or produces no output (workflow does not upload artifacts), document:

```
WARNING: no downloadable artifacts from workflow — evidence from log only
```

Log evidence showing `voyage_framework-4.3.0-*.whl` and `voyage_framework-4.3.0.tar.gz` is sufficient if artifacts are not uploaded.

If neither artifacts nor log prove the build step ran and produced 4.3.0 files, report `C. Dry-run evidence blocked`.

Do not commit downloaded artifacts. Delete the `docs/handoff/phase30/` directory or leave it untracked/ignored — it must not be staged.

---

## Post-run checks

```bash
git status --short
git diff --check
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
```

Expected tracked changed file only:

```
A       docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md
```

### Forbidden files check

```bash
git diff -- README.md
git diff -- docs/README.md
git diff -- AGENTS.md
git diff -- pyproject.toml
git diff -- voyage_framework
git diff -- tests
git diff -- docs/prompts
git diff -- docs/handoff/README.md
git diff -- tools
git diff -- docs/index.md
git diff -- docs/FAQ.md
git diff -- docs/_config.yml
git diff -- .github
git diff -- .gitignore
```

Expected: no output for all forbidden paths.

### Generated files check

```bash
git status --short | grep -E "^(\?\?|A|M).*\.claude|^(\?\?|A|M).*docs/handoff/LATEST_AGENT_REPORT.md|^(\?\?|A|M).*docs/handoff/NEXT_ACTION.md|^(\?\?|A|M).*docs/handoff/phase30|^(\?\?|A|M).*dist/|^(\?\?|A|M).*build/|^(\?\?|A|M).*\.egg-info" || true
```

Expected:
- `.claude/` may exist locally but must not be staged.
- Handoff/evidence files may exist locally but must not be staged.
- `dist/`, `build/`, `egg-info` must not be staged.

---

## Classification scheme

Every finding and check result must be classified as one of:

| Label | Meaning |
|-------|---------|
| `SAFE` | Verified evidence and not blocking |
| `WARNING` | Safe but needs later manual or release verification |
| `BLOCKER` | Prevents Phase 31 re-audit or future tag authorization |
| `UNKNOWN` | Requires human decision before proceeding |

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md
```

Also write:

- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked file that may change:

```
docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md
```

---

## Required report structure

The report `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` must use exactly this structure:

```markdown
# Phase 30 Workflow Dispatch Dry-Run Evidence Report

## Scope
-

## Inputs
-

## Preconditions
-

## GitHub environment release protection
-

## Workflow dispatch command
-

## Workflow run evidence
- Run id:
- Run URL:
- Event:
- Ref/branch:
- Commit SHA:
- dry_run input:
- Status:
- Conclusion:

## Job evidence
-

## Build artifact evidence
-

## Twine check evidence
-

## GitHub Release gating evidence
-

## PyPI publish evidence
-

## Tag check
- Local v4.3*:
- Remote v4.3*:
- v4.1.0-mvp:
- v4.2.0-adapter-contract:

## Version check
- pyproject.toml:
- voyage_framework/__init__.py:

## Downloaded artifacts
-

## Validation summary
-

## Forbidden actions check
-

## Remaining blockers
-

## Next phase
-

## v4.3.0 authorization
- Authorized now: no
- Reason:

## Risks / deviations
-

## Verdict
A. Dry-run evidence collected, ready for final re-audit phase
B. Dry-run evidence collected with safe warnings
C. Dry-run evidence blocked
```

Fill in every section. Do not leave placeholders.

---

## Commit

Only if report is complete and all checks pass:

```bash
git add docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md
git commit -m "docs: add Phase 30 dry-run evidence report"
```

Do not push unless explicitly instructed.

---

## Handoff requirements

After commit:

1. Write `docs/handoff/LATEST_AGENT_REPORT.md` as a full terminal-style final report (UTF-8).
2. Write `docs/handoff/NEXT_ACTION.md` with the recommended next step (UTF-8).
3. Do NOT commit either handoff file.
4. Keep your terminal response short — use the summary format below.

---

## Short terminal response format

Return only:

```markdown
# Phase 30 Execution Summary

- Branch:
- Workflow run id:
- Workflow run URL:
- Dry-run event:
- Build artifacts confirmed:
- GitHub Release step:
- Commit:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
