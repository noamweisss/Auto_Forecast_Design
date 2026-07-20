"""Validated, template-ready packing list for the future Story renderer."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timezone
from pathlib import Path
import shutil
from typing import Mapping
from urllib.parse import unquote, urlparse

import pytest

from src.app_paths import AppPaths, PATHS
from src.data.models import DailyForecast
from src.data.parser import parse_daily_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from src.design.render_context import (
    CityLabelLayout,
    RenderContextError,
    StoryCity,
    build_story_render_context,
)
from tests.conftest import load_ims_fixture


FIXTURE_DATE = date(2025, 12, 18)
STORY_DATE = date(2025, 11, 17)
FETCHED_AT = datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc)


def _snapshot(feed_type: FeedType):
    fixture = {
        FeedType.COUNTRY: "country_forecast.xml",
        FeedType.CITIES: "cities_forecast.xml",
    }[feed_type]
    return build_snapshot(
        load_ims_fixture(fixture),
        feed_type,
        source=SnapshotSource.FIXTURE,
        fetched_at=FETCHED_AT,
    )


def _forecast(settings) -> DailyForecast:
    parsed = parse_daily_forecast(
        [_snapshot(FeedType.COUNTRY)],
        [_snapshot(FeedType.CITIES)],
        FIXTURE_DATE,
        settings=settings,
    )
    country = replace(
        parsed.country_forecast,
        forecast_date=STORY_DATE,
        provenance=replace(
            parsed.country_forecast.provenance,
            source_forecast_date=STORY_DATE,
        ),
    )
    cities = [
        replace(
            city,
            forecast_date=STORY_DATE,
            provenance=replace(city.provenance, source_forecast_date=STORY_DATE),
        )
        for city in parsed.city_forecasts
    ]
    return DailyForecast(STORY_DATE, country, cities)


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _settings_with_position_change(settings, change):
    tokens = _thaw(settings.design_tokens)
    change(tokens["city_positions"])
    return replace(settings, design_tokens=tokens)


def _copy_render_assets(destination: Path, settings) -> AppPaths:
    relative_files = {
        Path("Map") / "Israel Map 01.svg",
        Path("Logos") / "ims_logo.svg",
        Path("Logos") / "mot_logo.svg",
        Path("Fonts") / "NotoSansHebrew-Black.ttf",
        Path("Fonts") / "NotoSansHebrew-SemiBold.ttf",
    }
    relative_files.update(
        Path("Weather_Icons") / str(entry["icon"])
        for entry in settings.weather_codes.values()
    )
    for relative in relative_files:
        target = destination / "assets" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PATHS.assets / relative, target)
    return AppPaths(root=destination)


def _uri_path(uri: str) -> Path:
    parsed = urlparse(uri)
    path = unquote(parsed.path)
    if len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]
    return Path(path)


def test_valid_forecast_builds_fifteen_story_cities_in_settings_order(app_settings):
    forecast = _forecast(app_settings)
    forecast.city_forecasts.reverse()

    context = build_story_render_context(forecast, app_settings, PATHS)

    assert context.canvas_width == 1080
    assert context.canvas_height == 1920
    assert context.target_date_iso == "2025-11-17"
    assert context.header_gregorian_numeric == "17/11/2025"
    assert context.header_hebrew_calendar == "כ״ו בחשוון התשפ״ו"
    assert [city.city_id for city in context.cities] == list(app_settings.cities)
    assert len({city.city_id for city in context.cities}) == len(context.cities) == 15


def test_temperature_layouts_and_physical_positions_are_template_ready(app_settings):
    forecast = _forecast(app_settings)
    context = build_story_render_context(forecast, app_settings, PATHS)

    by_id = {city.city_id: city for city in forecast.city_forecasts}
    for city in context.cities:
        source = by_id[city.city_id]
        position = app_settings.design_tokens["city_positions"][city.internal_key]
        assert city.temperature_text == f"{source.min_temp}° - {source.max_temp}°"
        assert city.x == float(position["x"])
        assert city.y == float(position["y"])
        assert city.layout.value == position["layout"]
    assert {city.layout for city in context.cities} == set(CityLabelLayout)
    assert next(city for city in context.cities if city.city_id == "510").x == 456.0


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate"])
def test_forecast_city_ids_must_exactly_match_configuration(kind, app_settings):
    forecast = _forecast(app_settings)
    if kind == "missing":
        forecast.city_forecasts.pop()
    elif kind == "extra":
        forecast.city_forecasts.append(
            replace(forecast.city_forecasts[-1], city_id="999")
        )
    else:
        forecast.city_forecasts[-1] = replace(
            forecast.city_forecasts[-1],
            city_id=forecast.city_forecasts[0].city_id,
        )

    with pytest.raises(RenderContextError, match="city IDs.*configured 15"):
        build_story_render_context(forecast, app_settings, PATHS)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda positions: positions.pop("jerusalem"), "missing.*jerusalem"),
        (
            lambda positions: positions["jerusalem"].update(x=float("nan")),
            "finite numeric x",
        ),
        (
            lambda positions: positions["jerusalem"].update(layout="AUTO"),
            "unsupported layout",
        ),
    ],
)
def test_invalid_positions_fail_before_rendering(change, message, app_settings):
    settings = _settings_with_position_change(app_settings, change)

    with pytest.raises(RenderContextError, match=message):
        build_story_render_context(_forecast(app_settings), settings, PATHS)


def test_missing_country_hebrew_text_fails_before_rendering(app_settings):
    forecast = _forecast(app_settings)
    forecast.country_forecast = replace(
        forecast.country_forecast,
        description_hebrew="  ",
    )

    with pytest.raises(RenderContextError, match="country Hebrew description"):
        build_story_render_context(forecast, app_settings, PATHS)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda city: replace(city, weather_code="9999"), "unknown weather code"),
        (
            lambda city: replace(city, weather_description_hebrew="לא תואם"),
            "description does not match",
        ),
    ],
)
def test_unknown_or_mismatched_weather_catalog_values_fail(change, message, app_settings):
    forecast = _forecast(app_settings)
    forecast.city_forecasts[0] = change(forecast.city_forecasts[0])

    with pytest.raises(RenderContextError, match=message):
        build_story_render_context(forecast, app_settings, PATHS)


def test_asset_and_font_uris_are_absolute_existing_files(app_settings):
    context = build_story_render_context(_forecast(app_settings), app_settings, PATHS)
    asset_uris = [getattr(context.assets, field.name) for field in fields(context.assets)]

    assert all(uri.startswith("file:///") for uri in asset_uris)
    assert all(_uri_path(uri).is_file() for uri in asset_uris)
    assert "%20" in context.assets.map_uri
    assert context.assets.black_font_uri.endswith("NotoSansHebrew-Black.ttf")
    assert context.assets.semibold_font_uri.endswith("NotoSansHebrew-SemiBold.ttf")
    assert all("ExtraCondensed" not in uri for uri in asset_uris)
    assert all(_uri_path(city.icon_uri).is_file() for city in context.cities)


def test_missing_asset_fails_before_rendering(tmp_path, app_settings):
    paths = _copy_render_assets(tmp_path, app_settings)
    (paths.assets / "Logos" / "mot_logo.svg").unlink()

    with pytest.raises(RenderContextError, match="MOT logo.*ordinary file"):
        build_story_render_context(_forecast(app_settings), app_settings, paths)


def test_git_lfs_pointer_asset_is_rejected(tmp_path, app_settings):
    paths = _copy_render_assets(tmp_path, app_settings)
    (paths.assets / "Map" / "Israel Map 01.svg").write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
        "size 123\n",
        encoding="utf-8",
    )

    with pytest.raises(RenderContextError, match="Israel map.*Git LFS pointer"):
        build_story_render_context(_forecast(app_settings), app_settings, paths)


def test_context_is_frozen_and_contains_only_template_values(app_settings):
    context = build_story_render_context(_forecast(app_settings), app_settings, PATHS)

    assert isinstance(context.cities, tuple)
    assert all(isinstance(city, StoryCity) for city in context.cities)
    assert isinstance(context.country_description_hebrew, str)
    assert not hasattr(context, "forecast")
    with pytest.raises(FrozenInstanceError):
        context.canvas_width = 1
    with pytest.raises(FrozenInstanceError):
        context.cities[0].x = 0


def test_used_fallback_is_derived_from_forecast_provenance(app_settings):
    forecast = _forecast(app_settings)
    first = forecast.city_forecasts[0]
    forecast.city_forecasts[0] = replace(
        first,
        provenance=replace(
            first.provenance,
            fallback_reason="preferred cities snapshot had unusable data",
        ),
    )

    context = build_story_render_context(forecast, app_settings, PATHS)

    assert context.used_fallback is True


def test_context_building_is_independent_of_current_working_directory(
    monkeypatch, tmp_path, app_settings
):
    monkeypatch.chdir(tmp_path)

    context = build_story_render_context(_forecast(app_settings), app_settings, PATHS)

    assert len(context.cities) == 15
