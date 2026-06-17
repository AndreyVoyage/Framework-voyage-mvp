"""Golden Dataset — хранение эталонных решений для Self-Improving Engine."""

from __future__ import annotations

import difflib
from pathlib import Path

from pydantic import BaseModel, Field
from ulid import ULID

from voyage_framework.core.event_engine import EventEngine
from voyage_framework.core.models import Event, EventType
from voyage_framework.core.storage import atomic_write


class GoldenSolution(BaseModel):
    """Эталонное решение задачи."""

    id: str = Field(default_factory=lambda: str(ULID()))
    task_pattern: str = Field(..., description="Паттерн задачи для fuzzy matching")
    reference_code: str = Field(..., description="Эталонный код")
    explanation: str = Field(default="", description="Пояснение к решению")
    language: str = Field(default="python", description="Язык кода")
    tags: list[str] = Field(default_factory=list, description="Теги")
    complexity_score: float = Field(default=0.0, ge=0.0, le=1.0)


class GoldenDataset:
    """Набор эталонных решений с fuzzy поиском.

    Использует чисто-Python difflib вместо rapidfuzz для кросс-платформенности.
    """

    def __init__(
        self,
        engine: EventEngine | None = None,
        dataset_path: Path | str | None = None,
    ) -> None:
        self.engine = engine
        self.dataset_path = Path(dataset_path) if dataset_path else None
        self._solutions: dict[str, GoldenSolution] = {}

        if self.dataset_path:
            self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def add_solution(self, solution: GoldenSolution) -> GoldenSolution:
        """Добавить эталонное решение в датасет."""
        solution.complexity_score = self._complexity_score(solution.reference_code)
        self._solutions[solution.id] = solution
        self._save()
        return solution

    def find_match(
        self,
        task: str,
        threshold: float = 0.6,
    ) -> GoldenSolution | None:
        """Найти ближайшее эталонное решение по task_pattern (fuzzy match).

        Args:
            task: Текст задачи.
            threshold: Порог схожести (0-1).

        Returns:
            GoldenSolution | None: лучшее совпадение или None.
        """
        if not self._solutions:
            return None

        best_match: GoldenSolution | None = None
        best_score = threshold
        for solution in self._solutions.values():
            score = self._similarity(task.lower(), solution.task_pattern.lower())
            if score > best_score:
                best_score = score
                best_match = solution

        if best_match and self.engine:
            self.engine.append(
                Event(
                    event_type=EventType.GOLDEN_MATCH_FOUND,
                    payload={
                        "solution_id": best_match.id,
                        "task": task,
                        "score": best_score,
                    },
                )
            )

        return best_match

    def compare(self, produced: str, reference: str) -> float:
        """Сравнить produced code с эталоном, вернуть similarity score 0-1."""
        if not produced and not reference:
            return 1.0
        if not produced or not reference:
            return 0.0
        return self._similarity(produced, reference)

    def save(self) -> None:
        """Сохранить датасет на диск."""
        if not self.dataset_path:
            return
        lines = [solution.model_dump_json() for solution in self._solutions.values()]
        atomic_write(self.dataset_path, "\n".join(lines) + "\n" if lines else "")

    def load(self) -> None:
        """Загрузить датасет с диска."""
        self._load()

    def count(self) -> int:
        """Количество эталонных решений."""
        return len(self._solutions)

    def list_solutions(self) -> list[GoldenSolution]:
        """Вернуть список всех решений."""
        return list(self._solutions.values())

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Fuzzy similarity через чисто-Python difflib."""
        return difflib.SequenceMatcher(None, a, b).ratio()

    def _load(self) -> None:
        """Внутренняя загрузка из JSONL."""
        if not self.dataset_path or not self.dataset_path.exists():
            return

        with open(self.dataset_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                solution = GoldenSolution.model_validate_json(line)
                self._solutions[solution.id] = solution

    def _save(self) -> None:
        """Внутреннее сохранение."""
        self.save()

    @classmethod
    def _complexity_score(cls, code: str) -> float:
        """Примитивная оценка сложности по количеству токенов (0-1)."""
        tokens = len(code.split())
        # Нормализация: 50 токенов = 0.05, 1000+ = 1.0
        score = min(1.0, max(0.0, tokens / 1000.0))
        return round(score, 2)
