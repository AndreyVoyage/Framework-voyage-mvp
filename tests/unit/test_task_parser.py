"""Тесты TaskParser и TaskYamlSpec (Phase 1).

Покрывают:
- Чтение валидного task.yaml (минимальный и полный)
- Парсинг из строки
- Валидация обязательных полей
- Валидация роли через PolicyEnforcer
- Валидация статуса (только pending для новых задач)
- Валидация priority и mode
- Пустые acceptance_criteria
- Значения по умолчанию
- Обработка ошибок (нет файла, невалидный YAML)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from voyage_framework.core.task_models import TaskFiles, TaskYamlSpec
from voyage_framework.core.task_parser import (
    RoleValidationError,
    TaskParser,
    TaskValidationError,
)

# ───────────────────────────────────────────────────────────────
# Fixtures
# ───────────────────────────────────────────────────────────────


@pytest.fixture
def parser() -> TaskParser:
    """TaskParser с default PolicyEnforcer."""
    return TaskParser()


@pytest.fixture
def minimal_yaml() -> str:
    """Минимальный валидный task.yaml."""
    return """\
id: VF-001
title: Test Task
description: A simple test task.
role: developer
acceptance_criteria:
  - Test passes
"""


@pytest.fixture
def full_yaml() -> str:
    """Полный валидный task.yaml со всеми опциональными полями."""
    return """\
id: VF-002
title: Implement Task Engine
description: >
  Create a runtime lifecycle management system for Voyage tasks
  with SQLite persistence and event logging.
role: architect
mode: solution
priority: high
status: pending
acceptance_criteria:
  - Task can be parsed from task.yaml
  - Task can be created as TaskRecord in SQLite
  - Status transitions follow the contract
files:
  read:
    - voyage_framework/cli.py
    - voyage_framework/core/models.py
  modify:
    - voyage_framework/core/task_engine.py
    - tests/test_task_engine.py
tests:
  - pytest tests/test_task_parser.py -v
  - pytest tests/test_task_engine.py -v
metadata:
  sprint: 2
  estimated_hours: 4
