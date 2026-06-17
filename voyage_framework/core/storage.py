"""Файловое хранилище Voyage Framework.

Atomic writes, frontmatter parsing, journal rotation.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def atomic_write(path: Path, content: str) -> None:
    """Атомарная запись файла через temp + rename.

    Гарантирует, что файл либо полностью записан, либо не изменён.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise


def append_entry(path: Path, content: str, frontmatter: dict[str, Any] | None = None) -> None:
    """Добавить запись в журнал с frontmatter.

    Формат:
    ---
    timestamp: 2026-05-28T00:00:00Z
    type: event
    ---
    Содержимое записи
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fm = frontmatter or {}
    fm.setdefault("timestamp", datetime.now(UTC).isoformat())

    fm_lines = "\n".join(f"{k}: {v}" for k, v in fm.items())
    entry = f"---\n{fm_lines}\n---\n{content}\n\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)


def parse_frontmatter_entries(path: Path) -> list[dict[str, Any]]:
    """Распарсить журнал с frontmatter-записями.

    Возвращает список dict с ключами 'frontmatter' и 'content'.
    """
    path = Path(path)
    if not path.exists():
        return []

    entries = []
    with open(path, encoding="utf-8") as f:
        text = f.read()

    parts = text.split("\n---\n")
    for i in range(0, len(parts) - 1, 2):
        fm_text = parts[i].removeprefix("---\n")
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""

        fm: dict[str, Any] = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()

        entries.append({"frontmatter": fm, "content": content})

    return entries


def journal_rotate(path: Path, max_size_bytes: int = 10 * 1024 * 1024, max_files: int = 5) -> None:
    """Ротация журнала: если файл > max_size — архивировать.

    Сохраняет max_files архивов (journal.1, journal.2, ...).
    """
    path = Path(path)
    if not path.exists() or path.stat().st_size < max_size_bytes:
        return

    # Сдвинуть существующие архивы
    for i in range(max_files - 1, 0, -1):
        old = path.parent / f"{path.name}.{i}"
        new = path.parent / f"{path.name}.{i + 1}"
        if old.exists():
            if new.exists():
                new.unlink()
            old.rename(new)

    # Переименовать текущий в .1
    archive = path.parent / f"{path.name}.1"
    if archive.exists():
        archive.unlink()
    path.rename(archive)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Загрузить JSONL файл."""
    path = Path(path)
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    """Добавить строку в JSONL файл."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
