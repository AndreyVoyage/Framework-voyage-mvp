"""Dedicated forbidden-path compatibility policy registry for validate-report.

This module is intentionally simple: it is stdlib-only, performs no file I/O,
has no environment or CLI coupling, and exposes a deterministic resolver that
returns the policy data for a given repo role.

The Narrative-specific compatibility patterns live here as plain data so that
`report_validator.py` does not need to embed product-repo literals. External or
repo-local policy loading is intentionally deferred to a later phase.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping

_FORBIDDEN_PATTERNS_BY_ROLE: Mapping[str, tuple[str, ...]] = {
    "framework": (
        ".env",
        ".env.*",
        ".voyage/**",
        "tools/**",
        "personas/**",
        "**/CLAUDE.md",
        ".claude/**",
        "**/.claude/**",
        "C:/Users/*/.claude/**",
        "**/tool-output/**",
        "**/temp/**",
    ),
    "narrative": (
        ".env",
        ".env.*",
        ".voyage/**",
        "tools/**",
        "personas/**",
        "*.rpy",
        "novel/game/script.rpy",
        "novel/game/screens.rpy",
        "script.rpy",
        "screens.rpy",
        "scenarios/INDEX.json",
        "scenarios/SCENARIO_LIBRARY.json",
        "scenarios/SCENARIO_MATRIX.json",
        "scenarios/*.py",
        "scenarios/*.md",
    ),
    "generic": (
        ".env",
        ".env.*",
        ".voyage/**",
    ),
}


def forbidden_patterns_for_role(repo_role: str) -> tuple[str, ...]:
    """Return the immutable forbidden-path patterns for ``repo_role``.

    Unknown roles fall back to the ``generic`` policy, preserving the
    historical behavior of ``report_validator.py``.
    """
    return _FORBIDDEN_PATTERNS_BY_ROLE.get(
        repo_role.lower(), _FORBIDDEN_PATTERNS_BY_ROLE["generic"]
    )


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _match_pattern(path: str, pattern: str) -> bool:
    normalized = _normalize_repo_path(pattern)
    if normalized.endswith("/**"):
        prefix = normalized[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    return path == normalized or fnmatch.fnmatch(path, normalized)


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = _normalize_repo_path(path)
    return any(_match_pattern(normalized, pattern) for pattern in patterns)
