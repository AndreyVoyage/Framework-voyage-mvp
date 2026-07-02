"""Architecture boundary guard tests.

Fast, read-only guards against Framework/Narrative-adapter re-coupling.
These do not call git and do not touch any external repo.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = PROJECT_ROOT / "voyage_framework" / "core"
CLI_FILE = PROJECT_ROOT / "voyage_framework" / "cli.py"
REPORT_VALIDATOR_FILE = CORE_DIR / "report_validator.py"
REPO_CONTROL_ADAPTER_FILE = CORE_DIR / "repo_control_adapter.py"

_FORBIDDEN_CONTRACT_TERMS: tuple[str, ...] = (
    "narrative",
    "renpy",
    "scene",
    "arc",
    "persona",
    "scenario",
    "sc_",
    "story",
    "voyage-narrative",
)


def _imports_module(tree: ast.Module, target: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[-1] == target for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".")[-1] == target
        ):
            return True
    return False


def _top_level_imports_module(tree: ast.Module, target: str) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[-1] == target for alias in node.names
        ):
            return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.split(".")[-1] == target
        ):
            return True
    return False


class TestCoreImportGuard:
    def test_no_other_core_module_imports_narrative_adapter(self) -> None:
        offenders: list[str] = []
        for path in sorted(CORE_DIR.glob("*.py")):
            if path.name == "narrative_adapter.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if _imports_module(tree, "narrative_adapter"):
                offenders.append(path.name)
        assert offenders == []


class TestCliLazyImportGuard:
    def test_cli_top_level_does_not_import_narrative_adapter(self) -> None:
        tree = ast.parse(CLI_FILE.read_text(encoding="utf-8"), filename=str(CLI_FILE))
        assert _top_level_imports_module(tree, "narrative_adapter") is False

    def test_cli_may_still_reference_narrative_adapter_inside_functions(self) -> None:
        tree = ast.parse(CLI_FILE.read_text(encoding="utf-8"), filename=str(CLI_FILE))
        assert _imports_module(tree, "narrative_adapter") is True


class TestReportValidatorPolicyGuard:
    def test_report_validator_does_not_import_narrative_adapter(self) -> None:
        tree = ast.parse(
            REPORT_VALIDATOR_FILE.read_text(encoding="utf-8"),
            filename=str(REPORT_VALIDATOR_FILE),
        )
        assert _imports_module(tree, "narrative_adapter") is False

    def test_forbidden_by_role_is_plain_data(self) -> None:
        from voyage_framework.core.report_validator import FORBIDDEN_BY_ROLE

        assert isinstance(FORBIDDEN_BY_ROLE, dict)
        for role, patterns in FORBIDDEN_BY_ROLE.items():
            assert isinstance(role, str)
            assert isinstance(patterns, tuple)
            assert all(isinstance(pattern, str) for pattern in patterns)
        # This guard does not forbid the existing "narrative" role key;
        # it only asserts the policy stays data, not imported behavior.
        assert "narrative" in FORBIDDEN_BY_ROLE


class TestContractGenericityGuard:
    def test_repo_control_adapter_has_no_narrative_specific_terms(self) -> None:
        text = REPO_CONTROL_ADAPTER_FILE.read_text(encoding="utf-8").lower()
        hits = [term for term in _FORBIDDEN_CONTRACT_TERMS if term in text]
        assert hits == []
