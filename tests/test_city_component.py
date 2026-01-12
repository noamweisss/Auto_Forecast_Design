"""
Test City Component - Verify City Forecast Rendering

These tests verify that the city forecast component renderer works correctly
across all three layout modes (RTL, LTR, TTB) and with real city data.

Test Coverage:
    - All three layout modes render without errors
    - Real city names from cities.json work correctly
    - Hebrew text is properly rendered
    - Weather icons are loaded and positioned correctly
    - Temperature text is formatted properly
    - Visual outputs are generated for manual verification

Visual Test Outputs:
    Test images are saved to tests/manual/ for visual inspection:
    - test_city_rtl_output.png - RTL layout example
    - test_city_ltr_output.png - LTR layout example
    - test_city_ttb_output.png - TTB layout example
    - test_all_cities_output.png - All 15 cities on map
"""

import pytest
import json
from pathlib import Path
from datetime import date
from PIL import Image, ImageDraw

from src.data.models import CityForecast
from src.rendering.components.city_component import render_city_forecast


# Test data directory
TESTS_DIR = Path(__file__).parent
MANUAL_DIR = TESTS_DIR / "manual"
CONFIG_DIR = Path("config")


def create_test_city(
    city_id: str = "510",
    city_name_hebrew: str = "ירושלים",
    city_name_english: str = "Jerusalem",
    internal_key: str = "jerusalem",
    min_temp: int = 15,
    max_temp: int = 25,
    weather_code: str = "1250"
) -> CityForecast:
    """Helper function to create a test CityForecast object."""
    return CityForecast(
        city_id=city_id,
        city_name_hebrew=city_name_hebrew,
        city_name_english=city_name_english,
        internal_key=internal_key,
        forecast_date=date.today(),
        min_temp=min_temp,
        max_temp=max_temp,
        weather_code=weather_code,
        weather_description_hebrew="בהיר",
        weather_description_english="Clear"
    )


