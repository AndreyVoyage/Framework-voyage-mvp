"""Rule Engine — генерация правил из ошибок агента."""

from __future__ import annotations

import re
from pathlib import Path

from ulid import ULID

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import (
    Event,
    EventType,
    NodeResult,
    RuleSuggestion,
    TaskSpec,
    ToolResult,
)
from voyage_framework.core.storage import atomic_write


class RuleEngine:
    """Анализирует ошибки агента и генерирует RuleSuggestion."""

    DEFAULT_CATEGORIES = {
        "SyntaxError": "style",
        "ImportError": "ops",
        "ModuleNotFoundError": "ops",
        "TypeError": "style",
        "AttributeError": "style",
        "NameError": "style",
        "mypy": "style",
        "ruff": "style",
        "pytest": "ops",
    }

    def __init__(
        self,
        engine: EventEngine | None = None,
        rules_path: Path | str | None = None,
    ) -> None:
        self.engine = engine
        self.rules_path = Path(rules_path) if rules_path else None
        self._rules: dict[str, RuleSuggestion] = {}

        if self.rules_path:
            self.rules_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def analyze_error(
        self,
        result: ToolResult | NodeResult,
        project_id: str = "default",
    ) -> RuleSuggestion | None:
        """Проанализировать ошибку и сгенерировать правило."""
        error_text = ""
        source_event_id = ""

        if isinstance(result, ToolResult):
            error_text = result.stderr or result.stdout or ""
            source_event_id = ""
        elif isinstance(result, NodeResult):
            failed = [r for r in result.state.results if not r.success]
            error_text = "\n".join(r.stderr for r in failed if r.stderr)
            source_event_id = result.state.agent_id

        if not error_text:
            return None

        pattern = self.extract_pattern(error_text)
        category = self._detect_category(error_text)
        severity = "must" if "Error" in error_text else "should"

        rule = RuleSuggestion(
            rule_id=str(ULID()),
            pattern=pattern,
            rule_text=f"Avoid pattern: {pattern}",
            severity=severity,  # type: ignore[arg-type]
            category=category,  # type: ignore[arg-type]
            source_event_id=source_event_id,
            confidence=min(1.0, len(error_text) / 500.0),
        )

        if self.deduplicate(rule):
            return None

        self._rules[rule.rule_id] = rule
        self._save()

        if self.engine:
            self.engine.append(
                Event(
                    event_type=EventType.RULE_SUGGESTED,
                    payload={
                        "rule_id": rule.rule_id,
                        "pattern": rule.pattern,
                        "category": rule.category,
                        "severity": rule.severity,
                        "project_id": project_id,
                    },
                    project_id=project_id,
                )
            )

        return rule

    def extract_pattern(self, text: str) -> str:
        """Извлечь ключевой паттерн ошибки."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return "unknown_error"

        first_line = lines[0]

        # Искать конкретные типы ошибок Python
        match = re.search(r"(\w+Error):?\s*(.*)", first_line)
        if match:
            return f"{match.group(1)}: {match.group(2)[:60]}".strip()

        # Искать mypy/ruff messages
        match = re.search(r"error:\s*(.+)", first_line)
        if match:
            return f"type_error: {match.group(1)[:60]}"

        # Fallback: первые 80 символов
        return first_line[:80]

    def deduplicate(self, rule: RuleSuggestion) -> bool:
        """Проверить, есть ли уже похожее правило."""
        rule_hash = rule.hash()
        return any(existing.hash() == rule_hash for existing in self._rules.values())

    def apply_rules(
        self,
        task_spec: TaskSpec,
        project_id: str = "default",
    ) -> TaskSpec:
        """Дополнить TaskSpec накопленными правилами проекта."""
        project_rules = self.get_rules(project_id)
        rule_texts = [r.rule_text for r in project_rules]
        task_spec.rules.extend(rule_texts)
        return task_spec

    def get_rules(self, project_id: str | None = None) -> list[RuleSuggestion]:
        """Получить правила, опционально отфильтрованные по project_id."""
        rules = list(self._rules.values())
        if project_id:
            rules = [
                r
                for r in rules
                if not r.source_event_id or r.source_event_id.startswith(project_id)
            ]
        return rules

    def save_rules(self) -> None:
        """Сохранить правила на диск."""
        if not self.rules_path:
            return
        lines = [rule.model_dump_json() for rule in self._rules.values()]
        atomic_write(self.rules_path, "\n".join(lines) + "\n" if lines else "")

    def load_rules(self) -> None:
        """Загрузить правила с диска."""
        self._load()

    def _load(self) -> None:
        """Внутренняя загрузка правил."""
        if not self.rules_path or not self.rules_path.exists():
            return

        with open(self.rules_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rule = RuleSuggestion.model_validate_json(line)
                self._rules[rule.rule_id] = rule

    def _save(self) -> None:
        """Внутреннее сохранение."""
        self.save_rules()

    def _detect_category(self, error_text: str) -> str:
        """Определить категорию ошибки."""
        lowered = error_text.lower()
        for key, category in self.DEFAULT_CATEGORIES.items():
            if key.lower() in lowered:
                return category
        return "ops"
