"""Exact-date, complete-forecast contracts for the snapshot parser."""

from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timezone

from lxml import etree
import pytest

import src.data.parser as parser_module
from src.data.parser import (
    ForecastDataError,
    parse_cities_forecast,
    parse_country_forecast,
    parse_daily_forecast,
)
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from tests.conftest import load_ims_fixture


TARGET_DATE = date(2025, 12, 18)
FETCHED_AT = datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc)


def _snapshot(
    feed_type: FeedType,
    *,
    source: SnapshotSource = SnapshotSource.FIXTURE,
    xml: str | None = None,
    fetched_hour: int = 3,
):
    fixture_name = {
        FeedType.COUNTRY: "country_forecast.xml",
        FeedType.CITIES: "cities_forecast.xml",
    }[feed_type]
    return build_snapshot(
        xml or load_ims_fixture(fixture_name),
        feed_type,
        source=source,
        fetched_at=FETCHED_AT.replace(hour=fetched_hour),
    )


def _root(xml: str):
    return etree.fromstring(xml.encode("utf-8"))


def _xml(root) -> str:
    return etree.tostring(root, encoding="unicode")


def _city(root, city_id: str = "520"):
    return next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == city_id
    )


def _time_unit(location, forecast_date: date = TARGET_DATE):
    return next(
        item
        for item in location.findall("LocationData/TimeUnitData")
        if item.findtext("Date") == forecast_date.isoformat()
    )


def _element(time_unit, name: str):
    return next(
        element
        for element in time_unit.findall("Element")
        if element.findtext("ElementName") == name
    )


def _set_or_add_element(time_unit, name: str, value: str) -> None:
    try:
        element = _element(time_unit, name)
    except StopIteration:
        element = etree.SubElement(time_unit, "Element")
        etree.SubElement(element, "ElementName").text = name
        etree.SubElement(element, "ElementValue")
    element.find("ElementValue").text = value


def _mutated_cities(kind: str) -> str:
    root = _root(load_ims_fixture("cities_forecast.xml"))
    eilat = _city(root)
    time_unit = _time_unit(eilat)

    if kind == "missing_city":
        root.remove(eilat)
    elif kind == "duplicate_city":
        root.append(deepcopy(eilat))
    elif kind == "missing_maximum":
        time_unit.remove(_element(time_unit, "Maximum temperature"))
    elif kind == "nonnumeric_temperature":
        _element(time_unit, "Minimum temperature").find("ElementValue").text = "warm"
    elif kind == "reversed_temperature":
        _element(time_unit, "Minimum temperature").find("ElementValue").text = "30"
        _element(time_unit, "Maximum temperature").find("ElementValue").text = "10"
    elif kind == "unknown_weather_code":
        _element(time_unit, "Weather code").find("ElementValue").text = "999999"
    elif kind == "nonnumeric_humidity":
        _set_or_add_element(time_unit, "Maximum relative humidity", "wet")
    elif kind == "out_of_range_humidity":
        _set_or_add_element(time_unit, "Maximum relative humidity", "101")
    elif kind == "reversed_humidity":
        _set_or_add_element(time_unit, "Minimum relative humidity", "90")
        _set_or_add_element(time_unit, "Maximum relative humidity", "10")
    elif kind == "malformed_wind":
        _set_or_add_element(time_unit, "Wind direction and speed", "north/fast")
    else:
        raise AssertionError(f"unknown mutation: {kind}")
    return _xml(root)


def _country_without_hebrew() -> str:
    root = _root(load_ims_fixture("country_forecast.xml"))
    time_unit = _time_unit(root.find("Location"))
    weather = _element(time_unit, "Weather in Hebrew")
    weather.find("ElementValue").text = "   "
    return _xml(root)


def test_fixture_country_parses_nonempty_hebrew_for_exact_date():
    snapshot = _snapshot(FeedType.COUNTRY)
    result = parse_country_forecast([snapshot], TARGET_DATE)

    assert result.forecast_date == TARGET_DATE
    assert result.description_hebrew.strip()
    assert result.provenance.snapshot_id == snapshot.snapshot_id
    assert result.provenance.feed_type is snapshot.feed_type
    assert result.provenance.source is snapshot.source
    assert result.provenance.fetched_at == snapshot.fetched_at
    assert result.provenance.issued_at == snapshot.issued_at
    assert result.provenance.source_forecast_date == TARGET_DATE


def test_fixture_cities_are_complete_unique_and_in_settings_order(app_settings):
    snapshot = _snapshot(FeedType.CITIES)
    result = parse_cities_forecast(
        [snapshot], TARGET_DATE, settings=app_settings
    )

    ids = [city.city_id for city in result]
    assert ids == list(app_settings.cities)
    assert len(ids) == len(set(ids)) == 15
    assert all(city.provenance.snapshot_id == snapshot.snapshot_id for city in result)
    assert all(city.provenance.fetched_at == snapshot.fetched_at for city in result)
    assert all(city.provenance.issued_at == snapshot.issued_at for city in result)
    assert all(city.provenance.source_forecast_date == TARGET_DATE for city in result)


