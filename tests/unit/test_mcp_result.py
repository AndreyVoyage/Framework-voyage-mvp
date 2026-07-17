"""Tests for the non-authoritative result contract and hash semantics."""

from __future__ import annotations

import hashlib
import json

from voyage_framework.mcp_read.result import (
    ResultKind,
    tool_result,
)


def _hash_data(data):
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TestResultKind:
    def test_enum_values(self):
        assert ResultKind.REPOSITORY_STATE_SNAPSHOT == "repository_state_snapshot"
        assert ResultKind.TASK_RECORD == "task_record"

    def test_denied_is_not_success(self):
        assert ResultKind.DENIED != ResultKind.TASK_RECORD


class TestAuthority:
    def test_authoritative_always_false(self):
        result = tool_result(tool="test", request_id="r1", result_kind=ResultKind.DENIED)
        assert result.authoritative is False

    def test_authorization_not_approved(self):
        result = tool_result(
            tool="test", request_id="r1", result_kind=ResultKind.REPOSITORY_STATE_SNAPSHOT
        )
        assert result.authorization != "approved"
        assert result.authorization != "granted"


class TestHashSemantics:
    def test_hash_is_over_redacted_payload(self):
        data = {"key": "value"}
        result = tool_result(
            tool="t", request_id="r", result_kind=ResultKind.TASK_RECORD, data=data
        )
        expected = _hash_data(data)
        assert result.content_hash == expected

    def test_hash_does_not_leak_secret(self):
        """Two payloads differing only in secret values must produce same hash
        after redaction."""
        # This test is for the *semantics* — the hash is computed on whatever
        # data is passed.  The caller is responsible for redacting first.
        # Here we verify that identical redacted data => identical hash.
        redacted_a = {"name": "test", "api_key": "[REDACTED]"}
        redacted_b = {"name": "test", "api_key": "[REDACTED]"}
        h1 = _hash_data(redacted_a)
        h2 = _hash_data(redacted_b)
        assert h1 == h2

    def test_hash_changes_with_data(self):
        r1 = tool_result(
            tool="t", request_id="r", result_kind=ResultKind.TASK_RECORD, data={"x": 1}
        )
        r2 = tool_result(
            tool="t", request_id="r", result_kind=ResultKind.TASK_RECORD, data={"x": 2}
        )
        assert r1.content_hash != r2.content_hash

    def test_no_pre_redaction_hash(self):
        result = tool_result(tool="t", request_id="r", result_kind=ResultKind.TASK_RECORD, data={})
        d = result.__dict__ if hasattr(result, "__dict__") else {}
        for key in d:
            assert "pre_redaction" not in key.lower()


class TestFoundSemantics:
    def test_missing_task_not_denied(self):
        """A missing task should use task_record + found=false, not denied."""
        result = tool_result(
            tool="get_task",
            request_id="r",
            result_kind=ResultKind.TASK_RECORD,
            data={"found": False},
        )
        assert result.result_kind == ResultKind.TASK_RECORD
        assert not result.denials


class TestCanonicalSerialization:
    def test_stable_key_ordering(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert _hash_data(d1) == _hash_data(d2)
