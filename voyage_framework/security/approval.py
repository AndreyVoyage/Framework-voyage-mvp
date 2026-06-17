"""Approval Flow — human approval для dangerous tier команд.

Через файл .voyage_approval_pending.json.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from voyage_framework.core.models import ApprovalRequest, ApprovalStatus


class ApprovalQueue:
    """Очередь approval запросов."""

    def __init__(self, queue_path: Path | str = ".voyage_approval_pending.json") -> None:
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._requests: dict[str, ApprovalRequest] = {}
        self._load()

    def _load(self) -> None:
        """Загрузить существующие запросы."""
        if not self.queue_path.exists():
            return
        try:
            with open(self.queue_path, encoding="utf-8") as f:
                data = json.load(f)
            for req_data in data.get("requests", []):
                req_data["timestamp"] = datetime.fromisoformat(req_data["timestamp"])
                if req_data.get("approval_timestamp"):
                    raw_ts = req_data["approval_timestamp"]
                    req_data["approval_timestamp"] = datetime.fromisoformat(raw_ts)
                req = ApprovalRequest(**req_data)
                self._requests[req.request_id] = req
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        """Сохранить запросы в файл."""
        data = {
            "requests": [
                {
                    "request_id": req.request_id,
                    "command": req.command,
                    "agent_id": req.agent_id,
                    "role": req.role,
                    "timestamp": req.timestamp.isoformat(),
                    "status": req.status.value,
                    "approved_by": req.approved_by,
                    "approval_timestamp": (
                        req.approval_timestamp.isoformat() if req.approval_timestamp else None
                    ),
                    "reason": req.reason,
                    "ttl_hours": req.ttl_hours,
                }
                for req in self._requests.values()
            ]
        }
        with open(self.queue_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_request(self, request: ApprovalRequest) -> ApprovalRequest:
        """Добавить запрос в очередь."""
        self._requests[request.request_id] = request
        self._save()
        return request

    def get_pending(self) -> list[ApprovalRequest]:
        """Получить все pending запросы."""
        return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]

    def approve(self, request_id: str, approved_by: str) -> ApprovalRequest | None:
        """Approve запрос."""
        req = self._requests.get(request_id)
        if not req:
            return None
        req.status = ApprovalStatus.APPROVED
        req.approved_by = approved_by
        req.approval_timestamp = datetime.now(UTC)
        self._save()
        return req

    def reject(self, request_id: str, reason: str | None = None) -> ApprovalRequest | None:
        """Reject запрос."""
        req = self._requests.get(request_id)
        if not req:
            return None
        req.status = ApprovalStatus.REJECTED
        req.reason = reason
        self._save()
        return req

    def cleanup_expired(self) -> int:
        """Удалить просроченные запросы. Возвращает количество удалённых."""
        now = datetime.now(UTC)
        expired = [
            rid for rid, req in self._requests.items()
            if req.status == ApprovalStatus.PENDING
            and (now - req.timestamp) > timedelta(hours=req.ttl_hours)
        ]
        for rid in expired:
            self._requests[rid].status = ApprovalStatus.EXPIRED
        if expired:
            self._save()
        return len(expired)

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Получить запрос по ID."""
        return self._requests.get(request_id)


class ApprovalManager:
    """Менеджер approval flow."""

    def __init__(self, queue: ApprovalQueue | None = None) -> None:
        self.queue = queue or ApprovalQueue()

    def request_approval(
        self,
        command: list[str],
        agent_id: str,
        role: str,
    ) -> ApprovalRequest:
        """Создать запрос на approval."""
        req = ApprovalRequest(
            command=command,
            agent_id=agent_id,
            role=role,
        )
        return self.queue.create_request(req)

    def is_approved(self, request_id: str) -> bool:
        """Проверить, approved ли запрос."""
        req = self.queue.get_request(request_id)
        return req is not None and req.status == ApprovalStatus.APPROVED
