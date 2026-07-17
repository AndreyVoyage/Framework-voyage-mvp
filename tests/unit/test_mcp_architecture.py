"""AST-enforced architecture boundaries for ``voyage_framework.mcp_read``."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_MCP_READ_DIR = Path(__file__).resolve().parents[2] / "voyage_framework" / "mcp_read"
_SERVICES = {"task_read.py", "git_read.py", "report_read.py"}
_GLOBAL_FORBIDDEN = (
    "voyage_framework.core.task_engine",
    "voyage_framework.core.task_models",
    "voyage_framework.core.event_engine",
    "voyage_framework.core._git_utils",
    "voyage_framework.core.report_validator",
    "voyage_framework.cli",
    "voyage_framework.agents",
    "voyage_framework.langgraph_tools",
    "socket",
    "http",
    "urllib",
    "requests",
    "mcp",
)
_ALLOWED_CORE_IMPORT = "voyage_framework.core.forbidden_paths"


def _python_files() -> list[Path]:
    return sorted(_MCP_READ_DIR.rglob("*.py"))


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imports(path: Path) -> list[tuple[str, list[str]]]:
    found: list[tuple[str, list[str]]] = []
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            found.extend((alias.name, []) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, [alias.name for alias in node.names]))
    return found


def test_package_exists() -> None:
    import voyage_framework.mcp_read  # noqa: F401


def test_global_forbidden_imports() -> None:
    for path in _python_files():
        for module, _names in _imports(path):
            for forbidden in _GLOBAL_FORBIDDEN:
                assert not module.startswith(forbidden), f"{path.name}: forbidden {module}"


def test_only_public_forbidden_paths_core_import() -> None:
    for path in _python_files():
        for module, names in _imports(path):
            if module.startswith("voyage_framework.core."):
                assert module == _ALLOWED_CORE_IMPORT
            if module.startswith(("voyage_framework.core", "voyage_framework.mcp_read")):
                assert not any(name.startswith("_") for name in names), (
                    f"{path.name}: private import from {module}"
                )


def test_subprocess_and_threading_only_in_git_reader() -> None:
    for path in _python_files():
        modules = {module for module, _names in _imports(path)}
        if modules & {"subprocess", "threading"}:
            assert path.name == "git_read.py"


def test_service_separation() -> None:
    for path in _python_files():
        if path.name not in _SERVICES:
            continue
        modules = {module for module, _names in _imports(path)}
        assert "voyage_framework.mcp_read.audit" not in modules
        assert "voyage_framework.mcp_read.identity" not in modules
        if path.name == "task_read.py":
            assert not modules & {
                "voyage_framework.mcp_read.git_read",
                "voyage_framework.mcp_read.report_read",
            }
        if path.name == "git_read.py":
            assert not modules & {
                "voyage_framework.mcp_read.task_read",
                "voyage_framework.mcp_read.report_read",
            }
        if path.name == "report_read.py":
            assert "voyage_framework.mcp_read.task_read" not in modules


def test_approved_services_exist_without_server_surface() -> None:
    names = {path.name for path in _MCP_READ_DIR.iterdir() if path.is_file()}
    assert names >= _SERVICES
    assert not names & {"server.py", "tools.py", "registry.py", "service_registry.py"}


def test_no_shell_true_or_dynamic_process_command() -> None:
    git_tree = _tree(_MCP_READ_DIR / "git_read.py")
    for node in ast.walk(git_tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                assert not (
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                )


def test_git_command_literals_exclude_network_and_mutation() -> None:
    banned = {
        "fetch",
        "pull",
        "push",
        "ls-remote",
        "remote",
        "commit",
        "checkout",
        "switch",
        "reset",
        "clean",
        "restore",
        "add",
        "-C",
        "--git-dir",
        "--work-tree",
    }
    tree = _tree(_MCP_READ_DIR / "git_read.py")
    values = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)}
    assert not banned & values


def test_package_import_no_side_effects() -> None:
    module = importlib.import_module("voyage_framework.mcp_read")
    assert hasattr(module, "MCP_READ_SCHEMA_VERSION")


def test_no_eval_exec_or_mcp_sdk() -> None:
    for path in _python_files():
        tree = _tree(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec"}
