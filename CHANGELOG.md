# Changelog

## v4.3.0 — 2026-06-24

### Released
- Published GitHub Release `v4.3.0`.
- Created annotated tag `v4.3.0` targeting the Phase 31 authorized release commit.
- Uploaded release assets:
  - `voyage_framework-4.3.0-py3-none-any.whl`
  - `voyage_framework-4.3.0.tar.gz`

### Release safety
- Release workflow uses `workflow_dispatch` with `dry_run` support.
- GitHub Release creation is gated to tag-push events only.
- Protected `release` environment requires manual approval from `AndreyVoyage`.
- Admin bypass is disabled for the `release` environment.
- PyPI publishing remains intentionally disabled/commented out.

### Validation
- Phase 30 dry-run passed in GitHub Actions.
- CI tests passed: `416 passed`.
- CI build produced both wheel and sdist.
- Phase 31 final re-audit passed with 17/17 criteria.
- Phase 32 protected release workflow completed successfully.

### Notes
- PyPI was not published in this release.
- Post-release maintenance items are tracked in `docs/BACKLOG.md`.
