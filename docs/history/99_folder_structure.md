# Project Folder Structure

This document explains the organization of the IMS Weather Forecast Generator project. Use this as a quick reference to find what you're looking for.

---

## Quick Reference

| Folder | Purpose |
|--------|---------|
| `src/` | All Python source code |
| `config/` | Configuration files (JSON) |
| `assets/` | Static files (fonts, icons, logos) |
| `tests/` | Automated tests |
| `docs/` | Documentation |
| `output/` | Generated images (gitignored) |
| `archive/` | XML backups (gitignored) |

---

## Complete Structure

```
Auto_Forecast_Design/
│
├── 📄 CLAUDE.md                    # AI assistant context and project overview
├── 📄 CHANGELOG.md                 # Version history (to be created)
├── 📄 README.md                    # Project overview (to be created)
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env                         # Email credentials (gitignored - NEVER COMMIT)
├── 📄 .gitignore                   # Files to exclude from git
│
├── 📁 src/                         # ═══ SOURCE CODE ═══
│   ├── 📄 __init__.py              # Package marker
│   ├── 📄 main.py                  # Entry point - run with: python -m src.main
│   │
│   ├── 📁 data/                    # Data fetching & processing
│   │   ├── 📄 fetcher.py           # Download XML from IMS website
│   │   ├── 📄 parser.py            # Convert XML to Python objects
│   │   ├── 📄 models.py            # Data structures (CityForecast, etc.)
│   │   └── 📄 archive.py           # XML backup and fallback system
│   │
│   ├── 📁 design/                  # Design system
│   │   ├── 📄 tokens.py            # Load colors, fonts, positions from JSON
│   │   └── 📄 icon_mapper.py       # Map weather codes to icon files
│   │
│   ├── 📁 rendering/               # Image generation
│   │   ├── 📄 base_renderer.py     # Abstract base class (template)
│   │   ├── 📄 instagram_story.py   # 1080×1920 Instagram Story layout
│   │   ├── 📄 text_utils.py        # Hebrew text rendering helpers
│   │   └── 📁 components/          # Reusable visual components (future)
│   │
│   ├── 📁 delivery/                # Output & distribution
│   │   ├── 📄 file_saver.py        # Save images as JPEG + PNG
│   │   └── 📄 email_sender.py      # Send via Gmail SMTP
│   │
│   └── 📁 utils/                   # Shared helpers
│       ├── 📄 logger.py            # Logging setup
│       └── 📄 date_utils.py        # Hebrew + Georgian dates
│
├── 📁 config/                      # ═══ CONFIGURATION ═══
│   ├── 📄 design_tokens.json       # Figma-extracted: colors, fonts, positions
│   ├── 📄 cities.json              # City ID mapping and names
│   └── 📄 weather_codes.json       # Weather code → description mapping
│
├── 📁 assets/                      # ═══ STATIC ASSETS ═══
│   ├── 📁 Fonts/                   # Noto Sans Hebrew (9 weights)
│   ├── 📁 Logos/                   # IMS and MOT logos
│   ├── 📁 Weather_Icons/           # 16 weather condition icons
│   └── 📁 Map/                     # Israel map background
│
├── 📁 docs/                        # ═══ DOCUMENTATION ═══
│   ├── 📄 00_initial_plan.md       # Comprehensive project plan
│   ├── 📄 01_folder_structure.md   # This file
│   └── 📁 internal/                # Internal dev docs (gitignored)
│
├── 📁 tests/                       # ═══ AUTOMATED TESTS ═══
│   ├── 📄 test_parser.py           # Test XML parsing
│   ├── 📄 test_date_utils.py       # Test date formatting
│   └── 📄 test_rendering.py        # Test image generation
│
├── 📁 output/                      # ═══ GENERATED IMAGES ═══ (gitignored)
│   └── forecast_YYYY-MM-DD.jpg/png
│
├── 📁 archive/                     # ═══ XML BACKUPS ═══ (gitignored)
│   └── YYYY-MM-DD_cities/country.xml
│
└── 📁 .github/                     # ═══ GITHUB CONFIGURATION ═══
    └── 📁 workflows/
        └── 📄 daily_forecast.yml   # Scheduled daily execution at 6:00 AM
```

---

## Module Purposes

### `src/data/` — Data Pipeline

Handles everything related to getting and parsing weather data:

- **fetcher.py**: HTTP requests to IMS XML feeds
- **parser.py**: XML → Python objects conversion
- **models.py**: Dataclasses defining data shapes
- **archive.py**: 7-day backup system for fallback

### `src/design/` — Design System

Manages the visual design configuration:

- **tokens.py**: Loads values from `design_tokens.json`
- **icon_mapper.py**: Maps weather codes (1250) → icons (clear.png)

### `src/rendering/` — Image Generation

Creates the actual forecast images:

- **base_renderer.py**: Template that all layouts follow
- **instagram_story.py**: The 1080×1920 layout implementation
- **text_utils.py**: Hebrew RTL text handling

### `src/delivery/` — Distribution

Handles output and sending:

- **file_saver.py**: Saves both JPEG and PNG
- **email_sender.py**: SMTP email with attachment

### `src/utils/` — Shared Utilities

Helper functions used across modules:

- **logger.py**: Consistent logging format
- **date_utils.py**: Hebrew calendar conversion

---

## Config Files

| File | Purpose | Updated By |
|------|---------|------------|
| `design_tokens.json` | Colors, fonts, positions | Figma MCP extraction |
| `cities.json` | City ID → name mapping | Manual (rarely changes) |
| `weather_codes.json` | Code → description | Manual (from IMS docs) |

---

## Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the generator (placeholder mode)
python -m src.main

# 3. Run tests
python -m pytest tests/ -v
```

---

## Notes for Future Developers

1. **Adding a new layout**: Create a new file in `src/rendering/` that extends `BaseRenderer`
2. **Adding a delivery method**: Create a new file in `src/delivery/`
3. **Changing design**: Update `config/design_tokens.json` — no code changes needed
4. **Adding cities**: Update both `config/cities.json` and `design_tokens.json`

For full documentation, see [00_initial_plan.md](./00_initial_plan.md).
