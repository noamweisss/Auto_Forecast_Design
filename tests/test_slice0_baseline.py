"""Offline baseline contracts for committed IMS fixtures and design assets."""

import json

from lxml import etree
from PIL import Image

from src.app_paths import PATHS
from src.settings import load_settings
from tests.conftest import load_ims_fixture


EXPECTED_FORECAST_DATES = {"2025-12-17", "2025-12-18", "2025-12-19", "2025-12-20"}
EXPECTED_ISRAEL_ICONS = {
    "1010": "warning.png",
    "1020": "thunderstorm.png",
    "1060": "snow.png",
    "1070": "snow.png",
    "1080": "snow.png",
    "1140": "rainy.png",
    "1160": "cloudy.png",
    "1220": "partly_cloudy.png",
    "1230": "cloudy.png",
    "1250": "clear.png",
    "1260": "windy.png",
    "1270": "cloudy.png",
    "1300": "frost.png",
    "1310": "hot.png",
    "1320": "frost.png",
    "1510": "thunderstorm.png",
    "1520": "snow.png",
    "1530": "partly_cloudy_rain.png",
    "1540": "partly_cloudy_rain.png",
    "1560": "rainy.png",
    "1570": "warning.png",
    "1580": "very_hot.png",
    "1590": "frost.png",
}


def test_cities_fixture_preserves_ims_metadata_dates_and_configured_cities():
    root = etree.fromstring(load_ims_fixture("cities_forecast.xml").encode("utf-8"))
    configured_city_ids = set(
        json.loads((PATHS.config / "cities.json").read_text(encoding="utf-8"))["cities"]
    )

    assert root.findtext("Originator/Organization") == "Israel Meteorological Service"
    assert root.findtext("Identification/IssueDateTime") == "2025-12-17 04:23"
    assert {item.findtext("Date") for item in root.findall(".//TimeUnitData")} == EXPECTED_FORECAST_DATES
    assert {item.findtext("LocationMetaData/LocationId") for item in root.findall("Location")} == configured_city_ids
    assert root.findtext(".//LocationNameHeb") == "אילת"


def test_country_fixture_preserves_ims_metadata_and_all_forecast_dates():
    root = etree.fromstring(load_ims_fixture("country_forecast.xml").encode("utf-8"))

    assert root.findtext("Originator/Organization") == "Israel Meteorological Service"
    assert root.findtext("Identification/IssueDateTime") == "2025-12-17 04:23"
    assert {item.findtext("Date") for item in root.findall(".//TimeUnitData")} == EXPECTED_FORECAST_DATES
    assert "היום:" in root.findtext(".//Element[ElementName='Weather in Hebrew']/ElementValue")


def test_all_supported_israel_codes_use_existing_160_pixel_icons():
    settings = load_settings(PATHS)

    assert {
        code: entry["icon"] for code, entry in settings.weather_codes.items()
    } == EXPECTED_ISRAEL_ICONS
    for entry in settings.weather_codes.values():
        icon_path = PATHS.assets / "Weather_Icons" / entry["icon"]
        assert icon_path.is_file()
        with Image.open(icon_path) as image:
            assert image.size == (160, 160)


def test_parallel_icon_and_token_sources_are_removed():
    assert not (PATHS.root / "src" / "design" / "icon_mapper.py").exists()
    assert not (PATHS.root / "src" / "design" / "tokens.py").exists()
