"""Tests for MCP identity — weak local session identity, no crypto."""

from __future__ import annotations

import uuid

import pytest

from voyage_framework.mcp_read.identity import (
    MCPIdentity,
    generate_request_id,
    generate_session_id,
)


def test_session_id_unique():
    assert generate_session_id() != generate_session_id()


def test_request_id_unique():
    assert generate_request_id() != generate_request_id()


def test_uuid_format():
    sid = generate_session_id()
    uuid.UUID(sid)  # raises if invalid


def test_operator_populated():
    ident = MCPIdentity.create(
        client_id="test-client",
        project_root="/tmp",
        report_root="/tmp/reports",
    )
    assert ident.operator
    assert ident.operator != "unknown_operator"


def test_client_id_required():
    with pytest.raises(ValueError):
        MCPIdentity(operator="test", client_id="")


def test_auth_strength_weak():
    ident = MCPIdentity.create(client_id="x", project_root="/tmp", report_root="/tmp")
    assert ident.client_auth_strength == "os_level_same_user"
    assert "strong" not in ident.client_auth_strength.lower()
    assert "crypt" not in ident.client_auth_strength.lower()
    assert "authenticated" not in ident.client_auth_strength.lower()


def test_no_crypto_claims():
    ident = MCPIdentity.create(client_id="x", project_root="/tmp", report_root="/tmp")
    from dataclasses import fields

    for f in fields(ident):
        val = getattr(ident, f.name)
        if isinstance(val, str):
            assert "RSA" not in val
            assert "cert" not in val.lower()


def test_with_request_id_changes():
    ident = MCPIdentity.create(client_id="x", project_root="/tmp", report_root="/tmp")
    r1 = ident.with_request_id()
    r2 = ident.with_request_id()
    assert r1.request_id != r2.request_id
    assert r1.session_id == r2.session_id
