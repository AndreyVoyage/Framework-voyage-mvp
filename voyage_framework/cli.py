"""CLI для Voyage Framework.

Voyage Framework — a local Project Knowledge OS / Development Memory System
for structured development workflows, task memory, context packaging,
audit logs, and external AI tool handoff.

Команды:
    voyage tasks         — task runtime management (canonical)
    voyage sync          — context sync commands (canonical)
    voyage run <role>    — legacy agent runner (non-canonical compatibility)
    voyage graph ...     — legacy LangGraph compatibility commands
    voyage task ...      — legacy TASK.md generator (non-canonical compatibility)
    voyage init          — инициализировать проект
    voyage status        — статус проекта
    voyage events        — показать последние события
    voyage approve       — показать pending approval запросы
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

# Imported only for the legacy 'voyage run' compatibility path.
from voyage_framework.agents.runtime import AgentRuntime
from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.docs_builder import DocsBuilder
from voyage_framework.chronicler.journal import ProcessJournal
from voyage_framework.core._git_utils import collect_repo_state
from voyage_framework.core.auto_loop import (
    AutoLoopError,
    run_plan,
    run_preflight,
    run_validate,
)
from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.launcher import LauncherConfig, run_dry_run
from voyage_framework.core.models import SecurityPolicy
from voyage_framework.core.repo_control_adapter import RepoControlAdapter
from voyage_framework.core.report_validator import ReportValidatorError, validate_report
from voyage_framework.core.task_engine import (
    TaskAlreadyExistsError,
    TaskEngine,
    TaskNotFoundError,
    TaskTransitionError,
)
from voyage_framework.core.task_parser import TaskParser, TaskValidationError
from voyage_framework.security.policy import PolicyEnforcer
from voyage_framework.security.sandbox import SecureExecutor
from voyage_framework.specs.task_generator import TaskGenerator

if TYPE_CHECKING:
    from voyage_framework.core.context_builder import ContextBuilder


def _docs_engine_and_builder(
    args: argparse.Namespace,
) -> tuple[EventEngine, ProcessJournal, DecisionLog, DocsBuilder]:
    """Создать EventEngine, ProcessJournal, DecisionLog и DocsBuilder."""
    engine = EventEngine()
    journal = ProcessJournal(
        engine,
        project_id=getattr(args, "project", "default") or "default",
    )
    decision_log = DecisionLog(engine)
    builder = DocsBuilder(journal, decision_log)
    return engine, journal, decision_log, builder


def docs_build(args: argparse.Namespace) -> int:
    """Собрать всю документацию в docs/."""
    _, _, _, builder = _docs_engine_and_builder(args)
    output_dir = Path(args.output) if args.output else Path("docs")
    builder.build_all(
        project_id=getattr(args, "project", "default") or "default",
        output_dir=output_dir,
    )
    print(f"📚 Documentation built in {output_dir.absolute()}")
    return 0


def docs_tutorial(args: argparse.Namespace) -> int:
    """Сгенерировать один tutorial-файл."""
    _, _, _, builder = _docs_engine_and_builder(args)
    output_dir = Path(args.output) if args.output else Path("docs")
    path = builder.build_tutorial(args.correlation_id, output_dir=output_dir)
    print(f"📖 Tutorial saved to {path.absolute()}")
    return 0


def docs_example(args: argparse.Namespace) -> int:
    """Сгенерировать example-директорию."""
    _, _, _, builder = _docs_engine_and_builder(args)
    output_dir = Path(args.output) if args.output else Path("docs/examples")
    path = builder.generator.save_example(
        args.correlation_id,
        args.name,
        output_dir,
    )
    print(f"📂 Example saved to {path.absolute()}")
    return 0


def docs_serve(args: argparse.Namespace) -> int:
    """Запустить локальный сервер для docs/."""
    import subprocess

    docs_dir = Path(args.dir) if args.dir else Path("docs")
    if not docs_dir.exists():
        print(f"❌ Directory not found: {docs_dir.absolute()}")
        return 1
    print(f"🌐 Serving docs at http://localhost:{args.port}")
    print("   Press Ctrl+C to stop")
    try:
        subprocess.run(
            [sys.executable, "-m", "http.server", str(args.port)],
            cwd=docs_dir,
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except FileNotFoundError:
        print("❌ Could not start http.server")
        return 1
    return 0


def init_project(args: argparse.Namespace) -> int:
    """Инициализировать проект Voyage."""
    project_dir = Path(args.dir)
    voyage_dir = project_dir / ".voyage"
    voyage_dir.mkdir(parents=True, exist_ok=True)

    # Создать базовые файлы
    (voyage_dir / "events.db").touch()
    (voyage_dir / "events.jsonl").touch()
    (voyage_dir / "audit.jsonl").touch()

    # README
    readme = project_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            """# Voyage Project

Generated by Voyage Framework — a local Project Knowledge OS / Development Memory System.

## Quick Start

