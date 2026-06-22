"""Abstract, side-effect-free interface for external Voyage adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from .adapter_contract import AgentRequest, AgentResponse, ValidationResult
from .prompt_generator import PromptPackage


class AdapterProtocol(ABC):
    """Abstract contract for external adapters.

    This protocol defines method signatures only. It does not implement
    task creation, execution, orchestration, model calls, persistence,
    TaskEngine mutations, or EventEngine writes.
    """

    @abstractmethod
    def validate_request(self, request: AgentRequest) -> ValidationResult: ...
    @abstractmethod
    def create_task(self, request: AgentRequest) -> AgentResponse: ...
    @abstractmethod
    def get_context(self, task_id: str) -> Mapping[str, Any]: ...
    @abstractmethod
    def request_prompt(self, task_id: str, role_id: str, mode_id: str) -> PromptPackage: ...
    @abstractmethod
    def submit_result(self, task_id: str, result: Mapping[str, Any]) -> AgentResponse: ...
    @abstractmethod
    def request_approval(self, task_id: str, action: str) -> AgentResponse: ...
