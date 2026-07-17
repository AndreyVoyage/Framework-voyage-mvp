"""Tests for frozen numeric limits and rate limiter."""

from __future__ import annotations

from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.limits import RateLimiter, RateLimitExceededError


class TestLimitsDefaults:
    def test_all_constants_match_plan(self):
        limits = Limits()
        assert limits.max_request_bytes == 64 * 1024
        assert limits.max_response_bytes == 1 * 1024 * 1024
        assert limits.max_report_bytes == 1 * 1024 * 1024
        assert limits.max_git_output_bytes == 1 * 1024 * 1024
        assert limits.max_task_rows == 100
        assert limits.max_offset == 10_000
        assert limits.git_timeout_seconds == 30.0
        assert limits.sqlite_timeout_seconds == 5.0
        assert limits.request_timeout_seconds == 60.0
        assert limits.max_concurrent_requests == 1
        assert limits.requests_per_minute == 60
        assert limits.max_audit_event_bytes == 64 * 1024
        assert limits.max_warnings_errors == 50
        assert limits.max_task_id_length == 100


class TestRateLimiter:
    def test_allows_within_limit(self):
        clock = [0.0]

        def fake_clock():
            return clock[0]

        limiter = RateLimiter(requests_per_minute=60, clock=fake_clock)
        for _ in range(60):
            limiter.check(clock=fake_clock)
        # next should fail
        with __import__("pytest").raises(RateLimitExceededError):
            limiter.check(clock=fake_clock)

    def test_refills_over_time(self):
        clock = [0.0]

        def fake_clock():
            return clock[0]

        limiter = RateLimiter(requests_per_minute=10, clock=fake_clock)
        # exhaust
        for _ in range(10):
            limiter.check(clock=fake_clock)
        # advance 6 seconds (1 token per 6s at 10/min)
        clock[0] = 6.0
        limiter.check(clock=fake_clock)  # should succeed

    def test_retry_after_seconds(self):
        limiter = RateLimiter(requests_per_minute=10)
        for _ in range(10):
            limiter.check()
        with __import__("pytest").raises(RateLimitExceededError) as exc_info:
            limiter.check()
        assert exc_info.value.retry_after_seconds > 0

    def test_state_reflects_bucket(self):
        limiter = RateLimiter(requests_per_minute=60)
        assert limiter.state.limit == 60
        assert limiter.state.tokens == 60.0

    def test_limits_immutable(self):
        limits = Limits()
        with __import__("pytest").raises(Exception):
            limits.max_task_rows = 200  # type: ignore[misc]
