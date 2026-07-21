"""Validated, immutable values supplied to the future Story template."""

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path
from typing import Any, Mapping, TypeGuard

from src.app_paths import AppPaths
from src.data.models import DailyForecast
from src.settings import AppSettings
from src.utils.date_utils import format_hebrew_calendar_date


class RenderContextError(ValueError):
    """A visible value or local asset is unsafe for Story rendering."""


class CityLabelLayout(str, Enum):
    RTL = "RTL"
    LTR = "LTR"
    TTB = "TTB"


@dataclass(frozen=True)
class StoryCity:
    """One city's template-ready label, temperature, icon, and position."""

    city_id: str
    internal_key: str
    name_hebrew: str
    temperature_text: str
    condition_hebrew: str
    weather_code: str
    icon_uri: str
    x: float
    y: float
    layout: CityLabelLayout


@dataclass(frozen=True)
class StoryAssets:
    """Absolute ``file:`` URIs for the map, logos, and fonts the template needs."""

    map_uri: str
    mot_logo_uri: str
    ims_logo_uri: str
    black_font_uri: str
    semibold_font_uri: str


@dataclass(frozen=True)
class StoryRenderContext:
    """The complete, validated packing list handed to the Story renderer."""

    canvas_width: int
    canvas_height: int
    target_date_iso: str
    header_gregorian_numeric: str
    header_hebrew_calendar: str
    country_description_hebrew: str
    cities: tuple[StoryCity, ...]
    assets: StoryAssets
    used_fallback: bool


def build_story_render_context(
    forecast: DailyForecast,
    settings: AppSettings,
    paths: AppPaths,
) -> StoryRenderContext:
    """Pack and validate every value needed before a browser is opened."""
    width, height = _fixed_canvas(settings.design_tokens)
    description = forecast.country_forecast.description_hebrew
    if not isinstance(description, str) or not description.strip():
        raise RenderContextError("A nonempty country Hebrew description is required")

    configured_ids = list(settings.cities)
    actual_ids = [city.city_id for city in forecast.city_forecasts]
    if (
        len(configured_ids) != 15
        or len(actual_ids) != 15
        or len(set(actual_ids)) != 15
        or set(actual_ids) != set(configured_ids)
    ):
        raise RenderContextError(
            "Forecast city IDs must equal the configured 15 IDs exactly; "
            f"configured={configured_ids}, actual={actual_ids}"
        )
    forecast_by_id = {city.city_id: city for city in forecast.city_forecasts}

    positions = _validated_positions(settings)
    assets = StoryAssets(
        map_uri=_file_uri(paths.assets / "Map" / "Israel Map 01.svg", "Israel map"),
        mot_logo_uri=_file_uri(paths.assets / "Logos" / "mot_logo.svg", "MOT logo"),
        ims_logo_uri=_file_uri(paths.assets / "Logos" / "ims_logo.svg", "IMS logo"),
        black_font_uri=_file_uri(
            paths.assets / "Fonts" / "NotoSansHebrew-Black.ttf",
            "Noto Sans Hebrew Black font",
        ),
        semibold_font_uri=_file_uri(
            paths.assets / "Fonts" / "NotoSansHebrew-SemiBold.ttf",
            "Noto Sans Hebrew SemiBold font",
        ),
    )

    story_cities = []
    for city_id, city_settings in settings.cities.items():
        city = forecast_by_id[city_id]
        if (
            city.internal_key != city_settings.internal_key
            or city.city_name_hebrew != city_settings.name_hebrew
        ):
            raise RenderContextError(
                f"City {city_id} identity does not match configured display values"
            )
        weather = settings.weather_codes.get(city.weather_code)
        if not isinstance(weather, Mapping):
            raise RenderContextError(
                f"City {city_id} has unknown weather code {city.weather_code!r}"
            )
        catalog_hebrew = weather.get("hebrew")
        catalog_english = weather.get("english")
        if (
            city.weather_description_hebrew != catalog_hebrew
            or city.weather_description_english != catalog_english
        ):
            raise RenderContextError(
                f"City {city_id} weather description does not match code {city.weather_code}"
            )
        icon = weather.get("icon")
        if not _safe_plain_filename(icon):
            raise RenderContextError(
                f"Weather code {city.weather_code} has an unsafe icon filename"
            )

        position = positions[city_settings.internal_key]
        story_cities.append(
            StoryCity(
                city_id=city_id,
                internal_key=city_settings.internal_key,
                name_hebrew=city_settings.name_hebrew,
                temperature_text=f"{city.min_temp}° - {city.max_temp}°",
                condition_hebrew=str(catalog_hebrew),
                weather_code=city.weather_code,
                icon_uri=_file_uri(
                    paths.assets / "Weather_Icons" / icon,
                    f"weather icon for code {city.weather_code}",
                ),
                x=position[0],
                y=position[1],
                layout=position[2],
            )
        )

    target_date = forecast.forecast_date
    return StoryRenderContext(
        canvas_width=width,
        canvas_height=height,
        target_date_iso=target_date.isoformat(),
        header_gregorian_numeric=target_date.strftime("%d/%m/%Y"),
        header_hebrew_calendar=format_hebrew_calendar_date(target_date),
        country_description_hebrew=description.strip(),
        cities=tuple(story_cities),
        assets=assets,
        used_fallback=forecast.is_fallback,
    )


