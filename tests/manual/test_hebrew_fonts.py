"""
Manual Hebrew Font Testing - Visual Verification

This script generates test images to visually verify Hebrew text rendering.
Run this script to generate sample images, then manually inspect them to
ensure:
- Hebrew text is displayed right-to-left
- Mixed Hebrew/English/numbers are ordered correctly
- All font styles render properly
- Character shapes are correct

Usage:
    python tests/manual/test_hebrew_fonts.py

Output:
    Images saved to tests/manual/hebrew_text_samples/
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime

# Import our Hebrew text utilities
from src.rendering.text_utils import draw_hebrew_text, get_text_size
from src.rendering.font_loader import get_fonts_from_tokens, load_font


# Directories
OUTPUT_DIR = Path(__file__).parent / "hebrew_text_samples"
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def create_output_directory():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def test_all_font_styles():
    """Test all typography styles from design_tokens.json."""
    print("\n=== Testing All Font Styles ===")

    # Load all fonts
    fonts = get_fonts_from_tokens()

    # Create a test image
    img_width = 800
    img_height = len(fonts) * 100 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    title_font = load_font("NotoSansHebrew-Black", 28)
    draw_hebrew_text(draw, "כל סגנונות הפונטים", (img_width // 2, 30), title_font, fill="black", anchor="mm")

    # Draw a line
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Test each font style
    y_pos = 100
    sample_text = "עברית שלום עולם 123"

    for style_name, font in fonts.items():
        # Style name (in English)
        info_font = load_font("NotoSansHebrew-Regular", 12)
        draw.text((50, y_pos - 10), f"{style_name} - {font.size}px", font=info_font, fill="gray")

        # Hebrew text in this style
        draw_hebrew_text(draw, sample_text, (img_width // 2, y_pos + 20), font, fill="black", anchor="mm")

        y_pos += 80

    # Save
    output_path = OUTPUT_DIR / "01_all_font_styles.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_city_names():
    """Test rendering city names from cities.json."""
    print("\n=== Testing City Names ===")

    # Load cities
    cities_path = CONFIG_DIR / "cities.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        cities_data = json.load(f)

    cities = cities_data["cities"]

    # Load font
    city_font = load_font("NotoSansHebrew-Black", 24)
    english_font = load_font("NotoSansHebrew-Regular", 14)

    # Create image
    num_cities = len(cities)
    img_width = 600
    img_height = num_cities * 60 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    title_font = load_font("NotoSansHebrew-Black", 28)
    draw_hebrew_text(draw, "שמות ערים", (img_width // 2, 30), title_font, fill="black", anchor="mm")
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Draw each city
    y_pos = 100
    for city_id, city_data in cities.items():
        hebrew_name = city_data["name_hebrew"]
        english_name = city_data["name_english"]

        # Hebrew name (large)
        draw_hebrew_text(draw, hebrew_name, (img_width // 2, y_pos), city_font, fill="black", anchor="mm")

        # English name (small, below)
        draw.text((img_width // 2, y_pos + 25), english_name, font=english_font, fill="gray", anchor="mm")

        y_pos += 60

    # Save
    output_path = OUTPUT_DIR / "02_city_names.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_temperature_display():
    """Test temperature rendering with degree symbols."""
    print("\n=== Testing Temperature Display ===")

    # Load font
    temp_font = load_font("NotoSansHebrew-SemiBold", 48)
    label_font = load_font("NotoSansHebrew-Regular", 20)

    # Temperature test cases
    temperatures = [
        ("חם מאוד - 42°C", "Very hot"),
        ("חם - 30°C", "Hot"),
        ("נעים - 22°C", "Pleasant"),
        ("קר - 10°C", "Cold"),
        ("קפוא - 0°C", "Freezing"),
        ("תחת אפס - -5°C", "Below zero"),
    ]

    # Create image
    img_width = 500
    img_height = len(temperatures) * 100 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    title_font = load_font("NotoSansHebrew-Black", 28)
    draw_hebrew_text(draw, "תצוגת טמפרטורות", (img_width // 2, 30), title_font, fill="black", anchor="mm")
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Draw each temperature
    y_pos = 110
    for hebrew_text, english_text in temperatures:
        # Hebrew text with temperature
        draw_hebrew_text(draw, hebrew_text, (img_width // 2, y_pos), temp_font, fill="black", anchor="mm")

        # English label
        draw.text((img_width // 2, y_pos + 35), english_text, font=label_font, fill="gray", anchor="mm")

        y_pos += 100

    # Save
    output_path = OUTPUT_DIR / "03_temperatures.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_hebrew_dates():
    """Test Hebrew date formatting."""
    print("\n=== Testing Hebrew Dates ===")

    # Load font
    date_font = load_font("NotoSansHebrew-Black", 36)
    small_font = load_font("NotoSansHebrew-Regular", 18)

    # Date test cases (Hebrew dates)
    dates = [
        "יום ראשון, 1 בינואר 2024",
        "יום שני, 15 בפברואר 2024",
        "יום שלישי, 22 במרץ 2024",
        "יום רביעי, 10 באפריל 2024",
        "יום חמישי, 5 במאי 2024",
        "יום שישי, 30 ביוני 2024",
        "שבת, 25 בדצמבר 2024",
    ]

    # Create image
    img_width = 600
    img_height = len(dates) * 80 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    title_font = load_font("NotoSansHebrew-Black", 28)
    draw_hebrew_text(draw, "תאריכים בעברית", (img_width // 2, 30), title_font, fill="black", anchor="mm")
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Draw each date
    y_pos = 100
    for date_text in dates:
        draw_hebrew_text(draw, date_text, (img_width // 2, y_pos), date_font, fill="black", anchor="mm")
        y_pos += 80

    # Save
    output_path = OUTPUT_DIR / "04_hebrew_dates.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_mixed_content():
    """Test mixed Hebrew, English, and numbers."""
    print("\n=== Testing Mixed Content ===")

    # Load font
    mixed_font = load_font("NotoSansHebrew-SemiBold", 28)
    title_font = load_font("NotoSansHebrew-Black", 28)

    # Mixed content test cases
    test_cases = [
        ("תל אביב - Tel Aviv", "City with translation"),
        ("Temperature: 25°C", "English label with number"),
        ("25°C :טמפרטורה", "Hebrew label with number"),
        ("IMS - שירות המטאורולוגי", "Acronym with Hebrew"),
        ("2024 שנה טובה", "Number before Hebrew"),
        ("יום שני 22/01/2024", "Date in mixed format"),
        ("Latitude: 31.7683° N", "Coordinates"),
        ("קו רוחב: 31.7683° צפון", "Coordinates in Hebrew"),
    ]

    # Create image
    img_width = 700
    img_height = len(test_cases) * 80 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    draw_hebrew_text(draw, "תוכן מעורב - עברית + אנגלית + מספרים", (img_width // 2, 30), title_font, fill="black", anchor="mm")
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Draw each test case
    y_pos = 100
    label_font = load_font("NotoSansHebrew-Regular", 14)
    for mixed_text, description in test_cases:
        # The mixed text
        draw_hebrew_text(draw, mixed_text, (img_width // 2, y_pos), mixed_font, fill="black", anchor="mm")

        # Description
        draw.text((img_width // 2, y_pos + 25), description, font=label_font, fill="gray", anchor="mm")

        y_pos += 80

    # Save
    output_path = OUTPUT_DIR / "05_mixed_content.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_bidi_edge_cases():
    """Test BiDi edge cases and potential issues."""
    print("\n=== Testing BiDi Edge Cases ===")

    # Load font
    test_font = load_font("NotoSansHebrew-SemiBold", 24)
    title_font = load_font("NotoSansHebrew-Black", 28)

    # Edge cases
    edge_cases = [
        ("123 שלום 456", "Numbers on both sides"),
        ("(ירושלים)", "Hebrew in parentheses"),
        ("[תל אביב]", "Hebrew in brackets"),
        ('שלום "עולם"', "Hebrew with quotes"),
        ("א-ב-ג", "Hebrew with hyphens"),
        ("25°C - 30°C", "Temperature range"),
        ("10:00 - 18:00", "Time range"),
        ("א/ב/ג", "Hebrew with slashes"),
    ]

    # Create image
    img_width = 600
    img_height = len(edge_cases) * 70 + 100
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Title
    draw_hebrew_text(draw, "מקרי קצה - BiDi", (img_width // 2, 30), title_font, fill="black", anchor="mm")
    draw.line([(50, 60), (img_width - 50, 60)], fill="gray", width=2)

    # Draw each edge case
    y_pos = 100
    label_font = load_font("NotoSansHebrew-Regular", 14)
    for text, description in edge_cases:
        # The text
        draw_hebrew_text(draw, text, (img_width // 2, y_pos), test_font, fill="black", anchor="mm")

        # Description
        draw.text((img_width // 2, y_pos + 22), description, font=label_font, fill="gray", anchor="mm")

        y_pos += 70

    # Save
    output_path = OUTPUT_DIR / "06_bidi_edge_cases.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def test_realistic_forecast():
    """Test a realistic weather forecast card layout."""
    print("\n=== Testing Realistic Forecast Layout ===")

    # Load fonts from design tokens
    fonts = get_fonts_from_tokens()

    # Load city data
    cities_path = CONFIG_DIR / "cities.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        cities_data = json.load(f)

    # Pick a few cities for testing
    selected_cities = ["jerusalem", "tel_aviv", "haifa", "beer_sheva", "eilat"]

    # Create image (similar to actual forecast layout)
    img_width = 800
    img_height = 900
    img = Image.new("RGB", (img_width, img_height), "#F0F8FF")
    draw = ImageDraw.Draw(img)

    # Header with date
    header_y = 40
    draw_hebrew_text(
        draw,
        "יום שלישי, 22 בינואר 2024",
        (img_width // 2, header_y),
        fonts["header_date"],
        fill="#1E3A8A",
        anchor="mm"
    )

    # Separator line
    draw.line([(100, 80), (img_width - 100, 80)], fill="#1E3A8A", width=3)

    # Title
    title_font = load_font("NotoSansHebrew-Black", 32)
    draw_hebrew_text(
        draw,
        "תחזית מזג אויר",
        (img_width // 2, 120),
        title_font,
        fill="#1E3A8A",
        anchor="mm"
    )

    # City forecasts
    y_pos = 180
    for city_key in selected_cities:
        # Find city data
        city_data = None
        for cid, cdata in cities_data["cities"].items():
            if cdata["internal_key"] == city_key:
                city_data = cdata
                break

        if not city_data:
            continue

        # Draw city card background
        card_x = 100
        card_y = y_pos
        card_width = img_width - 200
        card_height = 80

        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            radius=15,
            fill="white",
            outline="#1E3A8A",
            width=2
        )

        # City name
        city_name = city_data["name_hebrew"]
        draw_hebrew_text(
            draw,
            city_name,
            (card_x + card_width - 30, card_y + 25),
            fonts["city_name"],
            fill="#000000",
            anchor="rm"
        )

        # Temperature
        import random
        temp = random.randint(15, 30)
        temp_text = f"{temp}°C"
        draw_hebrew_text(
            draw,
            temp_text,
            (card_x + 50, card_y + 25),
            fonts["temperature"],
            fill="#1E3A8A",
            anchor="lm"
        )

        # Description
        descriptions = ["שמיים בהירים", "מעונן חלקית", "גשום", "שמשי", "מעורפל"]
        desc_text = random.choice(descriptions)
        desc_font = load_font("NotoSansHebrew-SemiBold", 16)
        draw_hebrew_text(
            draw,
            desc_text,
            (card_x + card_width // 2, card_y + 55),
            desc_font,
            fill="#555555",
            anchor="mm"
        )

        y_pos += 100

    # Footer
    footer_font = load_font("NotoSansHebrew-Regular", 16)
    draw_hebrew_text(
        draw,
        "שירות המטאורולוגי הישראלי",
        (img_width // 2, img_height - 30),
        footer_font,
        fill="#666666",
        anchor="mm"
    )

    # Save
    output_path = OUTPUT_DIR / "07_realistic_forecast.png"
    img.save(output_path)
    print(f"✓ Saved: {output_path}")


def main():
    """Run all manual tests and generate visual samples."""
    print("="*60)
    print("Hebrew Font Visual Testing")
    print("="*60)

    # Create output directory
    create_output_directory()

    # Run all tests
    try:
        test_all_font_styles()
        test_city_names()
        test_temperature_display()
        test_hebrew_dates()
        test_mixed_content()
        test_bidi_edge_cases()
        test_realistic_forecast()

        print("\n" + "="*60)
        print("✓ All visual tests completed successfully!")
        print(f"✓ Output saved to: {OUTPUT_DIR}")
        print("="*60)
        print("\nPlease manually inspect the generated images to verify:")
        print("  1. Hebrew text is displayed right-to-left")
        print("  2. Mixed Hebrew/English/numbers are ordered correctly")
        print("  3. All font styles render properly")
        print("  4. Character shapes are correct")
        print("  5. No garbled or reversed text")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
