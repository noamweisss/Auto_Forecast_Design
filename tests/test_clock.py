"""Contracts for the Israel-aware application clock."""

from datetime import datetime

from src.clock import ISRAEL_TIMEZONE, Clock, SystemClock


def test_system_clock_returns_aware_jerusalem_time():
    now = SystemClock().now()

    assert now.tzinfo is ISRAEL_TIMEZONE
    assert now.utcoffset() is not None


def test_clock_protocol_only_requires_now():
    class FixedClock:
        def now(self) -> datetime:
            return datetime(2026, 7, 20, 9, 30, tzinfo=ISRAEL_TIMEZONE)

    clock: Clock = FixedClock()

    assert clock.now().date().isoformat() == "2026-07-20"
