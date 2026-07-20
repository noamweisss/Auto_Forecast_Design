"""Offline baseline contracts for committed IMS fixtures and design assets."""

import json

from lxml import etree

from src.app_paths import PATHS
from src.design.icon_mapper import ICONS_DIR, WEATHER_CODE_TO_ICON
from tests.conftest import load_ims_fixture


EXPECTED_FORECAST_DATES = {"2025-12-17", "2025-12-18", "2025-12-19", "2025-12-20"}


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


def test_every_mapped_weather_icon_is_a_committed_asset():
    missing = sorted(
        filename for filename in set(WEATHER_CODE_TO_ICON.values()) if not (ICONS_DIR / filename).is_file()
    )

    assert missing == []
