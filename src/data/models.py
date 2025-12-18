"""
Data Models - Structured Types for Forecast Data

This module defines dataclasses that represent weather forecast data.
Using dataclasses makes the code clearer and provides automatic
type checking and nice string representations.

Think of these like TypeScript interfaces or Figma component properties -
they define the "shape" of our data.

Models:
    CityForecast    - Weather data for a single city
    CountryForecast - General weather description for Israel
    DailyForecast   - Complete data package for one day
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class CityForecast:
    """
    Weather forecast for a single city on a single day.
    
    This represents one <Location> element from the isr_cities.xml file.
    Each city has temperature, weather condition, and optional wind/humidity.
    
    Attributes:
        city_id: IMS location ID (e.g., "510" for Jerusalem)
        city_name_hebrew: City name in Hebrew (e.g., "ירושלים")
        city_name_english: City name in English (e.g., "Jerusalem")
        forecast_date: The date this forecast is for
        min_temp: Minimum temperature in Celsius
        max_temp: Maximum temperature in Celsius
        weather_code: IMS weather code (e.g., "1250" for Clear)
        weather_description_hebrew: Condition in Hebrew (e.g., "בהיר")
        weather_description_english: Condition in English (e.g., "Clear")
        humidity_min: Minimum relative humidity % (optional)
        humidity_max: Maximum relative humidity % (optional)
        wind_direction: Wind direction in degrees, e.g., "315-45" (optional)
        wind_speed: Wind speed in km/h, e.g., "10-30" (optional)
    """
    city_id: str
    city_name_hebrew: str
    city_name_english: str
    forecast_date: date
    
    min_temp: int
    max_temp: int
    
    weather_code: str
    weather_description_hebrew: str
    weather_description_english: str
    
    # Optional fields - not always present in XML
    humidity_min: Optional[int] = None
    humidity_max: Optional[int] = None
    wind_direction: Optional[str] = None
    wind_speed: Optional[str] = None


@dataclass
class CountryForecast:
    """
    General weather description for all of Israel.
    
    This contains the narrative forecast text from isr_country.xml,
    describing overall weather conditions and any warnings.
    
    Attributes:
        forecast_date: The date this forecast is for
        description_hebrew: Main forecast text in Hebrew
        description_english: Main forecast text in English
        warning_hebrew: Any active weather warning in Hebrew (optional)
        warning_english: Any active weather warning in English (optional)
    """
    forecast_date: date
    description_hebrew: str
    description_english: str
    warning_hebrew: Optional[str] = None
    warning_english: Optional[str] = None


@dataclass
class DailyForecast:
    """
    Complete forecast data for a single day.
    
    This is the "master object" that gets passed to the renderer.
    It contains everything needed to generate a forecast image.
    
    Attributes:
        forecast_date: The date this forecast is for
        country_forecast: General weather description
        city_forecasts: List of all 15 city forecasts
        xml_fetch_time: When we fetched the XML (for debugging)
        is_fallback: True if using archived data instead of fresh fetch
    """
    forecast_date: date
    country_forecast: CountryForecast
    city_forecasts: List[CityForecast]
    
    # Metadata for debugging and logging
    xml_fetch_time: datetime = field(default_factory=datetime.now)
    is_fallback: bool = False
    
    def get_city_by_id(self, city_id: str) -> Optional[CityForecast]:
        """
        Find a city forecast by its IMS ID.
        
        Args:
            city_id: The IMS location ID (e.g., "510")
            
        Returns:
            CityForecast if found, None otherwise
        """
        for city in self.city_forecasts:
            if city.city_id == city_id:
                return city
        return None
    
    def get_city_by_name(self, name_english: str) -> Optional[CityForecast]:
        """
        Find a city forecast by its English name.
        
        Args:
            name_english: City name in English (e.g., "Jerusalem")
            
        Returns:
            CityForecast if found, None otherwise
        """
        for city in self.city_forecasts:
            if city.city_name_english.lower() == name_english.lower():
                return city
        return None
