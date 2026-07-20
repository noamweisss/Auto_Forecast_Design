"""Passing regressions for the two parser defects found in Slice 0."""

from datetime import date, datetime, timezone

from lxml import etree
import pytest

from src.data.parser import ForecastDataError, parse_cities_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from tests.conftest import load_ims_fixture


FETCHED_AT = datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc)


def _mutate_eilat_value(xml: str, target: date, name: str, value: str | None) -> str:
    root = etree.fromstring(xml.encode("utf-8"))
    eilat = next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == "520"
    )
    time_unit = next(
        item
        for item in eilat.findall("LocationData/TimeUnitData")
        if item.findtext("Date") == target.isoformat()
    )
    element = next(
        item for item in time_unit.findall("Element") if item.findtext("ElementName") == name
    )
    if value is None:
        time_unit.remove(element)
    else:
        element.find("ElementValue").text = value
    return etree.tostring(root, encoding="unicode")


def _snapshot(xml: str, source: SnapshotSource, fetched_hour: int):
    return build_snapshot(
        xml,
        FeedType.CITIES,
        source=source,
        fetched_at=FETCHED_AT.replace(hour=fetched_hour),
    )


def test_f02_fallback_uses_target_date_values_from_multiday_snapshot(app_settings):
    target = date(2025, 12, 18)
    fixture = load_ims_fixture("cities_forecast.xml")
    invalid_live = _mutate_eilat_value(fixture, target, "Maximum temperature", None)

    cities = parse_cities_forecast(
        [
            _snapshot(invalid_live, SnapshotSource.LIVE, 3),
            _snapshot(fixture, SnapshotSource.ARCHIVE, 2),
        ],
        target,
        settings=app_settings,
    )
    eilat = next(city for city in cities if city.city_id == "520")

    assert eilat.max_temp == 17
    assert eilat.provenance.source is SnapshotSource.ARCHIVE
    assert eilat.provenance.source_forecast_date == target


def test_f03_invalid_optional_city_data_cannot_return_incomplete_forecast(app_settings):
    target = date(2025, 12, 17)
    invalid = _mutate_eilat_value(
        load_ims_fixture("cities_forecast.xml"),
        target,
        "Maximum relative humidity",
        "not-a-number",
    )

    with pytest.raises(ForecastDataError, match=r"unresolved.*520"):
        parse_cities_forecast(
            [_snapshot(invalid, SnapshotSource.LIVE, 3)],
            target,
            settings=app_settings,
        )
