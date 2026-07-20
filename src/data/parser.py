"""Resolve ordered IMS snapshots into one complete, exact-date forecast."""

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Mapping, Optional, Sequence

from lxml import etree  # type: ignore[import-untyped]

from src.data.models import CityForecast, CountryForecast, DailyForecast
from src.data.snapshots import (
    FeedType,
    ForecastProvenance,
    ForecastSnapshot,
    SnapshotSource,
)
from src.settings import AppSettings, CitySettings


class ForecastDataError(ValueError):
    """Available snapshots cannot produce a complete, truthful forecast."""


@dataclass(frozen=True)
class _ParsedCandidate:
    position: int
    snapshot: ForecastSnapshot
    root: Any


def parse_country_forecast(
    snapshots: Sequence[ForecastSnapshot],
    target_date: date,
    *,
    unavailable_reason: str | None = None,
) -> CountryForecast:
    """Select the first publishable exact-date country narrative."""
    candidates = _candidate_roots(snapshots, FeedType.COUNTRY, target_date)
    rejected: list[str] = []
    for candidate in candidates:
        try:
            time_unit = _country_time_unit(candidate.root, target_date)
            elements = time_unit.findall("Element")
            description_hebrew = (_element_value(elements, "Weather in Hebrew") or "").strip()
            if not description_hebrew:
                raise ForecastDataError("missing nonempty Hebrew weather description")
            return CountryForecast(
                forecast_date=target_date,
                description_hebrew=description_hebrew,
                description_english=(
                    _element_value(elements, "Weather in English") or ""
                ).strip(),
                warning_hebrew=_optional_text(
                    _element_value(elements, "Warning in Hebrew")
                ),
                warning_english=_optional_text(
                    _element_value(elements, "Warning in English")
                ),
                provenance=_provenance(
                    candidate,
                    target_date,
                    unavailable_reason,
                    "preferred country snapshot had unusable data",
                ),
            )
        except ForecastDataError as error:
            rejected.append(f"{candidate.snapshot.snapshot_id}: {error}")

    details = "; ".join(rejected) if rejected else "no exact-date country candidate"
    raise ForecastDataError(
        f"country feed cannot publish {target_date.isoformat()}: {details}"
    )


def parse_cities_forecast(
    snapshots: Sequence[ForecastSnapshot],
    target_date: date,
    *,
    settings: AppSettings,
    unavailable_reason: str | None = None,
) -> list[CityForecast]:
    """Resolve every configured city independently from exact-date candidates."""
    candidates = _candidate_roots(snapshots, FeedType.CITIES, target_date)
    resolved: list[CityForecast] = []
    unresolved: list[str] = []
    duplicate_ids: set[str] = set()
    rejection_details: dict[str, list[str]] = {}

    for city_id, city_settings in settings.cities.items():
        city_rejections: list[str] = []
        for candidate in candidates:
            try:
                city = _parse_city_candidate(
                    candidate,
                    city_settings,
                    target_date,
                    settings,
                    unavailable_reason,
                )
            except ForecastDataError as error:
                if "duplicate configured location" in str(error):
                    duplicate_ids.add(city_id)
                city_rejections.append(f"{candidate.snapshot.snapshot_id}: {error}")
                continue
            resolved.append(city)
            break
        else:
            unresolved.append(city_id)
            rejection_details[city_id] = city_rejections

    expected_ids = list(settings.cities)
    actual_ids = [city.city_id for city in resolved]
    if unresolved or actual_ids != expected_ids or len(set(actual_ids)) != len(actual_ids):
        duplicate_text = f", duplicate candidate IDs={sorted(duplicate_ids)}" if duplicate_ids else ""
        detail_text = "; ".join(
            f"{city_id}: {', '.join(details) or 'no exact-date candidate'}"
            for city_id, details in rejection_details.items()
        )
        raise ForecastDataError(
            f"cities feed cannot publish {target_date.isoformat()}; "
            f"unresolved configured IDs={unresolved}{duplicate_text}. {detail_text}"
        )
    return resolved


