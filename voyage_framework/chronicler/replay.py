"""ReplayGenerator — генерация bash-скриптов и markdown из ProcessJournal."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from voyage_framework.chronicler.journal import ProcessJournal


class ReplayGenerator:
    """Генерирует replay-скрипты на основе записанных шагов."""

    def __init__(self, journal: ProcessJournal) -> None:
        self.journal = journal

    def generate_script(self, correlation_id: str, format: str = "bash") -> str:
        """Сгенерировать bash-скрипт для воспроизведения процесса."""
        steps = self.journal.get_steps(correlation_id=correlation_id, limit=10000)
        steps = list(reversed(steps))  # chronological order

        lines = [
            "#!/bin/bash",
            "# Voyage Framework Process Replay",
            f"# Generated: {datetime.now(UTC).isoformat()}",
            f"# Correlation ID: {correlation_id}",
            f"# Total steps: {len(steps)}",
            "set -e",
            "",
        ]

        for idx, event in enumerate(steps, start=1):
            payload = event.payload
            step_type = payload.get("step_type", "unknown")
            description = payload.get("description", "")
            command = payload.get("command")

            lines.append(f'echo "=== Step {idx}: {step_type} — {description} ==="')
            if command:
                lines.append(command)
            else:
                lines.append(f"# No command recorded for: {description}")
            lines.append("")

        lines.append('echo "=== Replay completed ==="')
        return "\n".join(lines)

    def generate_markdown(self, correlation_id: str) -> str:
        """Сгенерировать human-readable markdown replay."""
        steps = self.journal.get_steps(correlation_id=correlation_id, limit=10000)
        steps = list(reversed(steps))

        lines = [
            f"# Process Replay: {correlation_id}",
            "",
            f"- Generated: {datetime.now(UTC).isoformat()}",
            f"- Total steps: {len(steps)}",
            "",
        ]

        for idx, event in enumerate(steps, start=1):
            payload = event.payload
            step_type = payload.get("step_type", "unknown")
            description = payload.get("description", "")
            command = payload.get("command")
            decision = payload.get("decision")

            lines.append(f"## Step {idx}: {step_type}")
            lines.append("")
            lines.append(description)
            lines.append("")
            if command:
                lines.append("```bash")
                lines.append(command)
                lines.append("```")
                lines.append("")
            if decision:
                chosen = decision.get("chosen", "")
                rationale = decision.get("rationale", "")
                lines.append(f"**Decision:** {chosen} — {rationale}")
                lines.append("")

        return "\n".join(lines)

    def save_script(
        self,
        correlation_id: str,
        path: Path | str | None = None,
    ) -> Path:
        """Сохранить replay-скрипт на диск."""
        safe_id = self._sanitize(correlation_id)
        path = Path(f".voyage/replay_{safe_id}.sh") if path is None else Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        script = self.generate_script(correlation_id)
        path.write_text(script, encoding="utf-8")
        return path

    @staticmethod
    def _sanitize(value: str) -> str:
        """Очистить строку для использования в имени файла."""
        return re.sub(r"[^\w\-_.]", "_", value)
