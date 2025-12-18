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

from pathlib import Path
from typing import Dict
from PIL import Image

# Output directory
OUTPUT_DIR = Path("output")


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
    
    # === Save as PNG ===
    # PNG supports transparency and is lossless
    png_path = OUTPUT_DIR / f"{base_name}.png"
    image.save(
        png_path,
        "PNG",
        optimize=True    # Compress without losing quality
    )
    paths["png"] = str(png_path)
    
    return paths


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
