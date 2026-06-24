# Backlog

## Release workflow hardening

Status: deferred.

Future improvements:
- Add `twine check dist/*` directly into the release workflow.
- Add explicit verification that GitHub Release assets were uploaded.
- Review GitHub Actions versions and update when appropriate.
- Keep PyPI publishing disabled unless a separate PyPI plan authorizes it.

## PyPI publishing plan

Status: deferred.

Do not publish to PyPI until a separate plan is approved.

Future steps:
- Confirm package name availability and publishing policy.
- Configure PyPI account and token.
- Prefer TestPyPI validation before real PyPI publish.
- Add PyPI secret only when publishing is explicitly authorized.
- Enable PyPI publish step only in a dedicated PyPI phase.