def _fixed_canvas(tokens: Mapping[str, Any]) -> tuple[int, int]:
    canvas = tokens.get("canvas")
    if not isinstance(canvas, Mapping):
        raise RenderContextError("Design settings require a canvas object")
    width = canvas.get("width")
    height = canvas.get("height")
    if type(width) is not int or type(height) is not int or (width, height) != (1080, 1920):
        raise RenderContextError("Story canvas must be exactly 1080x1920")
    return width, height


def _validated_positions(
    settings: AppSettings,
) -> dict[str, tuple[float, float, CityLabelLayout]]:
    positions = settings.design_tokens.get("city_positions")
    if not isinstance(positions, Mapping):
        raise RenderContextError("Design settings require city positions")
    expected = {city.internal_key for city in settings.cities.values()}
    actual = set(positions)
    if actual != expected:
        raise RenderContextError(
            "City positions must match configured keys exactly; "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )

    validated = {}
    for city_key, raw_position in positions.items():
        if not isinstance(raw_position, Mapping):
            raise RenderContextError(f"Position {city_key!r} must be an object")
        x = raw_position.get("x")
        y = raw_position.get("y")
        if not _finite_number(x):
            raise RenderContextError(
                f"Position {city_key!r} requires finite numeric x"
            )
        if not _finite_number(y):
            raise RenderContextError(
                f"Position {city_key!r} requires finite numeric y"
            )
        try:
            layout = CityLabelLayout(raw_position.get("layout"))
        except ValueError as error:
            raise RenderContextError(
                f"Position {city_key!r} has unsupported layout {raw_position.get('layout')!r}"
            ) from error
        validated[city_key] = (float(x), float(y), layout)
    return validated


def _file_uri(path: Path, label: str) -> str:
    resolved = path.resolve()
    if not resolved.is_file():
        raise RenderContextError(f"{label} must be an existing ordinary file: {resolved}")
    try:
        with resolved.open("rb") as asset_file:
            header = asset_file.read(200)
    except OSError as error:
        raise RenderContextError(f"{label} could not be read: {resolved}") from error
    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise RenderContextError(f"{label} is a Git LFS pointer, not hydrated content")
    return resolved.as_uri()


def _finite_number(value: Any) -> TypeGuard[int | float]:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _safe_plain_filename(value: Any) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value == value.strip()
        and value not in {".", ".."}
        and "/" not in value
        and "\\" not in value
        and Path(value).name == value
        and not Path(value).is_absolute()
    )
