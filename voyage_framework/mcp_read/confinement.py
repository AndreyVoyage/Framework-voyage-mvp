"""Path confinement, basename validation, and recursive redaction helpers.

Only allowed core import: voyage_framework.core.forbidden_paths.public API.
"""

from __future__ import annotations

import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from voyage_framework.core.forbidden_paths import forbidden_patterns_for_role

# --- report-id validation ---------------------------------------------------
_REPORT_ID_RE = re.compile(r"^[A-Za-z0-9][-A-Za-z0-9_ ]*\.(md|json)$")
_MAX_REPORT_ID_LENGTH = 200

# --- MCP-local secret-name patterns -----------------------------------------
_MCP_SECRET_PATTERNS: tuple[str, ...] = (
    ".env*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.ppk",
    "*credentials*",
    "*secret*",
    "*token*",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
    "*.netrc",
    ".git-credentials",
)

# --- redaction ---------------------------------------------------------------
_REDACTED_MARKER = "[REDACTED]"
_SECRET_FIELD_KEYWORDS = frozenset(
    {
        "api_key",
        "apikey",
        "secret",
        "password",
        "passwd",
        "token",
        "credential",
        "private",
        "auth",
    }
)


def canonicalize_root(path: str | Path) -> Path:
    """Resolve and normalize a root directory path."""
    return Path(path).resolve()


def check_root_containment(resolved_path: Path, root: Path) -> bool:
    """Return True if *resolved_path* is under *root*."""
    try:
        resolved_path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_report_id(report_id: str) -> bool:
    """Return True if *report_id* is a valid basename-only identifier."""
    if not report_id or len(report_id) > _MAX_REPORT_ID_LENGTH:
        return False
    if not _REPORT_ID_RE.fullmatch(report_id):
        return False
    return not (".." in report_id or "/" in report_id or "\\" in report_id or ":" in report_id)


def _normalise_basename(path: str) -> str:
    return Path(path).name


def classify_sensitive_filename(filename: str) -> str | None:
    """Return 'potentially_sensitive' if the filename matches denied patterns.

    Returns None otherwise.
    """
    name = _normalise_basename(filename)
    # Framework canonical patterns
    framework_patterns = forbidden_patterns_for_role("framework")
    if _matches_any_glob(name, framework_patterns):
        return "potentially_sensitive"
    if _matches_any_glob(name, _MCP_SECRET_PATTERNS):
        return "potentially_sensitive"
    return None


def is_path_denied(resolved_path: Path, root: Path) -> str | None:
    """Return a denial reason if the path should be blocked, else None."""
    # Traversal check
    if not check_root_containment(resolved_path, root):
        return "path_outside_root"
    # Windows checks
    path_str = str(resolved_path)
    if path_str.startswith("\\\\"):
        return "unc_path_denied"
    if path_str.startswith("\\\\.\\"):
        return "device_path_denied"
    # ADS detection (colon after drive letter position)
    drive, tail = os.path.splitdrive(path_str)
    if tail and ":" in tail:
        return "alternate_data_stream_denied"
    # Secret basename
    name = resolved_path.name
    if classify_sensitive_filename(name) is not None:
        return "secret_path_denied"
    return None


def _matches_any_glob(name: str, patterns: tuple[str, ...]) -> bool:
    from fnmatch import fnmatch

    normalized = name.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    for pat in patterns:
        np = pat.replace("\\", "/").strip()
        if np.endswith("/**"):
            prefix = np[:-3]
            if normalized == prefix or normalized.startswith(f"{prefix}/"):
                return True
        elif fnmatch(normalized, np):
            return True
    return False


def _is_secret_key(key: str) -> bool:
    lower = key.lower().replace("_", "").replace("-", "")
    if lower in _SECRET_FIELD_KEYWORDS:
        return True
    # Also catch compound forms like "api_key_value" containing standalone kw
    for kw in _SECRET_FIELD_KEYWORDS:
        if kw in lower.split():
            return True
        # Check as word boundary: kw surrounded by non-alpha or edges
        import re

        if re.search(rf"(?:^|[^a-z]){re.escape(kw)}(?:[^a-z]|$)", lower):
            return True
    return False


def redact_recursive(obj: Any, *, in_place: bool = False) -> Any:
    """Deep-copy and redact sensitive values recursively.

    Returns a new object (never mutates *obj* unless in_place=True).
    """
    if not in_place:
        obj = deepcopy(obj)

    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if isinstance(key, str) and _is_secret_key(key):
                obj[key] = _REDACTED_MARKER
            else:
                obj[key] = redact_recursive(obj[key], in_place=True)
        return obj
    if isinstance(obj, list):
        return [redact_recursive(item, in_place=True) for item in obj]
    if isinstance(obj, str) and _is_secret_key(obj):
        return _REDACTED_MARKER
    return obj
