# PROMPT: Phase 32 — v4.3.0 Tag and Protected Release Trigger

## Role

You are a tag and release operator.
You create the annotated `v4.3.0` tag on `main`, push it to trigger the protected GitHub Actions release workflow, wait for environment approval, monitor the run, and collect evidence.
You do NOT edit source files, workflow files, or version files. You do NOT publish to PyPI. You do NOT bypass the environment approval gate.

---

## Project

```
C:\DEV\FRAMEWORK\Framework-voyage-mvp
```

---

## Phase

Phase 32 — v4.3.0 Tag and Protected Release Trigger

---

## Background

Phase 31 final re-audit is merged to `main` at `c3e8d59`. All 17 authorization criteria passed.

Authorization:
- `v4.3.0 tag authorized: YES`
- `Verdict: A. Final re-audit passed, v4.3.0 tag authorized for Phase 32`
- Source: `docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md`

Release environment protection:
- Environment: `release`
- Required reviewers: `AndreyVoyage`
- `can_admins_bypass: false`
- `prevent_self_review: false`

Release workflow safety (all confirmed in Phase 31):
- `workflow_dispatch` trigger present
- `dry_run default: true`
- `environment: release` on the job
- `pip install -e ".[dev,ast]"`
- `Create GitHub Release` gated on `github.event_name == 'push' && github.ref_type == 'tag'`
- PyPI publish disabled/commented

Dry-run evidence (Phase 30 rerun `28080683596`):
- Conclusion: `success`
- Tests: `416 passed`
- Build: `voyage_framework-4.3.0.tar.gz` and `voyage_framework-4.3.0-py3-none-any.whl`
- `Create GitHub Release` step: skipped on `workflow_dispatch`
- No `v4.3*` tags existed at dry-run time

---

## FORBIDDEN — do NOT do any of the following

- Create `v4.3` tag (any tag other than `v4.3.0`)
- Create lightweight tag (must use annotated tag)
- Force-push
- Move existing tags
- Delete existing tags (unless user explicitly approves rollback after a reported failure)
- Edit `.github/workflows/release.yml` or any workflow file
- Edit `pyproject.toml`
- Edit `voyage_framework/__init__.py` or any package source file
- Edit `tests/*`
- Edit `README.md`, `docs/README.md`, `docs/index.md`, `docs/FAQ.md`, `docs/_config.yml`
- Edit any file in `docs/prompts/*`
- Edit any file in `tools/*`
- Publish to PyPI
- Run `twine upload`
- Change release workflow
- Change version in any file
- Approve the deployment automatically (must wait for human approval in GitHub UI)
- Stage or commit `docs/handoff/LATEST_AGENT_REPORT.md`
- Stage or commit `docs/handoff/NEXT_ACTION.md`

---

## Required input files

Read and confirm before tagging:

- `docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md` — Phase 31 authorization (17/17 pass, verdict A, tag authorized: yes)
- `docs/reports/VOYAGE_PHASE_30_WORKFLOW_DISPATCH_DRY_RUN_EVIDENCE_REPORT.md` — dry-run evidence
- `.github/workflows/release.yml` — confirm all safety controls present
- `pyproject.toml` — confirm `version = "4.3.0"`
- `voyage_framework/__init__.py` — confirm `__version__ = "4.3.0"`

---

## Required pre-tag checks

### Repository state

```bash
git fetch origin --tags
git switch main
git pull --ff-only origin main
git status --short
git rev-parse HEAD
git rev-parse origin/main
git --no-pager log --oneline --decorate -20
git tag --list "v4.3*"
git ls-remote --tags origin "refs/tags/v4.3*"
```

Expected:
- `main` and `origin/main` at `c3e8d59` (or later approved main containing Phase 31)
- No local or remote `v4.3*` tag
- Working tree clean

### Version check

```bash
git grep -n -E "version|__version__|4\.0\.0|4\.3\.0" -- pyproject.toml voyage_framework/__init__.py || true
```

