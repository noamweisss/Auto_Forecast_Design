"""
Test Rendering - Verify Image Generation Works Correctly

These tests ensure that images are generated correctly.
Visual tests are harder than data tests, so we focus on:
- Canvas size is correct
- All required elements exist
- No exceptions during rendering

For visual verification, we save test images and compare manually.
"""

import pytest
from pathlib import Path
from PIL import Image, ImageDraw

# Import our Hebrew text utilities
from src.rendering.text_utils import (
    prepare_hebrew_text,
    draw_hebrew_text,
    get_text_size,
    BIDI_AVAILABLE
)
from src.rendering.font_loader import (
    load_font,
    get_fonts_from_tokens,
    list_available_fonts,
    clear_font_cache,
    get_cache_size
)


class TestInstagramStoryRenderer:
    """Tests for Instagram Story layout generation."""

    def test_canvas_size_is_1080x1920(self):
        """
        Verify the canvas is exactly 1080x1920 pixels.

        This is the Instagram Story standard size (9:16 aspect ratio).
        """
        # renderer = InstagramStoryRenderer()
        # width, height = renderer.get_canvas_size()
        # assert width == 1080
        # assert height == 1920
        pass

    def test_render_completes_without_error(self):
        """
        Verify that rendering doesn't crash with valid input.

        This is a basic smoke test - if it passes, the code at least runs.
        """
        # TODO: Implement when renderer is ready
        pass

    def test_output_is_rgba_image(self):
        """
        Verify the output is an RGBA PIL Image.

        We use RGBA to support transparency for compositing.
        """
        # TODO: Implement when renderer is ready
        pass


class TestTextRendering:
    """Tests for Hebrew text handling."""

    def test_hebrew_text_renders_without_error(self):
        """
        Verify that Hebrew text can be drawn without exceptions.

        Hebrew requires special BiDi handling which can fail if
        the libraries aren't configured correctly.
        """
        # Create a test image
        img = Image.new("RGB", (400, 100), "white")
        draw = ImageDraw.Draw(img)

        # Load a Hebrew font
        font = load_font("NotoSansHebrew-Bold", 32)

        # Draw Hebrew text (should not raise any exceptions)
        hebrew_text = "שלום עולם"
        draw_hebrew_text(draw, hebrew_text, (200, 50), font, fill="black", anchor="mm")

        # If we got here, the test passed
        assert True

    def test_bidi_text_preparation(self):
        """
        Verify that BiDi algorithm is applied to Hebrew text.

        The prepare_hebrew_text() function should reorder characters.
        """
        if not BIDI_AVAILABLE:
            pytest.skip("BiDi libraries not installed")

        # Original Hebrew text
        original = "שלום עולם"

        # Prepare for display
        prepared = prepare_hebrew_text(original)

        # The prepared text should be different from the original
        # (BiDi algorithm reorders the characters for display)
        assert prepared != original

        # The length should be the same
        assert len(prepared) == len(original)

    def test_mixed_hebrew_english_numbers(self):
        """
        Test rendering of mixed Hebrew, English, and numbers.

        This is common in weather forecasts: "תל אביב 25°C"
        """
        # Create a test image
        img = Image.new("RGB", (400, 100), "white")
        draw = ImageDraw.Draw(img)

        # Load a font
        font = load_font("NotoSansHebrew-Regular", 24)

        # Mixed text with Hebrew, English, and numbers
        mixed_texts = [
            "תל אביב 25°C",
            "ירושלים - Jerusalem",
            "2024 שנה טובה",
            "Temperature: 25°",
        ]

        # Each should render without error
        y_pos = 20
        for text in mixed_texts:
            draw_hebrew_text(draw, text, (200, y_pos), font, fill="black", anchor="mm")
            y_pos += 25

        assert True

    def test_text_measurement(self):
        """
        Test that get_text_size() returns correct dimensions.

        This is important for positioning text elements.
        """
        font = load_font("NotoSansHebrew-Bold", 32)

        # Test Hebrew text
        hebrew_text = "ירושלים"
        width, height = get_text_size(hebrew_text, font)

        # Width and height should be positive
        assert width > 0
        assert height > 0

        # Longer text should be wider
        longer_text = "ירושלים העיר הבירה"
        longer_width, longer_height = get_text_size(longer_text, font)

        assert longer_width > width
        # Height should be similar (same font size)
        assert abs(longer_height - height) < 10


class TestFontLoader:
    """Tests for font loading and caching."""

    def test_load_font_basic(self):
        """Test loading a basic Hebrew font."""
        clear_font_cache()

        font = load_font("NotoSansHebrew-Regular", 24)

        assert font is not None
        assert font.size == 24

    def test_font_caching(self):
        """Test that fonts are cached correctly."""
        clear_font_cache()

        # Load the same font twice
        font1 = load_font("NotoSansHebrew-Bold", 32)
        font2 = load_font("NotoSansHebrew-Bold", 32)

        # They should be the exact same object (from cache)
        assert font1 is font2

        # Cache should contain 1 font
        assert get_cache_size() == 1

    def test_different_sizes_cached_separately(self):
        """Test that different font sizes are cached separately."""
        clear_font_cache()

        # Load same family, different sizes
        font_24 = load_font("NotoSansHebrew-Regular", 24)
        font_32 = load_font("NotoSansHebrew-Regular", 32)

        # They should be different objects
        assert font_24 is not font_32

        # Cache should contain 2 fonts
        assert get_cache_size() == 2

    def test_list_available_fonts(self):
        """Test listing available fonts."""
        fonts = list_available_fonts()

        # Should return a list
        assert isinstance(fonts, list)

        # Should contain at least some NotoSansHebrew fonts
        assert any("NotoSansHebrew" in font for font in fonts)

        # Should contain Bold variant
        assert "NotoSansHebrew-Bold" in fonts

    def test_load_missing_font_raises_error(self):
        """Test that loading a non-existent font raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_font("NonExistentFont", 24)

        # Error message should be helpful
        assert "Font file not found" in str(exc_info.value)

    def test_get_fonts_from_tokens(self):
        """Test loading all fonts from design_tokens.json."""
        clear_font_cache()

        fonts = get_fonts_from_tokens()

        # Should return a dictionary
        assert isinstance(fonts, dict)

        # Should contain expected typography styles
        expected_styles = ["header_date", "city_name", "temperature", "description"]
        for style in expected_styles:
            assert style in fonts
            assert fonts[style] is not None

    def test_typography_font_sizes_match_tokens(self):
        """Test that loaded fonts have the correct sizes from design tokens."""
        fonts = get_fonts_from_tokens()

        # Check specific font sizes from design_tokens.json
        assert fonts["header_date"].size == 36
        assert fonts["city_name"].size == 24
        assert fonts["temperature"].size == 20
        assert fonts["description"].size == 24

    def test_all_typography_styles(self):
        """Test rendering with all typography styles from design tokens."""
        fonts = get_fonts_from_tokens()

        # Create a test image
        img = Image.new("RGB", (600, 400), "white")
        draw = ImageDraw.Draw(img)

        test_texts = {
            "header_date": "יום שלישי, 22 בינואר",
            "city_name": "ירושלים",
            "temperature": "25°C",
            "description": "שמיים בהירים",
            "ims_logo_text": "שירות המטאורולוגי",
        }

        y_pos = 30
        for style_name, text in test_texts.items():
            if style_name in fonts:
                font = fonts[style_name]
                draw_hebrew_text(draw, text, (300, y_pos), font, fill="black", anchor="mm")
                y_pos += 60

        # If we got here without exceptions, test passed
        assert True