def parse_daily_forecast(
    country_snapshots: Sequence[ForecastSnapshot],
    cities_snapshots: Sequence[ForecastSnapshot],
    target_date: date,
    *,
    settings: AppSettings,
    feed_failure_reasons: Mapping[FeedType, str] | None = None,
) -> DailyForecast:
    """Build the complete daily object after each feed resolves independently."""
    reasons = feed_failure_reasons or {}
    country = parse_country_forecast(
        country_snapshots,
        target_date,
        unavailable_reason=reasons.get(FeedType.COUNTRY),
    )
    cities = parse_cities_forecast(
        cities_snapshots,
        target_date,
        settings=settings,
        unavailable_reason=reasons.get(FeedType.CITIES),
    )
    configured_ids = list(settings.cities)
    actual_ids = [city.city_id for city in cities]
    if actual_ids != configured_ids:
        raise ForecastDataError(
            "Daily forecast city IDs do not exactly match configured IDs; "
            f"expected={configured_ids}, actual={actual_ids}"
        )
    return DailyForecast(
        forecast_date=target_date,
        country_forecast=country,
        city_forecasts=cities,
    )


def _candidate_roots(
    snapshots: Sequence[ForecastSnapshot],
    feed_type: FeedType,
    target_date: date,
) -> list[_ParsedCandidate]:
    candidates: list[_ParsedCandidate] = []
    expected_root = {
        FeedType.COUNTRY: "IsraelWeatherForecastMorning",
        FeedType.CITIES: "IsraelCitiesWeatherForecastMorning",
    }[feed_type]
    for position, snapshot in enumerate(snapshots):
        if snapshot.feed_type is not feed_type or target_date not in snapshot.forecast_dates:
            continue
        try:
            root = _parse_snapshot_xml(snapshot.xml)
        except etree.XMLSyntaxError:
            continue
        if root.tag != expected_root:
            continue
        candidates.append(_ParsedCandidate(position, snapshot, root))
    return candidates


def _parse_snapshot_xml(xml: str):
    normalized = re.sub(
        r"encoding=['\"][^'\"]+['\"]",
        'encoding="UTF-8"',
        xml,
        count=1,
        flags=re.IGNORECASE,
    )
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    return etree.fromstring(normalized.encode("utf-8"), parser=parser)


def _country_time_unit(root, target_date: date):
    target = target_date.isoformat()
    for time_unit in root.findall("Location/LocationData/TimeUnitData"):
        if (time_unit.findtext("Date") or "").strip() == target:
            return time_unit
    raise ForecastDataError(f"no country values for exact date {target}")


