"""Shared fixtures for Voyage Framework tests."""

from __future__ import annotations

import pytest

from voyage_framework.core.event_engine import EventEngine


@pytest.fixture
def tmp_engine(tmp_path):
    """Свежий EventEngine во временной директории."""
    return EventEngine(db_path=tmp_path / "events.db")
