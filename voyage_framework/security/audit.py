"""Audit Logger — лог всех попыток выполнения команд."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from voyage_framework.core.storage import append_jsonl


class AuditLogger:
    """Logger для audit trail.

    Все команды, блокировки, approval'ы логируются в JSONL.
    """

    def __init__(self, log_path: Path | str = ".voyage/audit.jsonl") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        agent_id: str,
        role: str,
        command: list[str],
        result: str,
        blocked: bool = False,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Залогировать действие."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "agent_id": agent_id,
            "role": role,
            "command": command,
            "result": result,
            "blocked": blocked,
            "reason": reason,
            "metadata": metadata or {},
        }
        append_jsonl(self.log_path, entry)

    def get_log(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Получить последние записи audit log."""
        from voyage_framework.core.storage import load_jsonl
        entries = load_jsonl(self.log_path)
        return entries[-limit:]
