"""Integrity checks for the one publishable daily forecast shape."""

from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from src.data.models import CityForecast, CountryForecast, DailyForecast
from src.data.snapshots import FeedType, ForecastProvenance, SnapshotSource


TARGET_DATE = date(2025, 12, 18)
AWARE_TIME = datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc)


def _provenance(
    feed_type: FeedType,
    *,
    source: SnapshotSource = SnapshotSource.LIVE,
) -> ForecastProvenance:
    reason = "archive exact-date fallback" if source is SnapshotSource.ARCHIVE else None
    return ForecastProvenance(
        snapshot_id=f"{feed_type.value}-1",
        feed_type=feed_type,
        source=source,
        fetched_at=AWARE_TIME,
        issued_at=AWARE_TIME,
        source_forecast_date=TARGET_DATE,
        fallback_reason=reason,
    )


def _city(city_id: str, *, source: SnapshotSource = SnapshotSource.LIVE) -> CityForecast:
    return CityForecast(
        city_id=city_id,
        city_name_hebrew=f"he-{city_id}",
        city_name_english=f"en-{city_id}",
        internal_key=f"city_{city_id}",
        forecast_date=TARGET_DATE,
        min_temp=10,
        max_temp=20,
        weather_code="1250",
        weather_description_hebrew="clear-he",
        weather_description_english="Clear",
        provenance=_provenance(FeedType.CITIES, source=source),
    )


def _country(*, source: SnapshotSource = SnapshotSource.LIVE) -> CountryForecast:
    return CountryForecast(
        forecast_date=TARGET_DATE,
        description_hebrew="forecast-he",
        description_english="Forecast",
        provenance=_provenance(FeedType.COUNTRY, source=source),
    )


def _cities() -> list[CityForecast]:
    return [_city(str(index)) for index in range(15)]


def test_daily_forecast_rejects_fourteen_cities():
    with pytest.raises(ValueError, match="exactly 15"):
        DailyForecast(TARGET_DATE, _country(), _cities()[:14])


def test_daily_forecast_rejects_duplicate_city_ids():
    cities = _cities()
    cities[-1] = replace(cities[-1], city_id=cities[0].city_id)

    with pytest.raises(ValueError, match="unique"):
        DailyForecast(TARGET_DATE, _country(), cities)


@pytest.mark.parametrize("component", ["country", "city"])
def test_daily_forecast_rejects_component_date_mismatch(component):
    country = _country()
    cities = _cities()
    if component == "country":
        country = replace(country, forecast_date=date(2025, 12, 17))
    else:
        cities[0] = replace(cities[0], forecast_date=date(2025, 12, 17))

    with pytest.raises(ValueError, match="forecast_date"):
        DailyForecast(TARGET_DATE, country, cities)


def test_fallback_flags_are_read_only_and_derived_from_provenance():
    archive_city = _city("0", source=SnapshotSource.ARCHIVE)
    cities = _cities()
    cities[0] = archive_city
    forecast = DailyForecast(TARGET_DATE, _country(), cities)

    assert archive_city.is_fallback is True
    assert forecast.is_fallback is True
    with pytest.raises(AttributeError):
        archive_city.is_fallback = False
    with pytest.raises(AttributeError):
        forecast.is_fallback = False


def test_live_provenance_is_not_fallback():
    forecast = DailyForecast(TARGET_DATE, _country(), _cities())

    assert all(not city.is_fallback for city in forecast.city_forecasts)
    assert forecast.is_fallback is False
