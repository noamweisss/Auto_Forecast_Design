"""Vocabulary for immutable forecast source snapshots and provenance."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class FeedType(str, Enum):
    COUNTRY = "country"
    CITIES = "cities"


class SnapshotSource(str, Enum):
    LIVE = "live"
    ARCHIVE = "archive"
    FIXTURE = "fixture"


@dataclass(frozen=True)
class ForecastSnapshot:
    snapshot_id: str
    feed_type: FeedType
    source: SnapshotSource
    xml: str
    fetched_at: datetime
    issued_at: datetime
    forecast_dates: tuple[date, ...]

    def __post_init__(self) -> None:
        _require_nonempty_text("snapshot_id", self.snapshot_id)
        _require_nonempty_text("xml", self.xml)
        _require_aware("fetched_at", self.fetched_at)
        _require_aware("issued_at", self.issued_at)
        if not isinstance(self.forecast_dates, tuple) or not self.forecast_dates:
            raise ValueError("forecast_dates must be nonempty and stored as a tuple")
        if not all(isinstance(item, date) for item in self.forecast_dates):
            raise ValueError("forecast_dates must contain only dates")


@dataclass(frozen=True)
class ForecastProvenance:
    snapshot_id: str
    feed_type: FeedType
    source: SnapshotSource
    fetched_at: datetime
    issued_at: datetime
    source_forecast_date: date
    fallback_reason: Optional[str] = None

    def __post_init__(self) -> None:
        _require_nonempty_text("snapshot_id", self.snapshot_id)
        _require_aware("fetched_at", self.fetched_at)
        _require_aware("issued_at", self.issued_at)
        if not isinstance(self.source_forecast_date, date):
            raise ValueError("source_forecast_date must be a date")


def _require_nonempty_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonempty")


def _require_aware(field_name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
