"""
Font Loader - Load and Cache Hebrew Fonts

This module provides utilities for loading Hebrew fonts from the assets directory.
It includes caching to avoid reloading the same fonts multiple times.

Usage:
    from src.rendering.font_loader import load_font, get_fonts_from_tokens

    # Load a single font
    font = load_font("NotoSansHebrew-Bold", 32)

    # Load all fonts from design tokens
    fonts = get_fonts_from_tokens()
    header_font = fonts["header_date"]
"""

import json
from pathlib import Path
from typing import Dict, Optional
from PIL import ImageFont

# Font cache to avoid reloading the same font
_FONT_CACHE: Dict[tuple, ImageFont.FreeTypeFont] = {}

# Base path for fonts
FONTS_DIR = Path(__file__).parent.parent.parent / "assets" / "Fonts"

# Font family fallbacks for missing variants
FONT_FALLBACKS = {
    "NotoSansHebrew-ExtraCondensed": "NotoSansHebrew-Regular",
    "NotoSansHebrew-Condensed": "NotoSansHebrew-Regular",
}


def load_font(font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TTF font from assets/Fonts/ directory.

    This function caches loaded fonts to improve performance when the same
    font is requested multiple times.

    Args:
        font_family: Font family name (e.g., "NotoSansHebrew-Bold")
        font_size: Font size in pixels

    Returns:
        PIL FreeTypeFont object

    Raises:
        FileNotFoundError: If the font file doesn't exist and no fallback is available

    Example:
        font = load_font("NotoSansHebrew-Bold", 32)
        draw.text((100, 100), "שלום", font=font)
    """
    # Check cache first
    cache_key = (font_family, font_size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    # Construct font file path
    font_path = FONTS_DIR / f"{font_family}.ttf"

    # Check if font exists, if not try fallback
    if not font_path.exists():
        if font_family in FONT_FALLBACKS:
            fallback_family = FONT_FALLBACKS[font_family]
            print(f"Warning: Font '{font_family}' not found. Using fallback: '{fallback_family}'")
            font_path = FONTS_DIR / f"{fallback_family}.ttf"

            if not font_path.exists():
                raise FileNotFoundError(
                    f"Font file not found: {font_path}\n"
                    f"Expected location: {FONTS_DIR}\n"
                    f"Please ensure the font file exists in the assets/Fonts/ directory."
                )
        else:
            raise FileNotFoundError(
                f"Font file not found: {font_path}\n"
                f"Expected location: {FONTS_DIR}\n"
                f"Available fonts: {list_available_fonts()}\n"
                f"Please ensure the font file exists in the assets/Fonts/ directory."
            )

    # Load the font
    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load font '{font_family}' at size {font_size}: {e}\n"
            f"Font path: {font_path}"
        )

    # Cache the font
    _FONT_CACHE[cache_key] = font

    return font


def list_available_fonts() -> list[str]:
    """
    List all available font families in the assets/Fonts/ directory.

    Returns:
        List of font family names (without .ttf extension)

    Example:
        fonts = list_available_fonts()
        print(f"Available fonts: {', '.join(fonts)}")
    """
    if not FONTS_DIR.exists():
        return []

    return [f.stem for f in FONTS_DIR.glob("*.ttf")]


def get_fonts_from_tokens(tokens_path: Optional[Path] = None) -> Dict[str, ImageFont.FreeTypeFont]:
    """
    Load all fonts specified in design_tokens.json.

    This function reads the typography section from design tokens and loads
    all the fonts with their specified sizes.

    Args:
        tokens_path: Path to design_tokens.json (optional, defaults to config/design_tokens.json)

    Returns:
        Dictionary mapping typography style names to loaded fonts

    Raises:
        FileNotFoundError: If design_tokens.json doesn't exist
        ValueError: If design tokens are malformed

    Example:
        fonts = get_fonts_from_tokens()
        header_font = fonts["header_date"]
        city_font = fonts["city_name"]
    """
    # Default path to design tokens
    if tokens_path is None:
        tokens_path = Path(__file__).parent.parent.parent / "config" / "design_tokens.json"

    # Load design tokens
    if not tokens_path.exists():
        raise FileNotFoundError(
            f"Design tokens file not found: {tokens_path}\n"
            f"Please ensure config/design_tokens.json exists."
        )

    try:
        with open(tokens_path, "r", encoding="utf-8") as f:
            tokens = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse design_tokens.json: {e}")

    # Extract typography section
    if "typography" not in tokens:
        raise ValueError(
            "Design tokens file is missing 'typography' section.\n"
            f"File: {tokens_path}"
        )

    typography = tokens["typography"]

    # Load each font
    fonts = {}
    for style_name, style_config in typography.items():
        font_family = style_config.get("font_family")
        font_size = style_config.get("font_size")

        if not font_family or not font_size:
            print(f"Warning: Typography style '{style_name}' is missing font_family or font_size. Skipping.")
            continue

        try:
            fonts[style_name] = load_font(font_family, font_size)
        except Exception as e:
            print(f"Warning: Failed to load font for style '{style_name}': {e}")
            continue

    return fonts


def clear_font_cache() -> None:
    """
    Clear the font cache.

    This is useful for testing or if you need to reload fonts after
    modifying font files.

    Example:
        clear_font_cache()  # All fonts will be reloaded on next load_font() call
    """
    global _FONT_CACHE
    _FONT_CACHE.clear()


def get_cache_size() -> int:
    """
    Get the number of fonts currently in cache.

    Returns:
        Number of cached fonts

    Example:
        size = get_cache_size()
        print(f"Cache contains {size} fonts")
    """
    return len(_FONT_CACHE)
