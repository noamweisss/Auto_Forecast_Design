"""
Icon Mapper - Weather Code to Icon File Mapping

This module maps IMS weather codes to the corresponding icon files
in assets/Weather_Icons/.

Weather codes are documented in docs/00_ims_weather_codes.json.

Usage:
    from src.design.icon_mapper import get_weather_icon_path, get_weather_description
    
    icon_path = get_weather_icon_path("1250")  # "assets/Weather_Icons/clear.png"
    description = get_weather_description("1250")  # ("בהיר", "Clear")
"""

from pathlib import Path
from typing import Tuple, Optional

# Path to weather icons folder
ICONS_DIR = Path("assets/Weather_Icons")

# Mapping from IMS weather codes to icon filenames
# Based on docs/00_ims_weather_codes.json
WEATHER_CODE_TO_ICON = {
    # Clear/Sunny conditions
    "1250": "clear.png",           # בהיר / Clear
    "1240": "mostly_clear.png",    # נאה / Bright, Sunny
    
    # Cloudy conditions
    "1220": "partly_cloudy.png",   # מעונן חלקית / Partly cloudy
    "1230": "cloudy.png",          # מעונן / Cloudy
    "1200": "mostly_cloudy.png",   # כיסוי מלא / Overcast
    
    # Rain conditions
    "1140": "rainy.png",           # גשם / Rain
    "1530": "partly_cloudy_rain.png",  # מעונן חלקית, אפשרות לגשם
    "1540": "partly_cloudy_rain.png",  # מעונן, אפשרות לגשם
    "1560": "rainy.png",           # מעונן, גשם קל
    "1090": "heavy_rain.png",      # ממטרים כבדים
    
    # Snow conditions
    "1060": "snow.png",            # שלג / Snow
    "1070": "snow.png",            # שלג קל / Light snow
    "1520": "snow.png",            # שלג כבד / Heavy snow
    
    # Severe weather
    "1020": "thunderstorm.png",    # סופת רעמים / Thunderstorms
    "1510": "thunderstorm.png",    # סוער / Stormy
    "1010": "warning.png",         # סופות חול / Sandstorms
    
    # Temperature conditions
    "1310": "hot.png",             # חם / Hot
    "1580": "very_hot.png",        # חם מאד / Extremely hot
    "1300": "frost.png",           # קרה / Frost
    "1320": "frost.png",           # קר / Cold
    
    # Wind
    "1260": "windy.png",           # רוחות ערות / Windy
}


def get_weather_icon_path(weather_code: str) -> Optional[Path]:
    """
    Get the icon file path for a weather code.
    
    Args:
        weather_code: IMS weather code (e.g., "1250")
        
    Returns:
        Path to the icon file, or None if code not recognized
        
    Example:
        path = get_weather_icon_path("1250")
        # Returns: Path("assets/Weather_Icons/clear.png")
    """
    icon_filename = WEATHER_CODE_TO_ICON.get(weather_code)
    
    if icon_filename is None:
        # Unknown code - return a default or None
        return None
    
    return ICONS_DIR / icon_filename


def get_weather_description(weather_code: str) -> Tuple[str, str]:
    """
    Get the Hebrew and English description for a weather code.
    
    Args:
        weather_code: IMS weather code (e.g., "1250")
        
    Returns:
        Tuple of (hebrew_description, english_description)
        
    Note: This should be loaded from docs/00_ims_weather_codes.json
          for a complete implementation.
    """
    # TODO: Implement in Phase 3 - load from JSON file
    raise NotImplementedError("Will be implemented in Phase 3: Design System")


def load_weather_codes() -> dict:
    """
    Load the complete weather codes mapping from JSON.
    
    Returns:
        Dictionary with all weather code data from 00_ims_weather_codes.json
    """
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")