Expected:
- `pyproject.toml`: `version = "4.3.0"` (line 7)
- `voyage_framework/__init__.py`: `__version__ = "4.3.0"` (line 9)
- No `4.0.0` in either file

### Workflow safety check

```bash
git grep -n -E "workflow_dispatch|dry_run|default: true|environment: release|pip install -e|\[dev,ast\]|github.event_name == 'push' && github.ref_type == 'tag'|gh release|twine|publish|pypi" -- .github/workflows/release.yml || true
```

Expected:
- `workflow_dispatch` present
- `dry_run` with `default: true` present
- `environment: release` present
- `pip install -e ".[dev,ast]"` present
- `if: github.event_name == 'push' && github.ref_type == 'tag'` present
- PyPI publish commented out

### Phase 31 authorization check

```bash
git grep -n -E "v4\.3\.0 tag authorized|Authorized now: yes|Final re-audit passed|Phase 32|17/17|required_reviewers|AndreyVoyage|can_admins_bypass: false" -- docs/reports/VOYAGE_PHASE_31_FINAL_RELEASE_READINESS_REAUDIT.md || true
```

Expected: all key authorization strings present.

### GitHub environment and auth check

```bash
gh auth status
gh api repos/AndreyVoyage/Framework-voyage-mvp/environments/release
```

Expected environment response:
- `can_admins_bypass: false`
- `protection_rules` non-empty
- rule type: `required_reviewers`
- reviewer login: `AndreyVoyage`
- `prevent_self_review: false`

If any of the above is missing or fails, stop and report `C. Phase 32 blocked`.

---

## Tag creation

Only after all pre-tag checks pass:

### Create annotated tag

```bash
git tag -a v4.3.0 -m "Release v4.3.0"
```

**Must use annotated tag (`-a`). Do NOT use lightweight tag.**

### Verify tag locally

```bash
git show v4.3.0 --no-patch
git tag --list "v4.3*"
```

Expected:
- Tag type: `tag` (annotated)
- Tag name: `v4.3.0`
- Tagger: matches git user
- Message: `Release v4.3.0`
- Tagged object: commit `c3e8d59` (or the approved `main` HEAD)

### Push tag only

```bash
git push origin v4.3.0
```

**Push only the tag. Do NOT push `main` or any branch as part of this step.**

Verify remote tag:

```bash
git ls-remote --tags origin "refs/tags/v4.3.0"
git ls-remote --tags origin "refs/tags/v4.3*"
```

Expected: `refs/tags/v4.3.0` points to the annotated tag object.

---

## Workflow monitoring

### Find the triggered run

After pushing the tag, wait ~10 seconds then run:

```bash
gh run list --workflow release.yml --event push --limit 10 --json databaseId,displayTitle,workflowName,headBranch,headSha,event,status,conclusion,url,createdAt,updatedAt
```

Identify the correct run by:
- `event = push`
- `headSha` matching the tag target commit (`c3e8d59...`)
- `createdAt` close to tag push time

### Watch run

```bash
gh run watch <RUN_ID> --exit-status --interval 10
```

### Environment approval gate

If the run enters `waiting` / `pending` / `action_required` state:

**STOP the watch.**

Tell the user:

```
The release job is waiting for environment approval.
Go to: https://github.com/AndreyVoyage/Framework-voyage-mvp/actions/runs/<RUN_ID>
Click "Review deployments" → select environment "release" → Approve.
Continue only after you confirm the approval.
```

Do NOT bypass approval. Do NOT approve automatically via CLI.

Continue watching only after user confirms approval.

---

## Post-run evidence collection

```bash
gh run view <RUN_ID> --json databaseId,displayTitle,workflowName,headBranch,headSha,event,status,conclusion,url,createdAt,updatedAt,jobs
gh run view <RUN_ID> --log
```

