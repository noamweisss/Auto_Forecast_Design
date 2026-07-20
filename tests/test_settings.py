"""Validated, immutable application settings contracts."""

import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
import math
from pathlib import Path

import pytest

from src.app_paths import AppPaths, PATHS
from src.data.parser import parse_cities_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from src.settings import ConfigurationError, load_settings
from tests.conftest import load_ims_fixture


def _fixture_snapshot():
    return build_snapshot(
        load_ims_fixture("cities_forecast.xml"),
        FeedType.CITIES,
        source=SnapshotSource.FIXTURE,
        fetched_at=datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc),
    )


def _copy_valid_config(destination: Path) -> AppPaths:
    config_dir = destination / "config"
    config_dir.mkdir(parents=True)
    for name in ("cities.json", "00_ims_weather_codes.json", "design_tokens.json"):
        (config_dir / name).write_bytes((PATHS.config / name).read_bytes())
    return AppPaths(root=destination)


def _read_json(paths: AppPaths, name: str) -> dict:
    return json.loads((paths.config / name).read_text(encoding="utf-8"))


def _write_json(paths: AppPaths, name: str, value: dict) -> None:
    (paths.config / name).write_text(
        json.dumps(value, ensure_ascii=False), encoding="utf-8"
    )


def test_load_settings_reads_all_committed_configuration_once():
    settings = load_settings(PATHS)

    assert len(settings.cities) == 15
    assert settings.cities["510"].internal_key == "jerusalem"
    assert settings.weather_codes["1250"]["english"] == "Clear"
    assert settings.weather_codes["1250"]["icon"] == "clear.png"
    assert settings.design_tokens["canvas"]["width"] == 1080


def test_design_tokens_keep_only_python_required_sections_and_values():
    settings = load_settings(PATHS)

    assert set(settings.design_tokens) == {"_meta", "canvas", "city_positions"}
    assert dict(settings.design_tokens["canvas"]) == {"width": 1080, "height": 1920}
    assert len(settings.design_tokens["city_positions"]) == 15
    assert settings.design_tokens["city_positions"]["jerusalem"] == {
        "x": 456,
        "y": 871,
        "layout": "RTL",
    }


def test_settings_values_are_immutable():
    settings = load_settings(PATHS)

    with pytest.raises(FrozenInstanceError):
        settings.cities["510"].internal_key = "changed"
    with pytest.raises(TypeError):
        settings.cities["510"] = settings.cities["510"]
    with pytest.raises(TypeError):
        settings.design_tokens["canvas"]["width"] = 1


def test_city_parser_uses_the_explicit_settings_value(tmp_path):
    paths = _copy_valid_config(tmp_path)
    cities = _read_json(paths, "cities.json")
    cities["cities"]["510"]["name_english"] = "Configured Jerusalem"
    _write_json(paths, "cities.json", cities)
    settings = load_settings(paths)

    city = next(
        city
        for city in parse_cities_forecast(
            [_fixture_snapshot()], date(2025, 12, 17), settings=settings
        )
        if city.city_id == "510"
    )

    assert city.city_name_english == "Configured Jerusalem"


def test_city_parser_requires_keyword_only_settings():
    settings = load_settings(PATHS)

    with pytest.raises(TypeError):
        parse_cities_forecast([_fixture_snapshot()], date(2025, 12, 17), settings)


@pytest.mark.parametrize("filename", ["cities.json", "00_ims_weather_codes.json", "design_tokens.json"])
def test_missing_configuration_file_has_actionable_error(tmp_path, filename):
    paths = _copy_valid_config(tmp_path)
    (paths.config / filename).unlink()

    with pytest.raises(ConfigurationError, match=rf"{filename}.*read"):
        load_settings(paths)


def test_invalid_utf8_json_has_actionable_error(tmp_path):
    paths = _copy_valid_config(tmp_path)
    (paths.config / "cities.json").write_bytes(b"\xff")

    with pytest.raises(ConfigurationError, match=r"cities\.json.*UTF-8 JSON"):
        load_settings(paths)


