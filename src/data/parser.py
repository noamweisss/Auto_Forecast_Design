"""
XML Parser - Convert IMS XML to Python Objects

This module parses the raw XML data from IMS into structured
Python dataclasses that are easy to work with.

The parser handles:
- UTF-8 encoding for Hebrew text
- Element extraction from nested XML structure
- Weather code translation
- Date parsing
- Fallback to archived data when fields are missing/invalid

Usage:
    from src.data.parser import parse_country_forecast, parse_cities_forecast
    from src.data.fetcher import fetch_country_forecast, fetch_cities_forecast
    
    country_xml = fetch_country_forecast()
    country_data = parse_country_forecast(country_xml)
    
    cities_xml = fetch_cities_forecast()
    cities_data = parse_cities_forecast(cities_xml)
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import date, datetime
from lxml import etree

from src.data.models import CityForecast, CountryForecast, DailyForecast
from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Path to weather codes configuration
WEATHER_CODES_PATH = Path("config/00_ims_weather_codes.json")
CITIES_CONFIG_PATH = Path("config/cities.json")

# Cache for weather codes (loaded once)
_weather_codes_cache: Optional[dict] = None
_cities_config_cache: Optional[dict] = None


def _normalize_xml_encoding(xml_content: str) -> bytes:
    """
    Normalize XML encoding declaration to match actual content.
    
    IMS sends XML with encoding="ISO-8859-8" declaration but we've
    decoded it to a Python string (Unicode). This function updates
    the declaration to UTF-8 and encodes as bytes for lxml.
    
    Args:
        xml_content: XML string that's already been decoded to Unicode
    
    Returns:
        UTF-8 encoded bytes with correct encoding declaration
    """
    # Replace any encoding declaration with UTF-8
    # Matches: encoding="ISO-8859-8" or encoding='windows-1255' etc.
    normalized = re.sub(
        r'encoding=["\'][^"\']+["\']',
        'encoding="UTF-8"',
        xml_content,
        count=1
    )
    return normalized.encode('utf-8')


def _load_weather_codes() -> dict:
    """Load and cache weather codes from JSON config."""
    global _weather_codes_cache
    
    if _weather_codes_cache is None:
        try:
            with open(WEATHER_CODES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Use israel_forecast_codes as primary
                _weather_codes_cache = data.get("israel_forecast_codes", {})
                logger.debug(f"Loaded {len(_weather_codes_cache)} weather codes")
        except Exception as e:
            logger.error(f"Failed to load weather codes: {e}")
            _weather_codes_cache = {}
    
    return _weather_codes_cache


def _load_cities_config() -> dict:
    """Load and cache cities configuration from JSON."""
    global _cities_config_cache
    
    if _cities_config_cache is None:
        try:
            with open(CITIES_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _cities_config_cache = data.get("cities", {})
                logger.debug(f"Loaded {len(_cities_config_cache)} city configurations")
        except Exception as e:
            logger.error(f"Failed to load cities config: {e}")
            _cities_config_cache = {}
    
    return _cities_config_cache


def _get_weather_description(code: str) -> Tuple[str, str]:
    """
    Look up weather code in configuration and return descriptions.
    
    Args:
        code: IMS weather code (e.g., "1250")
    
    Returns:
        Tuple of (hebrew_description, english_description)
        Returns ("Unknown", "Unknown") if code not found
    """
    weather_codes = _load_weather_codes()
    
    if code in weather_codes:
        code_data = weather_codes[code]
        return (code_data.get("hebrew", "לא ידוע"), code_data.get("english", "Unknown"))
    
    # Code not found - this triggers fallback behavior
    logger.warning(f"Unknown weather code: {code}")
    return ("לא ידוע", "Unknown")


def _get_internal_key(city_id: str) -> str:
    """
    Get the internal key for a city ID from cities.json.
    
    Args:
        city_id: IMS location ID (e.g., "510")
    
    Returns:
        Internal key (e.g., "jerusalem") or lowercase city ID if not found
    """
    cities_config = _load_cities_config()
    
    if city_id in cities_config:
        return cities_config[city_id].get("internal_key", city_id.lower())
    
    logger.warning(f"City ID {city_id} not found in cities.json")
    return city_id.lower()


def _get_city_names(city_id: str, xml_name_eng: str, xml_name_heb: str) -> Tuple[str, str]:
    """
    Get standardized city names from config, falling back to XML values.
    
    This ensures consistent spelling (e.g., "Eilat" not "Elat").
    
    Args:
        city_id: IMS location ID
        xml_name_eng: English name from XML (fallback)
        xml_name_heb: Hebrew name from XML (fallback)
    
    Returns:
        Tuple of (english_name, hebrew_name)
    """
    cities_config = _load_cities_config()
    
    if city_id in cities_config:
        config = cities_config[city_id]
        name_eng = config.get("name_english", xml_name_eng)
        name_heb = config.get("name_hebrew", xml_name_heb)
        return (name_eng, name_heb)
    
    # City not in config, use XML values
    return (xml_name_eng, xml_name_heb)



def _extract_element_value(elements: List, name: str) -> Optional[str]:
    """
    Find an Element with matching ElementName and return its ElementValue.
    
    Args:
        elements: List of <Element> nodes
        name: The ElementName to search for
    
    Returns:
        The ElementValue text, or None if not found
    """
    for element in elements:
        element_name = element.find("ElementName")
        if element_name is not None and element_name.text == name:
            element_value = element.find("ElementValue")
            if element_value is not None:
                return element_value.text
    return None


def _parse_wind_data(wind_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse wind direction and speed from IMS format.
    
    IMS format: "315-45/10-30" means direction 315-45 degrees, speed 10-30 km/h
    
    Args:
        wind_str: String like "315-45/10-30"
    
    Returns:
        Tuple of (direction, speed) or (None, None) if parse fails
    """
    if not wind_str or "/" not in wind_str:
        return (None, None)
    
    try:
        parts = wind_str.split("/")
        direction = parts[0] if len(parts) > 0 else None
        speed = parts[1] if len(parts) > 1 else None
        return (direction, speed)
    except Exception:
        return (None, None)


