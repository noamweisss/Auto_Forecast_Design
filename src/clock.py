"""Application clock contracts anchored to Israel's civil timezone."""

from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo


ISRAEL_TIMEZONE = ZoneInfo("Asia/Jerusalem")


class Clock(Protocol):
    """The smallest clock interface application code needs."""

    def now(self) -> datetime:
        """Return the current aware datetime."""
        ...


class SystemClock:
    """Read the real current time in Israel."""

    def now(self) -> datetime:
        return datetime.now(ISRAEL_TIMEZONE)
