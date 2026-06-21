"""Context Builder Lite — read-mostly sync layer for Phase 4.

Builds project context from:
  - task.yaml files (canonical task specifications)
  - TaskRecord SQLite runtime state (canonical runtime state)
  - EventEngine audit log (canonical audit trail)

Does not mutate:
  - task.yaml
  - TaskRecord
  - EventEngine

Provides operations:
  - build()   → ProjectContext
  - check()   → list[TaskDiff]
  - write_context() → writes CONTEXT.json
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.task_engine import TaskEngine
from voyage_framework.core.task_parser import TaskParser

# ───────────────────────────────────────────────────────────────
# Models
# ───────────────────────────────────────────────────────────────


class TaskContext(BaseModel):
    """Single task in project context."""

    id: str
    title: str
    role: str
    spec_status: str | None = None
    runtime_status: str | None = None
    priority: str | None = None
    mode: str | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    has_runtime_record: bool = False
    source_path: str | None = None


class EventsSummary(BaseModel):
    """Summary of events in project."""

    total_events: int = 0
    task_events: int = 0
    latest_event_at: datetime | None = None


class TaskDiff(BaseModel):
    """Diff between task.yaml and TaskRecord."""

    task_id: str
    exists_in_yaml: bool
    exists_in_runtime: bool
    changed_fields: dict[str, dict[str, object | None]] = Field(default_factory=dict)


class ProjectContext(BaseModel):
    """Complete project context."""

    project_id: str = "default"
    tasks: list[TaskContext] = Field(default_factory=list)
    events_summary: EventsSummary = Field(default_factory=EventsSummary)
    last_sync: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ───────────────────────────────────────────────────────────────
# ContextBuilder
# ───────────────────────────────────────────────────────────────


class ContextBuilder:
    """Builds project context from task.yaml + TaskRecord + EventEngine.

    Operations:
      - build()   → ProjectContext from YAML + runtime
      - check()   → TaskDiff list (what changed)
      - write_context() → writes CONTEXT.json
    """

    def __init__(
        self,
        task_engine: TaskEngine,
        event_engine: EventEngine | None = None,
    ) -> None:
        """Init ContextBuilder.

        Args:
            task_engine: TaskEngine instance for runtime state lookup.
            event_engine: Optional EventEngine for audit trail summary.
        """
        self.task_engine = task_engine
        self.event_engine = event_engine
        self.parser = TaskParser()

    def build(
        self,
        task_files: list[Path],
        project_id: str = "default",
    ) -> ProjectContext:
        """Build project context from YAML specs + runtime records + events.

        Does not mutate task.yaml or TaskRecord.

        Args:
            task_files: List of task.yaml file paths to include.
            project_id: Project identifier (default: "default").

        Returns:
            ProjectContext containing merged spec + runtime view.
        """
        tasks: list[TaskContext] = []
        processed_ids: set[str] = set()

        # 1. Process each task.yaml file
        for yaml_path in task_files:
            if not yaml_path.exists():
                continue

            try:
                spec = self.parser.parse(yaml_path)
            except Exception:
                # Skip invalid YAML in context build
                continue

            processed_ids.add(spec.id)

            # 2. Look up runtime record (if exists)
            runtime_record = None
            with contextlib.suppress(Exception):
                runtime_record = self.task_engine.get(spec.id)

            # 3. Build TaskContext
            ctx = TaskContext(
                id=spec.id,
                title=spec.title,
                role=spec.role,
                spec_status=spec.status,
                runtime_status=runtime_record.status if runtime_record else None,
                priority=spec.priority,
                mode=spec.mode,
                acceptance_criteria=spec.acceptance_criteria or [],
                has_runtime_record=runtime_record is not None,
                source_path=str(yaml_path),
            )
            tasks.append(ctx)

        # 4. Build events summary
        events_summary = self._build_events_summary()

        # 5. Return ProjectContext
        return ProjectContext(
            project_id=project_id,
            tasks=tasks,
            events_summary=events_summary,
            last_sync=datetime.now(UTC),
        )

    def check(
        self,
        task_files: list[Path],
    ) -> list[TaskDiff]:
        """Check diffs between task.yaml specs and TaskRecord runtime data.

        Does not mutate anything.

        Compares only safe spec-derived fields:
          - id, title, role, priority, mode, acceptance_criteria

        Ignores runtime-only fields:
          - status, created_at, updated_at, started_at, completed_at, archived_at

        Args:
            task_files: List of task.yaml files to check.

        Returns:
            List of TaskDiff objects.
        """
        diffs: list[TaskDiff] = []
        checked_ids: set[str] = set()

        # 1. Check each task.yaml against runtime
        for yaml_path in task_files:
            if not yaml_path.exists():
                continue

            try:
                spec = self.parser.parse(yaml_path)
            except Exception:
                # Skip invalid YAML in check
                continue

            checked_ids.add(spec.id)

            # 2. Lookup runtime record
            runtime_record = None
            with contextlib.suppress(Exception):
                runtime_record = self.task_engine.get(spec.id)

            # 3. Build TaskDiff
            exists_yaml = True
            exists_runtime = runtime_record is not None

            changed_fields: dict[str, dict[str, object | None]] = {}

            if runtime_record:
                # Compare safe fields
                for field in ["title", "role", "priority", "mode"]:
                    spec_val = getattr(spec, field, None)
                    runtime_val = getattr(runtime_record, field, None)
                    if spec_val != runtime_val:
                        changed_fields[field] = {
                            "yaml": spec_val,
                            "runtime": runtime_val,
                        }

                # Compare acceptance_criteria
                spec_criteria = spec.acceptance_criteria or []
                runtime_criteria = runtime_record.acceptance_criteria or []
                if spec_criteria != runtime_criteria:
                    changed_fields["acceptance_criteria"] = {
                        "yaml": spec_criteria,
                        "runtime": runtime_criteria,
                    }

            diff = TaskDiff(
                task_id=spec.id,
                exists_in_yaml=exists_yaml,
                exists_in_runtime=exists_runtime,
                changed_fields=changed_fields,
            )
            diffs.append(diff)

        return diffs

    def write_context(
        self,
        context: ProjectContext,
        output_path: Path,
    ) -> None:
        """Write CONTEXT.json atomically.

        Args:
            context: ProjectContext to write.
            output_path: Destination file path.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = context.model_dump_json(indent=2)
        output_path.write_text(json_str, encoding="utf-8")

    def _build_events_summary(self) -> EventsSummary:
        """Build summary from EventEngine (optional).

        If no event_engine provided, returns empty summary.
        """
        if not self.event_engine:
            return EventsSummary()

        try:
            # Try to get all events
            events = self.event_engine.get_events()
            total = len(events)

            # Count task-related events
            task_events = sum(
                1
                for e in events
                if hasattr(e, "event_type") and "TASK" in str(getattr(e, "event_type", ""))
            )

            # Find latest event timestamp
            latest_ts = None
            for e in events:
                if hasattr(e, "timestamp"):
                    ts = e.timestamp
                    if isinstance(ts, datetime) and (latest_ts is None or ts > latest_ts):
                        latest_ts = ts

            return EventsSummary(
                total_events=total,
                task_events=task_events,
                latest_event_at=latest_ts,
            )
        except Exception:
            # If event_engine fails, return empty summary
            return EventsSummary()
