"""
Test Gradient Renderer - Verify CSS-Style Gradient Generation

These tests ensure that the gradient renderer correctly:
- Converts hex colors to RGB
- Interpolates between colors
- Handles multiple color stops
- Matches CSS/Figma gradient angle behavior
- Generates correct image dimensions
"""

import pytest
from PIL import Image

from src.rendering.gradient import (
    hex_to_rgb,
    interpolate_color,
    get_color_at_position,
    create_gradient
)


class TestHexToRgb:
    """Tests for hex color string to RGB tuple conversion."""

    def test_converts_standard_hex_color(self):
        """
        Test that standard hex colors convert correctly.

        #1A1A2E should become (26, 26, 46)
        """
        result = hex_to_rgb("#1A1A2E")
        assert result == (26, 26, 46)

    def test_converts_hex_without_hash(self):
        """
        Test that hex colors without # prefix work.

        DCFF57 should become (220, 255, 87)
        """
        result = hex_to_rgb("DCFF57")
        assert result == (220, 255, 87)

    def test_converts_black(self):
        """
        Test that black (#000000) converts correctly.
        """
        result = hex_to_rgb("#000000")
        assert result == (0, 0, 0)

    def test_converts_white(self):
        """
        Test that white (#FFFFFF) converts correctly.
        """
        result = hex_to_rgb("#FFFFFF")
        assert result == (255, 255, 255)

    def test_converts_lowercase_hex(self):
        """
        Test that lowercase hex values work.

        #ff5733 should become (255, 87, 51)
        """
        result = hex_to_rgb("#ff5733")
        assert result == (255, 87, 51)


class TestInterpolateColor:
    """Tests for linear color interpolation."""

    def test_interpolate_at_zero_returns_first_color(self):
        """
        Test that t=0 returns the first color unchanged.
        """
        color1 = (255, 0, 0)  # Red
        color2 = (0, 0, 255)  # Blue
        result = interpolate_color(color1, color2, 0.0)
        assert result == (255, 0, 0)

    def test_interpolate_at_one_returns_second_color(self):
        """
        Test that t=1 returns the second color unchanged.
        """
        color1 = (255, 0, 0)  # Red
        color2 = (0, 0, 255)  # Blue
        result = interpolate_color(color1, color2, 1.0)
        assert result == (0, 0, 255)

    def test_interpolate_at_half_returns_midpoint(self):
        """
        Test that t=0.5 returns the midpoint color.

        Midpoint of red (255,0,0) and blue (0,0,255) should be (127,0,127)
        """
        color1 = (255, 0, 0)  # Red
        color2 = (0, 0, 255)  # Blue
        result = interpolate_color(color1, color2, 0.5)
        assert result == (127, 0, 127)

    def test_interpolate_between_black_and_white(self):
        """
        Test interpolation between black and white at 25%.

        25% of the way from black to white should be (63, 63, 63)
        """
        black = (0, 0, 0)
        white = (255, 255, 255)
        result = interpolate_color(black, white, 0.25)
        assert result == (63, 63, 63)

    def test_interpolate_with_identical_colors(self):
        """
        Test that interpolating between identical colors returns that color.
        """
        color = (100, 150, 200)
        result = interpolate_color(color, color, 0.5)
        assert result == (100, 150, 200)


