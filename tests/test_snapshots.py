"""Validation contracts for forecast snapshots and provenance."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from src.data.snapshots import (
    FeedType,
    ForecastProvenance,
    ForecastSnapshot,
    SnapshotSource,
    SnapshotValidationError,
    build_snapshot,
)
from tests.conftest import load_ims_fixture


AWARE_TIME = datetime(2026, 7, 20, 6, 30, tzinfo=timezone.utc)


def _small_xml(
    feed_type: FeedType,
    *,
    issue_time: str = "2026-07-20 04:23",
    dates: tuple[str, ...] = ("2026-07-20",),
) -> str:
    root = {
        FeedType.COUNTRY: "IsraelWeatherForecastMorning",
        FeedType.CITIES: "IsraelCitiesWeatherForecastMorning",
    }[feed_type]
    date_nodes = "".join(
        f"<TimeUnitData><Date>{forecast_date}</Date></TimeUnitData>"
        for forecast_date in dates
    )
    return (
        f"<{root}><Identification><IssueDateTime>{issue_time}</IssueDateTime>"
        f"</Identification><Location><LocationData>{date_nodes}</LocationData>"
        f"</Location></{root}>"
    )


@pytest.mark.parametrize(
    ("feed_type", "fixture_name", "expected_dates"),
    [
        (
            FeedType.COUNTRY,
            "country_forecast.xml",
            (date(2025, 12, 17), date(2025, 12, 18), date(2025, 12, 19), date(2025, 12, 20)),
        ),
        (
            FeedType.CITIES,
            "cities_forecast.xml",
            (date(2025, 12, 17), date(2025, 12, 18), date(2025, 12, 19), date(2025, 12, 20)),
        ),
    ],
)
def test_build_snapshot_extracts_production_fixture_metadata(
    feed_type, fixture_name, expected_dates
):
    snapshot = build_snapshot(
        load_ims_fixture(fixture_name),
        feed_type,
        source=SnapshotSource.FIXTURE,
        fetched_at=datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc),
    )

    assert snapshot.feed_type is feed_type
    assert snapshot.source is SnapshotSource.FIXTURE
    assert snapshot.issued_at.isoformat() == "2025-12-17T04:23:00+02:00"
    assert snapshot.fetched_at.isoformat() == "2025-12-17T05:00:00+02:00"
    assert snapshot.forecast_dates == expected_dates


def test_build_snapshot_applies_israel_summer_time_to_naive_issue_time():
    xml = _small_xml(
        FeedType.COUNTRY,
        issue_time="2026-07-20 04:23",
        dates=("2026-07-21",),
    )

    snapshot = build_snapshot(
        xml,
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=datetime(2026, 7, 20, 2, 0, tzinfo=timezone.utc),
    )

    assert snapshot.issued_at.utcoffset() == timedelta(hours=3)
    assert snapshot.fetched_at.isoformat() == "2026-07-20T05:00:00+03:00"


def test_build_snapshot_deduplicates_and_sorts_dates():
    xml = _small_xml(
        FeedType.CITIES,
        dates=("2026-07-22", "2026-07-20", "2026-07-22", "2026-07-21"),
    )

    snapshot = build_snapshot(
        xml,
        FeedType.CITIES,
        source=SnapshotSource.LIVE,
        fetched_at=AWARE_TIME,
    )

    assert snapshot.forecast_dates == (
        date(2026, 7, 20),
        date(2026, 7, 21),
        date(2026, 7, 22),
    )


@pytest.mark.parametrize(
    ("xml", "feed_type", "message"),
    [
        ("not XML", FeedType.COUNTRY, "Malformed country XML"),
        (
            _small_xml(FeedType.CITIES),
            FeedType.COUNTRY,
            "expected root IsraelWeatherForecastMorning",
        ),
        (
            _small_xml(FeedType.COUNTRY).replace(
                "<IssueDateTime>2026-07-20 04:23</IssueDateTime>", ""
            ),
            FeedType.COUNTRY,
            "IssueDateTime is required",
        ),
        (
            _small_xml(FeedType.COUNTRY, issue_time="not-a-time"),
            FeedType.COUNTRY,
            "IssueDateTime is invalid",
        ),
        (
            _small_xml(FeedType.COUNTRY, dates=("not-a-date",)),
            FeedType.COUNTRY,
            "forecast date is invalid",
        ),
        (
            _small_xml(FeedType.COUNTRY, dates=()),
            FeedType.COUNTRY,
            "at least one forecast date",
        ),
    ],
)
def test_build_snapshot_rejects_invalid_xml_metadata(xml, feed_type, message):
    with pytest.raises(SnapshotValidationError, match=message):
        build_snapshot(
            xml,
            feed_type,
            source=SnapshotSource.LIVE,
            fetched_at=AWARE_TIME,
        )


def test_build_snapshot_rejects_naive_fetch_time():
    with pytest.raises(SnapshotValidationError, match="fetched_at must be timezone-aware"):
        build_snapshot(
            _small_xml(FeedType.COUNTRY),
            FeedType.COUNTRY,
            source=SnapshotSource.LIVE,
            fetched_at=datetime(2026, 7, 20, 6, 30),
        )


def test_snapshot_id_is_stable_for_identical_source_facts():
    xml = _small_xml(FeedType.COUNTRY)
    kwargs = {
        "source": SnapshotSource.LIVE,
        "fetched_at": AWARE_TIME,
    }

    first = build_snapshot(xml, FeedType.COUNTRY, **kwargs)
    second = build_snapshot(xml, FeedType.COUNTRY, **kwargs)

    assert first.snapshot_id == second.snapshot_id


def test_snapshot_id_changes_for_content_or_fetch_microseconds():
    xml = _small_xml(FeedType.COUNTRY)
    first = build_snapshot(
        xml,
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=AWARE_TIME,
    )
    changed_content = build_snapshot(
        xml.replace("<Location>", "<!-- changed --><Location>"),
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=AWARE_TIME,
    )
    changed_microsecond = build_snapshot(
        xml,
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=AWARE_TIME.replace(microsecond=1),
    )

    assert len({first.snapshot_id, changed_content.snapshot_id, changed_microsecond.snapshot_id}) == 3


def test_forecast_snapshot_rejects_unsorted_or_duplicate_dates():
    snapshot = build_snapshot(
        _small_xml(FeedType.COUNTRY),
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=AWARE_TIME,
    )

    with pytest.raises(ValueError, match="sorted and unique"):
        replace(
            snapshot,
            forecast_dates=(date(2026, 7, 21), date(2026, 7, 20), date(2026, 7, 20)),
        )


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


def test_archived_provenance_requires_a_nonempty_fallback_reason():
    with pytest.raises(ValueError, match="archived provenance.*fallback reason"):
        ForecastProvenance(
            snapshot_id="country-archive-1",
            feed_type=FeedType.COUNTRY,
            source=SnapshotSource.ARCHIVE,
            fetched_at=AWARE_TIME,
            issued_at=AWARE_TIME,
            source_forecast_date=date(2026, 7, 20),
        )


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
