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

from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

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
    # Ensure archive directory exists
    ARCHIVE_DIR.mkdir(exist_ok=True)
    
    # Get the archive path
    archive_path = get_archive_path(xml_type, fetch_date)
    
    # Write with UTF-8 encoding (critical for Hebrew text)
    archive_path.write_text(xml_content, encoding='utf-8')
    
    logger.info(f"Archived {xml_type} XML to {archive_path}")
    return archive_path


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
    today = date.today()
    
    # Start from yesterday, go back up to MAX_ARCHIVE_DAYS
    for days_ago in range(1, MAX_ARCHIVE_DAYS + 1):
        check_date = today - timedelta(days=days_ago)
        archive_path = get_archive_path(xml_type, check_date)
        
        if archive_path.exists():
            try:
                xml_content = archive_path.read_text(encoding='utf-8')
                logger.info(f"Using fallback {xml_type} XML from {check_date}")
                return (xml_content, check_date)
            except Exception as e:
                logger.warning(f"Failed to read archive {archive_path}: {e}")
                continue
    
    # No archive found
    logger.error(
        f"No fallback {xml_type} XML available in last {MAX_ARCHIVE_DAYS} days"
    )
    return None


def get_fallback_for_date(xml_type: str, target_date: date) -> Optional[Tuple[str, date]]:
    """
    Get archived XML for a specific date or the closest earlier date.
    
    Useful for finding city-specific fallback data when a city
    has missing/invalid data.
    
    Args:
        xml_type: Either "country" or "cities"
        target_date: The date to start looking from
    
    Returns:
        Tuple of (xml_content, archive_date), or None if no archive found
    """
    # First try the exact date
    archive_path = get_archive_path(xml_type, target_date)
    if archive_path.exists():
        try:
            xml_content = archive_path.read_text(encoding='utf-8')
            return (xml_content, target_date)
        except Exception as e:
            logger.warning(f"Failed to read archive {archive_path}: {e}")
    
    # Then try earlier dates
    for days_ago in range(1, MAX_ARCHIVE_DAYS + 1):
        check_date = target_date - timedelta(days=days_ago)
        archive_path = get_archive_path(xml_type, check_date)
        
        if archive_path.exists():
            try:
                xml_content = archive_path.read_text(encoding='utf-8')
                logger.debug(f"Found fallback {xml_type} XML from {check_date}")
                return (xml_content, check_date)
            except Exception as e:
                logger.warning(f"Failed to read archive {archive_path}: {e}")
                continue
    
    return None


def cleanup_old_archives() -> int:
    """
    Remove archive files older than MAX_ARCHIVE_DAYS.
    
    Should be called after a successful fetch to keep the
    archive folder from growing indefinitely.
    
    Returns:
        Number of files deleted
    """
    if not ARCHIVE_DIR.exists():
        return 0
    
    today = date.today()
    cutoff_date = today - timedelta(days=MAX_ARCHIVE_DAYS)
    deleted_count = 0
    
    # Iterate through all XML files in archive
    for xml_file in ARCHIVE_DIR.glob("*.xml"):
        try:
            # Parse date from filename (format: YYYY-MM-DD_type.xml)
            filename = xml_file.stem  # e.g., "2024-12-18_cities"
            date_str = filename.split("_")[0]  # e.g., "2024-12-18"
            file_date = date.fromisoformat(date_str)
            
            # Delete if older than cutoff
            if file_date < cutoff_date:
                xml_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old archive: {xml_file}")
                
        except (ValueError, IndexError) as e:
            # Skip files that don't match expected naming pattern
            logger.warning(f"Skipping archive file with unexpected name: {xml_file}")
            continue
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old archive files")
    
    return deleted_count


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


def list_archives(xml_type: Optional[str] = None) -> list[Path]:
    """
    List all archive files, optionally filtered by type.
    
    Args:
        xml_type: Optional filter - "country", "cities", or None for all
    
    Returns:
        List of Path objects for matching archive files
    """
    if not ARCHIVE_DIR.exists():
        return []
    
    if xml_type:
        pattern = f"*_{xml_type}.xml"
    else:
        pattern = "*.xml"
    
    return sorted(ARCHIVE_DIR.glob(pattern), reverse=True)  # Newest first


# Allow running this module directly for quick testing
if __name__ == "__main__":
    print("Testing archive system...")
    print("-" * 50)
    
    # List existing archives
    archives = list_archives()
    print(f"Found {len(archives)} archive files:")
    for archive in archives[:5]:  # Show first 5
        print(f"  - {archive}")
    
    # Test save (with dummy content)
    print("\nTesting save_to_archive...")
    test_content = '<?xml version="1.0"?><test>Hello World</test>'
    test_path = save_to_archive(test_content, "test", date.today())
    print(f"  Saved to: {test_path}")
    
    # Cleanup test file
    test_path.unlink()
    print("  Cleaned up test file")
