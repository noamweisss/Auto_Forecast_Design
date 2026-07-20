"""Validated application configuration loaded at the application boundary."""

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, TypeGuard

from src.app_paths import AppPaths


class ConfigurationError(RuntimeError):
    """Configuration cannot be read or does not satisfy the application contract."""


@dataclass(frozen=True)
class CitySettings:
    """Display and design identity for one configured IMS city."""

    id: str
    internal_key: str
    name_hebrew: str
    name_english: str


@dataclass(frozen=True)
class AppSettings:
    """All committed configuration needed by parsing and future rendering."""

    cities: Mapping[str, CitySettings]
    weather_codes: Mapping[str, Mapping[str, Any]]
    design_tokens: Mapping[str, Any]


def load_settings(paths: AppPaths) -> AppSettings:
    """Load and validate application settings from ``paths``."""
    cities_document = _read_json(paths.config / "cities.json")
    weather_document = _read_json(paths.config / "00_ims_weather_codes.json")
    design_tokens = _read_json(paths.config / "design_tokens.json")

    city_entries = _required_mapping(cities_document, "cities", "cities.json")
    weather_entries = _required_mapping(
        weather_document,
        "israel_forecast_codes",
        "00_ims_weather_codes.json",
    )
    city_positions = _required_mapping(
        design_tokens,
        "city_positions",
        "design_tokens.json",
    )

    cities = _validate_cities(city_entries)
    _validate_design_positions(cities, city_positions)
    weather_codes = _validate_weather_codes(weather_entries)

    return AppSettings(
        cities=MappingProxyType(cities),
        weather_codes=MappingProxyType(weather_codes),
        design_tokens=_freeze(design_tokens),
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            f"{path.name} could not be read as UTF-8 JSON: {error}"
        ) from error

    if not isinstance(value, dict):
        raise ConfigurationError(f"{path.name} must contain a JSON object")
    return value


def _required_mapping(document: Mapping[str, Any], key: str, filename: str) -> Mapping[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ConfigurationError(f"{filename} must contain an object named {key!r}")
    return value


def _validate_cities(entries: Mapping[str, Any]) -> dict[str, CitySettings]:
    if len(entries) != 15:
        raise ConfigurationError(
            f"cities.json must define exactly 15 cities; found {len(entries)}"
        )

    cities: dict[str, CitySettings] = {}
    internal_keys: list[str] = []
    for city_id, raw_city in entries.items():
        if not isinstance(raw_city, dict):
            raise ConfigurationError(f"City {city_id!r} must be a JSON object")
        if raw_city.get("id") != city_id:
            raise ConfigurationError(
                f"City mapping key {city_id!r} must equal its stored ID"
            )

        name_hebrew = raw_city.get("name_hebrew")
        name_english = raw_city.get("name_english")
        if not _nonempty_string(name_hebrew) or not _nonempty_string(name_english):
            raise ConfigurationError(
                f"City {city_id!r} must have nonempty Hebrew and English names"
            )

        internal_key = raw_city.get("internal_key")
        if not _nonempty_string(internal_key):
            raise ConfigurationError(f"City {city_id!r} must have a nonempty internal key")

        city = CitySettings(
            id=city_id,
            internal_key=internal_key,
            name_hebrew=name_hebrew,
            name_english=name_english,
        )
        cities[city_id] = city
        internal_keys.append(internal_key)

    if len(set(internal_keys)) != len(internal_keys):
        raise ConfigurationError("City internal keys must be unique")
    return cities


def _validate_design_positions(
    cities: Mapping[str, CitySettings],
    positions: Mapping[str, Any],
) -> None:
    configured_keys = {city.internal_key for city in cities.values()}
    position_keys = {key for key in positions if not key.startswith("_")}
    if configured_keys != position_keys:
        missing = sorted(configured_keys - position_keys)
        unexpected = sorted(position_keys - configured_keys)
        raise ConfigurationError(
            "City internal keys must exactly match non-metadata design-position keys; "
            f"missing positions={missing}, unexpected positions={unexpected}"
        )


def _validate_weather_codes(
    entries: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    weather_codes: dict[str, Mapping[str, Any]] = {}
    for code, raw_entry in entries.items():
        if not isinstance(raw_entry, dict):
            raise ConfigurationError(f"Weather code {code!r} must be a JSON object")
        if raw_entry.get("code") != code:
            raise ConfigurationError(
                f"Weather mapping key {code!r} must equal its stored code"
            )
        if not _nonempty_string(raw_entry.get("hebrew")) or not _nonempty_string(
            raw_entry.get("english")
        ):
            raise ConfigurationError(
                f"Weather code {code!r} must have nonempty Hebrew and English descriptions"
            )
        weather_codes[code] = _freeze(raw_entry)
    return weather_codes


def _nonempty_string(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def _freeze(value: Any) -> Any:
    """Recursively make loaded JSON values read-only."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
