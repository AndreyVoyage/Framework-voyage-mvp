"""Tests for path confinement, basename validation, and redaction."""

from __future__ import annotations

import tempfile
from pathlib import Path

from voyage_framework.mcp_read.confinement import (
    canonicalize_root,
    check_root_containment,
    classify_sensitive_filename,
    is_path_denied,
    redact_recursive,
    validate_report_id,
)


class TestCanonicalizeRoot:
    def test_resolves_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sub"
            root.mkdir()
            result = canonicalize_root(str(root))
            assert result.is_absolute()
            assert result == root.resolve()

    def test_handles_windows_separators(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path_str = str(root).replace("\\", "/")
            result = canonicalize_root(path_str)
            assert result.is_absolute()


class TestCheckRootContainment:
    def test_file_inside_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            child = root / "child.txt"
            assert check_root_containment(child, root) is True

    def test_file_outside_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            outside = Path("/outside/file.txt")
            assert check_root_containment(outside, root) is False

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            escape = root / ".." / "etc" / "passwd"
            resolved = escape.resolve()
            assert check_root_containment(resolved, root) is False


class TestValidateReportId:
    def test_valid_basename_md(self):
        assert validate_report_id("BASELINE-READ-01-REPORT.md") is True

    def test_valid_basename_json(self):
        assert validate_report_id("REPORT_MCP.json") is True

    def test_rejects_subdirectory(self):
        assert validate_report_id("subdir/report.md") is False

    def test_rejects_absolute_path(self):
        assert validate_report_id("C:\\report.md") is False

    def test_rejects_traversal(self):
        assert validate_report_id("../report.md") is False

    def test_rejects_colon(self):
        assert validate_report_id("report:evil.md") is False

    def test_rejects_empty(self):
        assert validate_report_id("") is False

    def test_rejects_too_long(self):
        assert validate_report_id("A" * 201 + ".md") is False

    def test_rejects_non_md_json(self):
        assert validate_report_id("report.txt") is False

    def test_rejects_leading_dash(self):
        assert validate_report_id("-report.md") is False


class TestClassifySensitiveFilename:
    def test_env_file(self):
        assert classify_sensitive_filename(".env") == "potentially_sensitive"

    def test_env_local(self):
        assert classify_sensitive_filename(".env.local") is not None

    def test_pem_key(self):
        assert classify_sensitive_filename("private.pem") is not None

    def test_id_rsa(self):
        assert classify_sensitive_filename("id_rsa") is not None

    def test_normal_file(self):
        assert classify_sensitive_filename("README.md") is None


class TestIsPathDenied:
    def test_unc_path_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            unc = Path("\\\\server\\share\\file.txt")
            reason = is_path_denied(unc, root)
            assert reason is not None

    def test_traversal_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            escape = root / ".." / "outside"
            reason = is_path_denied(escape.resolve(), root)
            assert reason == "path_outside_root"

    def test_secret_basename_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            secret = root / ".env"
            reason = is_path_denied(secret, root)
            assert reason == "secret_path_denied"

    def test_normal_file_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            normal = root / "README.md"
            assert is_path_denied(normal, root) is None


class TestRedactRecursive:
    def test_top_level_api_key(self):
        data = {"name": "test", "api_key": "secret-abc-123"}
        result = redact_recursive(data)
        assert result["name"] == "test"
        assert "REDACTED" in result["api_key"]
        assert "secret-abc-123" not in result["api_key"]

    def test_nested_secret(self):
        data = {"config": {"settings": {"password": "s3cret!"}}}
        result = redact_recursive(data)
        assert "REDACTED" in result["config"]["settings"]["password"]

    def test_list_of_secrets(self):
        data = {"tokens": [{"token": "abc"}, {"token": "xyz"}]}
        result = redact_recursive(data)
        for entry in result["tokens"]:
            assert "REDACTED" in entry["token"]

    def test_does_not_mutate_input(self):
        data = {"key": "value", "api_key": "real"}
        original = {"key": "value", "api_key": "real"}
        redact_recursive(data, in_place=False)
        assert data == original

    def test_identical_payloads_same_result(self):
        a = {"api_key": "secret-aaa"}
        b = {"api_key": "secret-bbb"}
        ra = redact_recursive(a)
        rb = redact_recursive(b)
        assert ra == rb
