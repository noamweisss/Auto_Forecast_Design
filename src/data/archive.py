"""
XML Archive - Backup and Fallback System

This module manages a 7-day rolling archive of XML files.
If today's fetch fails, we can fall back to yesterday's data
(or earlier if needed).

Archive Structure:
    archive/
    ├── 2024-12-18_country.xml
    ├── 2024-12-18_cities.xml
    ├── 2024-12-17_country.xml
    ├── 2024-12-17_cities.xml
    └── ... (up to 7 days of history)

Usage:
    from src.data.archive import save_to_archive, get_fallback_xml
    
    # After successful fetch, save a backup
    save_to_archive(xml_content, "cities", date.today())
    
    # If fetch fails, get archived data
    fallback_xml, archive_date = get_fallback_xml("cities")
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Tuple

# Configuration
ARCHIVE_DIR = Path("archive")
MAX_ARCHIVE_DAYS = 7


def save_to_archive(xml_content: str, xml_type: str, fetch_date: date) -> Path:
    """
    Save XML content to the archive folder.
    
    Args:
        xml_content: The raw XML string to save
        xml_type: Either "country" or "cities"
        fetch_date: The date of the fetch (usually today)
    
    Returns:
        Path to the saved file
        
    Example:
        path = save_to_archive(xml, "cities", date(2024, 12, 18))
        # Saves to: archive/2024-12-18_cities.xml
    """
    # TODO: Implement in Phase 2
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")


def get_fallback_xml(xml_type: str) -> Optional[Tuple[str, date]]:
    """
    Get the most recent archived XML as fallback.
    
    Tries yesterday first, then goes back day by day
    up to MAX_ARCHIVE_DAYS.
    
    Args:
        xml_type: Either "country" or "cities"
    
    Returns:
        Tuple of (xml_content, archive_date), or None if no archive found
        
    Example:
        result = get_fallback_xml("cities")
        if result:
            xml_content, archive_date = result
            print(f"Using archive from {archive_date}")
    """
    # TODO: Implement in Phase 2
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")


def cleanup_old_archives() -> int:
    """
    Remove archive files older than MAX_ARCHIVE_DAYS.
    
    Should be called after a successful fetch to keep the
    archive folder from growing indefinitely.
    
    Returns:
        Number of files deleted
    """
    # TODO: Implement in Phase 2
    raise NotImplementedError("Will be implemented in Phase 2: Data Pipeline")


def get_archive_path(xml_type: str, archive_date: date) -> Path:
    """
    Generate the archive file path for a given date and type.
    
    Args:
        xml_type: Either "country" or "cities"
        archive_date: The date for the archive file
        
    Returns:
        Path object like: archive/2024-12-18_cities.xml
    """
    filename = f"{archive_date.isoformat()}_{xml_type}.xml"
    return ARCHIVE_DIR / filename
