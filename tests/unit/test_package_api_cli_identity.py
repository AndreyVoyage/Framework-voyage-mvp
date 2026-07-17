"""Smoke tests for package public identity and CLI help compatibility.

Covers Phase 25 requirements:
- canonical Project Knowledge OS identity in package docstring;
- legacy/deprecated/non-canonical wording for runtime/graph surfaces;
- CLI help does not promote AI agent/runtime/orchestration identity;
- CLI help does not create runtime pollution.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

LEGACY_WORDING = ("legacy", "deprecated", "non-canonical", "compatibility")
FORBIDDEN_IDENTITY = (
    "AI-native",
    "AI Agent Framework",
    "runtime orchestration framework",
    "Voyage AI Dev Framework v4.0",
)

# Frozen expected public API surface for voyage_framework/__init__.py, per
# MCP-READ-01-PACKAGE-INIT-CORRECTION-REPORT.md. Ground truth for what the
# package must still expose, independent of whatever __all__ happens to
# contain at runtime.
_EXPECTED_ALL = [
    "Event",
    "AgentState",
    "ToolResult",
    "ProjectContext",
    "EventEngine",
    "SecureExecutor",
    "SecurityPolicy",
    "TaskGenerator",
    "SemanticStore",
    "CodeSearch",
    "ASTParser",
    "CodeIndexer",
    "GoldenDataset",
    "GoldenSolution",
    "RuleEngine",
    "Evaluator",
    "FeedbackLoop",
    "ProcessJournal",
    "ReplayGenerator",
    "DecisionLog",
    "TutorialDraft",
    "TutorialGenerator",
    "DocsBuilder",
    "VoyageGraphBuilder",
    "MermaidExporter",
    "LangGraphRuntime",
]
_OPTIONAL_LAZY_NAMES = {"ASTParser", "CodeIndexer"}
_REQUIRED_LAZY_NAMES = {
    "SemanticStore",
    "CodeSearch",
    "VoyageGraphBuilder",
    "MermaidExporter",
    "LangGraphRuntime",
}
_BLOCKED_MODULES_ON_PLAIN_IMPORT = (
    "voyage_framework.ast_tools",
    "voyage_framework.langgraph_tools",
    "voyage_framework.memory",
    "voyage_framework.agents.langgraph_runtime",
    "voyage_framework.agents",
    "langgraph",
    "numpy",
    "mcp",
    "mcp.server",
)


def _run_cli_help(args: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "voyage_framework.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout + result.stderr


def test_import_voyage_framework() -> None:
    import voyage_framework

    assert voyage_framework.__doc__ is not None
    doc = voyage_framework.__doc__.lower()
    for forbidden in FORBIDDEN_IDENTITY:
        term = forbidden.lower()
        # The term may appear only as an explicit negation of current identity.
        if term in doc:
            pattern = rf"not\s+(an\s+)?{re.escape(term)}"
            assert re.search(pattern, doc), f"docstring asserts current identity: {forbidden}"
    assert "project knowledge os" in doc
    assert "development memory system" in doc


def test_langgraph_runtime_is_available_as_legacy_export() -> None:
    import voyage_framework

    assert hasattr(voyage_framework, "LangGraphRuntime")


def test_cli_top_help_uses_canonical_identity() -> None:
    output = _run_cli_help(["--help"]).lower()
    for forbidden in FORBIDDEN_IDENTITY:
        assert forbidden.lower() not in output, f"top help contains: {forbidden}"
    assert "project knowledge os" in output or "development memory system" in output


def test_cli_run_help_is_legacy() -> None:
    output = _run_cli_help(["run", "--help"]).lower()
    assert "run agent" not in output or any(w in output for w in LEGACY_WORDING)
    assert any(w in output for w in LEGACY_WORDING), "run help missing legacy wording"


def test_cli_graph_help_is_legacy() -> None:
    output = _run_cli_help(["graph", "--help"]).lower()
    assert any(w in output for w in LEGACY_WORDING), "graph help missing legacy wording"


def test_cli_graph_run_help_is_legacy() -> None:
    output = _run_cli_help(["graph", "run", "--help"]).lower()
    assert any(w in output for w in LEGACY_WORDING), "graph run help missing legacy wording"


def test_cli_tasks_help_available() -> None:
    output = _run_cli_help(["tasks", "--help"])
    assert "tasks" in output.lower()


def test_cli_sync_help_available() -> None:
    output = _run_cli_help(["sync", "--help"])
    assert "sync" in output.lower()


def test_core_exports_always_available() -> None:
    import voyage_framework

    assert voyage_framework.__version__ == "4.3.0"
    assert hasattr(voyage_framework, "EventEngine")
    assert hasattr(voyage_framework, "Event")
    assert "ASTParser" in voyage_framework.__all__
    assert "CodeIndexer" in voyage_framework.__all__


def test_optional_ast_exports_are_lazy_or_extra_gated() -> None:
    import voyage_framework

    # Verify in a fresh interpreter that plain ``import voyage_framework`` does
    # not eagerly import the optional ``ast_tools`` submodule.  Using a subprocess
    # avoids contamination from other tests that legitimately use AST tools.
    script = (
        "import sys\n"
        "import voyage_framework\n"
        "print('ast_tools_loaded:', 'voyage_framework.ast_tools' in sys.modules)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ast_tools_loaded: False" in result.stdout

    try:
        import tree_sitter  # noqa: F401
    except ImportError:
        ast_extra_installed = False
    else:
        ast_extra_installed = True

    if ast_extra_installed:
        parser = voyage_framework.ASTParser
        indexer = voyage_framework.CodeIndexer
        assert parser is not None
        assert indexer is not None
        # Accessing the name should cache it in the module globals.
        assert "ASTParser" in voyage_framework.__dict__
        assert "CodeIndexer" in voyage_framework.__dict__
    else:
        with pytest.raises(AttributeError, match="optional 'ast' extra"):
            _ = voyage_framework.ASTParser
        with pytest.raises(AttributeError, match="optional 'ast' extra"):
            _ = voyage_framework.CodeIndexer


def test_plain_import_avoids_heavy_optional_modules() -> None:
    """Plain ``import voyage_framework`` must not eagerly load AST tools,
    LangGraph tooling/runtime, the semantic memory store, numpy, or the MCP
    SDK. Uses a fresh subprocess so contamination from other tests in this
    session cannot hide a regression."""
    script = (
        "import sys\n"
        "import voyage_framework\n"
        f"blocked = {_BLOCKED_MODULES_ON_PLAIN_IMPORT!r}\n"
        "loaded = sorted(name for name in blocked if name in sys.modules)\n"
        "print('loaded:', loaded)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "loaded: []" in result.stdout, result.stdout


def test_all_public_names_preserved() -> None:
    import voyage_framework

    assert len(_EXPECTED_ALL) == 26
    assert set(voyage_framework.__all__) == set(_EXPECTED_ALL)
    assert len(voyage_framework.__all__) == 26
    assert set(voyage_framework.__all__) >= _REQUIRED_LAZY_NAMES
    assert set(voyage_framework.__all__) >= _OPTIONAL_LAZY_NAMES


def test_dir_includes_lazy_names() -> None:
    import voyage_framework

    names = dir(voyage_framework)
    assert len(names) == len(set(names)), "dir() must not contain duplicate names"
    assert set(names) >= (_OPTIONAL_LAZY_NAMES | _REQUIRED_LAZY_NAMES)


def test_unknown_attribute_raises_attribute_error() -> None:
    import voyage_framework

    with pytest.raises(AttributeError):
        _ = voyage_framework.ThisNameDoesNotExist


def test_required_memory_export_resolves_and_caches() -> None:
    import voyage_framework

    store_cls = voyage_framework.SemanticStore
    assert store_cls is not None
    assert "SemanticStore" in voyage_framework.__dict__
    assert voyage_framework.SemanticStore is store_cls

    search_cls = voyage_framework.CodeSearch
    assert search_cls is not None
    assert "CodeSearch" in voyage_framework.__dict__
    assert voyage_framework.CodeSearch is search_cls


def test_required_langgraph_export_resolves_and_caches() -> None:
    # LangGraph itself is not installed in this environment; these exports
    # must still resolve because voyage_framework.langgraph_tools.graph_builder
    # already tolerates its absence internally (falls back to SimpleStateGraph).
    import voyage_framework

    builder_cls = voyage_framework.VoyageGraphBuilder
    assert builder_cls is not None
    assert "VoyageGraphBuilder" in voyage_framework.__dict__
    assert voyage_framework.VoyageGraphBuilder is builder_cls

    exporter_cls = voyage_framework.MermaidExporter
    assert exporter_cls is not None
    assert "MermaidExporter" in voyage_framework.__dict__

    runtime_cls = voyage_framework.LangGraphRuntime
    assert runtime_cls is not None
    assert "LangGraphRuntime" in voyage_framework.__dict__


def test_required_lazy_mappings_resolve_correct_symbols() -> None:
    import voyage_framework
    from voyage_framework.agents.langgraph_runtime import LangGraphRuntime
    from voyage_framework.langgraph_tools import MermaidExporter, VoyageGraphBuilder
    from voyage_framework.memory import CodeSearch, SemanticStore

    assert voyage_framework.SemanticStore is SemanticStore
    assert voyage_framework.CodeSearch is CodeSearch
    assert voyage_framework.VoyageGraphBuilder is VoyageGraphBuilder
    assert voyage_framework.MermaidExporter is MermaidExporter
    assert voyage_framework.LangGraphRuntime is LangGraphRuntime


def test_error_policy_separation_optional_vs_required(monkeypatch: pytest.MonkeyPatch) -> None:
    import voyage_framework

    # Optional-lazy: a missing/broken module maps to a feature-specific
    # AttributeError naming the optional extra.
    monkeypatch.delitem(voyage_framework.__dict__, "ASTParser", raising=False)
    monkeypatch.setitem(
        voyage_framework._OPTIONAL_EXPORTS,
        "ASTParser",
        ("voyage_framework._nonexistent_module_for_test", "ASTParser"),
    )
    with pytest.raises(AttributeError, match="optional 'ast' extra"):
        _ = voyage_framework.ASTParser

    # Optional-lazy: an unrelated failure (module imports fine, symbol is
    # missing) is NOT masked as "optional extra missing" -- it is a plain
    # AttributeError from the symbol lookup itself.
    monkeypatch.delitem(voyage_framework.__dict__, "CodeIndexer", raising=False)
    monkeypatch.setitem(voyage_framework._OPTIONAL_EXPORTS, "CodeIndexer", ("json", "CodeIndexer"))
    with pytest.raises(AttributeError) as excinfo:
        _ = voyage_framework.CodeIndexer
    assert "optional 'ast' extra" not in str(excinfo.value)

    # Required-lazy: a genuine import failure propagates unchanged, it is
    # never rewritten as a missing-optional-feature error.
    monkeypatch.delitem(voyage_framework.__dict__, "SemanticStore", raising=False)
    monkeypatch.setitem(
        voyage_framework._REQUIRED_LAZY_EXPORTS,
        "SemanticStore",
        ("voyage_framework._nonexistent_module_for_test", "SemanticStore"),
    )
    with pytest.raises(ModuleNotFoundError):
        _ = voyage_framework.SemanticStore


def test_plain_import_no_repository_mutation(tmp_path: Path) -> None:
    import os

    # voyage_framework is not installed into the interpreter (canonical import
    # strategy: resolve via the repository working directory), so the child
    # process needs the repo root on PYTHONPATH even though its *cwd* is the
    # disposable tmp_path -- that isolates any accidental relative-path writes
    # to tmp_path without changing how the package is discovered.
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ, PYTHONPATH=str(repo_root))
    result = subprocess.run(
        [sys.executable, "-c", "import voyage_framework\n"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".voyage").exists()
    assert not (tmp_path / "TASK.md").exists()
    assert not (tmp_path / "CONTEXT.json").exists()


def test_cli_help_does_not_create_runtime_pollution(tmp_path: Path) -> None:
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        for args in [
            ["--help"],
            ["tasks", "--help"],
            ["sync", "--help"],
            ["run", "--help"],
            ["graph", "--help"],
            ["graph", "run", "--help"],
        ]:
            _run_cli_help(args)

        assert not (tmp_path / ".voyage").exists()
        assert not (tmp_path / "TASK.md").exists()
        assert not (tmp_path / "CONTEXT.json").exists()
    finally:
        os.chdir(original_cwd)