def _parse_city_candidate(
    candidate: _ParsedCandidate,
    city_settings: CitySettings,
    target_date: date,
    settings: AppSettings,
    unavailable_reason: str | None,
) -> CityForecast:
    locations = [
        location
        for location in candidate.root.findall("Location")
        if (location.findtext("LocationMetaData/LocationId") or "").strip()
        == city_settings.id
    ]
    if len(locations) > 1:
        raise ForecastDataError(
            f"duplicate configured location {city_settings.id} in one snapshot"
        )
    if not locations:
        raise ForecastDataError(f"missing configured city {city_settings.id}")

    target = target_date.isoformat()
    time_units = [
        item
        for item in locations[0].findall("LocationData/TimeUnitData")
        if (item.findtext("Date") or "").strip() == target
    ]
    if not time_units:
        raise ForecastDataError(f"city {city_settings.id} has no values for exact date {target}")
    elements = time_units[0].findall("Element")

    min_temp = _required_int(elements, "Minimum temperature", city_settings.id)
    max_temp = _required_int(elements, "Maximum temperature", city_settings.id)
    if min_temp > max_temp:
        raise ForecastDataError(
            f"city {city_settings.id} minimum temperature exceeds maximum temperature"
        )

    weather_code = (_element_value(elements, "Weather code") or "").strip()
    if not weather_code:
        raise ForecastDataError(f"city {city_settings.id} has no weather code")
    if weather_code not in settings.weather_codes:
        raise ForecastDataError(
            f"city {city_settings.id} has unknown weather code {weather_code!r}"
        )
    weather = settings.weather_codes[weather_code]

    humidity_min = _optional_int(
        elements, "Minimum relative humidity", city_settings.id
    )
    humidity_max = _optional_int(
        elements, "Maximum relative humidity", city_settings.id
    )
    for label, value in (("minimum", humidity_min), ("maximum", humidity_max)):
        if value is not None and not 0 <= value <= 100:
            raise ForecastDataError(
                f"city {city_settings.id} {label} humidity is outside 0..100"
            )
    if humidity_min is not None and humidity_max is not None and humidity_min > humidity_max:
        raise ForecastDataError(
            f"city {city_settings.id} minimum humidity exceeds maximum humidity"
        )

    wind_value = _element_value(elements, "Wind direction and speed")
    wind_direction, wind_speed = _parse_wind_data(wind_value, city_settings.id)

    return CityForecast(
        city_id=city_settings.id,
        city_name_hebrew=city_settings.name_hebrew,
        city_name_english=city_settings.name_english,
        internal_key=city_settings.internal_key,
        forecast_date=target_date,
        min_temp=min_temp,
        max_temp=max_temp,
        weather_code=weather_code,
        weather_description_hebrew=str(weather["hebrew"]),
        weather_description_english=str(weather["english"]),
        humidity_min=humidity_min,
        humidity_max=humidity_max,
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        provenance=_provenance(
            candidate,
            target_date,
            unavailable_reason,
            "preferred cities snapshot had unusable data",
        ),
    )


def _provenance(
    candidate: _ParsedCandidate,
    target_date: date,
    unavailable_reason: str | None,
    default_reason: str,
) -> ForecastProvenance:
    supplied_reason = _optional_text(unavailable_reason)
    needs_reason = (
        candidate.snapshot.source is SnapshotSource.ARCHIVE
        or candidate.position > 0
        or supplied_reason is not None
    )
    fallback_reason = supplied_reason or (default_reason if needs_reason else None)
    return ForecastProvenance(
        snapshot_id=candidate.snapshot.snapshot_id,
        feed_type=candidate.snapshot.feed_type,
        source=candidate.snapshot.source,
        fetched_at=candidate.snapshot.fetched_at,
        issued_at=candidate.snapshot.issued_at,
        source_forecast_date=target_date,
        fallback_reason=fallback_reason,
    )


def _element_value(elements: Sequence, name: str) -> Optional[str]:
    for element in elements:
        if (element.findtext("ElementName") or "").strip() == name:
            value = element.find("ElementValue")
            return "" if value is None or value.text is None else value.text
    return None


def _required_int(elements: Sequence, name: str, city_id: str) -> int:
    value = _element_value(elements, name)
    if value is None or not value.strip():
        raise ForecastDataError(f"city {city_id} is missing {name}")
    try:
        return int(value.strip())
    except ValueError as error:
        raise ForecastDataError(f"city {city_id} has nonnumeric {name}") from error


def _optional_int(elements: Sequence, name: str, city_id: str) -> Optional[int]:
    value = _element_value(elements, name)
    if value is None:
        return None
    try:
        return int(value.strip())
    except ValueError as error:
        raise ForecastDataError(f"city {city_id} has nonnumeric {name}") from error


def _parse_wind_data(
    wind_value: Optional[str], city_id: str
) -> tuple[Optional[str], Optional[str]]:
    if wind_value is None:
        return None, None
    parts = wind_value.strip().split("/")
    numeric_part = re.compile(r"^\d+(?:-\d+)?$")
    if len(parts) != 2 or not all(numeric_part.fullmatch(part.strip()) for part in parts):
        raise ForecastDataError(
            f"city {city_id} has malformed wind direction/speed {wind_value!r}"
        )
    return parts[0].strip(), parts[1].strip()


def _optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
