"""
File Saver - Save Generated Images

This module saves the generated forecast images to the output/ folder
in both JPEG and PNG formats.

Why both formats?
    - JPEG: Smaller file size, good for email attachments
    - PNG: Lossless quality, good for archive and social media uploads

Output Location:
    output/
    ├── forecast_2024-12-18.jpg
    └── forecast_2024-12-18.png

Usage:
    from src.delivery.file_saver import save_forecast_image
    
    paths = save_forecast_image(pil_image, "2024-12-18")
    print(paths["jpeg"])  # "output/forecast_2024-12-18.jpg"
    print(paths["png"])   # "output/forecast_2024-12-18.png"
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional

from PIL import Image

from src.utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Output directory
OUTPUT_DIR = Path("output")

# Default cleanup age
DEFAULT_MAX_AGE_DAYS = 30


def save_forecast_image(image: Image.Image, date_str: str) -> Dict[str, str]:
    """
    Save the generated image in both JPEG and PNG formats.
    
    Args:
        image: PIL Image object to save
        date_str: Date string for filename (e.g., "2024-12-18")
    
    Returns:
        Dictionary with paths to both saved files:
        {
            "jpeg": "output/forecast_2024-12-18.jpg",
            "png": "output/forecast_2024-12-18.png"
        }
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    base_name = f"forecast_{date_str}"
    paths = {}
    
    # === Save as JPEG ===
    # JPEG doesn't support transparency, so convert to RGB first
    jpeg_path = OUTPUT_DIR / f"{base_name}.jpg"
    rgb_image = image.convert("RGB")
    rgb_image.save(
        jpeg_path,
        "JPEG",
        quality=90,      # High quality but reasonable file size
        optimize=True    # Optimize Huffman tables for smaller size
    )
    paths["jpeg"] = str(jpeg_path)
    logger.info(f"Saved JPEG: {jpeg_path}")
    
    # === Save as PNG ===
    # PNG supports transparency and is lossless
    png_path = OUTPUT_DIR / f"{base_name}.png"
    image.save(
        png_path,
        "PNG",
        optimize=True    # Compress without losing quality
    )
    paths["png"] = str(png_path)
    logger.info(f"Saved PNG: {png_path}")
    
    return paths


def cleanup_old_outputs(max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> int:
    """
    Remove output files older than max_age_days.
    
    Keeps the output folder from growing indefinitely.
    
    Args:
        max_age_days: Delete files older than this many days (default: 30)
    
    Returns:
        Number of files deleted
    """
    if not OUTPUT_DIR.exists():
        return 0
    
    today = date.today()
    cutoff_date = today - timedelta(days=max_age_days)
    deleted_count = 0
    
    # Find and delete old forecast files
    for file_path in OUTPUT_DIR.glob("forecast_*.*"):
        try:
            # Parse date from filename (format: forecast_YYYY-MM-DD.ext)
            filename = file_path.stem  # e.g., "forecast_2024-12-18"
            date_str = filename.replace("forecast_", "")  # e.g., "2024-12-18"
            file_date = date.fromisoformat(date_str)
            
            # Delete if older than cutoff
            if file_date < cutoff_date:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old output: {file_path}")
                
        except (ValueError, IndexError) as e:
            # Skip files that don't match expected naming pattern
            logger.warning(f"Skipping file with unexpected name: {file_path}")
            continue
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old output files")
    
    return deleted_count


def get_latest_output() -> Dict[str, Path]:
    """
    Find the most recently saved forecast images.
    
    Returns:
        Dictionary with paths to the latest JPEG and PNG files,
        or empty dict if no outputs exist.
    """
    if not OUTPUT_DIR.exists():
        return {}
    
    jpeg_files = sorted(OUTPUT_DIR.glob("forecast_*.jpg"), reverse=True)
    png_files = sorted(OUTPUT_DIR.glob("forecast_*.png"), reverse=True)
    
    result = {}
    if jpeg_files:
        result["jpeg"] = jpeg_files[0]
    if png_files:
        result["png"] = png_files[0]
    
    return result


def get_output_path(date_str: str, format: str = "jpeg") -> Path:
    """
    Get the expected output path for a given date and format.
    
    Args:
        date_str: Date string (e.g., "2024-12-18")
        format: Either "jpeg" or "png"
    
    Returns:
        Path object for the output file
    """
    extension = "jpg" if format == "jpeg" else "png"
    return OUTPUT_DIR / f"forecast_{date_str}.{extension}"


def list_outputs(format: Optional[str] = None) -> list[Path]:
    """
    List all output files, optionally filtered by format.
    
    Args:
        format: Optional filter - "jpeg", "png", or None for all
    
    Returns:
        List of Path objects for matching output files
    """
    if not OUTPUT_DIR.exists():
        return []
    
    if format == "jpeg":
        pattern = "forecast_*.jpg"
    elif format == "png":
        pattern = "forecast_*.png"
    else:
        pattern = "forecast_*.*"
    
    return sorted(OUTPUT_DIR.glob(pattern), reverse=True)  # Newest first


# Allow running this module directly for quick testing
if __name__ == "__main__":
    print("Testing file saver...")
    print("-" * 50)
    
    # List existing outputs
    outputs = list_outputs()
    print(f"Found {len(outputs)} output files:")
    for output in outputs[:5]:  # Show first 5
        print(f"  - {output}")
    
    # Get latest
    latest = get_latest_output()
    if latest:
        print(f"\nLatest outputs:")
        for fmt, path in latest.items():
            print(f"  {fmt}: {path}")
    else:
        print("\nNo outputs found")
