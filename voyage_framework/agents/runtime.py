"""Agent Runtime — цикл работы агента.

Plan → Execute → Reflect → Retry → Done
Checkpoint после каждого node.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from voyage_framework.core.models import (
    AgentState, AgentStatus, Event, EventType, ToolResult, NodeResult,
)
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.security.policy import PolicyEnforcer


class AgentRuntime:
    """Runtime для AI-агентов.

    Управляет жизненным циклом агента: plan → execute → reflect → retry.
    Сохраняет checkpoint после каждого шага.
    """

    def __init__(
        self,
        engine: EventEngine,
        executor: SecureExecutor,
        policy: PolicyEnforcer,
    ) -> None:
        self.engine = engine
        self.executor = executor
        self.policy = policy
        self._checkpoints: dict[str, AgentState] = {}

    async def run(
        self,
        role: str,
        task: str,
        plan: list[str],
        project_id: str = "default",
        correlation_id: str | None = None,
    ) -> NodeResult:
        """Запустить агента на выполнение задачи.

        Args:
            role: Роль агента
            task: Описание задачи
            plan: Список шагов
            project_id: ID проекта
            correlation_id: ID сессии

        Returns:
            NodeResult: результат выполнения
        """
        state = AgentState(
            role=role,
            task=task,
            plan=plan,
            project_id=project_id,
            correlation_id=correlation_id,
        )

        # Логировать старт
        self.engine.append(Event(
            event_type=EventType.AGENT_STARTED,
            payload={"agent_id": state.agent_id, "role": role, "task": task},
            project_id=project_id,
            correlation_id=correlation_id,
            agent_id=state.agent_id,
            role=role,
        ))

        try:
            # PLAN
            state.status = AgentStatus.PLANNING
            self._save_checkpoint(state)

            # EXECUTE each step
            state.status = AgentStatus.EXECUTING
            for i, step in enumerate(plan):
                state.current_step = i
                result = await self._execute_step(state, step)
                state.results.append(result)

                if not result.success and not result.blocked:
                    # Ошибка — retry
                    state.status = AgentStatus.RETRYING
                    state.retry_count += 1
                    self._save_checkpoint(state)

                    if state.retry_count > state.max_retries:
                        state.status = AgentStatus.FAILED
                        return self._finalize(state, success=False)

                    # Retry текущего шага
                    result = await self._execute_step(state, step)
                    state.results.append(result)

            # REFLECT
            state.status = AgentStatus.REFLECTING
            state.confidence = self._calculate_confidence(state)
            self._save_checkpoint(state)

            # DONE
            state.status = AgentStatus.COMPLETED
            return self._finalize(state, success=True)

        except Exception as e:
            state.status = AgentStatus.FAILED
            return self._finalize(state, success=False, error=str(e))

    async def _execute_step(self, state: AgentState, step: str) -> ToolResult:
        """Выполнить один шаг плана.

        По умолчанию: запускает step как shell-команду через SecureExecutor.
        В реальности: агент интерпретирует step и выбирает tools.
        """
        # Для MVP: step = команда
        parts = step.split()
        if not parts:
            return ToolResult(success=True, stdout="Empty step")

        result = await self.executor.execute(parts)

        # Логировать
        self.engine.append(Event(
            event_type=EventType.TOOL_EXECUTED,
            payload={
                "agent_id": state.agent_id,
                "step": step,
                "success": result.success,
                "blocked": result.blocked,
            },
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        ))

        return result

    def _calculate_confidence(self, state: AgentState) -> float:
        """Рассчитать confidence score на основе результатов."""
        if not state.results:
            return 0.0

        successful = sum(1 for r in state.results if r.success)
        total = len(state.results)
        base = successful / total if total > 0 else 0.0

        # Штраф за retry
        retry_penalty = min(state.retry_count * 0.1, 0.3)

        return max(0.0, base - retry_penalty)

    def _save_checkpoint(self, state: AgentState) -> None:
        """Сохранить checkpoint состояния."""
        checkpoint_id = f"{state.agent_id}_{state.status.value}"
        state.checkpoint_id = checkpoint_id
        self._checkpoints[checkpoint_id] = state.model_copy()

    def _finalize(self, state: AgentState, success: bool, error: str | None = None) -> NodeResult:
        """Завершить выполнение и залогировать."""
        event_type = EventType.AGENT_COMPLETED if success else EventType.AGENT_FAILED
        payload: dict[str, Any] = {
            "agent_id": state.agent_id,
            "role": state.role,
            "task": state.task,
            "steps_completed": state.current_step + 1,
            "total_steps": len(state.plan),
            "retry_count": state.retry_count,
            "confidence": state.confidence,
        }
        if error:
            payload["error"] = error

        self.engine.append(Event(
            event_type=event_type,
            payload=payload,
            project_id=state.project_id,
            correlation_id=state.correlation_id,
            agent_id=state.agent_id,
            role=state.role,
        ))

        return NodeResult(
            node_name="agent_runtime",
            success=success,
            state=state,
            output=payload,
        )

    def resume_from_checkpoint(self, checkpoint_id: str) -> AgentState | None:
        """Возобновить выполнение из checkpoint."""
        return self._checkpoints.get(checkpoint_id)