def parse_country_forecast(
    xml_content: str,
    target_date: Optional[date] = None
) -> CountryForecast:
    """
    Parse country-wide forecast XML into a CountryForecast object.
    
    Args:
        xml_content: Raw XML string from IMS country forecast
        target_date: Date to extract forecast for (default: today)
        
    Returns:
        CountryForecast object with parsed data
        
    Raises:
        ValueError: If XML parsing fails or no data found for date
    """
    if target_date is None:
        target_date = date.today()
    
    target_date_str = target_date.isoformat()
    
    try:
        # Parse XML - normalize encoding declaration first
        xml_bytes = _normalize_xml_encoding(xml_content)
        root = etree.fromstring(xml_bytes)
        
        # Find the TimeUnitData for our target date
        location = root.find("Location")
        if location is None:
            raise ValueError("No Location element found in country XML")
        
        location_data = location.find("LocationData")
        if location_data is None:
            raise ValueError("No LocationData element found")
        
        # Find TimeUnitData matching our date
        target_time_unit = None
        for time_unit in location_data.findall("TimeUnitData"):
            date_elem = time_unit.find("Date")
            if date_elem is not None and date_elem.text == target_date_str:
                target_time_unit = time_unit
                break
        
        if target_time_unit is None:
            raise ValueError(f"No forecast data found for date {target_date_str}")
        
        # Extract elements
        elements = target_time_unit.findall("Element")
        
        description_hebrew = _extract_element_value(elements, "Weather in Hebrew") or ""
        description_english = _extract_element_value(elements, "Weather in English") or ""
        warning_hebrew = _extract_element_value(elements, "Warning in Hebrew")
        warning_english = _extract_element_value(elements, "Warning in English")
        
        return CountryForecast(
            forecast_date=target_date,
            description_hebrew=description_hebrew,
            description_english=description_english,
            warning_hebrew=warning_hebrew,
            warning_english=warning_english
        )
        
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML syntax: {e}")


