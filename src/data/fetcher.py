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

import time
import requests
from typing import Optional

from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# IMS XML data URLs
COUNTRY_FORECAST_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml"
CITIES_FORECAST_URL = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml"

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
RETRY_DELAYS = [30, 60]  # Wait times between retries (seconds)


def fetch_country_forecast() -> Optional[str]:
    """
    Fetch the country-wide weather forecast XML from IMS.
    
    This XML contains:
    - General weather description for Israel (Hebrew and English)
    - Multi-day forecast text
    - Any active weather warnings
    
    Returns:
        XML content as a string, or None if fetch fails after all retries
    """
    logger.info("Fetching country forecast from IMS...")
    return fetch_with_retry(COUNTRY_FORECAST_URL)


def fetch_cities_forecast() -> Optional[str]:
    """
    Fetch the per-city weather forecast XML from IMS.
    
    This XML contains forecast data for 15 Israeli cities:
    - Temperature (min/max)
    - Weather code (maps to condition and icon)
    - Humidity
    - Wind direction and speed
    
    Returns:
        XML content as a string, or None if fetch fails after all retries
    """
    logger.info("Fetching cities forecast from IMS...")
    return fetch_with_retry(CITIES_FORECAST_URL)


def fetch_with_retry(url: str, retries: int = 3) -> Optional[str]:
    """
    Fetch a URL with automatic retry on failure.
    
    Implements the retry strategy from the project plan:
    - Attempt 1: Immediate
    - Attempt 2: After 30 seconds
    - Attempt 3: After 60 seconds
    
    Args:
        url: The URL to fetch
        retries: Number of retry attempts (default: 3)
    
    Returns:
        Response content as string (UTF-8 decoded), or None if all retries fail
    """
    for attempt in range(1, retries + 1):
        try:
            logger.debug(f"Fetch attempt {attempt}/{retries}: {url}")
            
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx
            
            # Try multiple encodings for Hebrew content
            # IMS sometimes sends data in Windows-1255 or ISO-8859-8
            xml_content = None
            for encoding in ['utf-8', 'windows-1255', 'iso-8859-8']:
                try:
                    xml_content = response.content.decode(encoding)
                    logger.debug(f"Successfully decoded with {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if xml_content is None:
                raise UnicodeDecodeError(
                    'multiple', response.content, 0, len(response.content),
                    'Could not decode with utf-8, windows-1255, or iso-8859-8'
                )
            
            logger.info(f"Successfully fetched {len(xml_content)} bytes from IMS")
            return xml_content
            
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt}: Request timed out after {REQUEST_TIMEOUT}s")
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Attempt {attempt}: HTTP error {e.response.status_code}: {e}")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Attempt {attempt}: Connection error: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt}: Request failed: {e}")
            
        except UnicodeDecodeError as e:
            logger.error(f"Attempt {attempt}: Failed to decode response as UTF-8: {e}")
        
        # Wait before next retry (if not the last attempt)
        if attempt < retries:
            delay = RETRY_DELAYS[attempt - 1] if attempt - 1 < len(RETRY_DELAYS) else 60
            logger.info(f"Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    # All retries failed
    logger.error(f"Failed to fetch {url} after {retries} attempts")
    return None


def fetch_xml(url: str) -> Optional[str]:
    """
    Single fetch attempt (no retry).
    
    Useful for testing or when you want to handle retries yourself.
    
    Args:
        url: The URL to fetch
    
    Returns:
        XML content as string, or None on failure
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


# Allow running this module directly for quick testing
if __name__ == "__main__":
    print("Testing IMS XML fetch...")
    print("-" * 50)
    
    # Test country forecast
    country = fetch_country_forecast()
    if country:
        print(f"✓ Country forecast: {len(country)} bytes")
        # Show first 200 chars as preview
        print(f"  Preview: {country[:200]}...")
    else:
        print("✗ Failed to fetch country forecast")
    
    print()
    
    # Test cities forecast
    cities = fetch_cities_forecast()
    if cities:
        print(f"✓ Cities forecast: {len(cities)} bytes")
        print(f"  Preview: {cities[:200]}...")
    else:
        print("✗ Failed to fetch cities forecast")
