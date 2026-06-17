"""Sandbox — безопасное выполнение команд.

5 уровней защиты:
L1: Dangerous patterns (regex)
L2: Whitelist (base command)
L3: Path traversal (project_root)
L4: Network guard
L5: Dangerous tier → ApprovalRequest
"""

from __future__ import annotations

import asyncio
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from voyage_framework.core.models import ApprovalRequest, SecurityLevel, SecurityPolicy, ToolResult


class SandboxBackend(ABC):
    """ABC для backend'ов sandbox."""

    @abstractmethod
    async def execute(self, command: list[str], cwd: Path | None = None) -> ToolResult:
        """Выполнить команду и вернуть результат."""
        ...


class SubprocessBackend(SandboxBackend):
    """Backend через subprocess (default, zero-config)."""

    async def execute(self, command: list[str], cwd: Path | None = None) -> ToolResult:
        cwd = cwd or Path(".")
        start = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
            )
            stdout_b, stderr_b = await proc.communicate()
            elapsed = (time.time() - start) * 1000

            return ToolResult(
                success=proc.returncode == 0,
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                execution_time_ms=round(elapsed, 2),
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                stderr=f"Command not found: {command[0]}",
                exit_code=127,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                stderr=str(e),
                exit_code=1,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )


class DockerBackend(SandboxBackend):
    """Backend через Docker (future, requires Docker)."""

    async def execute(self, command: list[str], cwd: Path | None = None) -> ToolResult:
        # TODO: реализовать через docker run --rm
        return ToolResult(
            success=False,
            stderr="DockerBackend not yet implemented. Use SubprocessBackend.",
            exit_code=1,
        )


class SecureExecutor:
    """Безопасный executor с 5 уровнями защиты.

    Все команды проходят проверку перед выполнением.
    Dangerous tier требует ApprovalRequest.
    """

    def __init__(
        self,
        policy: SecurityPolicy,
        project_root: Path | str = ".",
        backend: SandboxBackend | None = None,
    ) -> None:
        self.policy = policy
        self.project_root = Path(project_root).resolve()
        self.backend = backend or SubprocessBackend()
        self._audit_log: list[dict[str, Any]] = []

    def _check_dangerous_patterns(self, command: list[str]) -> tuple[bool, str | None]:
        """L1: Проверка опасных паттернов через regex."""
        cmd_str = " ".join(command)
        for pattern in self.policy.dangerous_patterns:
            if re.search(pattern, cmd_str, re.IGNORECASE):
                return True, f"Dangerous pattern matched: {pattern}"
        return False, None

    def _check_whitelist(self, command: list[str]) -> tuple[bool, str | None]:
        """L2: Проверка whitelist."""
        if not command:
            return True, "Empty command"
        base = command[0]
        if base not in self.policy.allowed_commands and base not in self.policy.dangerous_commands:
            return True, f"Command '{base}' not in allowed or dangerous list"
        return False, None

    def _check_path_traversal(self, command: list[str]) -> tuple[bool, str | None]:
        """L3: Проверка path traversal."""
        for arg in command[1:]:
            if arg.startswith("-"):
                continue
            if arg.startswith("http") or arg.startswith("https"):
                continue
            # Разрешать относительные пути от project_root
            path = (self.project_root / arg).resolve()
            try:
                path.relative_to(self.project_root)
            except ValueError:
                return True, f"Path traversal: {arg} outside {self.project_root}"
        return False, None

    def _check_network(self, command: list[str]) -> tuple[bool, str | None]:
        """L4: Проверка сетевых операций."""
        if self.policy.allow_network:
            return False, None
        cmd_str = " ".join(command).lower()
        network_flags = ["--url", "http://", "https://", "-u ", "--host"]
        for flag in network_flags:
            if flag in cmd_str:
                return True, f"Network operation blocked: {flag}"
        return False, None

    def _check_dangerous_tier(self, command: list[str]) -> SecurityLevel:
        """L5: Определение уровня опасности."""
        if not command:
            return SecurityLevel.SAFE
        base = command[0]

        # Проверка dangerous patterns
        blocked, _ = self._check_dangerous_patterns(command)
        if blocked:
            return SecurityLevel.DANGEROUS

        # Caution tier: rm, mv, cp без опасных паттернов
        if base in {"rm", "mv", "cp"}:
            return SecurityLevel.CAUTION

        if base in self.policy.dangerous_commands:
            return SecurityLevel.DANGEROUS

        return SecurityLevel.SAFE

    def classify(self, command: list[str]) -> SecurityLevel:
        """Классифицировать команду по уровню безопасности."""
        return self._check_dangerous_tier(command)

    async def execute(self, command: list[str]) -> ToolResult:
        """Выполнить команду с полной проверкой безопасности.

        Returns:
            ToolResult: результат выполнения или блокировки.
        """
        # L1: Patterns
        blocked, reason = self._check_dangerous_patterns(command)
        if blocked:
            return self._block(command, reason or "Dangerous pattern")

        # L2: Whitelist
        blocked, reason = self._check_whitelist(command)
        if blocked:
            return self._block(command, reason or "Not whitelisted")

        # L3: Path traversal
        blocked, reason = self._check_path_traversal(command)
        if blocked:
            return self._block(command, reason or "Path traversal")

        # L4: Network
        blocked, reason = self._check_network(command)
        if blocked:
            return self._block(command, reason or "Network blocked")

        # L5: Dangerous tier
        level = self._check_dangerous_tier(command)
        if level == SecurityLevel.DANGEROUS:
            return ToolResult(
                success=False,
                blocked=True,
                approval_required=True,
                reason=f"Dangerous tier: {' '.join(command[:2])}...",
                stderr=f"APPROVAL_REQUIRED: Command requires human approval: {' '.join(command)}",
            )

        # Выполнение
        result = await self.backend.execute(command, cwd=self.project_root)

        # Audit log
        self._audit_log.append({
            "command": command,
            "level": level.value,
            "success": result.success,
            "blocked": result.blocked,
            "timestamp": time.time(),
        })

        return result

    def _block(self, command: list[str], reason: str) -> ToolResult:
        """Заблокировать команду с причиной."""
        self._audit_log.append({
            "command": command,
            "blocked": True,
            "reason": reason,
            "timestamp": time.time(),
        })
        return ToolResult(
            success=False,
            blocked=True,
            reason=reason,
            stderr=f"BLOCKED: {reason}",
        )

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Получить audit trail."""
        return self._audit_log.copy()

    def create_approval_request(
        self,
        command: list[str],
        agent_id: str,
        role: str,
    ) -> ApprovalRequest:
        """Создать запрос на approval для dangerous tier."""
        return ApprovalRequest(
            command=command,
            agent_id=agent_id,
            role=role,
        )
