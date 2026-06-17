"""Pydantic state schema для LangGraph runtime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from voyage_framework.core.models import ToolResult


class VoyageState(BaseModel):
    """Состояние графового workflow агента."""

    role: str = ""
    task: str = ""
    plan: list[str] = Field(default_factory=list)
    current_step: int = 0
    retry_count: int = 0
    max_retries: int = 3
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    results: list[ToolResult] = Field(default_factory=list)
    evaluation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_context: str = ""
    should_retry: bool = False
    status: str = "idle"
    project_id: str = "default"
    correlation_id: str | None = None
    agent_id: str | None = None
    error: str | None = None
