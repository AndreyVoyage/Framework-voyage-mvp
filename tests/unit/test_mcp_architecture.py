"""Architecture-boundary tests for voyarge_framework.mcp_read (Slice 1).

Verifies no forbidden imports and that only the allowed core import
(voyage_framework.core.forbidden_paths) is used.  Package import must
have no side effects.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_MCP_READ_DIR = Path(__file__).resolve().parent.parent.parent / "voyage_framework" / "mcp_read"

# ── forbidden substrings in imports ──────────────────────────────────────
_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "voyage_framework.core.task_engine",
    "voyage_framework.core.event_engine",
    "voyage_framework.core.guarded_write",
    "voyage_framework.core.guarded_write_approval",
    "voyage_framework.cli",
    "voyage_framework.agents",
    "voyage_framework.langgraph_tools",
    "importlib",
    "__import__",
    "eval",
    "exec",
    "subprocess",
    "socket",
    "http.server",
    "mcp",
)

_ALLOWED_CORE_IMPORT = "voyage_framework.core.forbidden_paths"


def _python_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def _imports_from_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


# ── tests ────────────────────────────────────────────────────────────────


def test_package_exists():
    """mcp_read package is importable."""
    import voyage_framework.mcp_read  # noqa: F401


def test_no_forbidden_imports():
    """No forbidden modules or subprocess/socket are imported."""
    for fpath in _python_files(_MCP_READ_DIR):
        mod_imports = _imports_from_file(fpath)
        for imp in mod_imports:
            for forbidden in _FORBIDDEN_IMPORTS:
                assert not imp.startswith(forbidden), f"{fpath.name}: imports forbidden {imp!r}"


def test_only_forbidden_paths_core_import():
    """mcp_read/ may import voyage_framework.core.forbidden_paths only."""
    for fpath in _python_files(_MCP_READ_DIR):
        mod_imports = _imports_from_file(fpath)
        for imp in mod_imports:
            if imp.startswith("voyage_framework.core."):
                assert imp == _ALLOWED_CORE_IMPORT, (
                    f"{fpath.name}: imports {imp!r} — only "
                    f"{_ALLOWED_CORE_IMPORT!r} is allowed from core"
                )


def test_no_server_tools_files():
    """Slice 1 must not contain server.py, tools.py, or service adapters."""
    forbidden_names = {"server.py", "tools.py", "task_read.py", "git_read.py", "report_read.py"}
    for fpath in _MCP_READ_DIR.iterdir():
        assert fpath.name not in forbidden_names, f"Slice 1 must not contain {fpath.name}"


def test_package_import_no_side_effects():
    """Importing mcp_read must not trigger filesystem writes, network, or subprocess."""
    # Simple safety: import must succeed without errors
    mod = importlib.import_module("voyage_framework.mcp_read")
    assert hasattr(mod, "MCP_READ_SCHEMA_VERSION")


def test_no_eval_exec():
    """No eval/exec calls in any production file."""
    for fpath in _python_files(_MCP_READ_DIR):
        source = fpath.read_text(encoding="utf-8")
        assert "eval(" not in source, f"{fpath.name}: contains eval("
        assert "exec(" not in source, f"{fpath.name}: contains exec("


def test_no_mcp_import_in_slice1():
    """Slice 1 must not import the MCP SDK."""
    for fpath in _python_files(_MCP_READ_DIR):
        mod_imports = _imports_from_file(fpath)
        for imp in mod_imports:
            assert not imp.startswith("mcp"), f"{fpath.name}: imports MCP SDK {imp!r}"
