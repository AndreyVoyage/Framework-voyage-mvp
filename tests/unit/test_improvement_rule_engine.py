"""Unit tests for RuleEngine."""

from pathlib import Path

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import ToolResult
from voyage_framework.improvement.rule_engine import RuleEngine


class TestRuleEngine:
    def test_extract_pattern_python_error(self) -> None:
        engine = RuleEngine()
        text = "NameError: name 'foo' is not defined"

        pattern = engine.extract_pattern(text)

        assert "NameError" in pattern

    def test_analyze_error_tool_result(self, tmp_path: Path) -> None:
        db = tmp_path / "events.db"
        engine = RuleEngine(engine=EventEngine(db_path=db))
        result = ToolResult(success=False, stderr="SyntaxError: invalid syntax")

        rule = engine.analyze_error(result)

        assert rule is not None
        assert "SyntaxError" in rule.pattern

    def test_deduplicate(self) -> None:
        engine = RuleEngine()
        result = ToolResult(success=False, stderr="NameError: name 'foo' is not defined")

        rule1 = engine.analyze_error(result)
        rule2 = engine.analyze_error(result)

        assert rule1 is not None
        assert rule2 is None

    def test_save_and_load_rules(self, tmp_path: Path) -> None:
        path = tmp_path / "rules.jsonl"
        engine = RuleEngine(rules_path=path)
        engine.analyze_error(ToolResult(success=False, stderr="TypeError"))

        engine2 = RuleEngine(rules_path=path)

        assert len(engine2.get_rules()) == 1

    def test_get_rules_filtered(self) -> None:
        engine = RuleEngine()
        rule = engine.analyze_error(
            ToolResult(success=False, stderr="ImportError"),
            project_id="proj-a",
        )

        assert rule is not None
        assert len(engine.get_rules()) == 1
