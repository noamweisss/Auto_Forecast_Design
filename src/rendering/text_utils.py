"""
Text Utilities - Hebrew Text Handling

This module provides utilities for rendering Hebrew text correctly.
Hebrew requires special handling because:

1. Right-to-Left (RTL): Text reads from right to left
2. Character Shaping: Some letters change appearance based on position
3. BiDi Mixing: Numbers and English within Hebrew need reordering

Solution: We use python-bidi and arabic-reshaper libraries to
properly prepare Hebrew text before drawing with Pillow.

Usage:
    from src.rendering.text_utils import draw_hebrew_text
    from PIL import Image, ImageDraw, ImageFont
    
    image = Image.new("RGB", (500, 100), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("assets/Fonts/NotoSansHebrew-Bold.ttf", 32)
    
    draw_hebrew_text(draw, "שלום עולם", (250, 50), font, fill="black")
"""

from PIL import ImageDraw, ImageFont
from typing import Tuple, Optional

# These imports will be available after installing dependencies
# pip install python-bidi arabic-reshaper

try:
    from bidi.algorithm import get_display
    import arabic_reshaper
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    print("Warning: python-bidi and arabic-reshaper not installed.")
    print("Hebrew text may not render correctly.")
    print("Run: pip install python-bidi arabic-reshaper")


def prepare_hebrew_text(text: str) -> str:
    """
    Prepare Hebrew text for correct rendering.
    
    This function applies:
    1. Arabic reshaper - fixes character forms
    2. BiDi algorithm - corrects display order
    
    Args:
        text: Hebrew text string
        
    Returns:
        Processed text ready for Pillow's draw.text()
        
    Example:
        original = "שלום עולם"
        prepared = prepare_hebrew_text(original)
        # prepared is now correctly ordered for display
    """
    if not BIDI_AVAILABLE:
        # Fall back to original text if libraries not installed
        return text
    
    # Step 1: Reshape characters (handle final forms, ligatures)
    reshaped = arabic_reshaper.reshape(text)
    
    # Step 2: Apply BiDi algorithm for correct display order
    bidi_text = get_display(reshaped)
    
    return bidi_text


def draw_hebrew_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    fill: str = "#FFFFFF",
    anchor: Optional[str] = None
) -> None:
    """
    Draw Hebrew text with proper RTL rendering.
    
    This is a wrapper around Pillow's draw.text() that automatically
    handles Hebrew text preparation.
    
    Args:
        draw: PIL ImageDraw object
        text: Hebrew text to draw
        position: (x, y) tuple for text position
        font: PIL ImageFont object
        fill: Text color (hex string or RGB tuple)
        anchor: Text anchor (e.g., "mm" for middle-middle)
        
    Example:
        draw_hebrew_text(draw, "ירושלים", (100, 50), font, fill="#FFFFFF")
    """
    # Prepare Hebrew text for correct display
    prepared_text = prepare_hebrew_text(text)
    
    # Draw using Pillow
    draw.text(position, prepared_text, font=font, fill=fill, anchor=anchor)


def get_text_size(text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    """
    Get the size of text when rendered with the given font.
    
    Args:
        text: Text to measure (Hebrew or English)
        font: PIL ImageFont object
        
    Returns:
        Tuple of (width, height) in pixels
    """
    # For Hebrew, we need to prepare the text first
    prepared_text = prepare_hebrew_text(text)
    
    # Use font.getbbox() for accurate measurement
    bbox = font.getbbox(prepared_text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    
    return (width, height)
