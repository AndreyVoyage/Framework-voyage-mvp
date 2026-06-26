"""Read-only каталог профилей ролей Voyage Framework."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_ID_PATTERN = r"^[a-z][a-z0-9_]*$"


class RoleCapability(BaseModel):
    """Возможность, которой обладает роль."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, pattern=_ID_PATTERN)
    description: str = Field(min_length=1)


class RoleBoundary(BaseModel):
    """Ограничение, которое роль обязана соблюдать."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, pattern=_ID_PATTERN)
    description: str = Field(min_length=1)


class RoleProfile(BaseModel):
    """Неизменяемое описание роли и ожидаемого от неё поведения."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: str = Field(min_length=1, pattern=_ID_PATTERN)
    display_name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    responsibilities: tuple[str, ...] = ()
    capabilities: tuple[RoleCapability, ...] = ()
    boundaries: tuple[RoleBoundary, ...] = ()
    prompt_hints: tuple[str, ...] = ()
    output_expectations: tuple[str, ...] = ()


class AgentRegistry:
    """Read-only registry профилей ролей без выполнения агентов."""

    def __init__(self, profiles: list[RoleProfile] | None = None) -> None:
        ordered_profiles = tuple(profiles or ())
        profiles_by_id: dict[str, RoleProfile] = {}
        for profile in ordered_profiles:
            if profile.role_id in profiles_by_id:
                raise ValueError(f"Duplicate role id: {profile.role_id}")
            profiles_by_id[profile.role_id] = profile
        self._profiles = ordered_profiles
        self._profiles_by_id = profiles_by_id

    def list_roles(self) -> list[str]:
        """Вернуть идентификаторы ролей в стабильном порядке регистрации."""
        return [profile.role_id for profile in self._profiles]

    def list_profiles(self) -> list[RoleProfile]:
        """Вернуть новый список неизменяемых профилей."""
        return list(self._profiles)

    def get(self, role_id: str) -> RoleProfile | None:
        """Вернуть профиль роли или ``None``, если роль неизвестна."""
        return self._profiles_by_id.get(role_id)

    def require(self, role_id: str) -> RoleProfile:
        """Вернуть профиль роли или выбросить понятную ошибку."""
        profile = self.get(role_id)
        if profile is None:
            raise KeyError(f"Unknown role: {role_id}")
        return profile

    def has_role(self, role_id: str) -> bool:
        """Проверить наличие роли в registry."""
        return role_id in self._profiles_by_id

    def describe(self, role_id: str) -> dict[str, Any]:
        """Вернуть JSON-совместимое описание известной роли."""
        return self.require(role_id).model_dump(mode="json")


def default_agent_registry() -> AgentRegistry:
    """Create the default registry with all registered Voyage role profiles."""
    from voyage_framework.core.default_roles import all_profiles

    return AgentRegistry(all_profiles())