class TestGetColorAtPosition:
    """Tests for color lookup at gradient positions."""

    def test_position_before_first_stop_returns_first_color(self):
        """
        Test that positions before the first stop return the first stop's color.

        Stops at 20% and 80%, position -10% should return first stop color.
        """
        stops = [
            {'color': (255, 0, 0), 'position': 20},
            {'color': (0, 0, 255), 'position': 80}
        ]
        result = get_color_at_position(stops, -10)
        assert result == (255, 0, 0)

    def test_position_after_last_stop_returns_last_color(self):
        """
        Test that positions after the last stop return the last stop's color.

        Stops at 20% and 80%, position 150% should return last stop color.
        """
        stops = [
            {'color': (255, 0, 0), 'position': 20},
            {'color': (0, 0, 255), 'position': 80}
        ]
        result = get_color_at_position(stops, 150)
        assert result == (0, 0, 255)

    def test_position_at_stop_returns_exact_color(self):
        """
        Test that a position exactly on a stop returns that stop's color.
        """
        stops = [
            {'color': (255, 0, 0), 'position': 0},
            {'color': (0, 255, 0), 'position': 50},
            {'color': (0, 0, 255), 'position': 100}
        ]
        result = get_color_at_position(stops, 50)
        assert result == (0, 255, 0)

    def test_position_between_stops_interpolates(self):
        """
        Test that positions between stops return interpolated colors.

        At 50% between red (0%) and blue (100%), should get purple.
        """
        stops = [
            {'color': (255, 0, 0), 'position': 0},
            {'color': (0, 0, 255), 'position': 100}
        ]
        result = get_color_at_position(stops, 50)
        assert result == (127, 0, 127)

    def test_multiple_stops_with_uneven_spacing(self):
        """
        Test gradient with multiple stops at irregular positions.

        Testing the example from the module docstring.
        """
        stops = [
            {'color': hex_to_rgb("#DCFF57"), 'position': 62.6},
            {'color': hex_to_rgb("#22B2FF"), 'position': 112.1}
        ]

        # Position before first stop
        result = get_color_at_position(stops, 0)
        assert result == hex_to_rgb("#DCFF57")

        # Position after last stop
        result = get_color_at_position(stops, 150)
        assert result == hex_to_rgb("#22B2FF")

        # Position at first stop
        result = get_color_at_position(stops, 62.6)
        assert result == hex_to_rgb("#DCFF57")

    def test_three_color_stops(self):
        """
        Test gradient with three color stops.

        Red -> Green -> Blue at 0%, 50%, 100%
        """
        stops = [
            {'color': (255, 0, 0), 'position': 0},
            {'color': (0, 255, 0), 'position': 50},
            {'color': (0, 0, 255), 'position': 100}
        ]

        # At 25%, halfway between red and green
        result = get_color_at_position(stops, 25)
        assert result == (127, 127, 0)

        # At 75%, halfway between green and blue
        result = get_color_at_position(stops, 75)
        assert result == (0, 127, 127)

    def test_stops_with_zero_range(self):
        """
        Test that stops at the same position don't cause division by zero.
        """
        stops = [
            {'color': (255, 0, 0), 'position': 50},
            {'color': (0, 0, 255), 'position': 50}
        ]
        # Should return one of the colors without crashing
        result = get_color_at_position(stops, 50)
        assert result in [(255, 0, 0), (0, 0, 255)]