def test_candidate_with_only_another_date_is_not_relabelled(app_settings):
    snapshot = _snapshot(FeedType.CITIES)

    with pytest.raises(ForecastDataError, match="2025-12-21.*unresolved"):
        parse_cities_forecast([snapshot], date(2025, 12, 21), settings=app_settings)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_city",
        "duplicate_city",
        "missing_maximum",
        "nonnumeric_temperature",
        "reversed_temperature",
        "unknown_weather_code",
        "nonnumeric_humidity",
        "out_of_range_humidity",
        "reversed_humidity",
        "malformed_wind",
    ],
)
def test_invalid_city_candidate_fails_the_complete_forecast(kind, app_settings):
    invalid = _snapshot(FeedType.CITIES, source=SnapshotSource.LIVE, xml=_mutated_cities(kind))

    with pytest.raises(ForecastDataError, match=r"unresolved.*520"):
        parse_cities_forecast([invalid], TARGET_DATE, settings=app_settings)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_city",
        "duplicate_city",
        "missing_maximum",
        "nonnumeric_temperature",
        "reversed_temperature",
        "unknown_weather_code",
        "nonnumeric_humidity",
        "out_of_range_humidity",
        "reversed_humidity",
        "malformed_wind",
    ],
)
def test_invalid_city_candidate_uses_valid_exact_date_archive(kind, app_settings):
    live = _snapshot(FeedType.CITIES, source=SnapshotSource.LIVE, xml=_mutated_cities(kind))
    archive = _snapshot(FeedType.CITIES, source=SnapshotSource.ARCHIVE, fetched_hour=2)

    result = parse_cities_forecast([live, archive], TARGET_DATE, settings=app_settings)
    eilat = next(city for city in result if city.city_id == "520")

    assert len(result) == 15
    assert eilat.provenance.source is SnapshotSource.ARCHIVE
    assert eilat.provenance.source_forecast_date == TARGET_DATE
    assert eilat.provenance.fallback_reason
    assert all(not city.is_fallback for city in result if city.city_id != "520")


def test_archive_fallback_uses_supplied_boundary_reason(app_settings):
    live = _snapshot(
        FeedType.CITIES,
        source=SnapshotSource.LIVE,
        xml=_mutated_cities("missing_maximum"),
    )
    archive = _snapshot(FeedType.CITIES, source=SnapshotSource.ARCHIVE, fetched_hour=2)

    result = parse_cities_forecast(
        [live, archive],
        TARGET_DATE,
        settings=app_settings,
        unavailable_reason="live cities feed timed out",
    )

    eilat = next(city for city in result if city.city_id == "520")
    assert eilat.max_temp == 17
    assert eilat.provenance.fallback_reason == "live cities feed timed out"


def test_invalid_optional_humidity_never_returns_fourteen_cities(app_settings):
    invalid = _snapshot(
        FeedType.CITIES,
        source=SnapshotSource.LIVE,
        xml=_mutated_cities("nonnumeric_humidity"),
    )

    with pytest.raises(ForecastDataError, match=r"unresolved.*520"):
        parse_cities_forecast([invalid], TARGET_DATE, settings=app_settings)


def test_missing_hebrew_country_text_uses_fallback_or_fails():
    live = _snapshot(
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        xml=_country_without_hebrew(),
    )
    archive = _snapshot(FeedType.COUNTRY, source=SnapshotSource.ARCHIVE, fetched_hour=2)

    result = parse_country_forecast([live, archive], TARGET_DATE)

    assert result.description_hebrew.strip()
    assert result.provenance.source is SnapshotSource.ARCHIVE
    assert result.provenance.fallback_reason

    with pytest.raises(ForecastDataError, match=r"country.*2025-12-18"):
        parse_country_forecast([live], TARGET_DATE)


def test_country_and_cities_resolve_sources_independently(app_settings):
    invalid_country = _snapshot(
        FeedType.COUNTRY,
        source=SnapshotSource.LIVE,
        xml=_country_without_hebrew(),
    )
    country_archive = _snapshot(FeedType.COUNTRY, source=SnapshotSource.ARCHIVE)
    cities_live = _snapshot(FeedType.CITIES, source=SnapshotSource.LIVE)

    result = parse_daily_forecast(
        [invalid_country, country_archive],
        [cities_live],
        TARGET_DATE,
        settings=app_settings,
    )

    assert result.country_forecast.provenance.source is SnapshotSource.ARCHIVE
    assert all(city.provenance.source is SnapshotSource.LIVE for city in result.city_forecasts)
    assert result.is_fallback is True


def test_extra_unconfigured_location_is_ignored(app_settings):
    root = _root(load_ims_fixture("cities_forecast.xml"))
    extra = deepcopy(root.find("Location"))
    extra.find("LocationMetaData/LocationId").text = "999"
    root.append(extra)

    result = parse_cities_forecast(
        [_snapshot(FeedType.CITIES, xml=_xml(root))], TARGET_DATE, settings=app_settings
    )

    assert [city.city_id for city in result] == list(app_settings.cities)


def test_wrong_feed_and_wrong_date_candidates_are_skipped_before_xml_parsing(app_settings):
    cities = _snapshot(FeedType.CITIES)
    wrong_feed = replace(cities, feed_type=FeedType.COUNTRY, xml="not XML")
    wrong_date = replace(
        cities,
        xml="not XML",
        forecast_dates=(date(2025, 12, 17),),
    )

    result = parse_cities_forecast(
        [wrong_feed, wrong_date, cities], TARGET_DATE, settings=app_settings
    )

    assert len(result) == 15


def test_programmer_error_is_not_swallowed(monkeypatch, app_settings):
    def explode(*args, **kwargs):
        raise RuntimeError("programmer defect")

    monkeypatch.setattr(parser_module, "_parse_city_candidate", explode)

    with pytest.raises(RuntimeError, match="programmer defect"):
        parse_cities_forecast(
            [_snapshot(FeedType.CITIES)], TARGET_DATE, settings=app_settings
        )
