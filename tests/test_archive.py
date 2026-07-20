"""Offline contracts for atomic, metadata-based snapshot storage."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from src.data.archive import SnapshotArchiveError, SnapshotStore
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot


AS_OF = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
TARGET_DATE = date(2026, 7, 21)


def test_save_and_find_preserve_hebrew_xml_exactly(tmp_path):
    store = SnapshotStore(tmp_path)
    snapshot = _snapshot(
        FeedType.CITIES,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="ירושלים",
    )

    path = store.save(snapshot)
    loaded = store.find_for_date(FeedType.CITIES, TARGET_DATE, as_of=AS_OF)

    assert path.name.endswith(".snapshot.json")
    assert loaded[0].xml == snapshot.xml
    assert "ירושלים" in loaded[0].xml


def test_multiple_snapshots_fetched_on_the_same_day_coexist(tmp_path):
    store = SnapshotStore(tmp_path)
    first = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=2),
        dates=(TARGET_DATE,),
        marker="first",
    )
    second = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="second",
    )

    first_path = store.save(first)
    second_path = store.save(second)

    assert first_path != second_path
    assert first_path.is_file()
    assert second_path.is_file()


def test_find_returns_archive_copies_newest_first_with_original_source_facts(tmp_path):
    store = SnapshotStore(tmp_path)
    older = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=2),
        dates=(TARGET_DATE,),
        marker="older",
    )
    newer = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="newer",
    )
    store.save(older)
    store.save(newer)

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == [newer.snapshot_id, older.snapshot_id]
    assert all(item.source is SnapshotSource.ARCHIVE for item in found)
    assert found[0].fetched_at == newer.fetched_at
    assert found[0].issued_at == newer.issued_at


def test_exact_date_lookup_ignores_newer_snapshot_without_target_date(tmp_path):
    store = SnapshotStore(tmp_path)
    matching = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=2),
        dates=(TARGET_DATE,),
        marker="matching",
    )
    newer_wrong_date = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(date(2026, 7, 22),),
        marker="wrong-date",
    )
    store.save(matching)
    store.save(newer_wrong_date)

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == [matching.snapshot_id]


def test_find_orders_by_metadata_not_filename(tmp_path):
    store = SnapshotStore(tmp_path)
    older = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=2),
        dates=(TARGET_DATE,),
        marker="older",
    )
    newer = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="newer",
    )
    older_path = store.save(older)
    newer_path = store.save(newer)
    older_path.rename(tmp_path / "zzz.snapshot.json")
    newer_path.rename(tmp_path / "aaa.snapshot.json")

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == [newer.snapshot_id, older.snapshot_id]


def test_equal_fetch_times_use_snapshot_id_as_a_stable_tie_breaker(tmp_path, monkeypatch):
    store = SnapshotStore(tmp_path)
    first = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="first",
    )
    second = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
        marker="second",
    )
    descending_ids = sorted((first, second), key=lambda item: item.snapshot_id, reverse=True)
    paths = []
    for snapshot in descending_ids:
        paths.append(store.save(snapshot))
    monkeypatch.setattr(store, "_record_paths", lambda: tuple(paths))

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == sorted(
        (first.snapshot_id, second.snapshot_id)
    )


def test_find_excludes_wrong_feed_future_and_outside_seven_day_window(tmp_path):
    store = SnapshotStore(tmp_path)
    matching = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(days=1),
        dates=(TARGET_DATE,),
        marker="matching",
    )
    wrong_feed = _snapshot(
        FeedType.CITIES,
        fetched_at=AS_OF - timedelta(days=1),
        dates=(TARGET_DATE,),
        marker="wrong-feed",
    )
    future = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF + timedelta(microseconds=1),
        dates=(TARGET_DATE,),
        marker="future",
    )
    too_old = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(days=7, microseconds=1),
        dates=(TARGET_DATE,),
        marker="old",
    )
    for snapshot in (matching, wrong_feed, future, too_old):
        store.save(snapshot)

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == [matching.snapshot_id]


def test_find_skips_corrupt_recognised_records(tmp_path, caplog):
    store = SnapshotStore(tmp_path)
    matching = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
    )
    store.save(matching)
    (tmp_path / "broken.snapshot.json").write_text("not JSON", encoding="utf-8")

    found = store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=AS_OF)

    assert [item.snapshot_id for item in found] == [matching.snapshot_id]
    assert "Skipping corrupt snapshot record" in caplog.text


def test_save_rejects_snapshot_whose_stored_facts_do_not_match_xml(tmp_path):
    store = SnapshotStore(tmp_path)
    snapshot = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
    )

    with pytest.raises(SnapshotArchiveError, match="facts do not match"):
        store.save(replace(snapshot, snapshot_id="tampered"))

    assert not tmp_path.exists() or not list(tmp_path.iterdir())


def test_atomic_replace_failure_preserves_existing_final_and_removes_temp(
    tmp_path, monkeypatch
):
    store = SnapshotStore(tmp_path)
    snapshot = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(hours=1),
        dates=(TARGET_DATE,),
    )
    final_path = store.save(snapshot)
    original_bytes = final_path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr("src.data.archive.os.replace", fail_replace)

    with pytest.raises(SnapshotArchiveError, match="Could not save snapshot"):
        store.save(snapshot)

    assert final_path.read_bytes() == original_bytes
    assert list(tmp_path.glob("*.tmp")) == []


def test_cleanup_removes_only_expired_valid_snapshot_records(tmp_path):
    store = SnapshotStore(tmp_path)
    expired = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(days=7, microseconds=1),
        dates=(TARGET_DATE,),
        marker="expired",
    )
    recent = _snapshot(
        FeedType.COUNTRY,
        fetched_at=AS_OF - timedelta(days=2),
        dates=(TARGET_DATE,),
        marker="recent",
    )
    expired_path = store.save(expired)
    recent_path = store.save(recent)
    unrelated = tmp_path / "notes.txt"
    unrelated.write_text("keep", encoding="utf-8")
    legacy = tmp_path / "2026-07-01_country.xml"
    legacy.write_text("<legacy />", encoding="utf-8")
    corrupt = tmp_path / "broken.snapshot.json"
    corrupt.write_text("not JSON", encoding="utf-8")

    deleted = store.cleanup(as_of=AS_OF)

    assert deleted == 1
    assert not expired_path.exists()
    assert recent_path.exists()
    assert unrelated.exists()
    assert legacy.exists()
    assert corrupt.exists()


@pytest.mark.parametrize("method", ["find", "cleanup"])
def test_store_rejects_naive_as_of_time(tmp_path, method):
    store = SnapshotStore(tmp_path)
    naive = datetime(2026, 7, 20, 12, 0)

    with pytest.raises(SnapshotArchiveError, match="as_of must be timezone-aware"):
        if method == "find":
            store.find_for_date(FeedType.COUNTRY, TARGET_DATE, as_of=naive)
        else:
            store.cleanup(as_of=naive)


def _snapshot(
    feed_type: FeedType,
    *,
    fetched_at: datetime,
    dates: tuple[date, ...],
    marker: str = "source",
):
    root = {
        FeedType.COUNTRY: "IsraelWeatherForecastMorning",
        FeedType.CITIES: "IsraelCitiesWeatherForecastMorning",
    }[feed_type]
    date_nodes = "".join(
        f"<TimeUnitData><Date>{item.isoformat()}</Date></TimeUnitData>" for item in dates
    )
    xml = (
        f"<{root}><Identification><IssueDateTime>2026-07-20 04:23</IssueDateTime>"
        f"</Identification><Location><LocationData>{date_nodes}</LocationData>"
        f"<Marker>{marker}</Marker></Location></{root}>"
    )
    return build_snapshot(
        xml,
        feed_type,
        source=SnapshotSource.LIVE,
        fetched_at=fetched_at,
    )
