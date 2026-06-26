"""Тесты deterministic read-only PromptGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from voyage_framework.core.prompt_generator import (
    PromptGenerationError,
    PromptGenerator,
    PromptPackage,
    default_prompt_generator,
)
from voyage_framework.core.prompt_modes import PromptModeNotFoundError
from voyage_framework.core.task_models import TaskFiles, TaskYamlSpec


@pytest.fixture
def task() -> TaskYamlSpec:
    return TaskYamlSpec(
        id="VF-600",
        title="Generate external prompt",
        description="Prepare a deterministic package for an external AI tool.",
        role="developer",
        acceptance_criteria=["Package is deterministic", "No filesystem writes"],
        files=TaskFiles(read=["README.md"], modify=["src/example.py"]),
        tests=["pytest tests/unit/test_example.py"],
        metadata={"owner": "voyage"},
    )


def test_default_prompt_generator_can_be_constructed() -> None:
    assert isinstance(default_prompt_generator(), PromptGenerator)


def test_generator_validates_role_id(task: TaskYamlSpec) -> None:
    with pytest.raises(PromptGenerationError, match="Unknown role: unknown"):
        default_prompt_generator().generate(task=task, role_id="unknown", mode_id="analysis")


def test_generator_validates_mode_id(task: TaskYamlSpec) -> None:
    with pytest.raises(PromptModeNotFoundError, match="Unknown prompt mode: unknown"):
        default_prompt_generator().generate(task=task, role_id="developer", mode_id="unknown")


def test_generator_returns_prompt_package(task: TaskYamlSpec) -> None:
    package = default_prompt_generator().generate(
        task=task, role_id="developer", mode_id="implementation"
    )
    assert isinstance(package, PromptPackage)


def test_prompt_package_is_json_serializable(task: TaskYamlSpec) -> None:
    package = default_prompt_generator().generate(task=task, role_id="developer", mode_id="qa")
    assert json.loads(package.model_dump_json())["task_id"] == "VF-600"


def test_prompt_package_is_frozen(task: TaskYamlSpec) -> None:
    package = default_prompt_generator().generate(task=task, role_id="developer", mode_id="qa")
    with pytest.raises(ValidationError):
        package.title = "Changed"


def test_as_messages_returns_system_and_user(task: TaskYamlSpec) -> None:
    package = default_prompt_generator().generate(
        task=task, role_id="developer", mode_id="analysis"
    )
    assert package.as_messages() == [
        {"role": "system", "content": package.system_prompt},
        {"role": "user", "content": package.user_prompt},
    ]


def test_prompt_includes_task_identity_and_description(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="analysis")
        .user_prompt
    )
    assert "VF-600" in prompt
    assert "Generate external prompt" in prompt
    assert task.description in prompt


def test_prompt_includes_acceptance_criteria(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="analysis")
        .user_prompt
    )
    assert all(criterion in prompt for criterion in task.acceptance_criteria)


def test_prompt_includes_files_and_tests(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="implementation")
        .user_prompt
    )
    assert "README.md" in prompt
    assert "src/example.py" in prompt
    assert "pytest tests/unit/test_example.py" in prompt


def test_prompt_includes_role_boundaries(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="implementation")
        .system_prompt
    )
    assert "Role boundaries" in prompt
    assert "no_broad_rewrites" in prompt


def test_prompt_includes_mode_constraints(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="review")
        .system_prompt
    )
    assert "Mode constraints" in prompt
    assert "Remain read-only by default" in prompt


def test_prompt_includes_global_constraints(task: TaskYamlSpec) -> None:
    prompt = (
        default_prompt_generator()
        .generate(task=task, role_id="developer", mode_id="analysis")
        .system_prompt
    )
    assert "Do not commit / do not push unless instructed" in prompt
    assert "Do not modify files outside task scope" in prompt
    assert "Report deviations instead of guessing" in prompt


def test_same_input_produces_same_output(task: TaskYamlSpec) -> None:
    generator = default_prompt_generator()
    kwargs = {"task": task, "role_id": "developer", "mode_id": "qa"}
    assert generator.generate(**kwargs) == generator.generate(**kwargs)


def test_context_is_sorted_and_copied(task: TaskYamlSpec) -> None:
    context = {"z": 1, "a": {"value": 2}}
    package = default_prompt_generator().generate(
        task=task, role_id="developer", mode_id="analysis", project_context=context
    )
    context["a"]["value"] = 99
    assert package.metadata["project_context"]["a"]["value"] == 2
    assert package.user_prompt.index('"a"') < package.user_prompt.index('"z"')


def test_non_json_context_raises_domain_error(task: TaskYamlSpec) -> None:
    with pytest.raises(PromptGenerationError, match="JSON-serializable"):
        default_prompt_generator().generate(
            task=task,
            role_id="developer",
            mode_id="analysis",
            project_context={"bad": object()},
        )


def test_generator_does_not_mutate_task(task: TaskYamlSpec) -> None:
    before = task.model_dump()
    default_prompt_generator().generate(task=task, role_id="developer", mode_id="analysis")
    assert task.model_dump() == before


def test_generator_does_not_touch_filesystem_or_create_voyage(
    task: TaskYamlSpec, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = Path.cwd()
    before_entries = {path.name for path in root.iterdir()}
    voyage_existed = (root / ".voyage").exists()

    def fail_io(*args: object, **kwargs: object) -> None:
        raise AssertionError("PromptGenerator attempted filesystem IO")

    monkeypatch.setattr("builtins.open", fail_io)
    monkeypatch.setattr(Path, "open", fail_io)
    monkeypatch.setattr(Path, "mkdir", fail_io)
    default_prompt_generator().generate(task=task, role_id="developer", mode_id="analysis")
    assert {path.name for path in root.iterdir()} == before_entries
    assert (root / ".voyage").exists() is voyage_existed


def test_prompt_generator_accepts_methodology_role() -> None:
    methodology_task = TaskYamlSpec(
        id="VF-700",
        title="Conduct requirements interview",
        description="Elicit project requirements from stakeholders.",
        role="interviewer",
        acceptance_criteria=["01-discovery.json produced"],
    )
    package = default_prompt_generator().generate(
        task=methodology_task, role_id="interviewer", mode_id="analysis"
    )
    assert "Interviewer" in package.system_prompt
    assert "no_design_decisions" in package.system_prompt
    assert package.task_id == "VF-700"
