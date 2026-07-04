# Framework Decisions Log

> Append-only record of significant decisions. Target path in repo: `docs/framework/FRAMEWORK_DECISIONS.md`.
> Each entry: id, date, status, decision, rationale. Reversal requires a new entry, not an edit.

## D-001 - Framework is a generic dev-control-OS
- Date: 2026-06-28, Status: Accepted
- Decision: Framework's direction is a repository-agnostic development-control OS (multi-repo control via adapters), not a Narrative-only tool and not an autonomous agent runtime.
- Rationale: avoids domain leakage; enables a second repo via an adapter rather than core changes.

## D-002 - Framework / Narrative separation
- Date: 2026-06-28, Status: Accepted (see `adr/ADR-0001`)
- Decision: Narrative is a separate product; Framework inspects/validates/audits/plans it via adapters/specs only and never becomes its runtime, nor writes to Narrative-`main`.
- Rationale: clear ownership; prevents the control layer from absorbing product concerns.

## D-003 - Structured JSON reports are mandatory
- Date: 2026-06-28, Status: Accepted
- Decision: Completion reports use structured `voyage.report.v1` JSON. Free-form markdown is human-only and is not the validation target.
- Rationale: stable parse target; closes the synthetic/short-hash gap that free-form markdown allowed.

## D-004 - Dogfood/closeout ritual via validate-report
- Date: 2026-06-28, Status: Accepted
- Decision: From F0-B onward, every significant step emits human-readable + `voyage.report.v1`, and `voyage validate-report` must pass; if it fails, the closeout is not closed. Dogfood is a continuous ritual, not a one-off phase.
- Rationale: the whole strategy rests on the trust engine; it must be exercised on every real artifact.

## D-005 - Phase ordering; Phase 2 deferred
- Date: 2026-06-28, Status: Accepted
- Decision: Locked order F0-B closeout -> F0-D docs+ADR -> F0-E negative assert -> F1 hygiene/perf -> F2 generic adapter. No new development until ADR + roadmap are written into the repo.
- Rationale: avoid building the adapter contract without a recorded map.

## D-006 - Validator hardening deferred to Phase 3
- Date: 2026-06-28, Status: Accepted
- Decision: `voyage report-state`, changed-files vs named `auto_commit` (error-grade), and spec-driven forbidden paths (replacing hardcoded `FORBIDDEN_BY_ROLE`) are deferred to F3.
- Rationale: the F0-B validator is sufficient as a consistency check now; hardening is additive and non-blocking.

## D-007 - Dirty Narrative handled outside Framework
- Date: 2026-06-28, Status: Accepted
- Decision: The Narrative working tree being dirty (observed at HEAD `5571bd2`) is handled in the Narrative chat/repo via a read-only dirty-state audit. Framework does not clean Narrative.
- Rationale: respects separation; Framework must not perform product-repo maintenance.

## D-008 - validate-report loader is BOM-tolerant
- Date: 2026-06-28, Status: Accepted (implemented in F0-B closeout, commit `01b1935`)
- Decision: `report_validator.ReportClaim.from_file` reads with `encoding="utf-8-sig"`, accepting reports with or without a UTF-8 BOM. Report writers should still prefer UTF-8 without BOM for clean diffs.
- Rationale: Windows/PowerShell commonly writes a BOM; the trust engine must not be brittle to it. Surfaced by the F0-B dogfood (validate-report initially failed to load a BOM-prefixed report).

## D-010 - Role Versioning and Freshness Policy
- Date: 2026-07-04, Status: Accepted (future architecture principle; no implementation yet)
- Decision:
  - `RoleProfile` versions are immutable; a published version never changes.
  - Improvements ship as new versions, for example `developer@1.1`, never as in-place edits to `developer@1.0`.
  - The Framework role catalog is append-only across versions.
  - Consuming projects pin exact role versions in a project-side role lockfile.
  - Updating the Framework role catalog does not affect any running project until that project explicitly upgrades its pinned role versions.
  - Role upgrades require explicit human approval, version diff review, tests/regression checks, `validate-report`, and audit trail.
  - Automatic role self-modification is forbidden.
  - Role freshness checks are allowed only as read-only / propose-only audits.
  - Role Freshness Auditor may propose role updates, but must not apply them.
  - Role Upgrade Gate applies approved updates through the normal guarded workflow.
  - Sequence:
    1. Implement role versioning, project-side role pinning, and role upgrade gate first.
    2. Add role regression tests.
    3. Only later add Role Freshness Auditor as read-only/propose-only, likely F8+.
- Rationale:
  - Roles are part of the Framework control surface.
  - In-place role mutation would make project behavior non-reproducible.
  - Versioning and pinning give dependency-lockfile style safety: reproducibility, explicit upgrades, auditability, and rollback clarity.
  - Existing trust/guarded-write machinery should become the substrate for safe role evolution.
