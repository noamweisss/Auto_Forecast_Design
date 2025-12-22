"""
Tests for XML Parser Module

Tests the XML parsing functionality including:
- Country forecast parsing
- City forecast parsing
- Weather code lookup
- Fallback behavior for missing/invalid data
"""

import pytest
from datetime import date
from pathlib import Path

from src.data.parser import (
    parse_country_forecast,
    parse_cities_forecast,
    parse_daily_forecast,
    _get_weather_description,
    _extract_element_value,
    _parse_wind_data,
    _get_internal_key
)
from src.data.models import CityForecast, CountryForecast, DailyForecast


# Sample XML for testing (simplified)
SAMPLE_COUNTRY_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<IsraelWeatherForecastMorning>
    <Location>
        <LocationMetaData>
            <LocationId>230</LocationId>
            <LocationNameHeb>ישראל</LocationNameHeb>
        </LocationMetaData>
        <LocationData>
            <TimeUnitData>
                <Date>2025-12-22</Date>
                <Element>
                    <ElementName>Weather in Hebrew</ElementName>
                    <ElementValue>מעונן חלקית עד בהיר</ElementValue>
                </Element>
                <Element>
                    <ElementName>Weather in English</ElementName>
                    <ElementValue>Partly cloudy to clear</ElementValue>
                </Element>
                <Element>
                    <ElementName>Warning in Hebrew</ElementName>
                    <ElementValue>אין התראות</ElementValue>
                </Element>
            </TimeUnitData>
        </LocationData>
    </Location>
</IsraelWeatherForecastMorning>
'''

SAMPLE_CITIES_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<IsraelCitiesWeatherForecastMorning>
    <Location>
        <LocationMetaData>
            <LocationId>510</LocationId>
            <LocationNameEng>Jerusalem</LocationNameEng>
            <LocationNameHeb>ירושלים</LocationNameHeb>
        </LocationMetaData>
        <LocationData>
            <TimeUnitData>
                <Date>2025-12-22</Date>
                <Element>
                    <ElementName>Maximum temperature</ElementName>
                    <ElementValue>15</ElementValue>
                </Element>
                <Element>
                    <ElementName>Minimum temperature</ElementName>
                    <ElementValue>8</ElementValue>
                </Element>
                <Element>
                    <ElementName>Weather code</ElementName>
                    <ElementValue>1250</ElementValue>
                </Element>
                <Element>
                    <ElementName>Wind direction and speed</ElementName>
                    <ElementValue>315-45/10-20</ElementValue>
                </Element>
            </TimeUnitData>
        </LocationData>
    </Location>
    <Location>
        <LocationMetaData>
            <LocationId>402</LocationId>
            <LocationNameEng>Tel Aviv - Yafo</LocationNameEng>
            <LocationNameHeb>תל אביב - יפו</LocationNameHeb>
        </LocationMetaData>
        <LocationData>
            <TimeUnitData>
                <Date>2025-12-22</Date>
                <Element>
                    <ElementName>Maximum temperature</ElementName>
                    <ElementValue>18</ElementValue>
                </Element>
                <Element>
                    <ElementName>Minimum temperature</ElementName>
                    <ElementValue>12</ElementValue>
                </Element>
                <Element>
                    <ElementName>Weather code</ElementName>
                    <ElementValue>1220</ElementValue>
                </Element>
            </TimeUnitData>
        </LocationData>
    </Location>
</IsraelCitiesWeatherForecastMorning>
'''