```bash
voyage tasks create --file task.yaml
voyage sync build --file task.yaml --output CONTEXT.json
```
""",
            encoding="utf-8",
        )

    print(f"✅ Project initialized in {project_dir.absolute()}")
    print(f"   Events DB: {voyage_dir / 'events.db'}")
    print(f"   Audit Log: {voyage_dir / 'audit.jsonl'}")
    return 0


def show_status(args: argparse.Namespace) -> int:
    """Показать статус проекта."""
    engine = EventEngine()
    count = engine.count()
    print(f"📊 Total events: {count}")

    # Последние события
    events = engine.get_events(limit=5)
    if events:
        print("\n📝 Last events:")
        for ev in events:
            ts = ev.timestamp.strftime("%H:%M:%S")
            print(f"   [{ts}] {ev.event_type.value} | {ev.project_id}")
    else:
        print("\n📝 No events yet. Create tasks with 'voyage tasks create' to start.")

    return 0


async def run_agent(args: argparse.Namespace) -> int:
    """Legacy agent runner (non-canonical compatibility)."""
    engine = EventEngine()
    policy = PolicyEnforcer()
    security = SecurityPolicy()
    if args.backend == "docker":
        from voyage_framework.security.docker_backend import DockerBackend

        executor = SecureExecutor(
            security,
            project_root=Path.cwd(),
            backend=DockerBackend(project_root=Path.cwd(), image=args.docker_image),
        )
    else:
        executor = SecureExecutor(security, project_root=Path.cwd())
    runtime = AgentRuntime(engine, executor, policy)

    role = args.role
    task = args.task or "No task specified"
    plan = args.plan.split(";") if args.plan else [task]

    print(f"🚀 Starting agent: role={role}, task={task}")
    result = await runtime.run(
        role=role,
        task=task,
        plan=plan,
        project_id=args.project or "default",
    )

    if result.success:
        print(f"✅ Agent completed. Confidence: {result.state.confidence:.2f}")
    else:
        print(f"❌ Agent failed. Status: {result.state.status.value}")
        if result.output.get("error"):
            print(f"   Error: {result.output['error']}")

    return 0 if result.success else 1


def generate_task(args: argparse.Namespace) -> int:
    """Сгенерировать TASK.md + CONTEXT.json."""
    engine = EventEngine()
    generator = TaskGenerator(engine)

    spec = generator.generate(
        role=args.role,
        task=args.task,
        micro_phase=args.phase,
        project_id=args.project or "default",
    )

    task_path, context_path = generator.write_task_files(spec)

    print("✅ Task generated:")
    print(f"   TASK.md:      {task_path.absolute()}")
    print(f"   CONTEXT.json: {context_path.absolute()}")
    print(f"   Task ID:      {spec.task_id}")
    return 0


def show_events(args: argparse.Namespace) -> int:
    """Показать события."""
    engine = EventEngine()
    events = engine.get_events(
        project_id=args.project,
        limit=args.limit,
    )

    print(f"📊 Events (limit={args.limit}):")
    for ev in events:
        ts = ev.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"   {ev.event_id[:8]} | {ev.event_type.value:25} | {ts} | {ev.project_id}")

    return 0


def show_approvals(args: argparse.Namespace) -> int:
    """Показать pending approval запросы."""
    from voyage_framework.security.approval import ApprovalQueue

    queue = ApprovalQueue()
    queue.cleanup_expired()
    pending = queue.get_pending()

    if not pending:
        print("✅ No pending approvals")
        return 0

    print(f"⏳ Pending approvals ({len(pending)}):")
    for req in pending:
        ts = req.timestamp.strftime("%H:%M:%S")
        cmd = " ".join(req.command[:3])
        print(f"   {req.request_id[:8]} | {cmd}... | {req.role} | {ts}")

    return 0


def evaluate_project(args: argparse.Namespace) -> int:
    """Показать evaluation summary проекта."""
    from voyage_framework.core.event_engine import EventEngine
    from voyage_framework.improvement.evaluator import Evaluator
    from voyage_framework.improvement.feedback_loop import FeedbackLoop
    from voyage_framework.improvement.golden_dataset import GoldenDataset
    from voyage_framework.improvement.rule_engine import RuleEngine

    engine = EventEngine()
    evaluator = Evaluator(project_root=Path(args.dir))
    rule_engine = RuleEngine(engine=engine)
    golden_dataset = GoldenDataset(engine=engine)
    feedback = FeedbackLoop(engine, evaluator, rule_engine, golden_dataset)

    summary = feedback.get_improvement_summary(project_id=args.project)

    print(f"📊 Improvement summary for project '{args.project}':")
    print(f"   Evaluations: {summary['evaluations_count']}")
    print(f"   Rules suggested: {summary['rules_suggested_count']}")
    print(f"   Golden matches: {summary['golden_matches_count']}")
    print(f"   Average score: {summary['average_score']:.2f}")
    print(f"   Last score: {summary['last_score']}")
    print(f"   Stored rules: {summary['stored_rules_count']}")
    print(f"   Golden solutions: {summary['golden_solutions_count']}")

    return 0


def graph_visualize(args: argparse.Namespace) -> int:
    """Визуализировать граф workflow."""
    from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
    from voyage_framework.core.event_engine import EventEngine
    from voyage_framework.security.policy import PolicyEnforcer
    from voyage_framework.security.sandbox import SecureExecutor

    engine = EventEngine()
    policy = PolicyEnforcer()
    executor = SecureExecutor(SecurityPolicy(), project_root=Path.cwd())
    runtime = LangGraphRuntime(engine, executor, policy)

    mermaid = runtime.visualize()
    print(mermaid)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mermaid, encoding="utf-8")
    print(f"📝 Graph saved to {output_path.absolute()}")
    return 0


async def graph_run(args: argparse.Namespace) -> int:
    """Legacy LangGraph agent runner (non-canonical compatibility)."""
    from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
    from voyage_framework.core.event_engine import EventEngine
    from voyage_framework.improvement.evaluator import Evaluator
    from voyage_framework.improvement.feedback_loop import FeedbackLoop
    from voyage_framework.improvement.golden_dataset import GoldenDataset
    from voyage_framework.improvement.rule_engine import RuleEngine
    from voyage_framework.security.docker_backend import DockerBackend
    from voyage_framework.security.policy import PolicyEnforcer
    from voyage_framework.security.sandbox import SecureExecutor

    engine = EventEngine()
    policy = PolicyEnforcer()
    security = SecurityPolicy()
    if args.backend == "docker":
        executor = SecureExecutor(
            security,
            project_root=Path.cwd(),
            backend=DockerBackend(project_root=Path.cwd(), image=args.docker_image),
        )
    else:
        executor = SecureExecutor(security, project_root=Path.cwd())

    feedback_loop = None
    if args.feedback:
        evaluator = Evaluator(project_root=Path.cwd())
        rule_engine = RuleEngine(engine=engine)
        golden = GoldenDataset(engine=engine)
        feedback_loop = FeedbackLoop(engine, evaluator, rule_engine, golden)

    runtime = LangGraphRuntime(engine, executor, policy, feedback_loop=feedback_loop)
    plan = args.plan.split(";") if args.plan else [args.task]

    result = await runtime.run(
        role=args.role,
        task=args.task,
        plan=plan,
        project_id=args.project or "default",
        correlation_id=args.correlation_id,
    )

    if result.success:
        print(f"✅ Graph completed. Confidence: {result.state.confidence:.2f}")
    else:
        print(f"❌ Graph failed. Status: {result.output.get('status')}")
        if result.output.get("error"):
            print(f"   Error: {result.output['error']}")

    return 0 if result.success else 1


def graph_state(args: argparse.Namespace) -> int:
    """Показать последний сохранённый state по correlation_id."""
    from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
    from voyage_framework.core.event_engine import EventEngine
    from voyage_framework.security.policy import PolicyEnforcer
    from voyage_framework.security.sandbox import SecureExecutor

    engine = EventEngine()
    policy = PolicyEnforcer()
    executor = SecureExecutor(SecurityPolicy(), project_root=Path.cwd())
    runtime = LangGraphRuntime(engine, executor, policy)

    state = runtime.get_state(args.correlation_id)
    if state is None:
        print(f"❌ No state found for correlation_id={args.correlation_id}")
        return 1

    print(f"📊 State for correlation_id={args.correlation_id}:")
    for key, value in state.model_dump().items():
        print(f"   {key}: {value}")
    return 0


def chronicler_journal(args: argparse.Namespace) -> int:
    """Показать последние шаги из ProcessJournal."""
    from voyage_framework.chronicler.journal import ProcessJournal
    from voyage_framework.core.event_engine import EventEngine

    engine = EventEngine()
    journal = ProcessJournal(
        engine,
        project_id=args.project or "default",
        correlation_id=args.correlation_id,
    )
    steps = journal.get_steps(
        correlation_id=args.correlation_id,
        step_type=args.step_type,
        limit=args.limit,
    )

    if not steps:
        print("📝 No steps found")
        return 0

    print(f"📝 Steps (limit={args.limit}):")
    for event in steps:
        payload = event.payload
        print(
            f"   {payload.get('step_type', 'unknown'):10} | {payload.get('description', '')[:60]}"
        )
    return 0


def chronicler_replay(args: argparse.Namespace) -> int:
    """Сгенерировать replay-скрипт для correlation_id."""
    from voyage_framework.chronicler.journal import ProcessJournal
    from voyage_framework.chronicler.replay import ReplayGenerator
    from voyage_framework.core.event_engine import EventEngine

    engine = EventEngine()
    journal = ProcessJournal(
        engine,
        project_id=args.project or "default",
        correlation_id=args.correlation_id,
    )
    generator = ReplayGenerator(journal)
    path = generator.save_script(args.correlation_id, path=args.output)
    print(f"🎬 Replay script saved to {path.absolute()}")
    return 0


def chronicler_decisions(args: argparse.Namespace) -> int:
    """Показать decision log."""
    from voyage_framework.chronicler.decision_log import DecisionLog
    from voyage_framework.core.event_engine import EventEngine

    engine = EventEngine()
    decision_log = DecisionLog(engine)
    decisions = decision_log.get_decisions(project_id=args.project or "default")

    if not decisions:
        print("🧠 No decisions recorded")
        return 0

    print(f"🧠 Decisions ({len(decisions)}):")
    for event in decisions:
        payload = event.payload
        print(f"   {payload.get('context', '')}: {payload.get('chosen', '')}")
        print(f"      {payload.get('rationale', '')[:80]}")
    return 0


def chronicler_tutorial(args: argparse.Namespace) -> int:
    """Сгенерировать tutorial draft для correlation_id."""
    from voyage_framework.chronicler.journal import ProcessJournal
    from voyage_framework.chronicler.tutorial_generator import TutorialDraft
    from voyage_framework.core.event_engine import EventEngine

    engine = EventEngine()
    journal = ProcessJournal(
        engine,
        project_id=args.project or "default",
        correlation_id=args.correlation_id,
    )
    draft = TutorialDraft(journal)
    tutorial = draft.generate_draft(args.correlation_id)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(tutorial, encoding="utf-8")
        print(f"📚 Tutorial draft saved to {output_path.absolute()}")
    else:
        print(tutorial)
    return 0


def _dispatch_graph(args: argparse.Namespace) -> int:
    """Диспетчер подкоманд graph."""
    if not args.graph_command:
        print("❌ No graph subcommand provided. Use: visualize, run, state")
        return 1
    if args.graph_command == "visualize":
        return graph_visualize(args)
    if args.graph_command == "run":
        return asyncio.run(graph_run(args))
    if args.graph_command == "state":
        return graph_state(args)
    return 1


def _dispatch_chronicler(args: argparse.Namespace) -> int:
    """Диспетчер подкоманд chronicler."""
    if not args.chronicler_command:
        print("❌ No chronicler subcommand provided. Use: journal, replay, decisions, tutorial")
        return 1
    if args.chronicler_command == "journal":
        return chronicler_journal(args)
    if args.chronicler_command == "replay":
        return chronicler_replay(args)
    if args.chronicler_command == "decisions":
        return chronicler_decisions(args)
    if args.chronicler_command == "tutorial":
        return chronicler_tutorial(args)
    return 1


def _dispatch_docs(args: argparse.Namespace) -> int:
    """Диспетчер подкоманд docs."""
    if not args.docs_command:
        print("❌ No docs subcommand provided. Use: build, tutorial, example, serve")
        return 1
    if args.docs_command == "build":
        return docs_build(args)
    if args.docs_command == "tutorial":
        return docs_tutorial(args)
    if args.docs_command == "example":
        return docs_example(args)
    if args.docs_command == "serve":
        return docs_serve(args)
    return 1


def _get_tasks_db_path(args: argparse.Namespace) -> Path:
    """Получить путь к runtime БД задач."""
    return Path(getattr(args, "tasks_db", ".voyage/tasks.db"))


def _build_task_engine(args: argparse.Namespace) -> TaskEngine:
    """Создать TaskEngine для обычного CLI-вызова."""
    return TaskEngine(db_path=_get_tasks_db_path(args))


def _dispatch_tasks(
    args: argparse.Namespace,
    engine: TaskEngine | None = None,
) -> int:
    """Диспетчер подкоманд tasks (plural, runtime task management)."""
    command = getattr(args, "tasks_command", None)
    if not command:
        print(
            "❌ No tasks subcommand provided. "
            "Use: create, list, show, start, block, unblock, complete, fail, archive"
        )
        return 1

    owns_engine = engine is None
    task_engine = engine or _build_task_engine(args)
    try:
        handlers: dict[str, Callable[[argparse.Namespace, TaskEngine], int]] = {
            "create": _tasks_create,
            "list": _tasks_list,
            "show": _tasks_show,
            "start": _tasks_start,
            "block": _tasks_block,
            "unblock": _tasks_unblock,
            "complete": _tasks_complete,
            "fail": _tasks_fail,
            "archive": _tasks_archive,
        }
        handler = handlers.get(command)
        return handler(args, task_engine) if handler is not None else 1
    finally:
        if owns_engine:
            task_engine.close()


def _tasks_create(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Создать задачу из task.yaml."""
    parser = TaskParser()
    try:
        spec = parser.parse(args.file)
    except (TaskValidationError, FileNotFoundError) as e:
        print(f"❌ Error: {e}")
        return 1

    try:
        record = engine.create_from_spec(spec)
    except TaskAlreadyExistsError as e:
        print(f"❌ Error: {e}")
        return 1

    print(f"✅ Created task {record.id}: {record.title}")
    print(f"   Role: {record.role}")
    print(f"   Status: {record.status}")
    return 0


