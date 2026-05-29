"""Unit tests for SecureExecutor."""

import pytest
import asyncio
from pathlib import Path
from voyage_framework.core.models import SecurityPolicy, SecurityLevel
from voyage_framework.security.sandbox import SecureExecutor, SubprocessBackend


class TestSecureExecutor:
    def test_classify_safe(self):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy)
        assert executor.classify(["git", "status"]) == SecurityLevel.SAFE

    def test_classify_dangerous(self):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy)
        assert executor.classify(["rm", "-rf", "/"]) == SecurityLevel.DANGEROUS

    def test_classify_caution(self):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy)
        assert executor.classify(["rm", "file.txt"]) == SecurityLevel.CAUTION

    @pytest.mark.asyncio
    async def test_execute_safe_command(self, tmp_path):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy, project_root=tmp_path)
        result = await executor.execute(["echo", "hello"])
        assert result.success is True
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_block_dangerous_pattern(self, tmp_path):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy, project_root=tmp_path)
        result = await executor.execute(["rm", "-rf", "/"])
        assert result.blocked is True
        assert result.success is False

    @pytest.mark.asyncio
    async def test_block_not_whitelisted(self, tmp_path):
        policy = SecurityPolicy(allowed_commands={"git", "pytest"})
        executor = SecureExecutor(policy, project_root=tmp_path)
        result = await executor.execute(["unknown_command"])
        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_approval_required_dangerous(self, tmp_path):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy, project_root=tmp_path)
        result = await executor.execute(["systemctl", "restart", "nginx"])
        assert result.approval_required is True
        assert result.blocked is True

    def test_audit_log(self, tmp_path):
        policy = SecurityPolicy()
        executor = SecureExecutor(policy, project_root=tmp_path)
        assert executor.get_audit_log() == []


class TestSubprocessBackend:
    @pytest.mark.asyncio
    async def test_execute_echo(self):
        backend = SubprocessBackend()
        result = await backend.execute(["echo", "test"])
        assert result.success is True
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        backend = SubprocessBackend()
        result = await backend.execute(["nonexistent_command_xyz"])
        assert result.success is False
        assert result.exit_code == 127