def parse_cities_forecast(
    xml_content: str,
    target_date: Optional[date] = None,
    fallback_xml: Optional[str] = None
) -> List[CityForecast]:
    """
    Parse per-city forecast XML into a list of CityForecast objects.
    
    Implements fallback logic for missing/invalid data:
    - If required fields are missing, uses yesterday's data for that city
    - If weather code is unknown, uses yesterday's data for that city
    
    Args:
        xml_content: Raw XML string from IMS cities forecast
        target_date: Date to extract forecast for (default: today)
        fallback_xml: Optional XML content to use for fallback data
        
    Returns:
        List of CityForecast objects, one per city
    """
    if target_date is None:
        target_date = date.today()
    
    target_date_str = target_date.isoformat()
    cities: List[CityForecast] = []
    
    try:
        root = etree.fromstring(_normalize_xml_encoding(xml_content))
        
        # Parse fallback data if provided
        fallback_cities: dict = {}
        if fallback_xml:
            try:
                fallback_root = etree.fromstring(_normalize_xml_encoding(fallback_xml))
                fallback_cities = _parse_cities_to_dict(fallback_root, target_date_str)
            except Exception as e:
                logger.warning(f"Failed to parse fallback XML: {e}")
        
        # Process each Location
        for location in root.findall("Location"):
            try:
                city_forecast = _parse_single_city(
                    location, target_date_str, target_date, fallback_cities
                )
                if city_forecast:
                    cities.append(city_forecast)
            except Exception as e:
                logger.error(f"Failed to parse city: {e}")
                continue
        
        logger.info(f"Parsed {len(cities)} city forecasts")
        return cities
        
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML syntax: {e}")


def _parse_cities_to_dict(root, target_date_str: str) -> dict:
    """
    Parse cities XML into a dictionary keyed by city_id.
    Used for fallback data lookup.
    """
    result = {}
    
    for location in root.findall("Location"):
        try:
            metadata = location.find("LocationMetaData")
            if metadata is None:
                continue
            
            city_id = metadata.find("LocationId")
            if city_id is None:
                continue
            
            location_data = location.find("LocationData")
            if location_data is None:
                continue
            
            # Find data for any available date (preferring target date)
            for time_unit in location_data.findall("TimeUnitData"):
                date_elem = time_unit.find("Date")
                if date_elem is not None:
                    elements = time_unit.findall("Element")
                    result[city_id.text] = {
                        "elements": elements,
                        "date": date_elem.text,
                        "metadata": metadata
                    }
                    break  # Use first available date
                    
        except Exception:
            continue
    
    return result


