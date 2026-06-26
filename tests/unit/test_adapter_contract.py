"""Tests for Phase 7 adapter contract models."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from voyage_framework.core.adapter_contract import (
    AdapterContract,
    AgentRequest,
    AgentResponse,
    ApprovalFlow,
    ValidationResult,
    default_adapter_contract,
)
from voyage_framework.core.agent_registry import default_agent_registry
from voyage_framework.core.prompt_generator import PromptPackage
from voyage_framework.core.prompt_modes import default_mode_registry


def request(**changes: object) -> AgentRequest:
    values = {
        "request_id": "r1",
        "agent_id": "a1",
        "role_id": "developer",
        "mode_id": "implementation",
        "task_hint": None,
        "project_context": None,
    }
    values.update(changes)
    return AgentRequest.model_validate(values)


def package() -> PromptPackage:
    return PromptPackage(
        role_id="developer",
        mode_id="implementation",
        task_id="VF-7",
        title="Contract",
        system_prompt="System",
        user_prompt="User",
    )


def test_default_contract_valid():
    assert isinstance(default_adapter_contract(), AdapterContract)


def test_all_roles():
    assert default_adapter_contract().supported_roles == tuple(
        default_agent_registry().list_roles()
    )


def test_twenty_roles():
    assert len(default_adapter_contract().supported_roles) == 20


def test_all_modes():
    assert default_adapter_contract().supported_modes == default_mode_registry().list_modes()


def test_six_modes():
    assert len(default_adapter_contract().supported_modes) == 6


def test_approvals():
    assert default_adapter_contract().approval_required_for == (
        "mutate_task",
        "delete_task",
        "change_status",
        "deploy",
    )


def test_request_requires_fields():
    with pytest.raises(ValidationError):
        AgentRequest.model_validate({})


def test_unknown_role():
    with pytest.raises(ValidationError, match="Unknown role"):
        request(role_id="unknown")


def test_unknown_mode():
    with pytest.raises(ValidationError, match="Unknown mode"):
        request(mode_id="unknown")


def test_known_role_mode():
    assert request().role_id == "developer"


@pytest.mark.parametrize("status", ["pending", "approved", "rejected", "completed"])
def test_response_statuses(status: str):
    assert AgentResponse.model_validate({"request_id": "r1", "status": status}).status == status


def test_bad_response_status():
    with pytest.raises(ValidationError):
        AgentResponse.model_validate({"request_id": "r1", "status": "running"})


def test_response_prompt():
    assert (
        AgentResponse(request_id="r1", status="completed", prompt_package=package()).prompt_package
        == package()
    )


def test_valid_result():
    assert ValidationResult(valid=True).errors == ()


def test_invalid_result():
    assert ValidationResult(valid=False, errors=("bad",)).valid is False


def test_valid_result_cannot_have_errors():
    with pytest.raises(ValidationError):
        ValidationResult(valid=True, errors=("bad",))


def test_invalid_result_needs_errors():
    with pytest.raises(ValidationError):
        ValidationResult(valid=False)


def test_approval_human_gate():
    assert ApprovalFlow(action="deploy", required=True, reason="Human", timeout_hours=24).required


def test_timeout_positive():
    with pytest.raises(ValidationError):
        ApprovalFlow(action="deploy", required=True, timeout_hours=0)


def test_version():
    assert default_adapter_contract().version == "v4.1.0"


def test_task_limit():
    assert default_adapter_contract().max_task_length == 10_000


def test_prompt_limit():
    assert default_adapter_contract().max_prompt_length == 15_000


def test_json_serializable():
    assert json.loads(default_adapter_contract().model_dump_json())["version"] == "v4.1.0"


def test_models_frozen():
    contract = default_adapter_contract()
    with pytest.raises(ValidationError):
        contract.version = "changed"


def test_no_filesystem_pollution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.iterdir())
    default_adapter_contract()
    assert list(tmp_path.iterdir()) == before
    assert not (tmp_path / ".voyage").exists()
