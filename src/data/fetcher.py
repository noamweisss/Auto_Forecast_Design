"""
XML Fetcher - Download Weather Data from IMS

This module handles fetching XML forecast data from the Israel
Meteorological Service (IMS) website.

Data Sources:
    - Country forecast: https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml
    - Cities forecast: https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml

Both files contain Hebrew text, so proper UTF-8 encoding is critical.

Usage:
    from src.data.fetcher import fetch_country_forecast, fetch_cities_forecast
    
    country_xml = fetch_country_forecast()
    cities_xml = fetch_cities_forecast()
"""

import requests
from typing import Optional

# IMS XML data URLs
COUNTRY_FORECAST_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml"
CITIES_FORECAST_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml"

# Request timeout in seconds
REQUEST_TIMEOUT = 30


def fetch_country_forecast() -> Optional[str]:
    """
    Fetch the country-wide weather forecast XML from IMS.
    
    This XML contains:
    - General weather description for Israel (Hebrew and English)
    - Multi-day forecast text
    - Any active weather warnings
    
    Returns:
        XML content as a string, or None if fetch fails
        
    Raises:
        requests.RequestException: If the HTTP request fails
    """
    # TODO: Implement in Phase 2
    # - Make HTTP GET request
    # - Handle encoding (UTF-8 for Hebrew)
    # - Return XML string
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")


def fetch_cities_forecast() -> Optional[str]:
    """
    Fetch the per-city weather forecast XML from IMS.
    
    This XML contains forecast data for 15 Israeli cities:
    - Temperature (min/max)
    - Weather code (maps to condition and icon)
    - Humidity
    - Wind direction and speed
    
    Returns:
        XML content as a string, or None if fetch fails
        
    Raises:
        requests.RequestException: If the HTTP request fails
    """
    # TODO: Implement in Phase 2
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")


def fetch_with_retry(url: str, retries: int = 3) -> Optional[str]:
    """
    Fetch a URL with automatic retry on failure.
    
    Args:
        url: The URL to fetch
        retries: Number of retry attempts (default: 3)
    
    Returns:
        Response content as string, or None if all retries fail
    """
    # TODO: Implement in Phase 2
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")