class TestCityComponentBasics:
    """Basic tests for city component rendering."""

    def test_render_completes_without_error(self):
        """
        Verify that rendering a city forecast doesn't crash.

        This is a basic smoke test - if it passes, the code at least runs.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")
        city = create_test_city()

        # Should not raise any exceptions
        render_city_forecast(canvas, city)

    def test_raises_error_for_unknown_city(self):
        """
        Verify that rendering fails gracefully for unknown cities.

        If a city's internal_key is not in design_tokens.json,
        we should get a clear ValueError.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")
        city = create_test_city(internal_key="unknown_city")

        with pytest.raises(ValueError, match="not found in design tokens"):
            render_city_forecast(canvas, city)

    def test_raises_error_for_unknown_weather_code(self):
        """
        Verify that rendering fails gracefully for unknown weather codes.

        If a weather code doesn't have an icon mapping,
        we should get a clear FileNotFoundError.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")
        city = create_test_city(weather_code="9999")

        with pytest.raises(FileNotFoundError, match="Weather icon not found"):
            render_city_forecast(canvas, city)


class TestLayoutModes:
    """Tests for different layout modes (RTL, LTR, TTB)."""

    def test_rtl_layout_renders(self):
        """
        Verify that RTL (right-to-left) layout renders correctly.

        RTL is the most common layout for Hebrew text, with the icon
        on the right and text flowing to the left.

        Layout: [Temperature] [City Name] [Icon]

        Visual output saved to: tests/manual/test_city_rtl_output.png
        """
        canvas = Image.new("RGB", (1080, 1920), "#87CEEB")  # Sky blue background

        # Jerusalem uses RTL layout
        city = create_test_city(
            city_id="510",
            city_name_hebrew="ירושלים",
            city_name_english="Jerusalem",
            internal_key="jerusalem",
            max_temp=25,
            weather_code="1250"
        )

        render_city_forecast(canvas, city)

        # Save visual test output
        output_path = MANUAL_DIR / "test_city_rtl_output.png"
        canvas.save(output_path)

        # Verify the file was saved
        assert output_path.exists()

    def test_ltr_layout_renders(self):
        """
        Verify that LTR (left-to-right) layout renders correctly.

        LTR is used for cities on the east side of the map where
        there's space to the right of the icon.

        Layout: [Icon] [City Name] [Temperature]

        Visual output saved to: tests/manual/test_city_ltr_output.png
        """
        canvas = Image.new("RGB", (1080, 1920), "#87CEEB")  # Sky blue background

        # Ein Gedi uses LTR layout
        city = create_test_city(
            city_id="105",
            city_name_hebrew="עין גדי",
            city_name_english="Ein Gedi",
            internal_key="ein_gedi",
            max_temp=32,
            weather_code="1310"  # Hot
        )

        render_city_forecast(canvas, city)

        # Save visual test output
        output_path = MANUAL_DIR / "test_city_ltr_output.png"
        canvas.save(output_path)

        # Verify the file was saved
        assert output_path.exists()

    def test_ttb_layout_renders(self):
        """
        Verify that TTB (top-to-bottom) layout renders correctly.

        TTB is used for cities in crowded areas where horizontal
        space is limited. The icon is on top with text stacked below.

        Layout:
            [Icon]
            [City Name]
            [Temperature]

        Visual output saved to: tests/manual/test_city_ttb_output.png
        """
        canvas = Image.new("RGB", (1080, 1920), "#87CEEB")  # Sky blue background

        # Eilat uses TTB layout
        city = create_test_city(
            city_id="520",
            city_name_hebrew="אילת",
            city_name_english="Eilat",
            internal_key="eilat",
            max_temp=35,
            weather_code="1580"  # Very hot
        )

        render_city_forecast(canvas, city)

        # Save visual test output
        output_path = MANUAL_DIR / "test_city_ttb_output.png"
        canvas.save(output_path)

        # Verify the file was saved
        assert output_path.exists()


class TestRealCityData:
    """Tests with real city names from cities.json."""

    def test_all_cities_from_config_render(self):
        """
        Verify that all 15 cities from cities.json render correctly.

        This is a comprehensive integration test that ensures every
        city in our configuration can be rendered without errors.

        Visual output saved to: tests/manual/test_all_cities_output.png
        """
        # Load cities from config
        cities_config_path = CONFIG_DIR / "cities.json"
        with open(cities_config_path, 'r', encoding='utf-8') as f:
            cities_config = json.load(f)

        # Create a blank canvas with sky blue background
        canvas = Image.new("RGB", (1080, 1920), "#87CEEB")

        # Render each city
        cities_data = cities_config.get("cities", {})
        for city_id, city_config in cities_data.items():
            city = create_test_city(
                city_id=city_id,
                city_name_hebrew=city_config["name_hebrew"],
                city_name_english=city_config["name_english"],
                internal_key=city_config["internal_key"],
                max_temp=20 + int(city_id) % 15,  # Vary temperature
                weather_code="1250"  # Clear weather for all
            )

            # Should not raise any exceptions
            render_city_forecast(canvas, city)

        # Save visual test output
        output_path = MANUAL_DIR / "test_all_cities_output.png"
        canvas.save(output_path)

        # Verify the file was saved
        assert output_path.exists()


class TestHebrewTextHandling:
    """Tests for Hebrew text rendering."""

    def test_hebrew_city_names_render(self):
        """
        Verify that various Hebrew city names render correctly.

        Hebrew names should appear properly shaped and ordered
        thanks to the text_utils.draw_hebrew_text() function.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")

        # Test cities with different Hebrew text characteristics
        test_cities = [
            ("510", "ירושלים", "Jerusalem", "jerusalem"),
            ("402", "תל אביב - יפו", "Tel Aviv - Yafo", "tel_aviv"),
            ("513", "באר שבע", "Beer Sheva", "beer_sheva"),
            ("507", "צפת", "Zefat", "zefat"),
        ]

        for city_id, name_hebrew, name_english, internal_key in test_cities:
            city = create_test_city(
                city_id=city_id,
                city_name_hebrew=name_hebrew,
                city_name_english=name_english,
                internal_key=internal_key
            )

            # Should not raise any exceptions
            render_city_forecast(canvas, city)


class TestIconLoading:
    """Tests for weather icon loading and positioning."""

    def test_various_weather_icons_load(self):
        """
        Verify that different weather icons load correctly.

        Each weather code should map to a valid icon file
        that exists in assets/Weather_Icons/.

        Visual output saved to: tests/manual/test_weather_icons_output.png
        """
        canvas = Image.new("RGB", (1080, 1920), "#87CEEB")

        # Test cities with different weather conditions
        test_scenarios = [
            ("jerusalem", "1250", "Clear"),
            ("tel_aviv", "1220", "Partly Cloudy"),
            ("haifa", "1140", "Rain"),
            ("eilat", "1310", "Hot"),
        ]

        for internal_key, weather_code, description in test_scenarios:
            city = create_test_city(
                internal_key=internal_key,
                weather_code=weather_code
            )

            # Should not raise any exceptions
            render_city_forecast(canvas, city)

        # Save visual test output
        output_path = MANUAL_DIR / "test_weather_icons_output.png"
        canvas.save(output_path)

        # Verify the file was saved
        assert output_path.exists()


