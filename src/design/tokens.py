"""
Design Tokens - Load and Access Figma-Extracted Values

This module loads design tokens from the JSON configuration file
and provides easy access to colors, typography, spacing, and positions.

Design tokens are the single source of truth for all visual properties.
They are extracted from Figma and stored in config/design_tokens.json.

Usage:
    from src.design.tokens import load_tokens, get_color, get_typography
    
    tokens = load_tokens()
    
    # Get specific values
    bg_color = get_color("background")  # "#1A1A2E"
    city_font = get_typography("city_name")  # {"font_family": ..., "font_size": ...}
    jerusalem_pos = get_city_position("jerusalem")  # {"x": 620, "y": 1100}
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

# Path to design tokens file
TOKENS_FILE = Path("config/design_tokens.json")

# Cache for loaded tokens
_tokens_cache: Optional[Dict[str, Any]] = None


def load_tokens() -> Dict[str, Any]:
    """
    Load design tokens from the JSON configuration file.
    
    Returns:
        Dictionary containing all design tokens
        
    Raises:
        FileNotFoundError: If config/design_tokens.json doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    global _tokens_cache
    
    if _tokens_cache is not None:
        return _tokens_cache
    
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")


def get_color(color_name: str) -> str:
    """
    Get a color value from the design tokens.
    
    Args:
        color_name: Key from the "colors" section (e.g., "background")
        
    Returns:
        Hex color string (e.g., "#1A1A2E")
    """
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")


def get_typography(style_name: str) -> Dict[str, Any]:
    """
    Get typography settings for a named style.
    
    Args:
        style_name: Key from the "typography" section (e.g., "city_name")
        
    Returns:
        Dictionary with font_family, font_size, color, etc.
    """
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")


def get_city_position(city_key: str) -> Dict[str, Any]:
    """
    Get the (x, y) position for a city on the map.
    
    Args:
        city_key: Internal city key (e.g., "jerusalem", "tel_aviv")
        
    Returns:
        Dictionary with x, y, and label_anchor
    """
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")


def get_canvas_size() -> tuple[int, int]:
    """
    Get the canvas dimensions from design tokens.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    # TODO: Implement in Phase 3
    raise NotImplementedError("Will be implemented in Phase 3: Design System")
