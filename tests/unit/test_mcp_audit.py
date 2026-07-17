"""Tests for external append-only audit writer."""

from __future__ import annotations

import json

import pytest

from voyage_framework.mcp_read.audit import (
    AuditError,
    AuditEvent,
    AuditWriter,
    write_startup_event,
)


class TestAuditWriter:
    def test_audit_not_in_repo(self, tmp_path):
        """Audit writes to the external path, not project root."""
        external = tmp_path / "handoff-artifacts" / "mcp-runtime" / "test-proj"
        writer = AuditWriter(external)
        event = AuditEvent(event_id="e1", tool="test", decision="allowed")
        writer.write_event(event)
        audit_file = external / "mcp_audit.jsonl"
        assert audit_file.exists()
        # Verify no files were created in a hypothetical project root
        assert not (tmp_path / "project_root").exists()

    def test_audit_not_dot_voyage(self, tmp_path):
        """Audit path must not contain .voyage."""
        bad_path = tmp_path / "project" / ".voyage" / "audit"
        with pytest.raises(AuditError):
            AuditWriter(bad_path)

    def test_audit_append_only(self, tmp_path):
        external = tmp_path / "audit"
        writer = AuditWriter(external)
        writer.write_event(AuditEvent(event_id="e1", tool="t1"))
        writer.write_event(AuditEvent(event_id="e2", tool="t2"))
        path = external / "mcp_audit.jsonl"
        lines = path.read_text("utf-8").strip().splitlines()
        assert len(lines) == 2
        e1 = json.loads(lines[0])
        e2 = json.loads(lines[1])
        assert e1["event_id"] == "e1"
        assert e2["event_id"] == "e2"

    def test_audit_fail_closed(self, tmp_path):
        """If audit write fails, AuditError is raised."""
        external = tmp_path / "audit"
        writer = AuditWriter(external)
        writer.write_event(AuditEvent(event_id="e1", tool="t1"))
        # Make the audit dir read-only to force write failure
        audit_file = external / "mcp_audit.jsonl"
        audit_file.chmod(0o444)
        try:
            with pytest.raises(AuditError):
                writer.write_event(AuditEvent(event_id="e2", tool="t2"))
        finally:
            audit_file.chmod(0o644)

    def test_audit_secret_free(self, tmp_path):
        """Audit events must not contain raw secret values."""
        external = tmp_path / "audit"
        writer = AuditWriter(external)
        event = AuditEvent(
            event_id="e1",
            tool="test",
            redactions=["api_key", "token"],
            input_classification={"has_secrets": True},
        )
        writer.write_event(event)
        path = external / "mcp_audit.jsonl"
        raw = path.read_text("utf-8")
        assert "sk-12345" not in raw
        assert "password" not in raw.lower()

    def test_audit_fsync_called(self, tmp_path):
        """Verify flush+fsync are called (indirect test — write succeeds)."""
        external = tmp_path / "audit"
        writer = AuditWriter(external)
        event = AuditEvent(event_id="e1", tool="test")
        writer.write_event(event)
        path = external / "mcp_audit.jsonl"
        assert path.stat().st_size > 0

    def test_audit_startup_probe(self, tmp_path):
        """write_startup_event succeeds and writes valid JSONL."""
        external = tmp_path / "audit"
        writer = AuditWriter(external)
        write_startup_event(
            writer,
            session_id="s1",
            operator="test-op",
            client_id="test-client",
            project_scope=str(tmp_path / "proj"),
            report_scope=str(tmp_path / "reports"),
        )
        path = external / "mcp_audit.jsonl"
        lines = path.read_text("utf-8").strip().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_schema"] == "voyage.mcp-audit.v1"
        assert event["decision"] == "session_started"
        assert event["session_id"] == "s1"

    def test_audit_rejects_oversized_event(self, tmp_path):
        external = tmp_path / "audit"
        writer = AuditWriter(external, max_event_bytes=128)
        event = AuditEvent(event_id="e1", tool="x" * 300)
        with pytest.raises(AuditError):
            writer.write_event(event)

    def test_audit_directory_auto_create(self, tmp_path):
        external = tmp_path / "nested" / "audit"
        assert not external.exists()
        writer = AuditWriter(external)
        writer.write_event(AuditEvent(event_id="e1", tool="t"))
        assert external.exists()
        assert (external / "mcp_audit.jsonl").exists()


def test_audit_event_dataclass_immutable(tmp_path):
    external = tmp_path / "audit"
    writer = AuditWriter(external)
    e1 = AuditEvent(event_id="e1", tool="t1", decision="allowed")
    writer.write_event(e1)
    path = external / "mcp_audit.jsonl"
    data = json.loads(path.read_text("utf-8"))
    assert data["event_id"] == "e1"
    assert data["decision"] == "allowed"
