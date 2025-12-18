"""
Date Utilities - Hebrew and Georgian Date Formatting

This module provides date formatting for the forecast header,
which displays both Hebrew and Georgian (Gregorian) dates.

Example Output:
    Hebrew: "כ״א בכסלו תשפ״ה"
    Georgian: "18 בדצמבר 2024"
    Day of Week: "יום רביעי"

Dependencies:
    For Hebrew calendar conversion, you'll need to install:
    pip install hebrew-calendar
    
    (Alternative: convertdate library also works)

Usage:
    from src.utils.date_utils import get_formatted_dates
    from datetime import date
    
    dates = get_formatted_dates(date(2024, 12, 18))
    print(dates["hebrew"])       # "כ״א בכסלו תשפ״ה"
    print(dates["georgian"])     # "18 בדצמבר 2024"
    print(dates["day_of_week"])  # "יום רביעי"
"""

from datetime import date
from typing import Dict

# Hebrew month names (for Georgian calendar display in Hebrew)
GEORGIAN_MONTHS_HEBREW = {
    1: "בינואר",
    2: "בפברואר",
    3: "במרץ",
    4: "באפריל",
    5: "במאי",
    6: "ביוני",
    7: "ביולי",
    8: "באוגוסט",
    9: "בספטמבר",
    10: "באוקטובר",
    11: "בנובמבר",
    12: "בדצמבר"
}

# Hebrew day names
DAYS_OF_WEEK_HEBREW = {
    0: "יום שני",
    1: "יום שלישי",
    2: "יום רביעי",
    3: "יום חמישי",
    4: "יום שישי",
    5: "יום שבת",
    6: "יום ראשון"
}


def get_formatted_dates(target_date: date) -> Dict[str, str]:
    """
    Get all date formats needed for the forecast header.
    
    Args:
        target_date: The date to format
        
    Returns:
        Dictionary with:
        {
            "hebrew": "כ״א בכסלו תשפ״ה",
            "georgian": "18 בדצמבר 2024",
            "day_of_week": "יום רביעי"
        }
    """
    return {
        "hebrew": get_hebrew_date(target_date),
        "georgian": get_georgian_date_hebrew(target_date),
        "day_of_week": get_day_of_week_hebrew(target_date)
    }


def get_hebrew_date(target_date: date) -> str:
    """
    Convert a Gregorian date to Hebrew calendar format.
    
    Args:
        target_date: Gregorian date to convert
        
    Returns:
        Hebrew date string like "כ״א בכסלו תשפ״ה"
        
    Note:
        Requires hebrew-calendar or convertdate library.
        Will return placeholder if library not installed.
    """
    # TODO: Implement with hebrew-calendar library in Phase 3
    # For now, return a placeholder
    return f"[Hebrew date for {target_date.isoformat()}]"


def get_georgian_date_hebrew(target_date: date) -> str:
    """
    Format a Gregorian date in Hebrew style.
    
    Args:
        target_date: Date to format
        
    Returns:
        String like "18 בדצמבר 2024"
    """
    day = target_date.day
    month = GEORGIAN_MONTHS_HEBREW[target_date.month]
    year = target_date.year
    
    return f"{day} {month} {year}"


def get_day_of_week_hebrew(target_date: date) -> str:
    """
    Get the Hebrew name of the day of the week.
    
    Args:
        target_date: Date to get day name for
        
    Returns:
        Hebrew day name like "יום רביעי" (Wednesday)
        
    Note:
        Python's weekday() returns 0=Monday through 6=Sunday
    """
    weekday = target_date.weekday()
    return DAYS_OF_WEEK_HEBREW[weekday]


def format_date_for_filename(target_date: date) -> str:
    """
    Format a date for use in filenames.
    
    Args:
        target_date: Date to format
        
    Returns:
        ISO format string like "2024-12-18"
    """
    return target_date.isoformat()