def _tasks_list(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Показать список задач."""
    records = engine.list(
        status=args.status,
        role=args.role,
        limit=args.limit or 20,
    )

    if not records:
        print("📝 No tasks found")
        return 0

    print(f"📝 Tasks ({len(records)}):")
    print(f"{'ID':12} {'Status':12} {'Role':12} {'Title'}")
    print("-" * 60)
    for r in records:
        short_id = r.id[:10]
        print(f"{short_id:12} {r.status:12} {r.role:12} {r.title[:40]}")
    return 0


def _tasks_show(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Показать детали задачи."""
    record = engine.get(args.task_id)
    if record is None:
        print(f"❌ Error: task {args.task_id} not found")
        return 1

    print(f"📋 Task {record.id}")
    print(f"   Title:       {record.title}")
    print(f"   Status:      {record.status}")
    print(f"   Role:        {record.role}")
    print(f"   Priority:    {record.priority or '—'}")
    print(f"   Mode:        {record.mode or '—'}")
    print(f"   Created:     {record.created_at}")
    if record.started_at:
        print(f"   Started:     {record.started_at}")
    if record.completed_at:
        print(f"   Completed:   {record.completed_at}")
    if record.archived_at:
        print(f"   Archived:    {record.archived_at}")
    print("   Criteria:")
    for c in record.acceptance_criteria:
        print(f"      - {c}")
    if record.description:
        print(f"   Description: {record.description[:100]}")
    return 0


def _tasks_start(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Начать задачу."""
    try:
        record = engine.start(args.task_id)
        print(f"🚀 Started task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


def _tasks_block(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Заблокировать задачу."""
    reason = args.reason or "No reason provided"
    try:
        record = engine.block(args.task_id, reason=reason)
        print(f"⏸️  Blocked task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


def _tasks_unblock(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Разблокировать задачу."""
    try:
        record = engine.unblock(args.task_id)
        print(f"▶️  Unblocked task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


def _tasks_complete(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Завершить задачу."""
    try:
        record = engine.complete(args.task_id)
        print(f"✅ Completed task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


def _tasks_fail(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Отметить задачу как failed."""
    reason = args.reason or "No reason provided"
    try:
        record = engine.fail(args.task_id, reason=reason)
        print(f"❌ Failed task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


def _tasks_archive(args: argparse.Namespace, engine: TaskEngine) -> int:
    """Архивировать задачу."""
    try:
        record = engine.archive(args.task_id)
        print(f"📦 Archived task {record.id} → {record.status}")
        return 0
    except TaskNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except TaskTransitionError as e:
        print(f"❌ Error: {e}")
        return 1


# ───────────────────────────────────────────────────────────────
# Sync commands (Phase 4: Context Builder Lite)
# ───────────────────────────────────────────────────────────────


def _sync_build(
    args: argparse.Namespace,
    builder: ContextBuilder | None = None,
) -> int:
    """Build project context (voyage sync build)."""
    from voyage_framework.core.context_builder import ContextBuilder

    try:
        if builder is None:
            task_engine = _build_task_engine(args)
            builder = ContextBuilder(task_engine)

        files = [Path(f) for f in (args.files or [])]
        output_path = Path(args.output)

        context = builder.build(
            files,
            project_id=getattr(args, "project", "default") or "default",
        )
        builder.write_context(context, output_path)

        print(f"✅ Context built: {len(context.tasks)} tasks")
        print(f"📄 Written to {output_path.absolute()}")
        return 0
    except Exception as e:
        print(f"❌ Error building context: {e}")
        return 1


def _sync_check(
    args: argparse.Namespace,
    builder: ContextBuilder | None = None,
) -> int:
    """Check diffs between YAML and runtime (voyage sync check)."""
    from voyage_framework.core.context_builder import ContextBuilder

    try:
        if builder is None:
            task_engine = _build_task_engine(args)
            builder = ContextBuilder(task_engine)

        files = [Path(f) for f in (args.files or [])]
        diffs = builder.check(files)

        if not diffs:
            print("✅ No diffs found")
            return 0

        for diff in diffs:
            if not diff.changed_fields:
                print(f"✅ {diff.task_id}: in sync")
            else:
                print(f"⚠️  {diff.task_id}: {len(diff.changed_fields)} field(s) changed")
                for field, changes in diff.changed_fields.items():
                    yaml_val = changes.get("yaml")
                    runtime_val = changes.get("runtime")
                    print(f"   {field}: {yaml_val} → {runtime_val}")

            if not diff.exists_in_runtime:
                print(f"   ⚠️  No runtime record for {diff.task_id}")

        return 0
    except Exception as e:
        print(f"❌ Error checking diffs: {e}")
        return 1


def _sync_status(
    args: argparse.Namespace,
    engine: TaskEngine | None = None,
) -> int:
    """Show runtime task status (voyage sync status).

    Reads TaskEngine runtime database, not task.yaml files.
    """
    try:
        if engine is None:
            engine = _build_task_engine(args)

        records = engine.list(limit=1000)
        total = len(records)

        if not records:
            print("✅ No runtime tasks found (empty project)")
            return 0

        # Count by status
        by_status: dict[str, int] = {}
        for r in records:
            by_status[r.status] = by_status.get(r.status, 0) + 1

        print("📊 Sync Status")
        print(f"   Total runtime tasks: {total}")
        print("   By status:")
        for status, count in sorted(by_status.items()):
            print(f"      {status}: {count}")

        # Latest updated task
        latest = max(records, key=lambda r: r.updated_at)
        print(f"   Latest updated: {latest.id} ({latest.title[:40]}) → {latest.status}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def _launcher_dry_run(args: argparse.Namespace) -> int:
    """Run the minimal controlled launcher in dry-run mode."""
    expected = args.expected_origin_main
    if len(expected) != 40 or not all(c in "0123456789abcdef" for c in expected.lower()):
        print("❌ expected_origin-main must be a full 40-character hex hash")
        return 1

    config = LauncherConfig(
        package_dir=Path(args.package),
        primary_repo=Path(args.primary_repo),
        auto_worktree=Path(args.auto_worktree),
        expected_origin_main=expected,
    )

    result = run_dry_run(config)
    if result.success:
        print(f"✅ Launcher dry-run completed: {result.report_path}")
        return 0

    print(f"❌ Launcher STOP: {result.message}")
    return 1


def _dispatch_launcher(args: argparse.Namespace) -> int:
    """Dispatcher for launcher subcommands."""
    command = getattr(args, "launcher_command", None)
    if command == "dry-run":
        return _launcher_dry_run(args)
    print("❌ No launcher subcommand provided. Use: dry-run")
    return 1


def _auto_preflight(args: argparse.Namespace) -> int:
    """Run source-only autoloop preflight checks."""
    try:
        ok, report = run_preflight(Path(args.spec))
    except AutoLoopError as exc:
        print(json.dumps({"command": "preflight", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


def _auto_plan(args: argparse.Namespace) -> int:
    """Build a non-executed source-only autoloop command plan."""
    try:
        ok, report = run_plan(Path(args.spec))
    except AutoLoopError as exc:
        print(json.dumps({"command": "plan", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


def _auto_validate(args: argparse.Namespace) -> int:
    """Validate current target repo changes against source-only path guards."""
    try:
        ok, report = run_validate(Path(args.spec))
    except AutoLoopError as exc:
        print(json.dumps({"command": "validate", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


def _dispatch_auto(args: argparse.Namespace) -> int:
    """Dispatcher for source-only autoloop scaffold commands."""
    command = getattr(args, "auto_command", None)
    if command == "preflight":
        return _auto_preflight(args)
    if command == "plan":
        return _auto_plan(args)
    if command == "validate":
        return _auto_validate(args)
    print("❌ No auto subcommand provided. Use: preflight, plan, or validate")
    return 1


def _narrative_scene_validate(args: argparse.Namespace) -> int:
    """Validate a Narrative scenario JSON file against structural and path guards."""
    from voyage_framework.core.narrative_adapter import validate_scene

    try:
        result = validate_scene(Path(args.spec), args.file)
    except AutoLoopError as exc:
        print(
            json.dumps(
                {"command": "scene-validate", "ok": False, "error": str(exc)},
                indent=2,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _narrative_arc_check(args: argparse.Namespace) -> int:
    """Check continuity and arc progression across multiple Narrative scenarios."""
    from voyage_framework.core.narrative_adapter import run_arc_check

    try:
        result = run_arc_check(Path(args.spec), args.from_id, args.count)
    except AutoLoopError as exc:
        print(
            json.dumps(
                {"command": "arc-check", "ok": False, "error": str(exc)},
                indent=2,
            )
        )
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _narrative_inventory(args: argparse.Namespace) -> int:
    """Read-only Narrative inventory/readiness summary (does not modify the repo)."""
    from voyage_framework.core.narrative_adapter import narrative_inventory

    spec: str | None = getattr(args, "spec", None)
    repo: str | None = getattr(args, "repo", None)
    if spec and repo:
        print(
            json.dumps(
                {
                    "command": "narrative.inventory",
                    "ok": False,
                    "error": "--spec and --repo are mutually exclusive",
                },
                indent=2,
            )
        )
        return 1
    if not spec and not repo:
        print(
            json.dumps(
                {
                    "command": "narrative.inventory",
                    "ok": False,
                    "error": "--spec or --repo is required",
                },
                indent=2,
            )
        )
        return 1

    source = spec if spec is not None else repo
    assert source is not None
    try:
        result = narrative_inventory(Path(source))
    except AutoLoopError as exc:
        print(
            json.dumps(
                {"command": "narrative.inventory", "ok": False, "error": str(exc)},
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def _dispatch_narrative(args: argparse.Namespace) -> int:
    """Dispatcher for Narrative source-only validation commands."""
    command = getattr(args, "narrative_command", None)
    if command == "scene-validate":
        return _narrative_scene_validate(args)
    if command == "arc-check":
        return _narrative_arc_check(args)
    if command == "inventory":
        return _narrative_inventory(args)
    print("❌ No narrative subcommand provided. Use: scene-validate, arc-check, inventory")
    return 1


def _get_repo_control_adapter(name: str) -> RepoControlAdapter | None:
    """Look up a RepoControlAdapter implementation by name.

    Supports "narrative" and "local". Lazy-imports the concrete
    implementation, keeping cli.py's top level free of any adapter-specific
    dependency.
    """
    if name == "narrative":
        from voyage_framework.core.narrative_adapter import NarrativeRepoControlAdapter

        return NarrativeRepoControlAdapter()
    if name == "local":
        from voyage_framework.core.local_repo_adapter import LocalRepoControlAdapter

        return LocalRepoControlAdapter()
    return None


def _repo_status(args: argparse.Namespace) -> int:
    """Generic repo-control status check via a RepoControlAdapter."""
    adapter = _get_repo_control_adapter(args.adapter)
    if adapter is None:
        print(
            json.dumps(
                {
                    "command": "repo.status",
                    "ok": False,
                    "error": f"Unknown repo adapter: {args.adapter}",
                    "adapter": args.adapter,
                },
                indent=2,
            )
        )
        return 1
    try:
        result = adapter.status(args.spec)
    except AutoLoopError as exc:
        print(json.dumps({"command": "repo.status", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _repo_validate(args: argparse.Namespace) -> int:
    """Generic repo-control validate check via a RepoControlAdapter."""
    adapter = _get_repo_control_adapter(args.adapter)
    if adapter is None:
        print(
            json.dumps(
                {
                    "command": "repo.validate",
                    "ok": False,
                    "error": f"Unknown repo adapter: {args.adapter}",
                    "adapter": args.adapter,
                },
                indent=2,
            )
        )
        return 1
    try:
        result = adapter.validate(args.spec, target=args.target)
    except AutoLoopError as exc:
        print(json.dumps({"command": "repo.validate", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _repo_audit(args: argparse.Namespace) -> int:
    """Generic repo-control audit check via a RepoControlAdapter."""
    adapter = _get_repo_control_adapter(args.adapter)
    if adapter is None:
        print(
            json.dumps(
                {
                    "command": "repo.audit",
                    "ok": False,
                    "error": f"Unknown repo adapter: {args.adapter}",
                    "adapter": args.adapter,
                },
                indent=2,
            )
        )
        return 1
    try:
        result = adapter.audit(args.spec, target=args.target, count=args.count)
    except AutoLoopError as exc:
        print(json.dumps({"command": "repo.audit", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _repo_preview(args: argparse.Namespace) -> int:
    """Generic repo-control preview (non-executed plan) via a RepoControlAdapter."""
    adapter = _get_repo_control_adapter(args.adapter)
    if adapter is None:
        print(
            json.dumps(
                {
                    "command": "repo.preview",
                    "ok": False,
                    "error": f"Unknown repo adapter: {args.adapter}",
                    "adapter": args.adapter,
                },
                indent=2,
            )
        )
        return 1
    try:
        result = adapter.preview(args.spec)
    except AutoLoopError as exc:
        print(json.dumps({"command": "repo.preview", "ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok else 1


def _dispatch_repo(args: argparse.Namespace) -> int:
    """Dispatcher for generic RepoControlAdapter commands."""
    command = getattr(args, "repo_command", None)
    if command == "status":
        return _repo_status(args)
    if command == "validate":
        return _repo_validate(args)
    if command == "audit":
        return _repo_audit(args)
    if command == "preview":
        return _repo_preview(args)
    print("❌ No repo subcommand provided. Use: status, validate, audit, preview")
    return 1


def _report_state_command(args: argparse.Namespace) -> int:
    """Emit canonical Voyage-observed repo/git state as JSON.

    This command is read-only and policy-neutral: a dirty worktree is observed
    and reported, not treated as a failure. Use it to compare agent reports
    against Voyage-generated facts.
    """
    state = collect_repo_state(getattr(args, "repo", "."))
    print(json.dumps(state, indent=2))
    return 0 if state["ok"] else 1


def _validate_report_command(args: argparse.Namespace) -> int:
    """Validate a structured report against current Git state."""
    try:
        result = validate_report(Path(args.report))
    except ReportValidatorError as exc:
        print(
            json.dumps(
                {"command": "validate-report", "ok": False, "error": str(exc)},
                indent=2,
            )
        )
        return 1

    print(json.dumps({"command": "validate-report", **result.to_dict()}, indent=2))
    return 0 if result.ok else 1


def _dispatch_sync(
    args: argparse.Namespace,
    builder: ContextBuilder | None = None,
    engine: TaskEngine | None = None,
) -> int:
    """Dispatcher for sync subcommands."""
    command = getattr(args, "sync_command", None)
    if not command:
        print("❌ No sync subcommand provided. Use: build, check, status")
        return 1

    if command == "build":
        return _sync_build(args, builder=builder)
    elif command == "check":
        return _sync_check(args, builder=builder)
    elif command == "status":
        if engine is None:
            engine = _build_task_engine(args)
        return _sync_status(args, engine=engine)
    else:
        print(f"❌ Unknown sync command: {command}")
        return 1


def main() -> int:
    """Точка входа CLI."""
    # Гарантировать UTF-8 для stdout/stderr на Windows
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="voyage",
        description=(
            "Voyage Framework — a local Project Knowledge OS / Development Memory System "
            "for structured development workflows, task memory, context packaging, "
            "audit logs, and external AI tool handoff."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize project")
    init_parser.add_argument("--dir", default=".", help="Project directory")

    # status
    subparsers.add_parser("status", help="Show project status")

    # run (legacy compatibility)
    run_parser = subparsers.add_parser(
        "run",
        help="Run agent (legacy/non-canonical compatibility)",
        description="Run agent (legacy/non-canonical compatibility).",
    )
    run_parser.add_argument("role", help="Agent role")
    run_parser.add_argument("--task", default="", help="Task description")
    run_parser.add_argument("--plan", default="", help="Execution plan (semicolon-separated)")
    run_parser.add_argument("--project", default="default", help="Project ID")
    run_parser.add_argument(
        "--backend",
        choices=["subprocess", "docker"],
        default="subprocess",
        help="Sandbox backend (default: subprocess)",
    )
    run_parser.add_argument(
        "--docker-image",
        default="python:3.11-slim",
        help="Docker image when --backend=docker",
    )

    # task (singular — legacy generate TASK.md)
    task_parser = subparsers.add_parser(
        "task",
        help="Generate TASK.md (legacy/non-canonical compatibility)",
        description="Generate TASK.md (legacy/non-canonical compatibility).",
    )
    task_parser.add_argument("role", help="Agent role")
    task_parser.add_argument("--task", required=True, help="Task description")
    task_parser.add_argument("--phase", help="Micro-phase")
    task_parser.add_argument("--project", default="default", help="Project ID")

    # tasks (plural — runtime task management)
    tasks_parser = subparsers.add_parser("tasks", help="Task runtime management commands")
    tasks_subparsers = tasks_parser.add_subparsers(dest="tasks_command")

    tasks_create_parser = tasks_subparsers.add_parser("create", help="Create task from task.yaml")
    tasks_create_parser.add_argument("--file", required=True, help="Path to task.yaml")

    tasks_list_parser = tasks_subparsers.add_parser("list", help="List tasks")
    tasks_list_parser.add_argument("--role", help="Filter by role")
    tasks_list_parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "blocked", "completed", "failed", "archived"],
        help="Filter by status",
    )
    tasks_list_parser.add_argument("--limit", type=int, default=20, help="Limit")

    tasks_show_parser = tasks_subparsers.add_parser("show", help="Show task details")
    tasks_show_parser.add_argument("task_id", help="Task ID")

    tasks_start_parser = tasks_subparsers.add_parser("start", help="Start task")
    tasks_start_parser.add_argument("task_id", help="Task ID")

    tasks_block_parser = tasks_subparsers.add_parser("block", help="Block task")
    tasks_block_parser.add_argument("task_id", help="Task ID")
    tasks_block_parser.add_argument("--reason", default="", help="Block reason")

    tasks_unblock_parser = tasks_subparsers.add_parser("unblock", help="Unblock task")
    tasks_unblock_parser.add_argument("task_id", help="Task ID")

    tasks_complete_parser = tasks_subparsers.add_parser("complete", help="Complete task")
    tasks_complete_parser.add_argument("task_id", help="Task ID")

    tasks_fail_parser = tasks_subparsers.add_parser("fail", help="Fail task")
    tasks_fail_parser.add_argument("task_id", help="Task ID")
    tasks_fail_parser.add_argument("--reason", default="", help="Fail reason")

    tasks_archive_parser = tasks_subparsers.add_parser("archive", help="Archive task")
    tasks_archive_parser.add_argument("task_id", help="Task ID")

    # events
    events_parser = subparsers.add_parser("events", help="Show events")
    events_parser.add_argument("--project", default="default", help="Project ID")
    events_parser.add_argument("--limit", type=int, default=20, help="Limit")

    # sync (Phase 4 Context Builder Lite)
    sync_parser = subparsers.add_parser("sync", help="Context sync commands (Phase 4)")
    sync_subparsers = sync_parser.add_subparsers(dest="sync_command")

    sync_build_parser = sync_subparsers.add_parser("build", help="Build project context")
    sync_build_parser.add_argument(
        "--file",
        action="append",
        dest="files",
        required=True,
        help="Task YAML file (can be specified multiple times)",
    )
    sync_build_parser.add_argument(
        "--output",
        required=True,
        help="Output CONTEXT.json path",
    )
    sync_build_parser.add_argument(
        "--project",
        default="default",
        help="Project ID",
    )

    sync_check_parser = sync_subparsers.add_parser(
        "check", help="Check diffs between YAML and runtime"
    )
    sync_check_parser.add_argument(
        "--file",
        action="append",
        dest="files",
        required=True,
        help="Task YAML file (can be specified multiple times)",
    )

    sync_status_parser = sync_subparsers.add_parser("status", help="Show sync status")
    sync_status_parser.add_argument(
        "--project",
        default="default",
        help="Project ID",
    )

    # launcher (Phase 10D minimal controlled launcher)
    launcher_parser = subparsers.add_parser(
        "launcher",
        help="Minimal controlled launcher commands",
    )
    launcher_subparsers = launcher_parser.add_subparsers(dest="launcher_command")

    launcher_dry_run_parser = launcher_subparsers.add_parser(
        "dry-run",
        help="Run a report-only launcher dry-run",
    )
    launcher_dry_run_parser.add_argument(
        "--package",
        required=True,
        help="Path to the runtime package directory",
    )
    launcher_dry_run_parser.add_argument(
        "--primary-repo",
        required=True,
        help="Path to the primary repository",
    )
    launcher_dry_run_parser.add_argument(
        "--auto-worktree",
        required=True,
        help="Path to the auto worktree",
    )
    launcher_dry_run_parser.add_argument(
        "--expected-origin-main",
        required=True,
        help="Full 40-character SHA-1 hash expected for origin/main",
    )

    # auto (D-0B source-only autoloop scaffold)
    auto_parser = subparsers.add_parser(
        "auto",
        help="Source-only autoloop dry-run commands",
    )
    auto_subparsers = auto_parser.add_subparsers(dest="auto_command")

    auto_preflight_parser = auto_subparsers.add_parser(
        "preflight",
        help="Run read-only source-only autoloop preflight checks",
    )
    auto_preflight_parser.add_argument("--spec", required=True, help="Path to JSON spec")

    auto_plan_parser = auto_subparsers.add_parser(
        "plan",
        help="Build a non-executed source-only autoloop command plan",
    )
    auto_plan_parser.add_argument("--spec", required=True, help="Path to JSON spec")

    auto_validate_parser = auto_subparsers.add_parser(
        "validate",
        help="Validate current changes against source-only path guards",
    )
    auto_validate_parser.add_argument("--spec", required=True, help="Path to JSON spec")

    # narrative (D0D-B Narrative source-only validation)
    narrative_parser = subparsers.add_parser(
        "narrative",
        help="Narrative source-only validation commands",
        description=(
            "Narrative-specific compatibility commands (source-only validation). "
            "These remain available as-is. Prefer `voyage repo ... --adapter narrative` "
            "for the generic repo-control interface. The inventory command is read-only "
            "and does not modify the Narrative repo."
        ),
    )
    narrative_subparsers = narrative_parser.add_subparsers(dest="narrative_command")

    narrative_inventory_parser = narrative_subparsers.add_parser(
        "inventory",
        help=(
            "Read-only Narrative inventory/readiness summary "
            "(scenarios, library/matrix, schema-version mix)"
        ),
        description=(
            "Read-only inventory of the target Narrative repo. Reports scenario files, "
            "presence of SCENARIO_LIBRARY.json / SCENARIO_MATRIX.json, schema-version "
            "mix, missing expected files, and a readiness verdict. Does not modify the repo."
        ),
    )
    narrative_inventory_parser.add_argument(
        "--spec",
        required=False,
        help="Path to the autoloop JSON spec",
    )
    narrative_inventory_parser.add_argument(
        "--repo",
        required=False,
        help=(
            "Path to the Narrative repo root (or scenarios directory, or "
            "SCENARIO_LIBRARY.json / SCENARIO_MATRIX.json). Reads scenario files "
            "and catalog files without modifying the repo."
        ),
    )

    narrative_scene_validate_parser = narrative_subparsers.add_parser(
        "scene-validate",
        help="Validate a Narrative scenario JSON file against structural and path guards",
    )
    narrative_scene_validate_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the autoloop JSON spec",
    )
    narrative_scene_validate_parser.add_argument(
        "--file",
        required=True,
        help="Relative path to the scenario JSON file inside the target Narrative repo",
    )

    narrative_arc_check_parser = narrative_subparsers.add_parser(
        "arc-check",
        help="Check continuity and arc progression across multiple Narrative scenarios",
    )
    narrative_arc_check_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the autoloop JSON spec",
    )
    narrative_arc_check_parser.add_argument(
        "--from-id",
        required=True,
        dest="from_id",
        help="Starting scenario ID (e.g. SC_020)",
    )
    narrative_arc_check_parser.add_argument(
        "--count",
        type=int,
        default=6,
        help="Number of consecutive scenarios to check (default: 6)",
    )

    # repo (F2-A-D-B generic RepoControlAdapter commands)
    repo_parser = subparsers.add_parser(
        "repo",
        help="Generic repo-control adapter commands (status/validate/audit/preview)",
        description=(
            "Generic repo-control commands backed by RepoControlAdapter implementations. "
            "Currently supported adapters: narrative, local. Select one with --adapter. "
            "No adapter auto-detection yet. See also: `voyage narrative ...` for the "
            "original Narrative-specific compatibility commands."
        ),
    )
    repo_subparsers = repo_parser.add_subparsers(dest="repo_command")

    repo_status_parser = repo_subparsers.add_parser(
        "status",
        help="Read-only repo-control status check via a RepoControlAdapter",
    )
    repo_status_parser.add_argument(
        "--adapter",
        required=True,
        help="Adapter name (narrative, local)",
    )
    repo_status_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the adapter JSON spec (narrative) or local repo root (local)",
    )

    repo_validate_parser = repo_subparsers.add_parser(
        "validate",
        help="Read-only repo-control validate check via a RepoControlAdapter",
    )
    repo_validate_parser.add_argument(
        "--adapter",
        required=True,
        help="Adapter name (narrative, local)",
    )
    repo_validate_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the adapter JSON spec (narrative) or local repo root (local)",
    )
    repo_validate_parser.add_argument(
        "--target",
        default=None,
        help=(
            "Adapter-specific validate target "
            "(e.g. a scenario file path for narrative; a repo-relative path for local)"
        ),
    )

    repo_audit_parser = repo_subparsers.add_parser(
        "audit",
        help="Read-only repo-control audit check via a RepoControlAdapter",
    )
    repo_audit_parser.add_argument(
        "--adapter",
        required=True,
        help="Adapter name (narrative, local)",
    )
    repo_audit_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the adapter JSON spec (narrative) or local repo root (local)",
    )
    repo_audit_parser.add_argument(
        "--target",
        default=None,
        help="Adapter-specific audit target (e.g. a starting scenario id for narrative)",
    )
    repo_audit_parser.add_argument(
        "--count",
        type=int,
        default=6,
        help="Adapter-specific audit option (e.g. scenario count for narrative; default: 6)",
    )

    repo_preview_parser = repo_subparsers.add_parser(
        "preview",
        help="Read-only, non-executed repo-control preview via a RepoControlAdapter",
    )
    repo_preview_parser.add_argument(
        "--adapter",
        required=True,
        help="Adapter name (narrative, local)",
    )
    repo_preview_parser.add_argument(
        "--spec",
        required=True,
        help="Path to the adapter JSON spec (narrative) or local repo root (local)",
    )

    report_state_parser = subparsers.add_parser(
        "report-state",
        help="Emit canonical Voyage-observed repo/git state as JSON",
        description=(
            "Read-only observation of a git repository. Emits a JSON snapshot "
            "of branch, HEAD, origin/main, worktree cleanliness, changed/staged/"
            "untracked files, and timestamps. Dirty worktrees are observed, not "
            "treated as policy failures. Useful for comparing agent reports with "
            "Voyage-observed facts."
        ),
    )
    report_state_parser.add_argument(
        "--repo",
        default=".",
        help="Path to the repository to observe (default: current working directory)",
    )

    validate_report_parser = subparsers.add_parser(
        "validate-report",
        help="Validate a structured report against current Git state",
    )
    validate_report_parser.add_argument("--report", required=True, help="Path to JSON report")

    # approve
    subparsers.add_parser("approve", help="Show pending approvals")

    # evaluate
    evaluate_parser = subparsers.add_parser("evaluate", help="Show improvement summary")
    evaluate_parser.add_argument("--dir", default=".", help="Project directory")
    evaluate_parser.add_argument("--project", default="default", help="Project ID")

    # graph (legacy compatibility)
    graph_parser = subparsers.add_parser(
        "graph",
        help="LangGraph compatibility commands (legacy/deprecated)",
        description="LangGraph compatibility commands (legacy/deprecated).",
    )
    graph_subparsers = graph_parser.add_subparsers(dest="graph_command")

    visualize_parser = graph_subparsers.add_parser(
        "visualize", help="Visualize LangGraph graph (legacy compatibility)"
    )
    visualize_parser.add_argument(
        "--output",
        default=".voyage/graph.md",
        help="Output path for Mermaid graph",
    )

    graph_run_parser = graph_subparsers.add_parser(
        "run",
        help="Run agent via LangGraph (legacy/non-canonical compatibility)",
        description="Run agent via LangGraph (legacy/non-canonical compatibility).",
    )
    graph_run_parser.add_argument("role", help="Agent role")
    graph_run_parser.add_argument("--task", default="", help="Task description")
    graph_run_parser.add_argument("--plan", default="", help="Execution plan (semicolon-separated)")
    graph_run_parser.add_argument("--project", default="default", help="Project ID")
    graph_run_parser.add_argument(
        "--correlation-id",
        default=None,
        help="Correlation ID for checkpointing",
    )
    graph_run_parser.add_argument(
        "--backend",
        choices=["subprocess", "docker"],
        default="subprocess",
        help="Sandbox backend (default: subprocess)",
    )
    graph_run_parser.add_argument(
        "--docker-image",
        default="python:3.11-slim",
        help="Docker image when --backend=docker",
    )
    graph_run_parser.add_argument(
        "--feedback",
        action="store_true",
        help="Enable FeedbackLoop",
    )

    graph_state_parser = graph_subparsers.add_parser(
        "state", help="Show LangGraph state (legacy compatibility)"
    )
    graph_state_parser.add_argument("correlation_id", help="Correlation ID")

    # chronicler
    chronicler_parser = subparsers.add_parser("chronicler", help="Chronicler commands")
    chronicler_subparsers = chronicler_parser.add_subparsers(dest="chronicler_command")

    chronicler_journal_parser = chronicler_subparsers.add_parser(
        "journal", help="Show process journal steps"
    )
    chronicler_journal_parser.add_argument("--project", default="default", help="Project ID")
    chronicler_journal_parser.add_argument("--correlation-id", help="Correlation ID")
    chronicler_journal_parser.add_argument("--step-type", help="Filter by step type")
    chronicler_journal_parser.add_argument("--limit", type=int, default=10, help="Limit")

    chronicler_replay_parser = chronicler_subparsers.add_parser(
        "replay", help="Generate replay script"
    )
    chronicler_replay_parser.add_argument("correlation_id", help="Correlation ID")
    chronicler_replay_parser.add_argument("--project", default="default", help="Project ID")
    chronicler_replay_parser.add_argument(
        "--output",
        help="Output path (default: .voyage/replay_<id>.sh)",
    )

    chronicler_decisions_parser = chronicler_subparsers.add_parser(
        "decisions", help="Show decision log"
    )
    chronicler_decisions_parser.add_argument("--project", default="default", help="Project ID")

    chronicler_tutorial_parser = chronicler_subparsers.add_parser(
        "tutorial", help="Generate tutorial draft"
    )
    chronicler_tutorial_parser.add_argument("correlation_id", help="Correlation ID")
    chronicler_tutorial_parser.add_argument("--project", default="default", help="Project ID")
    chronicler_tutorial_parser.add_argument("--output", help="Output path")

    # docs
    docs_parser = subparsers.add_parser("docs", help="Documentation commands")
    docs_subparsers = docs_parser.add_subparsers(dest="docs_command")

    docs_build_parser = docs_subparsers.add_parser("build", help="Build all documentation")
    docs_build_parser.add_argument("--project", default="default", help="Project ID")
    docs_build_parser.add_argument("--output", default="docs", help="Output directory")

    docs_tutorial_parser = docs_subparsers.add_parser("tutorial", help="Generate one tutorial file")
    docs_tutorial_parser.add_argument("correlation_id", help="Correlation ID")
    docs_tutorial_parser.add_argument("--project", default="default", help="Project ID")
    docs_tutorial_parser.add_argument(
        "--output",
        default="docs",
        help="Docs root directory",
    )

    docs_example_parser = docs_subparsers.add_parser("example", help="Generate example directory")
    docs_example_parser.add_argument("correlation_id", help="Correlation ID")
    docs_example_parser.add_argument("--name", required=True, help="Example name")
    docs_example_parser.add_argument("--project", default="default", help="Project ID")
    docs_example_parser.add_argument(
        "--output",
        default="docs/examples",
        help="Examples output directory",
    )

    docs_serve_parser = docs_subparsers.add_parser(
        "serve", help="Serve docs locally with http.server"
    )
    docs_serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to serve on",
    )
    docs_serve_parser.add_argument(
        "--dir",
        default="docs",
        help="Directory to serve",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands: dict[str, Callable[[argparse.Namespace], int]] = {
        "init": init_project,
        "status": show_status,
        "run": lambda a: asyncio.run(run_agent(a)),
        "task": generate_task,
        "tasks": _dispatch_tasks,
        "events": show_events,
        "sync": _dispatch_sync,
        "approve": show_approvals,
        "evaluate": evaluate_project,
        "graph": _dispatch_graph,
        "chronicler": _dispatch_chronicler,
        "docs": _dispatch_docs,
        "launcher": _dispatch_launcher,
        "auto": _dispatch_auto,
        "narrative": _dispatch_narrative,
        "repo": _dispatch_repo,
        "report-state": _report_state_command,
        "validate-report": _validate_report_command,
    }

    command_name: str = args.command
    handler = commands.get(command_name)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