"""


# ───────────────────────────────────────────────────────────────
# Success cases
# ───────────────────────────────────────────────────────────────


class TestParseValidMinimal:
    """Тесты парсинга минимального валидного task.yaml."""

    def test_parse_minimal_from_string(self, parser: TaskParser, minimal_yaml: str) -> None:
        spec = parser.parse_string(minimal_yaml)
        assert spec.id == "VF-001"
        assert spec.title == "Test Task"
        assert spec.description == "A simple test task."
        assert spec.role == "developer"
        assert spec.status == "pending"
        assert spec.acceptance_criteria == ["Test passes"]

    def test_parse_minimal_from_file(self, parser: TaskParser, minimal_yaml: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "task.yaml"
            path.write_text(minimal_yaml, encoding="utf-8")
            spec = parser.parse(path)
            assert spec.id == "VF-001"
            assert spec.title == "Test Task"

    def test_minimal_defaults(self, parser: TaskParser, minimal_yaml: str) -> None:
        spec = parser.parse_string(minimal_yaml)
        assert spec.mode == "solution"
        assert spec.priority == "medium"
        assert spec.metadata == {}
        assert spec.files is None
        assert spec.tests is None


class TestParseValidFull:
    """Тесты парсинга полного task.yaml со всеми полями."""

    def test_parse_full_from_string(self, parser: TaskParser, full_yaml: str) -> None:
        spec = parser.parse_string(full_yaml)
        assert spec.id == "VF-002"
        assert spec.title == "Implement Task Engine"
        assert spec.role == "architect"
        assert spec.mode == "solution"
        assert spec.priority == "high"
        assert spec.status == "pending"
        assert len(spec.acceptance_criteria) == 3

    def test_full_files_parsed(self, parser: TaskParser, full_yaml: str) -> None:
        spec = parser.parse_string(full_yaml)
        assert spec.files is not None
        assert isinstance(spec.files, TaskFiles)
        assert spec.files.read == [
            "voyage_framework/cli.py",
            "voyage_framework/core/models.py",
        ]
        assert spec.files.modify == [
            "voyage_framework/core/task_engine.py",
            "tests/test_task_engine.py",
        ]

    def test_full_tests_parsed(self, parser: TaskParser, full_yaml: str) -> None:
        spec = parser.parse_string(full_yaml)
        assert spec.tests is not None
        assert len(spec.tests) == 2
        assert "pytest tests/test_task_parser.py -v" in spec.tests

    def test_full_metadata_parsed(self, parser: TaskParser, full_yaml: str) -> None:
        spec = parser.parse_string(full_yaml)
        assert spec.metadata == {"sprint": 2, "estimated_hours": 4}

    def test_source_path_in_metadata(self, parser: TaskParser, full_yaml: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "task.yaml"
            path.write_text(full_yaml, encoding="utf-8")
            spec = parser.parse(path)
            assert spec.metadata.get("source_path") == str(path)


class TestParseDifferentRoles:
    """Тесты валидации разных ролей."""

    def test_role_architect(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-003
title: Architecture decision
description: Choose database
role: architect
acceptance_criteria:
  - ADR written
"""
        spec = parser.parse_string(yaml_content)
        assert spec.role == "architect"

    def test_role_devops(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-004
title: Deploy SSL
description: Setup certbot
role: devops
acceptance_criteria:
  - HTTPS works
"""
        spec = parser.parse_string(yaml_content)
        assert spec.role == "devops"

    def test_role_reviewer(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-005
title: Code review
description: Review PR
role: reviewer
acceptance_criteria:
  - Comments added
"""
        spec = parser.parse_string(yaml_content)
        assert spec.role == "reviewer"

    def test_role_security(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-006
title: Security audit
description: Check auth
role: security
acceptance_criteria:
  - No vulnerabilities
"""
        spec = parser.parse_string(yaml_content)
        assert spec.role == "security"

    def test_role_qa(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-007
title: Test coverage
description: Add tests
role: qa
acceptance_criteria:
  - Coverage > 80%
"""
        spec = parser.parse_string(yaml_content)
        assert spec.role == "qa"


# ───────────────────────────────────────────────────────────────
# Failure cases — missing required fields
# ───────────────────────────────────────────────────────────────


class TestMissingRequiredFields:
    """Тесты отсутствия обязательных полей."""

    def test_missing_id(self, parser: TaskParser) -> None:
        yaml_content = """\
title: No ID
description: Missing id field
role: developer
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="Missing required fields"):
            parser.parse_string(yaml_content)

    def test_missing_title(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-008
description: Missing title
role: developer
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="Missing required fields"):
            parser.parse_string(yaml_content)

    def test_missing_description(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-009
title: No description
role: developer
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="Missing required fields"):
            parser.parse_string(yaml_content)

    def test_missing_role(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-010
title: No role
description: Missing role field
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="Missing required fields"):
            parser.parse_string(yaml_content)

    def test_missing_acceptance_criteria(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-011
title: No criteria
description: Missing acceptance_criteria
role: developer
"""
        with pytest.raises(TaskValidationError, match="Missing required fields"):
            parser.parse_string(yaml_content)


class TestEmptyAcceptanceCriteria:
    """Тесты пустых acceptance_criteria."""

    def test_empty_list(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-012
title: Empty criteria list
description: Criteria is empty list
role: developer
acceptance_criteria: []
"""
        with pytest.raises(
            TaskValidationError,
            match="acceptance_criteria must be a non-empty list",
        ):
            parser.parse_string(yaml_content)

    def test_list_with_empty_string(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-013
title: Empty string in criteria
description: One item is empty
role: developer
acceptance_criteria:
  - ""
"""
        with pytest.raises(
            TaskValidationError,
            match="acceptance_criteria must be a non-empty list",
        ):
            parser.parse_string(yaml_content)


# ───────────────────────────────────────────────────────────────
# Failure cases — invalid role
# ───────────────────────────────────────────────────────────────


class TestInvalidRole:
    """Тесты невалидной роли."""

    def test_unknown_role(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-014
title: Unknown role
description: Role does not exist
role: designer
acceptance_criteria:
  - Fail
"""
        with pytest.raises(RoleValidationError, match="Role 'designer' is not defined"):
            parser.parse_string(yaml_content)

    def test_empty_role(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-015
title: Empty role
description: Role is empty string
role: ""
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="role must not be empty"):
            parser.parse_string(yaml_content)

    def test_whitespace_role(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-016
title: Whitespace role
description: Role is whitespace
role: "   "
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="role must not be empty"):
            parser.parse_string(yaml_content)

    def test_available_roles_in_error(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-017
title: Bad role
description: Check error message
role: wizard
acceptance_criteria:
  - Fail
"""
        with pytest.raises(RoleValidationError) as exc_info:
            parser.parse_string(yaml_content)
        error_msg = str(exc_info.value)
        assert "architect" in error_msg
        assert "developer" in error_msg
        assert "devops" in error_msg


# ───────────────────────────────────────────────────────────────
# Failure cases — invalid status
# ───────────────────────────────────────────────────────────────


class TestInvalidStatus:
    """Тесты невалидного статуса для новых задач."""

    def test_in_progress_status(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-018
title: Already in progress
description: Status is in_progress
role: developer
status: in_progress
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="New tasks must have status='pending'"):
            parser.parse_string(yaml_content)

    def test_completed_status(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-019
title: Already completed
description: Status is completed
role: developer
status: completed
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="New tasks must have status='pending'"):
            parser.parse_string(yaml_content)

    def test_blocked_status(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-020
title: Already blocked
description: Status is blocked
role: developer
status: blocked
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="New tasks must have status='pending'"):
            parser.parse_string(yaml_content)

    def test_invalid_status_string(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-021
title: Invalid status
description: Status is 'done'
role: developer
status: done
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="status must be one of"):
            parser.parse_string(yaml_content)


# ───────────────────────────────────────────────────────────────
# Failure cases — invalid priority/mode
# ───────────────────────────────────────────────────────────────


class TestInvalidPriorityMode:
    """Тесты невалидных priority и mode."""

    def test_invalid_priority(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-022
title: Bad priority
description: Invalid priority value
role: developer
priority: critical
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="priority must be one of"):
            parser.parse_string(yaml_content)

    def test_invalid_mode(self, parser: TaskParser) -> None:
        yaml_content = """\
id: VF-023
title: Bad mode
description: Invalid mode value
role: developer
mode: coding
acceptance_criteria:
  - Fail
"""
        with pytest.raises(TaskValidationError, match="mode must be one of"):
            parser.parse_string(yaml_content)


# ───────────────────────────────────────────────────────────────
# Failure cases — file/YAML errors
# ───────────────────────────────────────────────────────────────


class TestFileAndYamlErrors:
    """Тесты ошибок файловой системы и YAML."""

    def test_missing_file(self, parser: TaskParser) -> None:
        with pytest.raises(FileNotFoundError, match="task.yaml not found"):
            parser.parse("/nonexistent/path/task.yaml")

    def test_invalid_yaml_syntax(self, parser: TaskParser) -> None:
        yaml_content = "id: [unclosed bracket"
        with pytest.raises(TaskValidationError, match="Invalid YAML syntax"):
            parser.parse_string(yaml_content)

    def test_yaml_list_instead_of_dict(self, parser: TaskParser) -> None:
        yaml_content = "- item1\n- item2\n"
        with pytest.raises(TaskValidationError, match="task.yaml must be a YAML mapping"):
            parser.parse_string(yaml_content)

    def test_yaml_scalar_instead_of_dict(self, parser: TaskParser) -> None:
        yaml_content = "just a string\n"
        with pytest.raises(TaskValidationError, match="task.yaml must be a YAML mapping"):
            parser.parse_string(yaml_content)


# ───────────────────────────────────────────────────────────────
# TaskYamlSpec model validation (direct)
# ───────────────────────────────────────────────────────────────


class TestTaskYamlSpecDirectValidation:
    """Тесты прямой валидации TaskYamlSpec (без TaskParser)."""

    def test_valid_task_spec(self) -> None:
        spec = TaskYamlSpec(
            id="VF-100",
            title="Direct spec",
            description="Created directly",
            role="developer",
            acceptance_criteria=["Works"],
        )
        assert spec.id == "VF-100"
        assert spec.mode == "solution"
        assert spec.priority == "medium"

    def test_empty_title_fails(self) -> None:
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            TaskYamlSpec(
                id="VF-101",
                title="",
                description="Empty title",
                role="developer",
                acceptance_criteria=["Fail"],
            )

    def test_empty_criteria_fails(self) -> None:
        with pytest.raises(ValueError, match="acceptance_criteria must contain at least one item"):
            TaskYamlSpec(
                id="VF-102",
                title="No criteria",
                description="Empty criteria",
                role="developer",
                acceptance_criteria=[],
            )

    def test_task_files_model(self) -> None:
        files = TaskFiles(read=["a.py"], modify=["b.py"])
        assert files.read == ["a.py"]
        assert files.modify == ["b.py"]

    def test_task_files_defaults(self) -> None:
        files = TaskFiles()
        assert files.read == []
        assert files.modify == []

    def test_task_yaml_spec_is_frozen(self) -> None:
        spec = TaskYamlSpec(
            id="VF-103",
            title="Frozen spec",
            description="Cannot be reassigned",
            role="developer",
            acceptance_criteria=["Works"],
        )
        with pytest.raises(ValidationError, match="Instance is frozen"):
            spec.title = "Changed"

    @pytest.mark.parametrize("task_id", ["VF-001", "VF-123", "ST-001", "ST-1000"])
    def test_valid_task_id_formats(self, task_id: str) -> None:
        spec = TaskYamlSpec(
            id=task_id,
            title="Valid ID",
            description="Valid task identifier",
            role="developer",
            acceptance_criteria=["Works"],
        )
        assert spec.id == task_id

    @pytest.mark.parametrize("task_id", ["BAD-001", "VF-1", "VF001", "task-001"])
    def test_invalid_task_id_format_fails(self, task_id: str) -> None:
        with pytest.raises(ValueError, match="id must match"):
            TaskYamlSpec(
                id=task_id,
                title="Invalid ID",
                description="Invalid task identifier",
                role="developer",
                acceptance_criteria=["Fails"],
            )
