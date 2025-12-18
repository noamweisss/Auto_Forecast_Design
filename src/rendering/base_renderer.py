"""
Base Renderer - Abstract Template for Image Layouts

This module defines the base class that all layout renderers inherit from.
Think of it as a "template" that ensures all layouts work the same way.

Each layout (Instagram Story, Twitter Banner, etc.) extends this class
and implements its own render() method.

Why an abstract base class?
    - Ensures consistency across all layouts
    - Makes it easy to add new layouts
    - Provides common functionality (loading fonts, colors, etc.)

Usage:
    # You don't use BaseRenderer directly - you use a specific layout:
    from src.rendering.instagram_story import InstagramStoryRenderer
    
    renderer = InstagramStoryRenderer()
    image = renderer.render(forecast_data)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageFont

from src.design.tokens import load_tokens


class BaseRenderer(ABC):
    """
    Abstract base class for all image layout renderers.
    
    This class provides:
    - Loading of design tokens
    - Font caching
    - Common helper methods
    
    Subclasses must implement:
    - get_canvas_size() - return (width, height)
    - render() - generate the actual image
    """
    
    def __init__(self):
        """
        Initialize the renderer with design tokens and fonts.
        """
        self.tokens = load_tokens()
        self._font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self._setup_fonts()
    
    def _setup_fonts(self):
        """
        Pre-load commonly used fonts into the cache.
        
        Fonts are loaded from assets/Fonts/ based on design tokens.
        Caching prevents repeated disk reads during rendering.
        """
        # TODO: Implement in Phase 4
        pass
    
    def get_font(self, style_name: str) -> ImageFont.FreeTypeFont:
        """
        Get a font for a named typography style.
        
        Args:
            style_name: Key from typography tokens (e.g., "city_name")
            
        Returns:
            PIL ImageFont object ready for drawing
        """
        if style_name in self._font_cache:
            return self._font_cache[style_name]
        
        # TODO: Implement font loading in Phase 4
        raise NotImplementedError("Will be implemented in Phase 4: Rendering")
    
    @abstractmethod
    def get_canvas_size(self) -> Tuple[int, int]:
        """
        Return the canvas dimensions for this layout.
        
        Returns:
            Tuple of (width, height) in pixels
            
        Example:
            Instagram Story returns (1080, 1920)
            Twitter Banner might return (1500, 500)
        """
        pass
    
    @abstractmethod
    def render(self, forecast_data: Any) -> Image.Image:
        """
        Generate the complete image for this layout.
        
        Args:
            forecast_data: DailyForecast object with all weather data
            
        Returns:
            PIL Image object ready for saving
            
        This method should:
        1. Create the canvas
        2. Draw background/base layers
        3. Draw all components (header, cities, footer)
        4. Return the completed image
        """
        pass
    
    def create_canvas(self) -> Image.Image:
        """
        Create a blank canvas with the background color.
        
        Returns:
            New PIL Image with background color applied
        """
        width, height = self.get_canvas_size()
        bg_color = self.tokens.get("colors", {}).get("background", "#1A1A2E")
        
        # Create RGBA image (supports transparency)
        canvas = Image.new("RGBA", (width, height), bg_color)
        return canvas
