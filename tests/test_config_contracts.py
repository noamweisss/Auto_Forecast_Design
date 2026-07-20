"""Fast checks for the committed configuration that drives every forecast."""

import json
from datetime import date

from src.app_paths import PATHS
from src.data.parser import parse_cities_forecast
from src.settings import load_settings

SINGLE_CITY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<IsraelCitiesWeatherForecastMorning>
  <Location>
    <LocationMetaData>
      <LocationId>510</LocationId>
      <LocationNameEng>Different XML name</LocationNameEng>
      <LocationNameHeb>שם XML שונה</LocationNameHeb>
    </LocationMetaData>
    <LocationData><TimeUnitData><Date>2025-12-22</Date>
      <Element>
        <ElementName>Maximum temperature</ElementName><ElementValue>15</ElementValue>
      </Element>
      <Element>
        <ElementName>Minimum temperature</ElementName><ElementValue>8</ElementValue>
      </Element>
      <Element>
        <ElementName>Weather code</ElementName><ElementValue>1250</ElementValue>
      </Element>
    </TimeUnitData></LocationData>
  </Location>
</IsraelCitiesWeatherForecastMorning>
"""


def load_json(name: str) -> dict:
    return json.loads((PATHS.config / name).read_text(encoding="utf-8"))


def test_configured_city_keys_match_design_positions():
    cities = load_json("cities.json")["cities"]
    positions = load_json("design_tokens.json")["city_positions"]

    positioned_city_keys = {key for key in positions if not key.startswith("_")}

    assert {city["internal_key"] for city in cities.values()} == positioned_city_keys
    assert len(cities) == 15


def test_every_configured_city_has_display_names():
    cities = load_json("cities.json")["cities"]

    for city_id, city in cities.items():
        assert city["id"] == city_id
        assert city["name_hebrew"]
        assert city["name_english"]


def test_parser_uses_configured_hebrew_city_name_from_any_working_directory(monkeypatch, tmp_path):
    """Parser configuration is anchored to the repository, not the shell cwd."""
    monkeypatch.chdir(tmp_path)
    settings = load_settings(PATHS)

    city = parse_cities_forecast(
        SINGLE_CITY_XML,
        target_date=date(2025, 12, 22),
        settings=settings,
    )[0]

    assert city.city_name_english == "Jerusalem"
    assert city.city_name_hebrew == "ירושלים"