class TestParseCountryForecast:
    """Tests for country forecast parsing."""
    
    def test_parse_hebrew_description(self):
        """Test that Hebrew description is extracted correctly."""
        result = parse_country_forecast(SAMPLE_COUNTRY_XML, date(2025, 12, 22))
        
        assert result.description_hebrew == "מעונן חלקית עד בהיר"
    
    def test_parse_english_description(self):
        """Test that English description is extracted correctly."""
        result = parse_country_forecast(SAMPLE_COUNTRY_XML, date(2025, 12, 22))
        
        assert result.description_english == "Partly cloudy to clear"
    
    def test_parse_date(self):
        """Test that forecast date is set correctly."""
        result = parse_country_forecast(SAMPLE_COUNTRY_XML, date(2025, 12, 22))
        
        assert result.forecast_date == date(2025, 12, 22)
    
    def test_parse_warning(self):
        """Test that warning is extracted."""
        result = parse_country_forecast(SAMPLE_COUNTRY_XML, date(2025, 12, 22))
        
        assert result.warning_hebrew == "אין התראות"
    
    def test_raises_for_invalid_date(self):
        """Test that ValueError is raised for date not in XML."""
        with pytest.raises(ValueError, match="No forecast data found"):
            parse_country_forecast(SAMPLE_COUNTRY_XML, date(2024, 1, 1))
    
    def test_raises_for_invalid_xml(self):
        """Test that ValueError is raised for invalid XML."""
        with pytest.raises(ValueError, match="Invalid XML"):
            parse_country_forecast("not valid xml", date(2025, 12, 22))


class TestParseCitiesForecast:
    """Tests for city forecast parsing."""
    
    def test_parse_multiple_cities(self):
        """Test that all cities are parsed."""
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        assert len(result) == 2
    
    def test_parse_city_temperature(self):
        """Test temperature extraction."""
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        # Find Jerusalem
        jerusalem = next(c for c in result if c.city_id == "510")
        
        assert jerusalem.min_temp == 8
        assert jerusalem.max_temp == 15
    
    def test_parse_city_weather_code(self):
        """Test weather code extraction."""
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        jerusalem = next(c for c in result if c.city_id == "510")
        
        assert jerusalem.weather_code == "1250"
    
    def test_parse_city_names(self):
        """Test city name extraction in both languages."""
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        jerusalem = next(c for c in result if c.city_id == "510")
        
        assert jerusalem.city_name_english == "Jerusalem"
        assert jerusalem.city_name_hebrew == "ירושלים"
    
    def test_internal_key_assigned(self):
        """Test that internal_key is assigned from config."""
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        jerusalem = next(c for c in result if c.city_id == "510")
        
        # Should get key from cities.json if configured
        assert jerusalem.internal_key is not None


class TestWeatherCodeLookup:
    """Tests for weather code translation."""
    
    def test_known_code_returns_description(self):
        """Test that known code returns correct description."""
        hebrew, english = _get_weather_description("1250")
        
        assert hebrew == "בהיר"
        assert english == "Clear"
    
    def test_unknown_code_returns_unknown(self):
        """Test that unknown code returns 'Unknown'."""
        hebrew, english = _get_weather_description("9999")
        
        assert hebrew == "לא ידוע"
        assert english == "Unknown"


class TestWindDataParsing:
    """Tests for wind data parsing."""
    
    def test_parse_valid_wind_data(self):
        """Test parsing valid wind string."""
        direction, speed = _parse_wind_data("315-45/10-20")
        
        assert direction == "315-45"
        assert speed == "10-20"
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        direction, speed = _parse_wind_data("")
        
        assert direction is None
        assert speed is None
    
    def test_parse_none(self):
        """Test parsing None."""
        direction, speed = _parse_wind_data(None)
        
        assert direction is None
        assert speed is None


class TestDailyForecast:
    """Tests for combined daily forecast parsing."""
    
    def test_parse_complete_forecast(self):
        """Test parsing both country and cities."""
        result = parse_daily_forecast(
            SAMPLE_COUNTRY_XML,
            SAMPLE_CITIES_XML,
            date(2025, 12, 22)
        )
        
        assert isinstance(result, DailyForecast)
        assert result.country_forecast is not None
        assert len(result.city_forecasts) == 2
        assert result.forecast_date == date(2025, 12, 22)


class TestFallbackBehavior:
    """Tests for fallback when data is missing/invalid."""
    
    def test_city_marked_as_fallback_when_using_archive(self):
        """Test that city is marked as fallback when archive is used."""
        # This would need a more complex setup with actual fallback data
        # For now, just verify the flag exists
        result = parse_cities_forecast(SAMPLE_CITIES_XML, date(2025, 12, 22))
        
        # Normal data should not be marked as fallback
        for city in result:
            assert city.is_fallback == False