def test_city_configuration_requires_exactly_fifteen_cities(tmp_path):
    paths = _copy_valid_config(tmp_path)
    cities = _read_json(paths, "cities.json")
    cities["cities"].pop("520")
    _write_json(paths, "cities.json", cities)

    with pytest.raises(ConfigurationError, match="exactly 15 cities"):
        load_settings(paths)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda city: city.update(id="different"), "mapping key.*stored ID"),
        (lambda city: city.update(name_hebrew=""), "nonempty Hebrew and English names"),
        (lambda city: city.update(name_english=""), "nonempty Hebrew and English names"),
        (lambda city: city.update(internal_key=""), "nonempty internal key"),
    ],
)
def test_city_entry_validation_is_actionable(tmp_path, change, message):
    paths = _copy_valid_config(tmp_path)
    cities = _read_json(paths, "cities.json")
    change(cities["cities"]["510"])
    _write_json(paths, "cities.json", cities)

    with pytest.raises(ConfigurationError, match=message):
        load_settings(paths)


def test_city_internal_keys_must_be_unique(tmp_path):
    paths = _copy_valid_config(tmp_path)
    cities = _read_json(paths, "cities.json")
    cities["cities"]["510"]["internal_key"] = cities["cities"]["520"]["internal_key"]
    _write_json(paths, "cities.json", cities)

    with pytest.raises(ConfigurationError, match="unique"):
        load_settings(paths)


def test_city_internal_keys_must_exactly_match_design_positions(tmp_path):
    paths = _copy_valid_config(tmp_path)
    tokens = _read_json(paths, "design_tokens.json")
    tokens["city_positions"]["extra_city"] = {"x": 0, "y": 0}
    _write_json(paths, "design_tokens.json", tokens)

    with pytest.raises(ConfigurationError, match="exactly match.*design-position"):
        load_settings(paths)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda tokens: tokens["canvas"].update(width=1079), "1080x1920"),
        (lambda tokens: tokens["canvas"].update(height="1920"), "1080x1920"),
        (lambda tokens: tokens["canvas"].update(extra=1), "width and height"),
        (lambda tokens: tokens.update(extra={}), "exactly.*_meta.*canvas.*city_positions"),
    ],
)
def test_design_token_structure_and_canvas_are_strict(tmp_path, change, message):
    paths = _copy_valid_config(tmp_path)
    tokens = _read_json(paths, "design_tokens.json")
    change(tokens)
    _write_json(paths, "design_tokens.json", tokens)

    with pytest.raises(ConfigurationError, match=message):
        load_settings(paths)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("x", "456", "finite numeric x"),
        ("x", True, "finite numeric x"),
        ("x", math.inf, "finite numeric x"),
        ("y", math.nan, "finite numeric y"),
        ("layout", "AUTO", "RTL, LTR, or TTB"),
    ],
)
def test_city_position_fields_are_validated(tmp_path, field, value, message):
    paths = _copy_valid_config(tmp_path)
    tokens = _read_json(paths, "design_tokens.json")
    tokens["city_positions"]["jerusalem"][field] = value
    _write_json(paths, "design_tokens.json", tokens)

    with pytest.raises(ConfigurationError, match=message):
        load_settings(paths)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda entry: entry.update(code="different"), "mapping key.*stored code"),
        (lambda entry: entry.update(hebrew=""), "nonempty Hebrew and English descriptions"),
        (lambda entry: entry.update(english=""), "nonempty Hebrew and English descriptions"),
    ],
)
def test_weather_entry_validation_is_actionable(tmp_path, change, message):
    paths = _copy_valid_config(tmp_path)
    weather = _read_json(paths, "00_ims_weather_codes.json")
    change(weather["israel_forecast_codes"]["1250"])
    _write_json(paths, "00_ims_weather_codes.json", weather)

    with pytest.raises(ConfigurationError, match=message):
        load_settings(paths)


@pytest.mark.parametrize(
    "icon",
    ["", " clear.png ", "../clear.png", "nested/clear.png", "nested\\clear.png"],
)
def test_weather_icon_must_be_a_safe_plain_filename(tmp_path, icon):
    paths = _copy_valid_config(tmp_path)
    weather = _read_json(paths, "00_ims_weather_codes.json")
    weather["israel_forecast_codes"]["1250"]["icon"] = icon
    _write_json(paths, "00_ims_weather_codes.json", weather)

    with pytest.raises(ConfigurationError, match="safe plain icon filename"):
        load_settings(paths)
