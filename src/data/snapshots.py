"""Vocabulary for immutable forecast source snapshots and provenance."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import re
from typing import Optional

from lxml import etree  # type: ignore[import-untyped]

from src.clock import ISRAEL_TIMEZONE


class SnapshotValidationError(ValueError):
    """IMS XML cannot be represented as a trustworthy source snapshot."""


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
        if not isinstance(self.feed_type, FeedType):
            raise ValueError("feed_type must be a FeedType")
        if not isinstance(self.source, SnapshotSource):
            raise ValueError("source must be a SnapshotSource")
        _require_nonempty_text("xml", self.xml)
        _require_aware("fetched_at", self.fetched_at)
        _require_aware("issued_at", self.issued_at)
        if not isinstance(self.forecast_dates, tuple) or not self.forecast_dates:
            raise ValueError("forecast_dates must be nonempty and stored as a tuple")
        if not all(type(item) is date for item in self.forecast_dates):
            raise ValueError("forecast_dates must contain only dates")
        if tuple(sorted(set(self.forecast_dates))) != self.forecast_dates:
            raise ValueError("forecast_dates must be sorted and unique")


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
        if not isinstance(self.feed_type, FeedType):
            raise ValueError("feed_type must be a FeedType")
        if not isinstance(self.source, SnapshotSource):
            raise ValueError("source must be a SnapshotSource")
        _require_aware("fetched_at", self.fetched_at)
        _require_aware("issued_at", self.issued_at)
        if type(self.source_forecast_date) is not date:
            raise ValueError("source_forecast_date must be a date")
        if self.fallback_reason is not None:
            _require_nonempty_text("fallback_reason", self.fallback_reason)
        if self.source is SnapshotSource.ARCHIVE and self.fallback_reason is None:
            raise ValueError("archived provenance requires a nonempty fallback reason")


def _require_nonempty_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonempty")


def _require_aware(field_name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def build_snapshot(
    xml: str,
    feed_type: FeedType,
    *,
    source: SnapshotSource,
    fetched_at: datetime,
) -> ForecastSnapshot:
    """Seal validated XML and its IMS metadata into an immutable snapshot."""
    if not isinstance(feed_type, FeedType):
        raise SnapshotValidationError("feed_type must be a FeedType")
    if not isinstance(source, SnapshotSource):
        raise SnapshotValidationError("source must be a SnapshotSource")
    if not isinstance(xml, str) or not xml.strip():
        raise SnapshotValidationError("XML must be nonempty")
    try:
        _require_aware("fetched_at", fetched_at)
    except ValueError as error:
        raise SnapshotValidationError(str(error)) from error

    root = _parse_xml(xml, feed_type)
    expected_root = {
        FeedType.COUNTRY: "IsraelWeatherForecastMorning",
        FeedType.CITIES: "IsraelCitiesWeatherForecastMorning",
    }[feed_type]
    if root.tag != expected_root:
        raise SnapshotValidationError(
            f"{feed_type.value} XML expected root {expected_root}, found {root.tag}"
        )

    issue_text = root.findtext("Identification/IssueDateTime")
    if issue_text is None or not issue_text.strip():
        raise SnapshotValidationError("Identification/IssueDateTime is required")
    try:
        issued_at = datetime.fromisoformat(issue_text.strip())
    except ValueError as error:
        raise SnapshotValidationError(
            f"Identification/IssueDateTime is invalid: {issue_text!r}"
        ) from error
    if issued_at.tzinfo is None or issued_at.utcoffset() is None:
        issued_at = issued_at.replace(tzinfo=ISRAEL_TIMEZONE)
    else:
        issued_at = issued_at.astimezone(ISRAEL_TIMEZONE)

    forecast_dates: set[date] = set()
    for date_node in root.findall(".//TimeUnitData/Date"):
        date_text = (date_node.text or "").strip()
        try:
            forecast_dates.add(date.fromisoformat(date_text))
        except ValueError as error:
            raise SnapshotValidationError(
                f"IMS forecast date is invalid: {date_text!r}"
            ) from error
    if not forecast_dates:
        raise SnapshotValidationError("IMS XML must contain at least one forecast date")

    israel_fetched_at = fetched_at.astimezone(ISRAEL_TIMEZONE)
    snapshot_id = _snapshot_id(xml, feed_type, israel_fetched_at)
    return ForecastSnapshot(
        snapshot_id=snapshot_id,
        feed_type=feed_type,
        source=source,
        xml=xml,
        fetched_at=israel_fetched_at,
        issued_at=issued_at,
        forecast_dates=tuple(sorted(forecast_dates)),
    )


def _parse_xml(xml: str, feed_type: FeedType):
    normalized = re.sub(
        r"encoding=['\"][^'\"]+['\"]",
        'encoding="UTF-8"',
        xml,
        count=1,
        flags=re.IGNORECASE,
    )
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        return etree.fromstring(normalized.encode("utf-8"), parser=parser)
    except (etree.XMLSyntaxError, ValueError) as error:
        raise SnapshotValidationError(f"Malformed {feed_type.value} XML: {error}") from error


def _snapshot_id(xml: str, feed_type: FeedType, fetched_at: datetime) -> str:
    utc_stamp = fetched_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    digest = hashlib.sha256(xml.encode("utf-8")).hexdigest()[:12]
    return f"{feed_type.value}-{utc_stamp}-{digest}"