def _parse_single_city(
    location,
    target_date_str: str,
    target_date: date,
    fallback_cities: dict
) -> Optional[CityForecast]:
    """
    Parse a single city's forecast data.
    
    Implements fallback logic for missing/invalid data.
    """
    metadata = location.find("LocationMetaData")
    if metadata is None:
        return None
    
    # Extract city info
    city_id_elem = metadata.find("LocationId")
    city_id = city_id_elem.text if city_id_elem is not None else None
    if not city_id:
        return None
    
    city_name_heb_elem = metadata.find("LocationNameHeb")
    city_name_eng_elem = metadata.find("LocationNameEng")
    xml_name_hebrew = city_name_heb_elem.text if city_name_heb_elem is not None else ""
    xml_name_english = city_name_eng_elem.text if city_name_eng_elem is not None else ""
    
    # Get standardized names from config (fixes spelling inconsistencies like Elat→Eilat)
    city_name_english, city_name_hebrew = _get_city_names(city_id, xml_name_english, xml_name_hebrew)
    
    # Get internal key for design tokens mapping
    internal_key = _get_internal_key(city_id)
    
    # Find forecast data for target date
    location_data = location.find("LocationData")
    if location_data is None:
        logger.error(f"No LocationData for city {city_id}")
        return _use_fallback_city(city_id, city_name_hebrew, city_name_english, 
                                  internal_key, target_date, fallback_cities,
                                  "Missing LocationData")
    
    target_time_unit = None
    for time_unit in location_data.findall("TimeUnitData"):
        date_elem = time_unit.find("Date")
        if date_elem is not None and date_elem.text == target_date_str:
            target_time_unit = time_unit
            break
    
    if target_time_unit is None:
        logger.error(f"No data for date {target_date_str} for city {city_id}")
        return _use_fallback_city(city_id, city_name_hebrew, city_name_english,
                                  internal_key, target_date, fallback_cities,
                                  f"No data for date {target_date_str}")
    
    # Extract forecast elements
    elements = target_time_unit.findall("Element")
    
    # Extract required fields
    max_temp_str = _extract_element_value(elements, "Maximum temperature")
    min_temp_str = _extract_element_value(elements, "Minimum temperature")
    weather_code = _extract_element_value(elements, "Weather code")
    
    # Check for missing required fields
    missing_fields = []
    if max_temp_str is None:
        missing_fields.append("max_temp")
    if min_temp_str is None:
        missing_fields.append("min_temp")
    if weather_code is None:
        missing_fields.append("weather_code")
    
    if missing_fields:
        logger.error(f"Missing required fields {missing_fields} for city {city_name_english}")
        return _use_fallback_city(city_id, city_name_hebrew, city_name_english,
                                  internal_key, target_date, fallback_cities,
                                  f"Missing fields: {missing_fields}")
    
    # Parse temperature values
    try:
        max_temp = int(max_temp_str)
        min_temp = int(min_temp_str)
    except ValueError as e:
        logger.error(f"Invalid temperature values for {city_name_english}: {e}")
        return _use_fallback_city(city_id, city_name_hebrew, city_name_english,
                                  internal_key, target_date, fallback_cities,
                                  f"Invalid temperature: {e}")
    
    # Get weather description (check for unknown code)
    weather_hebrew, weather_english = _get_weather_description(weather_code)
    if weather_hebrew == "לא ידוע":
        logger.warning(f"Unknown weather code '{weather_code}' for {city_name_english}. Using yesterday's data.")
        return _use_fallback_city(city_id, city_name_hebrew, city_name_english,
                                  internal_key, target_date, fallback_cities,
                                  f"Unknown weather code: {weather_code}")
    
    # Extract optional fields
    humidity_max_str = _extract_element_value(elements, "Maximum relative humidity")
    humidity_min_str = _extract_element_value(elements, "Minimum relative humidity")
    wind_data = _extract_element_value(elements, "Wind direction and speed")
    
    humidity_max = int(humidity_max_str) if humidity_max_str else None
    humidity_min = int(humidity_min_str) if humidity_min_str else None
    wind_direction, wind_speed = _parse_wind_data(wind_data) if wind_data else (None, None)
    
    return CityForecast(
        city_id=city_id,
        city_name_hebrew=city_name_hebrew,
        city_name_english=city_name_english,
        internal_key=internal_key,
        forecast_date=target_date,
        min_temp=min_temp,
        max_temp=max_temp,
        weather_code=weather_code,
        weather_description_hebrew=weather_hebrew,
        weather_description_english=weather_english,
        humidity_min=humidity_min,
        humidity_max=humidity_max,
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        is_fallback=False
    )


