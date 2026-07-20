"""Validated, immutable application settings contracts."""

import json
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from src.app_paths import AppPaths, PATHS
from src.data.parser import parse_cities_forecast
from src.settings import ConfigurationError, load_settings


SINGLE_CITY_XML = """<IsraelCitiesWeatherForecastMorning>
<Location><LocationMetaData><LocationId>510</LocationId>
<LocationNameEng>XML name</LocationNameEng><LocationNameHeb>XML Hebrew</LocationNameHeb>
</LocationMetaData><LocationData><TimeUnitData><Date>2026-07-20</Date>
<Element><ElementName>Maximum temperature</ElementName><ElementValue>30</ElementValue></Element>
<Element><ElementName>Minimum temperature</ElementName><ElementValue>20</ElementValue></Element>
<Element><ElementName>Weather code</ElementName><ElementValue>1250</ElementValue></Element>
</TimeUnitData></LocationData></Location></IsraelCitiesWeatherForecastMorning>"""


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
    assert settings.design_tokens["canvas"]["width"] == 1080


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

    city = parse_cities_forecast(
        SINGLE_CITY_XML, date(2026, 7, 20), settings=settings
    )[0]

    assert city.city_name_english == "Configured Jerusalem"


def test_city_parser_requires_keyword_only_settings():
    settings = load_settings(PATHS)

    with pytest.raises(TypeError):
        parse_cities_forecast(SINGLE_CITY_XML, date(2026, 7, 20), settings)


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
