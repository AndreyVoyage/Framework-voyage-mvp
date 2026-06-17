"""Evaluator — оценка качества кода, produced by агентом."""

from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

from voyage_framework.core.models import EvaluationResult, NodeResult, SecurityPolicy
from voyage_framework.improvement.golden_dataset import GoldenDataset, GoldenSolution
from voyage_framework.security.sandbox import SecureExecutor


def _resolve_tool(name: str) -> str:
    """Найти исполняемый файл инструмента в текущем окружении Python."""
    scripts = Path(sys.executable).parent
    if sys.platform == "win32":
        candidate = scripts / f"{name}.exe"
    else:
        candidate = scripts / name
    if candidate.exists():
        return str(candidate)
    found = shutil.which(name)
    return found if found else name


class Evaluator:
    """Оценивает качество кода агента."""

    def __init__(
        self,
        project_root: Path | str = ".",
        executor: SecureExecutor | None = None,
        golden_dataset: GoldenDataset | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.ruff_cmd = _resolve_tool("ruff")
        self.mypy_cmd = _resolve_tool("mypy")

        if executor is None:
            policy = SecurityPolicy()
            policy.allowed_commands.add(self.ruff_cmd)
            policy.allowed_commands.add(self.mypy_cmd)
            executor = SecureExecutor(
                policy=policy,
                project_root=self.project_root,
            )
        self.executor = executor
        self.golden_dataset = golden_dataset or GoldenDataset()

    async def evaluate_code(
        self,
        code: str,
        language: str = "python",
    ) -> EvaluationResult:
        """Оценить отдельный snippet кода."""
        if language != "python":
            return EvaluationResult(
                syntax_valid=True,
                details={"reason": "Only Python evaluation is supported in MVP"},
            )

        syntax_valid = self._check_syntax(code)

        # Создаём временный файл внутри project_root, чтобы path traversal
        # SecureExecutor не блокировал ruff/mypy.
        self.project_root.mkdir(parents=True, exist_ok=True)
        tmp_path = self.project_root / f".voyage_eval_{id(code)}.py"
        tmp_path.write_text(code, encoding="utf-8")

        try:
            style_score = await self._run_ruff(tmp_path)
            type_score = await self._run_mypy(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        test_score = 1.0  # Для standalone snippet pytest не применим

        overall = (
            0.2 * float(syntax_valid) + 0.3 * style_score + 0.3 * type_score + 0.2 * test_score
        )

        return EvaluationResult(
            syntax_valid=syntax_valid,
            style_score=style_score,
            type_score=type_score,
            test_score=test_score,
            overall_score=round(overall, 2),
            details={
                "language": language,
                "lines": len(code.splitlines()),
            },
        )

    async def evaluate_task(self, node_result: NodeResult) -> EvaluationResult:
        """Оценить результат выполнения задачи агентом."""
        if not node_result.state.results:
            return EvaluationResult(
                syntax_valid=True,
                details={"reason": "No tool results to evaluate"},
            )

        # Оцениваем только stdout/stderr последнего шага как кода
        last_step = node_result.state.results[-1]
        candidate = last_step.stdout or ""
        if len(candidate) < 10:
            candidate = node_result.state.task

        return await self.evaluate_code(candidate)

    def compare_with_golden(
        self,
        produced: str,
        golden: GoldenSolution,
    ) -> float:
        """Сравнить produced code с эталонным решением."""
        return self.golden_dataset.compare(produced, golden.reference_code)

    def _check_syntax(self, code: str) -> bool:
        """Проверить синтаксис Python через ast.parse."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    async def _run_ruff(self, path: Path) -> float:
        """Запустить ruff check и вернуть score 0-1."""
        result = await self.executor.execute([self.ruff_cmd, "check", "--quiet", str(path)])
        return 1.0 if result.success else 0.0

    async def _run_mypy(self, path: Path) -> float:
        """Запустить mypy и вернуть score 0-1."""
        result = await self.executor.execute(
            [
                self.mypy_cmd,
                "--ignore-missing-imports",
                "--no-error-summary",
                str(path),
            ]
        )
        return 1.0 if result.success else 0.0
