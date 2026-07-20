"""Validation contracts for forecast snapshots and provenance."""

from datetime import date, datetime, timezone

import pytest

from src.data.snapshots import (
    FeedType,
    ForecastProvenance,
    ForecastSnapshot,
    SnapshotSource,
)


AWARE_TIME = datetime(2026, 7, 20, 6, 30, tzinfo=timezone.utc)


def test_forecast_snapshot_records_validated_source_facts():
    snapshot = ForecastSnapshot(
        snapshot_id="cities-20260720T063000Z",
        feed_type=FeedType.CITIES,
        source=SnapshotSource.LIVE,
        xml="<forecast />",
        fetched_at=AWARE_TIME,
        issued_at=AWARE_TIME,
        forecast_dates=(date(2026, 7, 20), date(2026, 7, 21)),
    )

    assert snapshot.forecast_dates == (date(2026, 7, 20), date(2026, 7, 21))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("snapshot_id", "", "snapshot_id must be nonempty"),
        ("xml", "", "xml must be nonempty"),
        ("fetched_at", datetime(2026, 7, 20, 6, 30), "fetched_at must be timezone-aware"),
        ("issued_at", datetime(2026, 7, 20, 6, 30), "issued_at must be timezone-aware"),
        ("forecast_dates", (), "forecast_dates must be nonempty"),
    ],
)
def test_forecast_snapshot_rejects_empty_or_naive_values(field, value, message):
    values = {
        "snapshot_id": "country-1",
        "feed_type": FeedType.COUNTRY,
        "source": SnapshotSource.FIXTURE,
        "xml": "<forecast />",
        "fetched_at": AWARE_TIME,
        "issued_at": AWARE_TIME,
        "forecast_dates": (date(2026, 7, 20),),
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        ForecastSnapshot(**values)


def test_forecast_provenance_records_exact_source_date_and_optional_reason():
    provenance = ForecastProvenance(
        snapshot_id="country-1",
        feed_type=FeedType.COUNTRY,
        source=SnapshotSource.ARCHIVE,
        fetched_at=AWARE_TIME,
        issued_at=AWARE_TIME,
        source_forecast_date=date(2026, 7, 19),
        fallback_reason="live feed unavailable",
    )

    assert provenance.source_forecast_date == date(2026, 7, 19)
    assert provenance.fallback_reason == "live feed unavailable"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("snapshot_id", "", "snapshot_id must be nonempty"),
        ("fetched_at", datetime(2026, 7, 20, 6, 30), "fetched_at must be timezone-aware"),
        ("issued_at", datetime(2026, 7, 20, 6, 30), "issued_at must be timezone-aware"),
    ],
)
def test_forecast_provenance_rejects_empty_or_naive_values(field, value, message):
    values = {
        "snapshot_id": "cities-1",
        "feed_type": FeedType.CITIES,
        "source": SnapshotSource.LIVE,
        "fetched_at": AWARE_TIME,
        "issued_at": AWARE_TIME,
        "source_forecast_date": date(2026, 7, 20),
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        ForecastProvenance(**values)
