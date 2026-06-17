"""Tutorial generation — черновик и полноценный tutorial из ProcessJournal."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from voyage_framework.chronicler.decision_log import DecisionLog
from voyage_framework.chronicler.journal import ProcessJournal


class TutorialDraft:
    """Генерирует черновик tutorial из журнала шагов."""

    def __init__(self, journal: ProcessJournal) -> None:
        self.journal = journal

    def generate_draft(self, correlation_id: str) -> str:
        """Сгенерировать markdown-черновик tutorial."""
        return TutorialGenerator(self.journal).generate_tutorial(correlation_id)


class TutorialGenerator:
    """Генерирует полноценный tutorial из журнала шагов и decision log."""

    def __init__(
        self,
        journal: ProcessJournal,
        decision_log: DecisionLog | None = None,
    ) -> None:
        self.journal = journal
        self.decision_log = decision_log

    def generate_tutorial(
        self,
        correlation_id: str,
        template: str = "step-by-step",
    ) -> str:
        """Сгенерировать markdown tutorial."""
        steps = self.journal.get_steps(correlation_id=correlation_id, limit=10000)
        steps = list(reversed(steps))

        if not steps:
            return f"# Tutorial\n\nNo steps found for correlation_id={correlation_id}\n"

        first_payload = steps[0].payload
        title = first_payload.get("description", "Tutorial")
        project_id = first_payload.get("project_id", "default")

        lines: list[str] = [
            "---",
            f"title: {title}",
            "description: Auto-generated tutorial from Voyage Chronicler",
            "difficulty: intermediate",
            "estimated_time: 30 minutes",
            "---",
            "",
            f"# {title}",
            "",
            f"_Generated at {datetime.now(UTC).isoformat()}_",
            "",
            "## Prerequisites",
            "",
            "- Python 3.11+",
            "- Installed `voyage-framework` package",
            "",
            "## Steps",
            "",
        ]

        for idx, event in enumerate(steps, start=1):
            payload = event.payload
            step_type = payload.get("step_type", "unknown")
            description = payload.get("description", "")
            outputs = payload.get("outputs") or {}
            decision = payload.get("decision")

            lines.append(f"### Step {idx}: {step_type}")
            lines.append("")
            lines.append(description)
            lines.append("")

            code = outputs.get("code")
            if code:
                lines.append("```python")
                lines.append(str(code))
                lines.append("```")
                lines.append("")

            command = payload.get("command")
            if command:
                lines.append("```bash")
                lines.append(command)
                lines.append("```")
                lines.append("")

            if decision:
                chosen = decision.get("chosen", "")
                rationale = decision.get("rationale", "")
                lines.append(f"**Why we did it:** {chosen} — {rationale}")
                lines.append("")
                options = decision.get("options", [])
                if options and chosen != options[0]:
                    lines.append(
                        "**Common pitfall:** the obvious first option "
                        f"`{options[0]}` was not the best fit here."
                    )
                    lines.append("")

            why = self._find_why_from_decisions(project_id, description)
            if why:
                lines.append(f"**Design context:** {why}")
                lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"This tutorial covered {len(steps)} real development steps "
            "recorded by Voyage Chronicler."
        )
        lines.append("")
        lines.append("## Next steps")
        lines.append("")
        lines.append("- Explore other tutorials in `docs/tutorial/`.")
        lines.append("- Run `voyage chronicler replay <correlation_id>` to reproduce the process.")
        lines.append("")
        return "\n".join(lines)

    def generate_example(self, correlation_id: str, name: str) -> dict[str, str]:
        """Сгенерировать структуру example для docs/examples/{name}/."""
        steps = self.journal.get_steps(correlation_id=correlation_id, limit=10000)
        steps = list(reversed(steps))

        plan_step = next(
            (e for e in steps if e.payload.get("step_type") == "plan"),
            None,
        )
        plan_payload = plan_step.payload if plan_step else {}
        description = plan_payload.get("description", name)

        task_md = f"# TASK: {description}\n\n## Plan\n\n"
        for step in steps:
            step_type = step.payload.get("step_type", "unknown")
            step_desc = step.payload.get("description", "")
            task_md += f"- {step_type}: {step_desc}\n"

        context_json = json.dumps(
            {
                "name": name,
                "description": description,
                "correlation_id": correlation_id,
                "steps": [e.payload.get("description", "") for e in steps],
            },
            indent=2,
            ensure_ascii=False,
        )

        readme = (
            f"# Example: {name}\n\n"
            f"This example was generated from correlation_id `{correlation_id}`.\n\n"
            f"## Description\n\n{description}\n\n"
            "## Files\n\n"
            "- `TASK.md` — task specification\n"
            "- `CONTEXT.json` — context captured by Chronicler\n"
        )

        return {
            "TASK.md": task_md,
            "CONTEXT.json": context_json,
            "README.md": readme,
        }

    def save_tutorial(
        self,
        correlation_id: str,
        path: Path | str,
    ) -> Path:
        """Сохранить tutorial в файл."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.generate_tutorial(correlation_id), encoding="utf-8")
        return output

    def save_example(
        self,
        correlation_id: str,
        name: str,
        path: Path | str,
    ) -> Path:
        """Сохранить example в директорию."""
        output_dir = Path(path) / name
        output_dir.mkdir(parents=True, exist_ok=True)
        files = self.generate_example(correlation_id, name)
        for filename, content in files.items():
            (output_dir / filename).write_text(content, encoding="utf-8")
        return output_dir

    def _find_why_from_decisions(self, project_id: str, description: str) -> str:
        """Найти связанное обоснование в DecisionLog по описанию."""
        if self.decision_log is None:
            return ""
        decisions = self.decision_log.get_decisions(project_id=project_id)
        for event in decisions:
            payload = event.payload
            if payload.get("context", "").lower() in description.lower():
                return f"{payload.get('chosen')} — {payload.get('rationale')}"
        return ""
