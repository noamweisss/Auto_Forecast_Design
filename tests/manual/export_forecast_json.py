"""
Manual Data Verification Script

This script fetches live data from IMS and exports it to a readable JSON file.
Use this to verify the data pipeline is working correctly.

Usage:
    python tests/manual/export_forecast_json.py

Output:
    tests/manual/output/forecast_YYYY-MM-DD.json
"""

import json
import sys
from datetime import date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.fetcher import fetch_cities_forecast, fetch_country_forecast
from src.data.parser import parse_daily_forecast

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output"


def forecast_to_dict(forecast) -> dict:
    """Convert DailyForecast object to a readable dictionary."""
    return {
        "_meta": {
            "description": "IMS Weather Forecast - Parsed Data Export",
            "generated_at": forecast.xml_fetch_time.isoformat(),
            "forecast_date": forecast.forecast_date.isoformat(),
            "is_fallback": forecast.is_fallback,
            "city_count": len(forecast.city_forecasts)
        },
        "country_forecast": {
            "date": forecast.country_forecast.forecast_date.isoformat(),
            "description_hebrew": forecast.country_forecast.description_hebrew,
            "description_english": forecast.country_forecast.description_english,
            "warning_hebrew": forecast.country_forecast.warning_hebrew,
            "warning_english": forecast.country_forecast.warning_english
        },
        "city_forecasts": [
            {
                "city_id": city.city_id,
                "internal_key": city.internal_key,
                "city_name_hebrew": city.city_name_hebrew,
                "city_name_english": city.city_name_english,
                "date": city.forecast_date.isoformat(),
                "temperature": {
                    "min": city.min_temp,
                    "max": city.max_temp,
                    "display": f"{city.min_temp}°-{city.max_temp}°"
                },
                "weather": {
                    "code": city.weather_code,
                    "description_hebrew": city.weather_description_hebrew,
                    "description_english": city.weather_description_english
                },
                "humidity": {
                    "min": city.humidity_min,
                    "max": city.humidity_max
                } if city.humidity_min else None,
                "wind": {
                    "direction": city.wind_direction,
                    "speed_kmh": city.wind_speed
                } if city.wind_direction else None,
                "is_fallback": city.is_fallback
            }
            for city in forecast.city_forecasts
        ]
    }


def main():
    print("=" * 60)
    print("IMS FORECAST DATA EXPORT")
    print("=" * 60)
    print()
    
    # Fetch data
    print("Fetching data from IMS...")
    country_xml = fetch_country_forecast()
    cities_xml = fetch_cities_forecast()
    
    if not country_xml or not cities_xml:
        print("ERROR: Failed to fetch data from IMS")
        return 1
    
    # Parse data
    print("Parsing XML data...")
    forecast = parse_daily_forecast(country_xml, cities_xml)
    
    # Convert to dictionary
    data = forecast_to_dict(forecast)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Save to JSON
    output_file = OUTPUT_DIR / f"forecast_{forecast.forecast_date.isoformat()}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print()
    print("SUCCESS!")
    print(f"Exported to: {output_file}")
    print()
    print("Summary:")
    print(f"  - Forecast date: {forecast.forecast_date}")
    print(f"  - Cities parsed: {len(forecast.city_forecasts)}")
    print(f"  - Fallback used: {forecast.is_fallback}")
    print()
    print("Open the JSON file to see all the parsed data!")
    
    return 0


if __name__ == "__main__":
    exit(main())
