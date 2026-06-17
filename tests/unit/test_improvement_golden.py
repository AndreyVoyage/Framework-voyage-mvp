"""Unit tests for GoldenDataset."""

from pathlib import Path

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import EventType
from voyage_framework.improvement.golden_dataset import GoldenDataset, GoldenSolution


class TestGoldenDataset:
    def test_add_solution(self, tmp_path: Path) -> None:
        dataset = GoldenDataset(dataset_path=tmp_path / "golden.jsonl")
        solution = GoldenSolution(
            task_pattern="authenticate user",
            reference_code="def login(user, password): ...",
            language="python",
        )

        added = dataset.add_solution(solution)

        assert added.id == solution.id
        assert dataset.count() == 1

    def test_find_match(self, tmp_path: Path) -> None:
        dataset = GoldenDataset(dataset_path=tmp_path / "golden.jsonl")
        dataset.add_solution(GoldenSolution(
            task_pattern="login user",
            reference_code="def login(): pass",
        ))
        dataset.add_solution(GoldenSolution(
            task_pattern="logout user",
            reference_code="def logout(): pass",
        ))

        match = dataset.find_match("how to login", threshold=0.3)

        assert match is not None
        assert "login" in match.task_pattern.lower()

    def test_compare_identical(self) -> None:
        dataset = GoldenDataset()
        score = dataset.compare("def foo(): pass", "def foo(): pass")

        assert score == 1.0

    def test_compare_different(self) -> None:
        dataset = GoldenDataset()
        score = dataset.compare("def foo(): pass", "class Bar: pass")

        assert 0.0 <= score < 1.0

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "golden.jsonl"
        dataset = GoldenDataset(dataset_path=path)
        dataset.add_solution(GoldenSolution(task_pattern="test", reference_code="x = 1"))

        dataset2 = GoldenDataset(dataset_path=path)

        assert dataset2.count() == 1
        assert dataset2.list_solutions()[0].task_pattern == "test"

    def test_find_match_logs_event(self, tmp_path: Path) -> None:
        db = tmp_path / "events.db"
        engine = EventEngine(db_path=db)
        dataset = GoldenDataset(engine=engine, dataset_path=tmp_path / "golden.jsonl")
        dataset.add_solution(GoldenSolution(
            task_pattern="login", reference_code="def login(): pass",
        ))

        dataset.find_match("login user", threshold=0.3)

        events = engine.get_events(event_type=EventType.GOLDEN_MATCH_FOUND)
        assert len(events) == 1
