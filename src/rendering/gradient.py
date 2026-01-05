"""
CSS-Style Linear Gradient Generator

This module creates linear gradients that match CSS/Figma gradient behavior.
Uses per-pixel vector projection to avoid rotation artifacts.

Design Decision:
    Chosen after experimentation because:
    - Simple algorithm, easy to understand and debug
    - No complex dependencies beyond Pillow
    - Matches design tokens gradient specification exactly
    - Pixel-perfect rendering

Usage:
    from src.rendering.gradient import create_gradient
    
    gradient = create_gradient(
        width=1080,
        height=1920,
        angle_deg=-23.24,
        stops=[
            {"color": "#DCFF57", "position": 62.6},
            {"color": "#22B2FF", "position": 112.1}
        ]
    )
"""

import math
from PIL import Image
RGB = tuple[int, int, int]

def hex_to_rgb(hex_color: str) -> RGB:
    """
    Convert hex color string to RGB tuple.
    
    Args:
        hex_color: string, e.g. "#1A1A2E"
    Returns:
        tuple of (R, G, B)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def interpolate_color(color_1: RGB, color_2: RGB, t: float) -> RGB:
    """
    Linearly interpolate between two RGB colors.
    
    Args:
        color_1: RGB tuple for start color
        color_2: RGB tuple for end color  
        t: float 0-1, interpolation factor
    Returns:
        RGB tuple
    """
    r = int(color_1[0] + (color_2[0] - color_1[0]) * t)
    g = int(color_1[1] + (color_2[1] - color_1[1]) * t)
    b = int(color_1[2] + (color_2[2] - color_1[2]) * t)
    return (r, g, b)


def get_color_at_position(stops: list[dict], position: float) -> RGB:
    """
    Get the interpolated color at a given position along the gradient.
    Handles multiple stops and positions outside 0-100%.
    
    Args:
        stops: list of dicts with 'color' (RGB tuple) and 'position' (0-100)
        position: float, position along gradient (0-100)
    Returns:
        RGB tuple
    """
    # Handle edge cases
    if position <= stops[0]['position']:
        return stops[0]['color']
    if position >= stops[-1]['position']:
        return stops[-1]['color']
    
    # Find the two stops we're between
    for i in range(len(stops) - 1):
        if stops[i]['position'] <= position <= stops[i + 1]['position']:
            # Calculate interpolation factor
            range_size = stops[i + 1]['position'] - stops[i]['position']
            if range_size == 0:
                return stops[i]['color']
            t = (position - stops[i]['position']) / range_size
            return interpolate_color(stops[i]['color'], stops[i + 1]['color'], t)
    
    return stops[-1]['color']


# ═══════════════════════════════════════════════════════════
# MAIN GRADIENT FUNCTION
# ═══════════════════════════════════════════════════════════

def create_gradient(width: int,
                        height: int,
                        angle_deg: float,
                        stops: list[dict]) -> Image.Image:
    """
    Create a linear gradient matching CSS/Figma behavior.
    
    This calculates the gradient per-pixel using vector projection,
    avoiding the rotation/cropping issues of the "draw then rotate" approach.
    
    Args:
        width: int, output image width
        height: int, output image height
        angle_deg: float, CSS-style angle (0° = to top, 90° = to right, etc.)
        stops: list of dicts with 'color' (hex string) and 'position' (float 0-100)
    
    Returns:
        PIL.Image: The gradient image
    """

    # Validate inputs
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid dimensions: {width}x{height}")
    
    if not stops or len(stops) < 2:
        raise ValueError("Need at least 2 color stops")
    
    # Convert hex colors to RGB
    processed_stops = []
    for stop in sorted(stops, key=lambda x: x['position']):
        color = stop['color']
        if isinstance(color, str):
            color = hex_to_rgb(color)
        processed_stops.append({
            'color': color,
            'position': stop['position']
        })
    
    # Create output image
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    # Convert CSS angle to math angle (radians)
    # CSS: 0° = up (towards top), 90° = right, 180° = down, 270° = left
    # Math: 0° = right, angles go counter-clockwise
    # So we need: math_angle = 90° - css_angle
    math_angle = math.radians(90 - angle_deg)
    
    # Calculate the gradient direction vector (unit vector)
    dx = math.cos(math_angle)
    dy = -math.sin(math_angle)  # Negative because screen Y increases downward
    
    # Calculate the gradient line length
    # This is the projection of the rectangle's diagonal onto the gradient direction
    # We need this to normalize our position values to match CSS percentages
    gradient_length = abs(width * dx) + abs(height * dy)
    
    # Center point of the image
    cx, cy = width / 2, height / 2
    
    for y in range(height):
        for x in range(width):
            # Vector from center to this pixel
            px, py = x - cx, y - cy
            
            # Project onto the gradient direction
            projection = (px * dx + py * dy)
            
            # Normalize to 0-100 range (CSS percentage)
            # projection ranges from -gradient_length/2 to +gradient_length/2
            # We map this to 0-100
            normalized_position = (projection / gradient_length + 0.5) * 100
            
            # Get the interpolated color at this position
            color = get_color_at_position(processed_stops, normalized_position)
            pixels[x, y] = color
    
    return img