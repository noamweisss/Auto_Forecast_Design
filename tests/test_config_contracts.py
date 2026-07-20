"""Fast checks for the committed configuration that drives every forecast."""

import json
from datetime import date, datetime, timezone

from src.app_paths import PATHS
from src.data.parser import parse_cities_forecast
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from src.settings import load_settings
from tests.conftest import load_ims_fixture


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


def test_parser_uses_configured_city_names_from_any_working_directory(monkeypatch, tmp_path):
    """Parser configuration is anchored to the repository, not the shell cwd."""
    monkeypatch.chdir(tmp_path)
    settings = load_settings(PATHS)
    snapshot = build_snapshot(
        load_ims_fixture("cities_forecast.xml"),
        FeedType.CITIES,
        source=SnapshotSource.FIXTURE,
        fetched_at=datetime(2025, 12, 17, 3, 0, tzinfo=timezone.utc),
    )

    city = next(
        city
        for city in parse_cities_forecast(
            [snapshot], date(2025, 12, 17), settings=settings
        )
        if city.city_id == "510"
    )

    assert city.city_name_english == settings.cities["510"].name_english
    assert city.city_name_hebrew == settings.cities["510"].name_hebrew