def _use_fallback_city(
    city_id: str,
    city_name_hebrew: str,
    city_name_english: str,
    internal_key: str,
    target_date: date,
    fallback_cities: dict,
    reason: str
) -> Optional[CityForecast]:
    """
    Create a CityForecast using fallback data.
    
    Logs a notification and marks the city's data as fallback.
    """
    if city_id not in fallback_cities:
        logger.error(
            f"FALLBACK FAILED: No archive data available for {city_name_english} ({city_id}). "
            f"Reason: {reason}"
        )
        return None
    
    fallback_data = fallback_cities[city_id]
    elements = fallback_data["elements"]
    fallback_date_str = fallback_data["date"]
    
    # Notify user about fallback
    logger.warning(
        f"USING FALLBACK DATA for {city_name_english}: {reason}. "
        f"Using data from {fallback_date_str}"
    )
    
    # Extract data from fallback
    max_temp_str = _extract_element_value(elements, "Maximum temperature")
    min_temp_str = _extract_element_value(elements, "Minimum temperature")
    weather_code = _extract_element_value(elements, "Weather code")
    
    if not all([max_temp_str, min_temp_str, weather_code]):
        logger.error(f"Fallback data also incomplete for {city_name_english}")
        return None
    
    try:
        max_temp = int(max_temp_str)
        min_temp = int(min_temp_str)
    except ValueError:
        logger.error(f"Fallback data has invalid temperatures for {city_name_english}")
        return None
    
    weather_hebrew, weather_english = _get_weather_description(weather_code)
    
    # Extract optional fields
    humidity_max_str = _extract_element_value(elements, "Maximum relative humidity")
    humidity_min_str = _extract_element_value(elements, "Minimum relative humidity")
    wind_data = _extract_element_value(elements, "Wind direction and speed")
    
    humidity_max = int(humidity_max_str) if humidity_max_str else None
    humidity_min = int(humidity_min_str) if humidity_min_str else None
    wind_direction, wind_speed = _parse_wind_data(wind_data) if wind_data else (None, None)
    
    return CityForecast(
        city_id=city_id,
        city_name_hebrew=city_name_hebrew,
        city_name_english=city_name_english,
        internal_key=internal_key,
        forecast_date=target_date,  # Use target date, not fallback date
        min_temp=min_temp,
        max_temp=max_temp,
        weather_code=weather_code,
        weather_description_hebrew=weather_hebrew,
        weather_description_english=weather_english,
        humidity_min=humidity_min,
        humidity_max=humidity_max,
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        is_fallback=True  # Mark as fallback
    )


def parse_daily_forecast(
    country_xml: str,
    cities_xml: str,
    target_date: Optional[date] = None,
    fallback_cities_xml: Optional[str] = None
) -> DailyForecast:
    """
    Parse both XML sources into a complete DailyForecast.
    
    This is the main entry point for parsing - it combines both
    data sources into a single object ready for rendering.
    
    Args:
        country_xml: Raw XML from country forecast
        cities_xml: Raw XML from cities forecast
        target_date: Date to extract (default: today)
        fallback_cities_xml: Optional XML for city fallback data
        
    Returns:
        DailyForecast object containing everything needed for image generation
    """
    if target_date is None:
        target_date = date.today()
    
    logger.info(f"Parsing daily forecast for {target_date}")
    
    # Parse country forecast
    country_forecast = parse_country_forecast(country_xml, target_date)
    
    # Parse city forecasts with fallback
    city_forecasts = parse_cities_forecast(cities_xml, target_date, fallback_cities_xml)
    
    # Check how many cities used fallback
    fallback_count = sum(1 for c in city_forecasts if c.is_fallback)
    if fallback_count > 0:
        logger.warning(f"{fallback_count} cities using fallback data")
    
    return DailyForecast(
        forecast_date=target_date,
        country_forecast=country_forecast,
        city_forecasts=city_forecasts,
        xml_fetch_time=datetime.now(),
        is_fallback=False  # Overall fetch succeeded
    )


# Allow running this module directly for testing
if __name__ == "__main__":
    from src.data.fetcher import fetch_cities_forecast, fetch_country_forecast
    
    print("Testing XML parser...")
    print("-" * 50)
    
    # Fetch live data
    country_xml = fetch_country_forecast()
    cities_xml = fetch_cities_forecast()
    
    if country_xml and cities_xml:
        try:
            forecast = parse_daily_forecast(country_xml, cities_xml)
            print(f"\n✓ Parsed forecast for {forecast.forecast_date}")
            print(f"  Country description: {forecast.country_forecast.description_hebrew[:50]}...")
            print(f"  Cities parsed: {len(forecast.city_forecasts)}")
            
            for city in forecast.city_forecasts[:3]:
                fallback_mark = " [FALLBACK]" if city.is_fallback else ""
                print(f"    - {city.city_name_english}: {city.min_temp}°-{city.max_temp}° {city.weather_description_hebrew}{fallback_mark}")
        except Exception as e:
            print(f"✗ Parse failed: {e}")
    else:
        print("✗ Failed to fetch XML")
