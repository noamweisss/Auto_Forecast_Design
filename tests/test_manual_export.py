"""Offline checks for the manual exporter's acquisition boundary."""

from datetime import date, datetime, timedelta, timezone

import pytest

from src.data.archive import SnapshotStore
from src.data.fetcher import COUNTRY_FORECAST_URL, FetchResult
from src.data.parser import parse_country_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from tests.conftest import load_ims_fixture
from tests.manual import export_forecast_json


TARGET_DATE = date(2025, 12, 18)
FETCHED_AT = datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "invalid_live_xml",
    [
        "not XML",
        pytest.param(
            load_ims_fixture("cities_forecast.xml"),
            id="wrong-root",
        ),
    ],
)
def test_invalid_successful_live_xml_keeps_archive_and_records_reason(
    tmp_path, invalid_live_xml
):
    store = SnapshotStore(tmp_path)
    archived_source = build_snapshot(
        load_ims_fixture("country_forecast.xml"),
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        fetched_at=FETCHED_AT,
    )
    stored_path = store.save(archived_source)
    now = FETCHED_AT + timedelta(hours=1)

    def fetch_success(feed_type):
        assert feed_type is FeedType.COUNTRY
        return FetchResult(
            feed_type=feed_type,
            url=COUNTRY_FORECAST_URL,
            attempt_count=1,
            xml=invalid_live_xml,
        )

    candidates, failure_reason = export_forecast_json.acquire_feed_candidates(
        FeedType.COUNTRY,
        TARGET_DATE,
        now=now,
        store=store,
        fetch=fetch_success,
    )

    assert [candidate.snapshot_id for candidate in candidates] == [
        archived_source.snapshot_id
    ]
    assert candidates[0].source is SnapshotSource.ARCHIVE
    assert failure_reason is not None
    assert "invalid live country snapshot" in failure_reason
    assert list(tmp_path.glob("*.snapshot.json")) == [stored_path]

    forecast = parse_country_forecast(
        candidates,
        TARGET_DATE,
        unavailable_reason=failure_reason,
    )
    assert forecast.provenance.source is SnapshotSource.ARCHIVE
    assert forecast.provenance.fallback_reason == failure_reason