class TestCreateGradient:
    """Tests for the main gradient creation function."""

    def test_creates_image_with_correct_dimensions(self):
        """
        Test that the output image has the requested dimensions.
        """
        gradient = create_gradient(
            width=100,
            height=200,
            angle_deg=0,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        assert gradient.size == (100, 200)
        assert isinstance(gradient, Image.Image)

    def test_creates_instagram_story_dimensions(self):
        """
        Test that Instagram Story size (1080x1920) works correctly.

        This is the primary use case for the application.
        """
        gradient = create_gradient(
            width=1080,
            height=1920,
            angle_deg=-23.24,
            stops=[
                {'color': '#DCFF57', 'position': 62.6},
                {'color': '#22B2FF', 'position': 112.1}
            ]
        )
        assert gradient.size == (1080, 1920)

    def test_creates_rgb_mode_image(self):
        """
        Test that the output image is in RGB mode.
        """
        gradient = create_gradient(
            width=50,
            height=50,
            angle_deg=90,
            stops=[
                {'color': '#000000', 'position': 0},
                {'color': '#FFFFFF', 'position': 100}
            ]
        )
        assert gradient.mode == "RGB"

    def test_vertical_gradient_top_to_bottom(self):
        """
        Test vertical gradient from top to bottom (180°).

        Top pixel should be first color, bottom should be last color.
        """
        gradient = create_gradient(
            width=10,
            height=100,
            angle_deg=180,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        pixels = gradient.load()

        # Check top row (should be close to red)
        top_color = pixels[5, 0]
        assert top_color[0] > 200  # Red channel high
        assert top_color[2] < 100  # Blue channel low

        # Check bottom row (should be close to blue)
        bottom_color = pixels[5, 99]
        assert bottom_color[0] < 100  # Red channel low
        assert bottom_color[2] > 200  # Blue channel high

    def test_horizontal_gradient_left_to_right(self):
        """
        Test horizontal gradient from left to right (90°).

        Left pixel should be first color, right should be last color.
        """
        gradient = create_gradient(
            width=100,
            height=10,
            angle_deg=90,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        pixels = gradient.load()

        # Check left column (should be close to red)
        left_color = pixels[0, 5]
        assert left_color[0] > 200  # Red channel high
        assert left_color[2] < 100  # Blue channel low

        # Check right column (should be close to blue)
        right_color = pixels[99, 5]
        assert right_color[0] < 100  # Red channel low
        assert right_color[2] > 200  # Blue channel high

    def test_angle_zero_points_upward(self):
        """
        Test that 0° creates a gradient pointing upward (CSS convention).

        Bottom should be first color, top should be last color.
        """
        gradient = create_gradient(
            width=10,
            height=100,
            angle_deg=0,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        pixels = gradient.load()

        # Check bottom row (should be close to red)
        bottom_color = pixels[5, 99]
        assert bottom_color[0] > 200  # Red channel high

        # Check top row (should be close to blue)
        top_color = pixels[5, 0]
        assert top_color[2] > 200  # Blue channel high

    def test_accepts_rgb_tuples_directly(self):
        """
        Test that color stops can use RGB tuples instead of hex strings.
        """
        gradient = create_gradient(
            width=50,
            height=50,
            angle_deg=0,
            stops=[
                {'color': (255, 0, 0), 'position': 0},
                {'color': (0, 0, 255), 'position': 100}
            ]
        )
        assert gradient.size == (50, 50)

    def test_handles_three_color_stops(self):
        """
        Test gradient with three color stops.
        """
        gradient = create_gradient(
            width=50,
            height=150,
            angle_deg=180,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#00FF00', 'position': 50},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        assert gradient.size == (50, 150)

    def test_raises_error_for_invalid_dimensions(self):
        """
        Test that invalid dimensions raise ValueError.
        """
        with pytest.raises(ValueError, match="Invalid dimensions"):
            create_gradient(
                width=0,
                height=100,
                angle_deg=0,
                stops=[
                    {'color': '#FF0000', 'position': 0},
                    {'color': '#0000FF', 'position': 100}
                ]
            )

        with pytest.raises(ValueError, match="Invalid dimensions"):
            create_gradient(
                width=100,
                height=-50,
                angle_deg=0,
                stops=[
                    {'color': '#FF0000', 'position': 0},
                    {'color': '#0000FF', 'position': 100}
                ]
            )

    def test_raises_error_for_insufficient_stops(self):
        """
        Test that fewer than 2 color stops raise ValueError.
        """
        with pytest.raises(ValueError, match="at least 2 color stops"):
            create_gradient(
                width=100,
                height=100,
                angle_deg=0,
                stops=[{'color': '#FF0000', 'position': 0}]
            )

        with pytest.raises(ValueError, match="at least 2 color stops"):
            create_gradient(
                width=100,
                height=100,
                angle_deg=0,
                stops=[]
            )

    def test_sorts_stops_by_position(self):
        """
        Test that color stops are automatically sorted by position.

        Even if stops are provided out of order, they should work correctly.
        """
        gradient = create_gradient(
            width=50,
            height=100,
            angle_deg=180,
            stops=[
                {'color': '#0000FF', 'position': 100},
                {'color': '#FF0000', 'position': 0}
            ]
        )
        pixels = gradient.load()

        # Top should still be red, bottom should be blue
        top_color = pixels[25, 0]
        assert top_color[0] > 200  # Red channel high

        bottom_color = pixels[25, 99]
        assert bottom_color[2] > 200  # Blue channel high

    def test_small_1x1_gradient(self):
        """
        Test edge case: 1x1 pixel gradient.

        Should not crash and should return a valid color.
        """
        gradient = create_gradient(
            width=1,
            height=1,
            angle_deg=45,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        assert gradient.size == (1, 1)
        pixels = gradient.load()
        # Center pixel should be somewhere between red and blue
        color = pixels[0, 0]
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_diagonal_gradient_45_degrees(self):
        """
        Test a diagonal gradient at 45°.

        Just verify it creates without error - visual testing would be manual.
        """
        gradient = create_gradient(
            width=100,
            height=100,
            angle_deg=45,
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        assert gradient.size == (100, 100)

    def test_negative_angle(self):
        """
        Test that negative angles work correctly.

        The example in the docstring uses -23.24°.
        """
        gradient = create_gradient(
            width=100,
            height=100,
            angle_deg=-23.24,
            stops=[
                {'color': '#DCFF57', 'position': 62.6},
                {'color': '#22B2FF', 'position': 112.1}
            ]
        )
        assert gradient.size == (100, 100)

    def test_large_angle_values(self):
        """
        Test that angles > 360° work (they should wrap around).
        """
        gradient = create_gradient(
            width=50,
            height=50,
            angle_deg=450,  # Same as 90°
            stops=[
                {'color': '#FF0000', 'position': 0},
                {'color': '#0000FF', 'position': 100}
            ]
        )
        assert gradient.size == (50, 50)