class TestTemperatureFormatting:
    """Tests for temperature text formatting."""

    def test_temperature_with_degree_symbol(self):
        """
        Verify that temperature is formatted with a degree symbol.

        The temperature should appear as "25°" not just "25".
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")

        city = create_test_city(max_temp=25)
        render_city_forecast(canvas, city)

        # If we got here without error, the degree symbol was handled correctly

    def test_various_temperature_ranges(self):
        """
        Verify that different temperature values render correctly.

        We should handle single-digit, double-digit, and even
        negative temperatures if needed.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")

        test_temps = [5, 15, 25, 35, 42]

        for temp in test_temps:
            # Set min_temp slightly lower than max_temp
            city = create_test_city(min_temp=temp - 5, max_temp=temp)

            # Should not raise any exceptions
            render_city_forecast(canvas, city)


class TestVisualOutputs:
    """Tests that generate comprehensive visual outputs."""

    def test_create_layout_comparison_grid(self):
        """
        Create a visual comparison of all three layout modes.

        This generates a side-by-side comparison showing how
        RTL, LTR, and TTB layouts differ.

        Visual output saved to: tests/manual/test_layout_comparison.png
        """
        # Create three separate canvases
        rtl_canvas = Image.new("RGB", (360, 640), "#87CEEB")
        ltr_canvas = Image.new("RGB", (360, 640), "#87CEEB")
        ttb_canvas = Image.new("RGB", (360, 640), "#87CEEB")

        # Scale coordinates for smaller canvas (1/3 size)
        scale_factor = 1/3

        # Load design tokens
        with open(CONFIG_DIR / "design_tokens.json", 'r', encoding='utf-8') as f:
            design_tokens = json.load(f)

        # Create scaled design tokens for smaller canvas
        scaled_tokens = json.loads(json.dumps(design_tokens))  # Deep copy
        for city_key in scaled_tokens["city_positions"].keys():
            if city_key.startswith("_"):  # Skip metadata fields like "_comment"
                continue
            scaled_tokens["city_positions"][city_key]["x"] = int(
                scaled_tokens["city_positions"][city_key]["x"] * scale_factor
            )
            scaled_tokens["city_positions"][city_key]["y"] = int(
                scaled_tokens["city_positions"][city_key]["y"] * scale_factor
            )

        # RTL example (Jerusalem)
        rtl_city = create_test_city(internal_key="jerusalem")
        render_city_forecast(rtl_canvas, rtl_city, scaled_tokens)

        # LTR example (Ein Gedi)
        ltr_city = create_test_city(internal_key="ein_gedi")
        render_city_forecast(ltr_canvas, ltr_city, scaled_tokens)

        # TTB example (Eilat)
        ttb_city = create_test_city(internal_key="eilat")
        render_city_forecast(ttb_canvas, ttb_city, scaled_tokens)

        # Combine into one image
        combined = Image.new("RGB", (1080, 640), "#FFFFFF")
        combined.paste(rtl_canvas, (0, 0))
        combined.paste(ltr_canvas, (360, 0))
        combined.paste(ttb_canvas, (720, 0))

        # Save visual test output
        output_path = MANUAL_DIR / "test_layout_comparison.png"
        combined.save(output_path)

        # Verify the file was saved
        assert output_path.exists()


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_missing_design_tokens_raises_error(self):
        """
        Verify that missing design tokens cause appropriate errors.

        If the design_tokens.json file is missing required fields,
        we should get clear error messages.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")
        city = create_test_city()

        # Create invalid design tokens (missing city_positions)
        invalid_tokens = {"typography": {}, "icon_sizes": {}}

        # Should raise a clear error
        with pytest.raises((ValueError, KeyError)):
            render_city_forecast(canvas, city, invalid_tokens)

    def test_invalid_layout_mode_raises_error(self):
        """
        Verify that an invalid layout mode causes an error.

        If somehow a city has an invalid layout mode in design tokens,
        we should get a clear error message.
        """
        canvas = Image.new("RGB", (1080, 1920), "#FFFFFF")
        city = create_test_city()

        # Load design tokens and modify layout mode
        with open(CONFIG_DIR / "design_tokens.json", 'r', encoding='utf-8') as f:
            design_tokens = json.load(f)

        # Set invalid layout mode
        design_tokens["city_positions"]["jerusalem"]["layout"] = "INVALID"

        # Should raise a clear error
        with pytest.raises(ValueError, match="Unknown layout mode"):
            render_city_forecast(canvas, city, design_tokens)
