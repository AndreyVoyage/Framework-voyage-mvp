# Framework Roadmap - Overview (one-page control map)

> Target path in repo: `docs/framework/FRAMEWORK_ROADMAP_OVERVIEW.md`.
> This is the STABLE high-level map. For LIVE status (current HEAD, what's done/in-progress) see `FRAMEWORK_PROGRESS.md`. Details live in `FRAMEWORK_ROADMAP.md`; rules in `FRAMEWORK_CONTROL_RULES.md`; decisions in `FRAMEWORK_DECISIONS.md`; separation in `adr/ADR-0001-...`.

## Final outcome
Framework = a **generic dev-control-OS**: a repository-agnostic system that *controls* development across projects (memory, tasks, events, chronicler, approvals, repo adapters, validated reports, archive/replay/metrics, read-only dashboard) **without becoming any of those projects**. Narrative is the first external project it learns to control, not part of Framework.

## Hard boundary (never changes)
Autonomy ends at **`auto branch + report`**. It never reaches `main`, `origin/main`, deploy, or a product runtime on its own. Merge, push, deploy, and any AI/agent invocation are **human-gated**.

## Phase map (stable)
  FOUNDATION
    F0-A  trust-engine design            [done]
    F0-B  validate-report trust engine   [done]
    F0-D  documentation + ADR            [done]
    F0-E  negative assert (bad report)   [done]
  NEAR-TERM
    F1    hygiene / performance          [done]
    F2    generic RepoControlAdapter (Narrative = first impl) [done]
    F3    trust hardening (report-state, auto_commit checks, spec-driven paths) [done]
  MID-TERM
    F4    Narrative read-only tools (preflight, spec-update) [done]
    F5    second adapter -> prove multi-repo [done]
    F6    edit-safety + preview (read-only, pre-write) [next]
  LONG-TERM
    F7    first guarded WRITE (authorized, gated)
  HORIZON (far, gated)
    F8+   agent runtime / scheduler / DASHBOARD / replay / metrics

## Locked next sequence
`F6 planning -> F6 implementation -> F7 guarded write`. No F6 development starts until the F6 planning phase is approved. LangGraph activation remains F8+ only.

## Where dashboard sits
Dashboard is **not a current feature**. It is a **future read-only observability layer** (Horizon / F8+). It shows:
- which tasks ran and which reports passed,
- which gates failed, which steps are blocked,
- which repos are clean/dirty, which phase is active,
- what is waiting for approval; replay/metrics.

Dashboard MUST NOT execute agents, merge, push, or deploy. It only *shows*; the human acts.

## Why dashboard cannot come first
A dashboard without the trust layer is just a pretty panel of unverified claims. It requires, first: `validate-report` + structured `voyage.report.v1` reports + an event/progress model + the adapter contract + repo-state checks. Only then can it display verifiable truth.
