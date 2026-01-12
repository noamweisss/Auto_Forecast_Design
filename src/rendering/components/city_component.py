"""
City Component Renderer - Figma-Inspired Weather Component

This module implements a reusable city forecast component for Instagram Stories.
The design follows a Figma-inspired component approach where:

1. Component Structure: Each city forecast is a self-contained visual element
2. Layout Variants: Supports RTL, LTR, and TTB layout modes
3. Design Tokens: All styling comes from config/design_tokens.json
4. Composition: Icon + City Name + Temperature arranged per layout mode

The component is designed to be placed at specific coordinates on the Israel map
background, with the layout mode chosen based on available space around each city.

Layout Modes Explained:
    RTL (Right-to-Left): [Temperature] [City Name] [Icon]
        - Icon on the right, text flowing to the left
        - Natural for Hebrew text, saves space horizontally
        - Used for cities with space to the left (west side of map)

    LTR (Left-to-Right): [Icon] [City Name] [Temperature]
        - Icon on the left, text flowing to the right
        - Used for cities with space to the right (east side of map)

    TTB (Top-to-Bottom):
        [Icon]
        [City Name]
        [Temperature]
        - Icon on top, text stacked below
        - Used for cities with limited horizontal space
        - Most compact for crowded areas

Usage:
    from PIL import Image, ImageDraw
    from src.rendering.components.city_component import render_city_forecast
    from src.data.models import CityForecast

    canvas = Image.new("RGB", (1080, 1920), "white")
    city_data = CityForecast(
        city_id="510",
        city_name_hebrew="ירושלים",
        city_name_english="Jerusalem",
        internal_key="jerusalem",
        forecast_date=date.today(),
        min_temp=15,
        max_temp=25,
        weather_code="1250",
        weather_description_hebrew="בהיר",
        weather_description_english="Clear"
    )

    render_city_forecast(canvas, city_data)
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from src.data.models import CityForecast
from src.design.icon_mapper import get_weather_icon_path
from src.rendering.text_utils import draw_hebrew_text, get_text_size


# Load design tokens once at module level
DESIGN_TOKENS_PATH = Path("config/design_tokens.json")
FONTS_DIR = Path("assets/Fonts")


def _load_design_tokens() -> Dict[str, Any]:
    """Load design tokens from JSON file."""
    with open(DESIGN_TOKENS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_font(font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
    """
    Load a font from the Fonts directory.

    Args:
        font_family: Font family name (e.g., "NotoSansHebrew-Black")
        font_size: Font size in pixels

    Returns:
        PIL ImageFont object

    Note:
        Falls back to PIL's default font if the specified font file is not found
        or is a Git LFS pointer. This enables testing without requiring full assets.
    """
    font_path = FONTS_DIR / f"{font_family}.ttf"

    try:
        # Check if file exists and is not a Git LFS pointer
        if font_path.exists():
            file_size = font_path.stat().st_size
            # Git LFS pointers are typically ~130 bytes
            if file_size < 1000:
                # Likely a Git LFS pointer, try to read it
                with open(font_path, 'r') as f:
                    first_line = f.readline()
                    if 'git-lfs' in first_line:
                        print(f"Warning: {font_path.name} is a Git LFS pointer. Using default font.")
                        return ImageFont.load_default()

        return ImageFont.truetype(str(font_path), font_size)
    except (OSError, IOError) as e:
        # Font file not found or invalid, use default
        print(f"Warning: Could not load font {font_family}. Using default font. Error: {e}")
        return ImageFont.load_default()


def _render_rtl_layout(
    draw: ImageDraw.ImageDraw,
    icon: Image.Image,
    city_name: str,
    temperature_text: str,
    position: Tuple[int, int],
    city_font: ImageFont.FreeTypeFont,
    temp_font: ImageFont.FreeTypeFont,
    icon_size: int,
    gap: int,
    text_color: str
) -> None:
    """
    Render city forecast in RTL (right-to-left) layout.

    Layout: [Temperature] [City Name] [Icon]

    Args:
        draw: PIL ImageDraw object
        icon: Weather icon image
        city_name: City name in Hebrew
        temperature_text: Temperature string (e.g., "25°")
        position: (x, y) anchor position (icon position)
        city_font: Font for city name
        temp_font: Font for temperature
        icon_size: Size of weather icon
        gap: Gap between elements
        text_color: Color for text
    """
    x, y = position

    # Icon is at the anchor position
    icon_x = x - icon_size // 2
    icon_y = y - icon_size // 2
    draw._image.paste(icon, (icon_x, icon_y), icon)

    # City name is to the left of the icon
    city_width, city_height = get_text_size(city_name, city_font)
    city_x = x - icon_size // 2 - gap - city_width
    city_y = y - city_height // 2
    draw_hebrew_text(draw, city_name, (city_x, city_y), city_font, fill=text_color)

    # Temperature is to the left of the city name
    temp_width, temp_height = get_text_size(temperature_text, temp_font)
    temp_x = city_x - gap - temp_width
    temp_y = y - temp_height // 2
    draw.text((temp_x, temp_y), temperature_text, font=temp_font, fill=text_color)


def _render_ltr_layout(
    draw: ImageDraw.ImageDraw,
    icon: Image.Image,
    city_name: str,
    temperature_text: str,
    position: Tuple[int, int],
    city_font: ImageFont.FreeTypeFont,
    temp_font: ImageFont.FreeTypeFont,
    icon_size: int,
    gap: int,
    text_color: str
) -> None:
    """
    Render city forecast in LTR (left-to-right) layout.

    Layout: [Icon] [City Name] [Temperature]

    Args:
        draw: PIL ImageDraw object
        icon: Weather icon image
        city_name: City name in Hebrew
        temperature_text: Temperature string (e.g., "25°")
        position: (x, y) anchor position (icon position)
        city_font: Font for city name
        temp_font: Font for temperature
        icon_size: Size of weather icon
        gap: Gap between elements
        text_color: Color for text
    """
    x, y = position

    # Icon is at the anchor position
    icon_x = x - icon_size // 2
    icon_y = y - icon_size // 2
    draw._image.paste(icon, (icon_x, icon_y), icon)

    # City name is to the right of the icon
    city_width, city_height = get_text_size(city_name, city_font)
    city_x = x + icon_size // 2 + gap
    city_y = y - city_height // 2
    draw_hebrew_text(draw, city_name, (city_x, city_y), city_font, fill=text_color)

    # Temperature is to the right of the city name
    temp_width, temp_height = get_text_size(temperature_text, temp_font)
    temp_x = city_x + city_width + gap
    temp_y = y - temp_height // 2
    draw.text((temp_x, temp_y), temperature_text, font=temp_font, fill=text_color)


def _render_ttb_layout(
    draw: ImageDraw.ImageDraw,
    icon: Image.Image,
    city_name: str,
    temperature_text: str,
    position: Tuple[int, int],
    city_font: ImageFont.FreeTypeFont,
    temp_font: ImageFont.FreeTypeFont,
    icon_size: int,
    gap: int,
    text_color: str
) -> None:
    """
    Render city forecast in TTB (top-to-bottom) layout.

    Layout:
        [Icon]
        [City Name]
        [Temperature]

    Args:
        draw: PIL ImageDraw object
        icon: Weather icon image
        city_name: City name in Hebrew
        temperature_text: Temperature string (e.g., "25°")
        position: (x, y) anchor position (icon center)
        city_font: Font for city name
        temp_font: Font for temperature
        icon_size: Size of weather icon
        gap: Gap between elements
        text_color: Color for text
    """
    x, y = position

    # Icon is at the anchor position
    icon_x = x - icon_size // 2
    icon_y = y - icon_size // 2
    draw._image.paste(icon, (icon_x, icon_y), icon)

    # City name is below the icon, centered
    city_width, city_height = get_text_size(city_name, city_font)
    city_x = x - city_width // 2
    city_y = y + icon_size // 2 + gap
    draw_hebrew_text(draw, city_name, (city_x, city_y), city_font, fill=text_color)

    # Temperature is below the city name, centered
    temp_width, temp_height = get_text_size(temperature_text, temp_font)
    temp_x = x - temp_width // 2
    temp_y = city_y + city_height + gap
    draw.text((temp_x, temp_y), temperature_text, font=temp_font, fill=text_color)


def render_city_forecast(
    canvas: Image.Image,
    city_data: CityForecast,
    design_tokens: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render a city forecast component on the canvas.

    This is the main entry point for rendering a city forecast. It:
    1. Loads the city's position and layout mode from design tokens
    2. Loads the weather icon for the forecast
    3. Formats the temperature text
    4. Renders the component using the appropriate layout mode

    Args:
        canvas: PIL Image object to draw on (1080x1920 Instagram Story)
        city_data: CityForecast object with weather data
        design_tokens: Optional design tokens dict (loaded from file if not provided)

    Raises:
        ValueError: If city's internal_key not found in design tokens
        FileNotFoundError: If icon file not found for weather code

    Example:
        from PIL import Image
        from datetime import date
        from src.data.models import CityForecast
        from src.rendering.components.city_component import render_city_forecast

        canvas = Image.new("RGB", (1080, 1920), "white")

        city = CityForecast(
            city_id="510",
            city_name_hebrew="ירושלים",
            city_name_english="Jerusalem",
            internal_key="jerusalem",
            forecast_date=date.today(),
            min_temp=15,
            max_temp=25,
            weather_code="1250",
            weather_description_hebrew="בהיר",
            weather_description_english="Clear"
        )

        render_city_forecast(canvas, city)
        canvas.save("output.png")
    """
    # Load design tokens if not provided
    if design_tokens is None:
        design_tokens = _load_design_tokens()

    # Get city position and layout from design tokens
    city_positions = design_tokens.get("city_positions", {})
    city_config = city_positions.get(city_data.internal_key)

    if city_config is None:
        raise ValueError(
            f"City '{city_data.internal_key}' not found in design tokens. "
            f"Available cities: {', '.join(city_positions.keys())}"
        )

    position = (city_config["x"], city_config["y"])
    layout_mode = city_config["layout"]

    # Get typography settings
    typography = design_tokens.get("typography", {})
    city_name_style = typography.get("city_name", {})
    temp_style = typography.get("temperature", {})

    # Get spacing settings
    spacing = design_tokens.get("spacing", {})
    component_spacing = spacing.get("city_component", {})
    gap = component_spacing.get("gap", 16)

    # Get icon size
    icon_sizes = design_tokens.get("icon_sizes", {})
    icon_size = icon_sizes.get("weather_icon", 50)

    # Load fonts
    city_font = _load_font(
        city_name_style.get("font_family", "NotoSansHebrew-Black"),
        city_name_style.get("font_size", 24)
    )
    temp_font = _load_font(
        temp_style.get("font_family", "NotoSansHebrew-SemiBold"),
        temp_style.get("font_size", 20)
    )

    # Load weather icon
    icon_path = get_weather_icon_path(city_data.weather_code)
    if icon_path is None or not icon_path.exists():
        raise FileNotFoundError(
            f"Weather icon not found for code '{city_data.weather_code}'. "
            f"Expected path: {icon_path}"
        )

    # Load and resize icon
    icon = Image.open(icon_path).convert("RGBA")
    icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    # Format temperature text (using max temperature)
    temperature_text = f"{city_data.max_temp}°"

    # Get text color
    text_color = city_name_style.get("color", "#000000")

    # Create draw object
    draw = ImageDraw.Draw(canvas)

    # Render based on layout mode
    if layout_mode == "RTL":
        _render_rtl_layout(
            draw, icon, city_data.city_name_hebrew, temperature_text,
            position, city_font, temp_font, icon_size, gap, text_color
        )
    elif layout_mode == "LTR":
        _render_ltr_layout(
            draw, icon, city_data.city_name_hebrew, temperature_text,
            position, city_font, temp_font, icon_size, gap, text_color
        )
    elif layout_mode == "TTB":
        _render_ttb_layout(
            draw, icon, city_data.city_name_hebrew, temperature_text,
            position, city_font, temp_font, icon_size, gap, text_color
        )
    else:
        raise ValueError(
            f"Unknown layout mode '{layout_mode}'. "
            f"Valid modes: RTL, LTR, TTB"
        )
