# IMS Automated Weather Forecast Generator

## Initial Project Plan — Version 1.0

**Created:** 2025-12-18  
**Author:** Noam Weiss + AI Planning Assistant  
**Status:** Approved for Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Goals](#project-goals)
3. [Tech Stack Decision](#tech-stack-decision)
4. [Design-to-Code Philosophy](#design-to-code-philosophy)
5. [System Architecture](#system-architecture)
6. [Folder Structure](#folder-structure)
7. [Module Specifications](#module-specifications)
8. [Configuration Files](#configuration-files)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Phases](#implementation-phases)
11. [Future Extensibility](#future-extensibility)

---

## Executive Summary

This project creates an **automated daily weather forecast image generator** for the Israel Meteorological Service (IMS) Media Team. The system will:

1. **Fetch** weather forecast data from IMS XML sources
2. **Generate** a designed image based on Figma specifications — a stylized Israel map layout (1080×1920 for Instagram Stories)
3. **Deliver** images via email to the media team for social media distribution
4. **Run** automatically each morning via GitHub Actions

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Clarity over cleverness** | Code must be understandable by a designer learning to code |
| **Design-first approach** | Layout mirrors Figma mental model — Auto-layout, Components, Tokens |
| **Modular architecture** | Each module has one job; easy to extend and debug |
| **Configuration-driven** | Design values live in JSON files, not hardcoded in Python |
| **Comprehensive documentation** | Every function explains WHY, not just WHAT |

---

## Project Goals

### Primary Goal

Generate a beautiful, accurate daily weather forecast image and deliver it to the IMS media team inbox by 6:00 AM each day.

### Secondary Goals

- Build a codebase that the primary developer (a designer) can understand, debug, and extend
- Create an extensible system that can support additional layouts (Twitter, Facebook, WhatsApp) in the future
- Establish proper development practices: version control, documentation, testing, changelogs

### Non-Goals (for v1.0)

- Real-time weather updates
- User-facing web interface
- Multiple recipients with different preferences
- API for external consumers

---

## Tech Stack Decision

### Primary Language: Python 3.11+

Python was selected for this project because:

| Reason | Details |
|--------|---------|
| **Beginner-friendly** | Clean, readable syntax that reads almost like English |
| **Excellent libraries** | Pillow for image generation, lxml for XML parsing |
| **GitHub Actions native** | First-class support for automated workflows |
| **Strong typing optional** | Can add type hints gradually for clarity |
| **Extensive documentation** | Every library has examples and tutorials |

### Core Dependencies

```text
requests>=2.31.0       # HTTP requests for fetching XML data
pillow>=10.0.0         # Image generation and manipulation
lxml>=4.9.0            # XML parsing with proper encoding support
python-dotenv>=1.0.0   # Environment variable management
python-bidi>=0.4.2     # BiDi algorithm for Hebrew text
arabic-reshaper>=3.0.0 # Hebrew/Arabic character shaping
```

### Why Pillow for Image Generation?

Initial consideration was given to browser-based screenshot approaches (HTML/CSS → image), but **Pillow** was chosen because:

1. **Pixel-perfect control** — Every element is positioned with exact coordinates
2. **Proper Hebrew rendering** — Full control over RTL text with BiDi support
3. **No browser dependencies** — Simpler deployment, faster execution
4. **Lighter weight** — Important for GitHub Actions (faster runs, lower costs)
5. **Reproducible output** — Same input always produces identical output

---

## Design-to-Code Philosophy

### The Figma Mental Model in Python

The code structure mirrors how a designer thinks in Figma. This makes the codebase intuitive for the primary developer.

| Figma Concept | Python Equivalent | Example |
|--------------|-------------------|---------|
| **Frame** | `Image.new(size)` | Create a canvas with exact dimensions |
| **Position (x, y)** | Tuple `(x, y)` | Every element has explicit coordinates |
| **Fill color** | Hex string | `fill="#1A1A2E"` |
| **Text style** | Dict from tokens | `tokens["typography"]["city_name"]` |
| **Auto-layout gap** | Math operation | `y += row_height + gap` |
| **Component** | Python function | A reusable function that draws a group |
| **Component instance** | Function call | Call the function with different data |
| **Design tokens** | JSON file | `config/design_tokens.json` |
| **Component states** | Conditional logic | `if weather.is_severe: use_warning_style()` |

### Component = Function Example

```python
def draw_city_forecast(canvas, city_data, position, tokens):
    """
    Draws a single city's forecast — equivalent to a Figma Component.
    
    Call this function 15 times with different city data and positions
    to populate all cities on the map.
    
    Parameters:
        canvas: The PIL Image to draw on
        city_data: CityForecast dataclass with weather info
        position: (x, y) tuple — the component's origin point
        tokens: Design tokens dict with styles and spacing
    """
    x, y = position
    style = tokens["typography"]["city_name"]
    
    # Draw city name (Hebrew, right-to-left)
    draw_hebrew_text(canvas, city_data.name_hebrew, (x, y), style)
    
    # Draw temperature
    temp_style = tokens["typography"]["temperature"]
    temp_offset = tokens["positions"]["temp_offset"]
    draw_text(canvas, f"{city_data.max_temp}°", (x + temp_offset, y), temp_style)
    
    # Draw weather icon
    icon = get_weather_icon(city_data.weather_code)
    icon_offset = tokens["positions"]["icon_offset"]
    canvas.paste(icon, (x + icon_offset, y - 10), icon)  # icon as mask for transparency
```

### Positions in Configuration, Not Code

All city positions on the Israel map are defined in `design_tokens.json`, extracted from Figma:

```json
{
  "city_positions": {
    "jerusalem": { "x": 540, "y": 1100, "anchor": "center" },
    "tel_aviv": { "x": 320, "y": 950, "anchor": "right" },
    "haifa": { "x": 400, "y": 580, "anchor": "left" },
    "eilat": { "x": 520, "y": 1650, "anchor": "center" }
  }
}
```

This means: **changing city positions on the map requires editing JSON, not Python code.**

---

## System Architecture

### Data Flow Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DAILY EXECUTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │  IMS Website │
     │  XML Feeds   │
     └──────┬───────┘
            │
            ▼
    ┌───────────────┐      ┌───────────────┐
    │   FETCHER     │─────▶│   ARCHIVE     │  ← Save copy (7-day history)
    │ Download XML  │      │ backup/       │
    └───────┬───────┘      └───────────────┘
            │                      │
            │    ┌─────────────────┘
            │    │ (fallback if fetch fails)
            ▼    ▼
    ┌───────────────┐
    │    PARSER     │
    │ XML → Python  │
    │   Objects     │
    └───────┬───────┘
            │
            │   CityForecast[]
            │   CountryForecast
            ▼
    ┌───────────────┐      ┌───────────────┐
    │   RENDERER    │◀─────│ DESIGN TOKENS │  ← Colors, fonts, positions
    │  Generate     │      │ JSON Config   │
    │  Image        │      └───────────────┘
    └───────┬───────┘              ▲
            │                      │
            │   PIL.Image          │ (one-time extraction from Figma)
            ▼                      │
    ┌───────────────┐      ┌───────────────┐
    │  FILE SAVER   │      │    FIGMA      │
    │  .jpg + .png  │      │   Design      │
    └───────┬───────┘      └───────────────┘
            │
            │   image paths
            ▼
    ┌───────────────┐
    │ EMAIL SENDER  │
    │  SMTP/Gmail   │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │  IMS MEDIA    │
    │  TEAM INBOX   │
    └───────────────┘
```

### Error Handling & Fallback Strategy

When the XML fetch fails:

1. **Attempt 1**: Fetch from IMS (primary source)
2. **Attempt 2**: Retry after 30 seconds
3. **Attempt 3**: Retry after 60 seconds
4. **Fallback**: Use yesterday's archived XML
5. **Last resort**: Use most recent available archive (up to 7 days)
6. **If all fail**: Send alert email to developer, skip image generation

The archive folder maintains a 7-day rolling history:

```text
archive/
├── 2024-12-18_country.xml
├── 2024-12-18_cities.xml
├── 2024-12-17_country.xml
├── 2024-12-17_cities.xml
└── ... (up to 7 days)
```

---

## Folder Structure

```text
Auto_Forecast_Design/
│
├── 📄 CLAUDE.md                    # AI assistant context
├── 📄 CHANGELOG.md                 # Version history
├── 📄 README.md                    # Project overview & quick start
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env                         # Environment variables (gitignored)
├── 📄 .gitignore                   # Git exclusions
│
├── 📁 assets/                      # Static design assets
│   ├── 📁 Fonts/                   # Noto Sans Hebrew (9 weights)
│   ├── 📁 Logos/                   # IMS + MOT logos (PNG + SVG)
│   ├── 📁 Weather_Icons/           # 16 weather condition icons
│   └── 📁 Map/                     # Israel map background [NEW]
│       └── israel_map_base.png
│
├── 📁 config/                      # Configuration files [NEW]
│   ├── 📄 design_tokens.json       # Figma extraction: colors, typography, positions
│   ├── 📄 layout_instagram_story.json  # Layout-specific settings
│   └── 📄 cities.json              # City metadata and display settings
│
├── 📁 docs/                        # Documentation
│   ├── 📄 00_initial_plan.md       # This document
│   ├── 📄 00_ims_weather_codes.json    # Weather code reference
│   └── 📁 internal/                # Internal dev docs (gitignored)
│
├── 📁 src/                         # Source code [NEW]
│   ├── 📄 __init__.py              # Package marker
│   ├── 📄 main.py                  # Entry point — orchestrates workflow
│   │
│   ├── 📁 data/                    # Data fetching & processing
│   │   ├── 📄 __init__.py
│   │   ├── 📄 fetcher.py           # Download XML from IMS URLs
│   │   ├── 📄 parser.py            # Parse XML into Python objects
│   │   ├── 📄 models.py            # Data classes (CityForecast, etc.)
│   │   └── 📄 archive.py           # XML backup & fallback logic [NEW]
│   │
│   ├── 📁 design/                  # Design system
│   │   ├── 📄 __init__.py
│   │   ├── 📄 tokens.py            # Load and access design tokens
│   │   └── 📄 icon_mapper.py       # Map weather codes → icon files
│   │
│   ├── 📁 rendering/               # Image generation
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_renderer.py     # Abstract base class for layouts
│   │   ├── 📄 instagram_story.py   # Instagram Story layout (1080×1920)
│   │   ├── 📄 text_utils.py        # Hebrew text handling (RTL, shaping)
│   │   └── 📁 components/          # Reusable visual components [FUTURE]
│   │
│   ├── 📁 delivery/                # Output & distribution
│   │   ├── 📄 __init__.py
│   │   ├── 📄 email_sender.py      # SMTP email functionality
│   │   └── 📄 file_saver.py        # Save JPEG + PNG to filesystem
│   │
│   └── 📁 utils/                   # Shared utilities
│       ├── 📄 __init__.py
│       ├── 📄 logger.py            # Logging configuration
│       └── 📄 date_utils.py        # Hebrew + Georgian date formatting
│
├── 📁 archive/                     # XML backup storage [NEW] (gitignored)
│   └── 📄 .gitkeep
│
├── 📁 output/                      # Generated images [NEW] (gitignored)
│   └── 📄 .gitkeep
│
├── 📁 tests/                       # Automated tests [NEW]
│   ├── 📄 __init__.py
│   ├── 📄 test_fetcher.py          # Test XML downloading
│   ├── 📄 test_parser.py           # Test XML parsing
│   ├── 📄 test_rendering.py        # Test image generation
│   └── 📄 test_date_utils.py       # Test date formatting
│
└── 📁 .github/                     # GitHub configuration [NEW]
    └── 📁 workflows/
        └── 📄 daily_forecast.yml   # Scheduled daily execution
```

### Files to Add to .gitignore

```gitignore
# Existing
logs/
.gemini/
.claude/
.env
docs/internal/

# New additions
archive/
output/
__pycache__/
*.pyc
.pytest_cache/
```

---

## Module Specifications

### Data Models (`src/data/models.py`)

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class CityForecast:
    """
    Weather forecast for a single city on a single day.
    
    This represents one <Location> element from the isr_cities.xml file,
    containing all forecast data for that city.
    """
    city_id: str                    # e.g., "510" for Jerusalem
    city_name_hebrew: str           # e.g., "ירושלים"
    city_name_english: str          # e.g., "Jerusalem"
    forecast_date: date             # The date this forecast is for
    
    min_temp: int                   # Minimum temperature in Celsius
    max_temp: int                   # Maximum temperature in Celsius
    
    weather_code: str               # e.g., "1250" for Clear
    weather_description_hebrew: str # e.g., "בהיר"
    weather_description_english: str # e.g., "Clear"
    
    # Optional fields (not always present in XML)
    humidity_min: Optional[int] = None
    humidity_max: Optional[int] = None
    wind_direction: Optional[str] = None  # e.g., "315-45" (degrees)
    wind_speed: Optional[str] = None      # e.g., "10-30" (km/h)


@dataclass
class CountryForecast:
    """
    General weather description for all of Israel.
    
    This represents the narrative forecast text from isr_country.xml,
    describing overall weather conditions.
    """
    forecast_date: date
    description_hebrew: str         # Main forecast text in Hebrew
    description_english: str        # Main forecast text in English
    warning_hebrew: Optional[str] = None
    warning_english: Optional[str] = None


@dataclass  
class DailyForecast:
    """
    Complete forecast data for a single day.
    
    This is what gets passed to the renderer — contains everything
    needed to generate an image.
    """
    forecast_date: date
    country_forecast: CountryForecast
    city_forecasts: list[CityForecast]  # All 15 cities
    
    # Metadata
    xml_fetch_time: str             # When we fetched the XML
    is_fallback: bool = False       # True if using archived data
```

### Date Utilities (`src/utils/date_utils.py`)

The header design uses both Hebrew and Georgian dates. This module handles conversion:

```python
def get_hebrew_date(gregorian_date: date) -> str:
    """
    Convert a Gregorian date to Hebrew calendar format.
    
    Example: 2024-12-18 → "כ״א בכסלו תשפ״ה"
    
    Uses the hebrew-calendar library for accurate conversion.
    """
    pass

def get_formatted_date(gregorian_date: date) -> dict:
    """
    Return both date formats for display.
    
    Returns:
        {
            "hebrew": "כ״א בכסלו תשפ״ה",
            "georgian": "18 בדצמבר 2024",
            "day_of_week_hebrew": "יום רביעי"
        }
    """
    pass
```

### XML Archive (`src/data/archive.py`)

```python
ARCHIVE_DIR = "archive"
MAX_ARCHIVE_DAYS = 7

def save_to_archive(xml_content: str, xml_type: str, fetch_date: date) -> str:
    """
    Save XML content to the archive folder.
    
    Args:
        xml_content: The raw XML string
        xml_type: Either "country" or "cities"
        fetch_date: The date of the fetch
    
    Returns:
        Path to the saved file
    
    Example:
        save_to_archive(xml, "cities", date(2024, 12, 18))
        # Saves to: archive/2024-12-18_cities.xml
    """
    pass

def get_fallback_xml(xml_type: str) -> Optional[tuple[str, date]]:
    """
    Get the most recent archived XML as fallback.
    
    Tries yesterday first, then goes back up to 7 days.
    
    Returns:
        Tuple of (xml_content, archive_date) or None if no archive available
    """
    pass

def cleanup_old_archives():
    """
    Remove archive files older than MAX_ARCHIVE_DAYS.
    
    Called after successful fetch to keep archive folder clean.
    """
    pass
```

### File Saver (`src/delivery/file_saver.py`)

Both JPEG and PNG formats are generated:

```python
from PIL import Image
from pathlib import Path

def save_forecast_image(image: Image.Image, date_str: str) -> dict:
    """
    Save the generated image in both JPEG and PNG formats.
    
    Args:
        image: The PIL Image object to save
        date_str: Date string for filename (e.g., "2024-12-18")
    
    Returns:
        {
            "jpeg": "output/forecast_2024-12-18.jpg",
            "png": "output/forecast_2024-12-18.png"
        }
    
    JPEG is used for email delivery (smaller file size).
    PNG is kept for archive and other potential uses.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    base_name = f"forecast_{date_str}"
    paths = {}
    
    # Save as JPEG (optimized for email)
    jpeg_path = output_dir / f"{base_name}.jpg"
    # Convert to RGB (JPEG doesn't support alpha channel)
    rgb_image = image.convert("RGB")
    rgb_image.save(jpeg_path, "JPEG", quality=90, optimize=True)
    paths["jpeg"] = str(jpeg_path)
    
    # Save as PNG (lossless, with transparency support)
    png_path = output_dir / f"{base_name}.png"
    image.save(png_path, "PNG", optimize=True)
    paths["png"] = str(png_path)
    
    return paths
```

---

## Configuration Files

### Design Tokens (`config/design_tokens.json`)

This file contains all values extracted from Figma. It is the single source of truth for the design system:

```jsonc
{
  "_meta": {
    "description": "Design tokens extracted from Figma for the IMS Weather Forecast Generator",
    "figma_url": "https://www.figma.com/design/YVPUc24KCJIFrHpoXKrHz7/Story-Layout-V2.0?node-id=1-2",
    "last_updated": "2025-12-22",
    "status": "VALIDATED - Extracted from Figma using Figma MCP",
    "extraction_method": "Figma MCP Desktop (http://127.0.0.1:3845/mcp)"
  },

  "canvas": {
    "width": 1080,
    "height": 1920,
    "background": {
      "type": "gradient",
      "gradient_type": "linear",
      "angle": -23.2359,
      "stops": [
        {"color": "#DCFF57", "position": 62.599},
        {"color": "#22B2FF", "position": 112.14}
      ]
    }
  },

  "colors": {
    "text_primary": "#FFFFFF",
    "text_secondary": "#000000",
    "gradient_start": "#DCFF57",
    "gradient_end": "#22B2FF",
    "header_separator": "#FFFFFF"
  },

  "typography": {
    "header_date": {
      "font_family": "NotoSansHebrew-Black",
      "font_size": 36,
      "font_weight": 900,
      "line_height": 28,
      "color": "#FFFFFF"
    },
    "city_name": {
      "font_family": "NotoSansHebrew-Black",
      "font_size": 24,
      "font_weight": 900,
      "line_height": 24,
      "color": "#000000"
    },
    "temperature": {
      "font_family": "NotoSansHebrew-SemiBold",
      "font_size": 20,
      "font_weight": 600,
      "line_height": 20,
      "color": "#000000"
    },
    "description": {
      "font_family": "NotoSansHebrew-SemiBold",
      "font_size": 24,
      "font_weight": 600,
      "line_height": 36,
      "color": "#000000"
    },
    "ims_logo_text": {
      "font_family": "NotoSansHebrew-ExtraCondensed",
      "font_size": 18,
      "font_weight": 400,
      "line_height": 18,
      "color": "#000000"
    }
  },

  "spacing": {
    "header": {
      "padding_top": 57,
      "padding_bottom": 18,
      "padding_horizontal": 100,
      "gap": 40,
      "separator_height": 7
    },
    "forecast_data_container": {
      "left": 128,
      "top": 248,
      "width": 847,
      "height": 1582
    },
    "city_component": {
      "gap": 16,
      "padding": 10,
      "border_radius": 18
    },
    "israel_map": {
      "left": 258,
      "top": 288.3,
      "width": 533.371,
      "height": 1495.196
    },
    "logos": {
      "left": 633,
      "top": 1709,
      "gap": 24
    }
  },

  "city_positions": {
    "_comment": "Coordinates extracted from Figma. Positions are (x, y) from top-left of canvas. Layout types: RTL (right-to-left), TTB (top-to-bottom), LTR (left-to-right)",
    "zefat": { "x": 463, "y": 267, "layout": "RTL" },
    "nazareth": { "x": 552, "y": 428, "layout": "RTL" },
    "qazrin": { "x": 809, "y": 418, "layout": "TTB" },
    "tiberias": { "x": 716, "y": 579, "layout": "RTL" },
    "haifa": { "x": 287, "y": 472, "layout": "RTL" },
    "afula": { "x": 552, "y": 537, "layout": "TTB" },
    "tel_aviv": { "x": 227, "y": 669, "layout": "RTL" },
    "lod": { "x": 465, "y": 705, "layout": "TTB" },
    "bet_shean": { "x": 702, "y": 738, "layout": "TTB" },
    "ashdod": { "x": 203, "y": 815, "layout": "RTL" },
    "jerusalem": { "x": 456, "y": 871, "layout": "RTL" },
    "ein_gedi": { "x": 699, "y": 950, "layout": "LTR" },
    "beer_sheva": { "x": 428, "y": 986, "layout": "TTB" },
    "mizpe_ramon": { "x": 393, "y": 1229, "layout": "TTB" },
    "eilat": { "x": 443, "y": 1508, "layout": "TTB" }
  },

  "icon_sizes": {
    "weather_icon": 50
  },

  "description_text": {
    "_comment": "Position and dimensions of the weather description text block",
    "left": 851,
    "top": 986,
    "width": 239,
    "transform": "translate-x-[-100%]"
  }
}
```

> **Note:** All values have been validated and extracted from the actual Figma design using Figma MCP on 2025-12-22. The design features a vibrant yellow-to-blue gradient background, with city data positioned on an Israel map overlay. Each city has a specific layout type (RTL, TTB, or LTR) that determines how the weather icon and text are arranged.

### Cities Configuration (`config/cities.json`)

Maps IMS city IDs to internal identifiers and display settings:

```json
{
  "cities": {
    "520": {
      "id": "520",
      "internal_key": "eilat",
      "name_hebrew": "אילת",
      "name_english": "Eilat",
      "display_priority": 1
    },
    "510": {
      "id": "510",
      "internal_key": "jerusalem",
      "name_hebrew": "ירושלים",
      "name_english": "Jerusalem",
      "display_priority": 2
    }
  }
}
```

---

## Testing Strategy

### What Are Unit Tests?

Unit tests are small programs that automatically verify your code works correctly. They act as a safety net — if you (or AI) accidentally break something, tests will fail immediately and tell you exactly what went wrong.

### Why Tests Help a "Vibe Coder"

| Benefit | How It Helps |
|---------|-------------|
| **Catch breaks early** | Tests fail immediately when something breaks, before you notice visual bugs |
| **Confident experimentation** | Try changes freely knowing tests will catch mistakes |
| **Living documentation** | Tests show exactly how each function should work |
| **Less debugging** | Instead of "why is the image wrong?", you'll know which specific part failed |

### Test Examples

```python
# test_parser.py

def test_parse_city_temperature():
    """
    Verify we correctly extract max/min temperatures from XML.
    """
    sample_xml = """
    <TimeUnitData>
        <Date>2024-12-18</Date>
        <Element>
            <ElementName>Maximum temperature</ElementName>
            <ElementValue>18</ElementValue>
        </Element>
        <Element>
            <ElementName>Minimum temperature</ElementName>
            <ElementValue>8</ElementValue>
        </Element>
    </TimeUnitData>
    """
    
    result = parse_city_forecast(sample_xml)
    
    assert result.max_temp == 18
    assert result.min_temp == 8


def test_weather_code_mapping():
    """
    Verify weather codes map to correct Hebrew descriptions.
    """
    assert get_weather_description("1250") == "בהיר"
    assert get_weather_description("1140") == "גשם"
    assert get_weather_description("1530") == "מעונן חלקית, אפשרות לגשם"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests and see which lines of code were executed
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Implementation Phases

### Phase 1: Project Foundation ⏱️ ~2 hours

**Goal:** Set up the project structure and configuration

- [x] Create folder structure as defined above
- [x] Initialize `requirements.txt` with dependencies
- [x] Set up basic logging (`src/utils/logger.py`)
- [x] Create placeholder `design_tokens.json` (to be filled by Figma MCP agent)
- [x] Update `.gitignore` with new folders
- [ ] Create `README.md` with quick start instructions

### Phase 2: Data Pipeline ⏱️ ~3 hours

**Goal:** Fetch, parse, and archive XML data

- [ ] Implement XML fetcher with proper UTF-8 encoding
- [ ] Create data models (`CityForecast`, `CountryForecast`, `DailyForecast`)
- [ ] Build XML parser with error handling
- [ ] Implement archive system (save, retrieve fallback, cleanup)
- [ ] Write tests for parser

### Phase 3: Design System ⏱️ ~2 hours

**Goal:** Load design tokens and map weather codes to assets

- [ ] Implement design token loader
- [ ] Create weather code → icon mapper
- [ ] Implement weather code → description mapper
- [ ] Add Hebrew date conversion utilities
- [ ] Write tests for mappings

### Phase 4: Image Rendering ⏱️ ~5 hours

**Goal:** Generate the Instagram Story image

- [ ] Create base renderer abstract class
- [ ] Implement Hebrew text rendering with RTL support
- [ ] Build Instagram Story renderer:
  - [ ] Background and map layer
  - [ ] Header component (both dates)
  - [ ] City forecast components (all 15 cities)
  - [ ] Footer component (logos)
- [ ] Implement dual-format file saver (JPEG + PNG)
- [ ] Write visual comparison tests

### Phase 5: Email Delivery ⏱️ ~1 hour

**Goal:** Send generated images via email

- [ ] Implement SMTP email sender
- [ ] Add attachment handling for JPEG
- [ ] Test with personal email before IMS team

### Phase 6: GitHub Actions ⏱️ ~2 hours

**Goal:** Automate daily execution

- [ ] Create workflow YAML file
- [ ] Configure secrets (email credentials)
- [ ] Set up scheduled trigger (6:00 AM Israel time)
- [ ] Test workflow execution
- [ ] Configure dual-remote deployment (personal + IMS account)

### Phase 7: Documentation & Polish ⏱️ ~2 hours

**Goal:** Finalize for "production"

- [ ] Complete `README.md` with full documentation
- [ ] Create initial `CHANGELOG.md` entry
- [ ] Review all code comments for clarity
- [ ] Final testing of complete workflow

---

## Future Extensibility

The modular architecture makes it easy to extend the system:

### Adding New Image Layouts

1. Create new layout config: `config/layout_twitter_banner.json`
2. Create new renderer: `src/rendering/twitter_banner.py`
3. Register in main: `LAYOUTS["twitter_banner"] = TwitterBannerRenderer`
4. Run with: `python -m src.main --layout twitter_banner`

### Adding New Data Sources

```python
# src/data/marine_forecast.py
def fetch_marine_forecast() -> MarineForecast:
    """Fetch marine weather for coastal cities."""
    pass

# src/data/uv_index.py  
def fetch_uv_index() -> UVIndexData:
    """Fetch UV index data for outdoor activity warnings."""
    pass
```

### Adding New Delivery Methods

```python
# src/delivery/twitter.py
def post_to_twitter(image_path: str) -> str:
    """Post image directly to Twitter/X. Returns tweet URL."""
    pass

# src/delivery/google_drive.py
def upload_to_drive(image_path: str) -> str:
    """Upload to shared Google Drive folder. Returns share link."""
    pass
```

---

## Appendix: Hebrew Text Handling

Hebrew text requires special handling because:

1. **Right-to-left (RTL)** — Text reads from right to left
2. **Character shaping** — Some letters change appearance based on position
3. **BiDi mixing** — Numbers and English text within Hebrew need proper ordering

### Solution: BiDi + Reshaper

```python
from bidi.algorithm import get_display
import arabic_reshaper
from PIL import ImageDraw, ImageFont

def draw_hebrew_text(draw: ImageDraw, text: str, position: tuple, font: ImageFont, fill: str):
    """
    Draw Hebrew text with proper RTL rendering.
    
    This function:
    1. Reshapes characters for correct display
    2. Applies BiDi algorithm for proper ordering
    3. Draws the text at the specified position
    """
    # Step 1: Reshape Hebrew/Arabic characters
    reshaped = arabic_reshaper.reshape(text)
    
    # Step 2: Apply BiDi algorithm for display order
    bidi_text = get_display(reshaped)
    
    # Step 3: Draw the processed text
    draw.text(position, bidi_text, font=font, fill=fill)
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-18 | Initial plan created |
| 1.1 | 2025-12-22 | Updated design tokens with actual values extracted from Figma via MCP |

---

*This document serves as the foundational plan for the IMS Weather Forecast Generator project. It should be updated as the project evolves and decisions are refined.*
