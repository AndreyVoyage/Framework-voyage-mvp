"""Task Parser — чтение task.yaml и валидация через TaskYamlSpec.

Интерфейс:
    TaskParser.parse(path) → TaskYamlSpec
    TaskParser.parse_string(content) → TaskYamlSpec

Валидирует:
- Обязательные поля (id, title, description, role, acceptance_criteria)
- role через PolicyEnforcer
- status == "pending" для новых задач
- priority, mode по списку допустимых значений

Не делает:
- Не пишет в SQLite
- Не генерирует TASK.md
- Не создаёт TaskRecord
- Не меняет CLI
"""

from __future__ import annotations

from pathlib import Path

import yaml

from voyage_framework.core.task_models import TaskYamlSpec
from voyage_framework.security.policy import PolicyEnforcer


class TaskValidationError(ValueError):
    """Ошибка валидации task.yaml."""

    pass


class RoleValidationError(TaskValidationError):
    """Ошибка валидации роли (role не существует в PolicyEnforcer)."""

    pass


class TaskParser:
    """Парсер task.yaml → TaskYamlSpec."""

    def __init__(self, policy_enforcer: PolicyEnforcer | None = None) -> None:
        self.policy = policy_enforcer or PolicyEnforcer()

    def parse(self, path: Path | str) -> TaskYamlSpec:
        """Прочитать и валидировать task.yaml из файла.

        Args:
            path: Путь к task.yaml

        Returns:
            TaskYamlSpec — валидированная спецификация задачи

        Raises:
            TaskValidationError: если YAML невалиден или обязательные поля отсутствуют.
            RoleValidationError: если роль не существует в PolicyEnforcer.
            FileNotFoundError: если файл не существует.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"task.yaml not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_string(content, source_path=str(path))

    def parse_string(
        self,
        yaml_content: str,
        source_path: str | None = None,
    ) -> TaskYamlSpec:
        """Парсить task.yaml из строки (полезно для тестов).

        Args:
            yaml_content: Содержимое YAML-файла.
            source_path: Опциональный путь к источнику (для ошибок).

        Returns:
            TaskYamlSpec — валидированная спецификация задачи.

        Raises:
            TaskValidationError: если YAML невалиден или обязательные поля отсутствуют.
            RoleValidationError: если роль не существует в PolicyEnforcer.
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise TaskValidationError(f"Invalid YAML syntax: {e}") from e

        if not isinstance(data, dict):
            raise TaskValidationError(
                "task.yaml must be a YAML mapping (dict), not a list or scalar"
            )

        # Проверить обязательные поля на уровне dict (до Pydantic)
        required_fields = {"id", "title", "description", "role", "acceptance_criteria"}
        missing = required_fields - set(data.keys())
        if missing:
            raise TaskValidationError(f"Missing required fields: {sorted(missing)}")

        # Проверить, что acceptance_criteria не пустой
        criteria = data.get("acceptance_criteria", [])
        if not criteria or not isinstance(criteria, list) or not all(criteria):
            raise TaskValidationError(
                "acceptance_criteria must be a non-empty list of non-empty strings"
            )

        # Проверить, что status в допустимых значениях, затем что == "pending" для новых задач
        status = data.get("status", "pending")
        allowed_statuses = {"pending", "in_progress", "blocked", "completed", "failed", "archived"}
        if status not in allowed_statuses:
            raise TaskValidationError(f"status must be one of {allowed_statuses}, got '{status}'")
        if status != "pending":
            raise TaskValidationError(
                f"New tasks must have status='pending', got '{status}'. "
                f"Use TaskEngine to change status after creation."
            )

        # Проверить role через PolicyEnforcer
        role = data.get("role", "").strip()
        if not role:
            raise TaskValidationError("role must not be empty")
        if role not in self.policy.policies:
            available = sorted(self.policy.policies.keys())
            raise RoleValidationError(f"Role '{role}' is not defined. Available roles: {available}")

        # Добавить source_path в metadata для трассировки
        if source_path:
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["source_path"] = source_path
            data["metadata"] = metadata

        # Валидация через Pydantic TaskYamlSpec
        try:
            return TaskYamlSpec(**data)
        except ValueError as e:
            raise TaskValidationError(f"TaskYamlSpec validation failed: {e}") from e
