"""Load the sanitized Story reference JSON into the real domain model."""

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

from src.data.models import CityForecast, CountryForecast, DailyForecast
from src.data.snapshots import FeedType, ForecastProvenance, SnapshotSource
from src.settings import AppSettings


REFERENCE_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "render" / "forecast_story_reference.json"
)


def load_story_reference_document(
    path: Path = REFERENCE_FIXTURE_PATH,
) -> dict[str, Any]:
    """Read the committed sanitized reference as UTF-8 JSON."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("Story reference fixture must contain a JSON object")
    return document


def build_story_reference_forecast(
    settings: AppSettings,
    path: Path = REFERENCE_FIXTURE_PATH,
) -> DailyForecast:
    """Construct model objects without reimplementing IMS XML parsing."""
    document = load_story_reference_document(path)
    forecast_date = date.fromisoformat(document["target_date"])
    source = document["provenance"]

    country = CountryForecast(
        forecast_date=forecast_date,
        description_hebrew=document["country"]["description_hebrew"],
        description_english="",
        provenance=_provenance(
            source,
            feed_type=FeedType.COUNTRY,
            snapshot_id=source["country_snapshot_id"],
            forecast_date=forecast_date,
        ),
    )

    cities = []
    for item in document["cities"]:
        weather_code = item["weather_code"]
        weather = settings.weather_codes[weather_code]
        cities.append(
            CityForecast(
                city_id=item["city_id"],
                city_name_hebrew=item["name_hebrew"],
                city_name_english=item["name_english"],
                internal_key=item["internal_key"],
                forecast_date=forecast_date,
                min_temp=item["min_temp"],
                max_temp=item["max_temp"],
                weather_code=weather_code,
                weather_description_hebrew=str(weather["hebrew"]),
                weather_description_english=str(weather["english"]),
                provenance=_provenance(
                    source,
                    feed_type=FeedType.CITIES,
                    snapshot_id=source["cities_snapshot_id"],
                    forecast_date=forecast_date,
                ),
            )
        )

    return DailyForecast(
        forecast_date=forecast_date,
        country_forecast=country,
        city_forecasts=cities,
    )


def _provenance(
    source: dict[str, Any],
    *,
    feed_type: FeedType,
    snapshot_id: str,
    forecast_date: date,
) -> ForecastProvenance:
    return ForecastProvenance(
        snapshot_id=snapshot_id,
        feed_type=feed_type,
        source=SnapshotSource(source["source"]),
        fetched_at=datetime.fromisoformat(source["fetched_at"]),
        issued_at=datetime.fromisoformat(source["issued_at"]),
        source_forecast_date=forecast_date,
    )
