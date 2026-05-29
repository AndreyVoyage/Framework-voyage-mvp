"""Unit tests for storage module."""

import pytest
import tempfile
from pathlib import Path
from voyage_framework.core.storage import (
    atomic_write, append_entry, parse_frontmatter_entries,
    journal_rotate, load_jsonl, append_jsonl,
)


class TestAtomicWrite:
    def test_atomic_write_creates_file(self, tmp_path):
        path = tmp_path / "test.txt"
        atomic_write(path, "hello world")
        assert path.exists()
        assert path.read_text() == "hello world"

    def test_atomic_write_overwrites(self, tmp_path):
        path = tmp_path / "test.txt"
        atomic_write(path, "first")
        atomic_write(path, "second")
        assert path.read_text() == "second"

    def test_atomic_write_creates_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "test.txt"
        atomic_write(path, "content")
        assert path.exists()


class TestAppendEntry:
    def test_append_frontmatter(self, tmp_path):
        path = tmp_path / "journal.md"
        append_entry(path, "First entry", {"type": "event"})
        append_entry(path, "Second entry", {"type": "log"})

        entries = parse_frontmatter_entries(path)
        assert len(entries) == 2
        assert entries[0]["frontmatter"]["type"] == "event"
        assert entries[0]["content"] == "First entry"

    def test_parse_empty_file(self, tmp_path):
        path = tmp_path / "empty.md"
        entries = parse_frontmatter_entries(path)
        assert entries == []


class TestJournalRotate:
    def test_rotation(self, tmp_path):
        path = tmp_path / "journal.jsonl"
        path.write_text("x" * 100)
        journal_rotate(path, max_size_bytes=50, max_files=3)
        assert not path.exists()
        assert (tmp_path / "journal.jsonl.1").exists()

    def test_no_rotation_small_file(self, tmp_path):
        path = tmp_path / "journal.jsonl"
        path.write_text("small")
        journal_rotate(path, max_size_bytes=1000)
        assert path.exists()


class TestJsonl:
    def test_append_and_load(self, tmp_path):
        path = tmp_path / "data.jsonl"
        append_jsonl(path, {"a": 1})
        append_jsonl(path, {"b": 2})

        entries = load_jsonl(path)
        assert len(entries) == 2
        assert entries[0]["a"] == 1
        assert entries[1]["b"] == 2

    def test_load_missing_file(self, tmp_path):
        path = tmp_path / "missing.jsonl"
        entries = load_jsonl(path)
        assert entries == []
