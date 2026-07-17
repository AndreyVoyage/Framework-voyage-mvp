"""Frozen numeric limits and in-memory single-session rate limiter.

No background threads, no network, no persistent state.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """Snapshot of the current rate-limit window."""

    tokens: float
    last_refill: float
    limit: int
    window_seconds: float


class RateLimitExceededError(Exception):
    """Raised when a request exceeds the rate limit."""

    def __init__(self, retry_after_seconds: float) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limit exceeded; retry after {retry_after_seconds:.1f}s")


class RateLimiter:
    """Token-bucket rate limiter for a single session."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._limit = max(requests_per_minute, 1)
        self._window = 60.0
        self._tokens = float(self._limit)
        self._last_refill = (clock or time.monotonic)()

    def _refill(self, now: float) -> None:
        elapsed = now - self._last_refill
        self._tokens = min(
            self._limit,
            self._tokens + elapsed * (self._limit / self._window),
        )
        self._last_refill = now

    def check(self, *, clock: Callable[[], float] | None = None) -> None:
        """Consume one token; raise RateLimitExceeded if none available."""
        now = (clock or time.monotonic)()
        self._refill(now)
        if self._tokens < 1.0:
            retry = self._window / self._limit
            raise RateLimitExceededError(retry_after_seconds=retry)
        self._tokens -= 1.0

    @property
    def state(self) -> RateLimitState:
        now = time.monotonic()
        self._refill(now)
        return RateLimitState(
            tokens=self._tokens,
            last_refill=self._last_refill,
            limit=self._limit,
            window_seconds=self._window,
        )
