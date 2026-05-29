"""Policy — ролевые разрешения для агентов.

RolePolicy определяет, что может каждая роль.
PolicyEnforcer проверяет разрешения в runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RolePolicy:
    """Политика роли: что может, что не может."""

    name: str
    can_write_adr: bool = False
    can_write_code: bool = False
    can_deploy: bool = False
    can_review: bool = False
    can_run_tests: bool = False
    can_run_linters: bool = False
    can_access_dangerous: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    max_retries: int = 3


class PolicyEnforcer:
    """Enforcer ролевых политик."""

    DEFAULT_POLICIES: dict[str, RolePolicy] = {
        "architect": RolePolicy(
            name="architect",
            can_write_adr=True,
            can_review=True,
            can_run_linters=True,
            allowed_paths=["*"],
        ),
        "developer": RolePolicy(
            name="developer",
            can_write_code=True,
            can_run_tests=True,
            can_run_linters=True,
            allowed_paths=["backend/", "frontend/", "tests/"],
            forbidden_paths=["ADR/", "voyage/adr/"],
        ),
        "reviewer": RolePolicy(
            name="reviewer",
            can_review=True,
            can_run_tests=True,
            can_run_linters=True,
            allowed_paths=["*"],
        ),
        "devops": RolePolicy(
            name="devops",
            can_deploy=True,
            can_access_dangerous=True,
            allowed_paths=["*"],
        ),
        "security": RolePolicy(
            name="security",
            can_review=True,
            can_run_tests=True,
            can_run_linters=True,
            allowed_paths=["*"],
        ),
        "qa": RolePolicy(
            name="qa",
            can_run_tests=True,
            can_review=True,
            allowed_paths=["*"],
        ),
    }

    def __init__(self, policies: Optional[dict[str, RolePolicy]] = None) -> None:
        self.policies = policies or self.DEFAULT_POLICIES.copy()

    def get_policy(self, role: str) -> RolePolicy:
        """Получить политику роли."""
        return self.policies.get(role, RolePolicy(name=role))

    def can(self, role: str, action: str) -> bool:
        """Проверить, может ли роль выполнить действие."""
        policy = self.get_policy(role)
        action_map = {
            "write_adr": policy.can_write_adr,
            "write_code": policy.can_write_code,
            "deploy": policy.can_deploy,
            "review": policy.can_review,
            "run_tests": policy.can_run_tests,
            "run_linters": policy.can_run_linters,
            "access_dangerous": policy.can_access_dangerous,
        }
        return action_map.get(action, False)

    def check_path(self, role: str, path: str) -> tuple[bool, Optional[str]]:
        """Проверить доступ к пути."""
        policy = self.get_policy(role)

        # Forbidden paths
        for fp in policy.forbidden_paths:
            if path.startswith(fp) or fp == "*":
                return False, f"Path '{path}' is forbidden for role '{role}'"

        # Allowed paths
        if "*" in policy.allowed_paths:
            return True, None
        for ap in policy.allowed_paths:
            if path.startswith(ap):
                return True, None

        return False, f"Path '{path}' not allowed for role '{role}'"
