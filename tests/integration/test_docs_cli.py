"""Integration tests for the `voyage docs` CLI commands."""

from __future__ import annotations

import subprocess
import sys

CLI = [sys.executable, "-m", "voyage_framework.cli"]


def _run(args, cwd):
    return subprocess.run(
        [*CLI, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_docs_build_creates_site(tmp_path):
    result = _run(["docs", "build", "--output", "docs"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    docs = tmp_path / "docs"
    assert (docs / "index.md").exists()
    assert (docs / "_config.yml").exists()
    assert (docs / "FAQ.md").exists()


def test_docs_tutorial_creates_file(tmp_path):
    result = _run(["docs", "tutorial", "demo", "--output", "docs"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    tutorial = tmp_path / "docs" / "tutorial" / "demo.md"
    assert tutorial.exists()


def test_docs_example_creates_directory(tmp_path):
    result = _run(
        ["docs", "example", "demo", "--name", "auth-module", "--output", "docs/examples"],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    example = tmp_path / "docs" / "examples" / "auth-module"
    assert example.is_dir()
    assert (example / "TASK.md").exists()
    assert (example / "CONTEXT.json").exists()
    assert (example / "README.md").exists()


def test_docs_serve_missing_directory(tmp_path):
    result = _run(
        ["docs", "serve", "--dir", str(tmp_path / "nonexistent")],
        cwd=tmp_path,
    )
    assert result.returncode == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Directory not found" in combined