### Verify GitHub Release

```bash
gh release view v4.3.0 --json tagName,name,isDraft,isPrerelease,url,createdAt,publishedAt,targetCommitish
```

Expected:
- `tagName`: `v4.3.0`
- `isDraft`: `false`
- `isPrerelease`: `false`
- `targetCommitish`: references `main` or the merge commit

### Verify PyPI publish

Confirm from workflow log that:
- The PyPI publish step (`Publish to PyPI`) is absent or commented out
- No `twine upload` was executed
- No upload to `pypi.org` occurred

---

## Rollback rules

**If tag was pushed but workflow fails before GitHub Release:**
- Do not retry blindly.
- Collect the full run log.
- Report failure with run ID and step details.
- Do NOT delete the tag unless user explicitly approves rollback in writing.

**If GitHub Release is created incorrectly (wrong name, wrong assets, wrong tag):**
- Stop immediately.
- Report exact release state.
- Do NOT delete the release unless user explicitly approves rollback.

**If wrong tag was created (e.g., lightweight instead of annotated, wrong commit):**
- Stop immediately.
- Run: `git show v4.3.0 --no-patch && git ls-remote --tags origin "refs/tags/v4.3*"`
- Report exact local and remote tag state.
- Request explicit human approval for any rollback action.

---

## Output

Create exactly one report file:

```
docs/reports/VOYAGE_PHASE_32_V4_3_0_TAG_RELEASE_TRIGGER_REPORT.md
```

Also write:
- `docs/handoff/LATEST_AGENT_REPORT.md` — full final terminal report (UTF-8, do NOT commit)
- `docs/handoff/NEXT_ACTION.md` — next action summary (UTF-8, do NOT commit)

The only tracked files that may change:
- `docs/reports/VOYAGE_PHASE_32_V4_3_0_TAG_RELEASE_TRIGGER_REPORT.md`

---

## Required report structure

```markdown
# Phase 32 v4.3.0 Tag and Protected Release Trigger Report

## Scope
-

## Preconditions
- Branch:
- HEAD:
- origin/main:
- Working tree:
- Phase 31 authorization:

## Version readiness
- pyproject.toml:
- voyage_framework/__init__.py:

## Workflow safety readiness
- workflow_dispatch:
- dry_run default:
- environment release:
- install extras:
- GitHub Release gating:
- PyPI publish policy:

## Environment protection
- Required reviewers:
- can_admins_bypass:
- prevent_self_review:
- Classification:

## Tag creation
- Tag:
- Type:
- Message:
- Target commit:
- Local tag created:
- Remote tag pushed:

## Workflow run
- Run ID:
- Run URL:
- Event:
- Ref/tag:
- Commit SHA:
- Status:
- Conclusion:

## Environment approval
- Required:
- Approved by:
- Evidence:

## GitHub Release evidence
- Release URL:
- Tag:
- Name:
- Draft:
- Prerelease:
- Target commitish:

## PyPI publish evidence
-

## Tag verification
- Local v4.3.0:
- Remote v4.3.0:
- Unexpected v4.3* tags:

## Generated artifacts / local hygiene
-

## Remaining warnings
-

## Remaining blockers
-

## Rollback needed
- yes/no
- Reason:

## Final release status
-

## Risks / deviations
-

## Verdict
A. v4.3.0 tag pushed and protected release completed
B. v4.3.0 tag pushed and release completed with warnings
C. Phase 32 blocked or failed
```

Fill in every section. Do not leave placeholders.

---

## Commit message (for use by the Phase 32 implementation agent, after checks pass)

```
docs: add Phase 32 v4.3.0 tag release trigger report
```

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
# Phase 32 Implementation Summary

- Branch:
- Tag created:
- Tag pushed:
- Run ID:
- Conclusion:
- GitHub Release:
- PyPI publish:
- Report saved to:
- Next action saved to:
- Copy command:
- Verdict:
```
