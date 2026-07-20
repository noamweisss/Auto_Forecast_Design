"""Fetch IMS snapshots and export one parsed forecast for manual inspection."""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app_paths import AppPaths  # noqa: E402
from src.clock import SystemClock  # noqa: E402
from src.data.archive import SnapshotStore  # noqa: E402
from src.data.fetcher import FetchResult, fetch_feed  # noqa: E402
from src.data.parser import ForecastDataError, parse_daily_forecast  # noqa: E402
from src.data.snapshots import (  # noqa: E402
    FeedType,
    ForecastProvenance,
    ForecastSnapshot,
    SnapshotSource,
    SnapshotValidationError,
    build_snapshot,
)
from src.settings import load_settings  # noqa: E402


OUTPUT_DIR = Path(__file__).parent / "output"


def _provenance_to_dict(provenance: ForecastProvenance) -> dict:
    return {
        "snapshot_id": provenance.snapshot_id,
        "feed_type": provenance.feed_type.value,
        "source": provenance.source.value,
        "fetched_at": provenance.fetched_at.isoformat(),
        "issued_at": provenance.issued_at.isoformat(),
        "source_forecast_date": provenance.source_forecast_date.isoformat(),
        "fallback_reason": provenance.fallback_reason,
    }


def forecast_to_dict(forecast, generated_at) -> dict:
    """Convert a DailyForecast and each value's source facts to JSON."""
    return {
        "_meta": {
            "description": "IMS Weather Forecast - Parsed Data Export",
            "generated_at": generated_at.isoformat(),
            "forecast_date": forecast.forecast_date.isoformat(),
            "is_fallback": forecast.is_fallback,
            "city_count": len(forecast.city_forecasts),
        },
        "country_forecast": {
            "date": forecast.country_forecast.forecast_date.isoformat(),
            "description_hebrew": forecast.country_forecast.description_hebrew,
            "description_english": forecast.country_forecast.description_english,
            "warning_hebrew": forecast.country_forecast.warning_hebrew,
            "warning_english": forecast.country_forecast.warning_english,
            "provenance": _provenance_to_dict(forecast.country_forecast.provenance),
        },
        "city_forecasts": [
            {
                "city_id": city.city_id,
                "internal_key": city.internal_key,
                "city_name_hebrew": city.city_name_hebrew,
                "city_name_english": city.city_name_english,
                "date": city.forecast_date.isoformat(),
                "temperature": {"min": city.min_temp, "max": city.max_temp},
                "weather": {
                    "code": city.weather_code,
                    "description_hebrew": city.weather_description_hebrew,
                    "description_english": city.weather_description_english,
                },
                "humidity": {"min": city.humidity_min, "max": city.humidity_max},
                "wind": {"direction": city.wind_direction, "speed_kmh": city.wind_speed},
                "is_fallback": city.is_fallback,
                "provenance": _provenance_to_dict(city.provenance),
            }
            for city in forecast.city_forecasts
        ],
    }


def acquire_feed_candidates(
    feed_type: FeedType,
    target_date: date,
    *,
    now: datetime,
    store: SnapshotStore,
    fetch: Callable[[FeedType], FetchResult] = fetch_feed,
) -> tuple[list[ForecastSnapshot], str | None]:
    """Return live-first candidates, preserving archives when live XML is invalid."""
    archived = list(store.find_for_date(feed_type, target_date, as_of=now))
    result = fetch(feed_type)
    if result.xml is None:
        failure = result.failure
        reason = failure.message if failure is not None else "IMS feed unavailable"
        return archived, reason

    try:
        live = build_snapshot(
            result.xml,
            feed_type,
            source=SnapshotSource.LIVE,
            fetched_at=now,
        )
    except SnapshotValidationError as error:
        return archived, f"invalid live {feed_type.value} snapshot: {error}"

    store.save(live)
    return [live, *archived], None


def main() -> int:
    paths = AppPaths.from_repository()
    settings = load_settings(paths)
    now = SystemClock().now()
    target_date = now.date()
    store = SnapshotStore(paths.archive)
    candidates: dict[FeedType, list[ForecastSnapshot]] = {}
    failure_reasons: dict[FeedType, str] = {}

    for feed_type in FeedType:
        feed_candidates, failure_reason = acquire_feed_candidates(
            feed_type,
            target_date,
            now=now,
            store=store,
        )
        candidates[feed_type] = feed_candidates
        if failure_reason is not None:
            failure_reasons[feed_type] = failure_reason

    try:
        forecast = parse_daily_forecast(
            candidates[FeedType.COUNTRY],
            candidates[FeedType.CITIES],
            target_date,
            settings=settings,
            feed_failure_reasons=failure_reasons,
        )
    except ForecastDataError as error:
        print(f"ERROR: {error}")
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"forecast_{target_date.isoformat()}.json"
    output_file.write_text(
        json.dumps(forecast_to_dict(forecast, now), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Exported {len(forecast.city_forecasts)} cities to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
