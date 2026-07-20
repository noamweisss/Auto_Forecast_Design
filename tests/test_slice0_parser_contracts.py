"""Temporary, strict contracts for parser defects found during the Slice 0 audit."""

from datetime import date

from lxml import etree
import pytest

from tests.conftest import load_ims_fixture
from src.data.parser import parse_cities_forecast


def _with_eilat_maximum_removed(xml_content: str, forecast_date: str) -> str:
    root = etree.fromstring(xml_content.encode("utf-8"))
    eilat = next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == "520"
    )
    time_unit = next(
        item
        for item in eilat.findall("LocationData/TimeUnitData")
        if item.findtext("Date") == forecast_date
    )
    maximum = next(
        element
        for element in time_unit.findall("Element")
        if element.findtext("ElementName") == "Maximum temperature"
    )
    time_unit.remove(maximum)
    return etree.tostring(root, encoding="unicode")


def _with_invalid_eilat_optional_data(xml_content: str, forecast_date: str) -> str:
    root = etree.fromstring(xml_content.encode("utf-8"))
    eilat = next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == "520"
    )
    time_unit = next(
        item
        for item in eilat.findall("LocationData/TimeUnitData")
        if item.findtext("Date") == forecast_date
    )
    humidity = next(
        element
        for element in time_unit.findall("Element")
        if element.findtext("ElementName") == "Maximum relative humidity"
    )
    humidity.find("ElementValue").text = "not-a-number"
    return etree.tostring(root, encoding="unicode")


@pytest.mark.xfail(
    strict=True,
    reason="F-02: fallback chooses the first available XML date instead of the target date.",
)
def test_f02_fallback_uses_target_date_values_from_multiday_xml():
    target_date = date(2025, 12, 18)
    fallback_xml = load_ims_fixture("cities_forecast.xml")
    invalid_primary_xml = _with_eilat_maximum_removed(fallback_xml, target_date.isoformat())

    cities = parse_cities_forecast(
        invalid_primary_xml,
        target_date=target_date,
        fallback_xml=fallback_xml,
    )
    eilat = next(city for city in cities if city.city_id == "520")

    assert eilat.is_fallback is True
    assert eilat.max_temp == 17


@pytest.mark.xfail(
    strict=True,
    reason="F-03: invalid optional city data can be swallowed and return fewer than 15 cities.",
)
def test_f03_invalid_optional_city_data_cannot_return_incomplete_forecast():
    target_date = date(2025, 12, 17)
    invalid_xml = _with_invalid_eilat_optional_data(
        load_ims_fixture("cities_forecast.xml"), target_date.isoformat()
    )

    with pytest.raises(ValueError, match="configured 15-city set"):
        parse_cities_forecast(invalid_xml, target_date=target_date)
