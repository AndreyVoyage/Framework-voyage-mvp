"""Generic, repo-agnostic contract for repository-control adapters.

Read-only. No repository mutations, no git writes, no staging, no commits.
This module defines method signatures and result shapes only. It must not
depend on any specific target-repo domain and must not import any concrete
adapter implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoStatusResult:
    """Result of a read-only repo status check."""

    command: str
    ok: bool
    adapter: str
    repo_path: str | None = None
    summary: str | None = None
    issues: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "ok": self.ok,
            "adapter": self.adapter,
            "repo_path": self.repo_path,
            "summary": self.summary,
            "issues": list(self.issues),
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class RepoValidationResult:
    """Result of a read-only repo/target validation check."""

    command: str
    ok: bool
    adapter: str
    target: str | None = None
    issues: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "ok": self.ok,
            "adapter": self.adapter,
            "target": self.target,
            "issues": list(self.issues),
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class RepoAuditResult:
    """Result of a read-only cross-target audit/continuity check."""

    command: str
    ok: bool
    adapter: str
    target: str | None = None
    issues: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "ok": self.ok,
            "adapter": self.adapter,
            "target": self.target,
            "issues": list(self.issues),
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class RepoPreviewResult:
    """Result of a read-only, non-executed action preview."""

    command: str
    ok: bool
    adapter: str
    summary: str | None = None
    actions: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "ok": self.ok,
            "adapter": self.adapter,
            "summary": self.summary,
            "actions": list(self.actions),
            "issues": list(self.issues),
            "details": dict(self.details),
        }


class RepoControlAdapter(ABC):
    """Abstract, side-effect-free contract for repo-control adapters.

    Implementations integrate a specific target repo (via its own spec/schema
    logic) without the generic contract itself knowing anything about that
    repo's domain.
    """

    @abstractmethod
    def status(self, spec_path: str | Path) -> RepoStatusResult: ...

    @abstractmethod
    def validate(
        self, spec_path: str | Path, target: str | None = None
    ) -> RepoValidationResult: ...

    @abstractmethod
    def audit(
        self,
        spec_path: str | Path,
        target: str | None = None,
        **options: object,
    ) -> RepoAuditResult: ...

    @abstractmethod
    def preview(self, spec_path: str | Path) -> RepoPreviewResult: ...
