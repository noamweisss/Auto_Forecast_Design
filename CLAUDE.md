# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated daily weather forecast image generator for the Israel Meteorological Service (IMS) Media Team. The system fetches forecast data from IMS XML sources, generates designed images (starting with 1080x1920 Instagram Story format), and emails them to the media team for social media distribution.

**Developer Context:** The primary developer is a designer with web development background (HTML/CSS/JavaScript), not a professional programmer. Code must be clear, well-documented, and debuggable by someone learning to code.

**Current Status:** Project structure and planning complete. Module scaffolding in place with placeholder implementations. Ready for incremental feature development.

## Data Sources

### IMS Weather Forecast XML Files

Both XML files contain Hebrew text - encoding handling is critical:

- **Country forecast:** https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml
- **Cities forecast:** https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml

### Weather Code Reference

Weather condition codes and their Hebrew/English translations are documented in `config/00_ims_weather_codes.json`. This file includes:
- Israel-specific forecast codes (23 codes)
- Worldwide forecast codes (31 codes)
- Wind direction mappings
- Categories: severe weather, precipitation, clouds, clear, visibility, wind, temperature, conditions

## Design System

The layout design is in Figma using Auto-layout Frames and Multi-State Components. Access via Figma MCP:
- **Figma URL:** https://www.figma.com/design/YVPUc24KCJIFrHpoXKrHz7/Story-Layout-V2.0?node-id=1-2&m=dev
- **Approach:** Designer thinks in DOM/CSS terms - implementations should mirror this mental model
- Use Figma MCP remote server (configured in VS Code) to accurately replicate designs

### Design Tokens

Design values extracted from Figma are stored in `config/design_tokens.json`:
- Colors (backgrounds, text, accents)
- Typography (font families, sizes, weights)
- Spacing and positions
- Component-specific styling

## Tech Stack

### Primary Language: Python 3.11+

Python provides clear, readable code that's easy to understand and debug.

### Core Dependencies

```
requests>=2.31.0        # HTTP requests for fetching XML data
Pillow>=10.0.0          # Image generation and manipulation
lxml>=4.9.0             # XML parsing with proper encoding support
python-dotenv>=1.0.0    # Environment variable management
python-bidi>=0.4.2      # BiDi algorithm for Hebrew text
arabic-reshaper>=3.0.0  # Hebrew/Arabic character shaping
pytest>=7.4.0           # Testing framework
pytest-cov>=4.1.0       # Test coverage reporting
```

See `requirements.txt` for the complete list with detailed comments.

## Project Structure

The codebase follows a modular architecture. Each module has a single responsibility:

```
src/
├── main.py                  # Entry point: python -m src.main
├── data/                    # Data fetching & processing
│   ├── fetcher.py           # Download XML from IMS
│   ├── parser.py            # Convert XML to Python objects
│   ├── models.py            # Data structures (CityForecast, etc.)
│   └── archive.py           # XML backup system
├── design/                  # Design system
│   ├── tokens.py            # Load design_tokens.json
│   └── icon_mapper.py       # Map weather codes to icons
├── rendering/               # Image generation
│   ├── base_renderer.py     # Abstract base class
│   ├── instagram_story.py   # 1080×1920 layout
│   └── text_utils.py        # Hebrew text rendering
├── delivery/                # Output & distribution
│   ├── file_saver.py        # Save images as JPEG/PNG
│   └── email_sender.py      # Send via Gmail SMTP
└── utils/                   # Shared helpers
    ├── logger.py            # Logging setup
    └── date_utils.py        # Hebrew calendar dates

config/                      # Configuration files
├── design_tokens.json       # Figma design values
├── cities.json              # City ID → name mapping
└── 00_ims_weather_codes.json # Weather code mappings

tests/                       # Automated tests
├── test_parser.py
├── test_date_utils.py
└── test_rendering.py
```

For complete structure documentation, see `docs/01_folder_structure.md`.

## Assets Structure

All design assets are in `assets/`:
- `Fonts/` - Typography assets (Noto Sans Hebrew - 9 weights)
- `Logos/` - IMS branding
- `Weather_Icons/` - Weather condition icons (16 variations)
- `Map/` - Israel map background

## Email Configuration

The system uses SMTP via Gmail for email automation. Configuration is in `.env`:
- Server: smtp.gmail.com
- Port: 587 (TLS)
- Sender account: mws430170@gmail.com
- Uses Gmail App Password (not regular password)
- Recipient: weissno@ims.gov.il

**Security:** Never commit `.env` - it's in `.gitignore`

## Deployment

**Production:** GitHub Actions for automated daily execution
- Dedicated IMS media team GitHub account exists for production deployment
- This repo should work with 2 remotes simultaneously: personal account + IMS media team account

## Development Philosophy

### Code Standards

1. **Clarity over cleverness** - Code must be understandable by a learning developer
2. **Comprehensive documentation** - Explain WHY, not just WHAT
3. **Hebrew text handling** - Always use proper encoding (UTF-8) for Hebrew content
4. **Incremental development** - Small, testable changes

### Git & Documentation Practices

Follow standards from `docs/internal/git_and_documentation_best_practices.md`:

**Commit Message Format:**
```
<type>: <description>

[optional body explaining WHY]
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
- `feat: add weather data XML parser with Hebrew encoding`
- `fix: correct temperature display rounding error`
- `docs: document Figma design system integration`

**Branching:**
- `main` - Always stable, deployable
- `feature/` - New functionality
- `fix/` - Bug fixes
- `docs/` - Documentation updates

### Architecture Approach

- **Design-first:** Layout matches Figma design system
- **Modular:** Separate data fetching, processing, rendering, and delivery
- **Extensible:** Easy to add new layout formats beyond initial Instagram Story template
- **Testable:** Components should be independently verifiable

### Documentation Requirements

- Keep `CHANGELOG.md` updated following keepachangelog.com format
- Document all design decisions
- Explain Hebrew text handling approaches
- Note any Figma-to-code translation decisions

### Key Documentation Files

- `docs/00_initial_plan.md` - Comprehensive project plan and architecture decisions
- `docs/01_folder_structure.md` - Quick reference for navigating the codebase
- `CLAUDE.md` - This file - AI assistant context and project overview

## Running the Project

### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Execution

```bash
# Run the main generator
python -m src.main

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Output

Generated images are saved to:
- `output/forecast_YYYY-MM-DD.jpg` - JPEG version
- `output/forecast_YYYY-MM-DD.png` - PNG version

XML backups are stored in:
- `archive/YYYY-MM-DD_cities.xml`
- `archive/YYYY-MM-DD_country.xml`

## Important Constraints

1. **No blind AI generation** - Developer must understand all code for debugging
2. **Hebrew encoding** - Critical for XML parsing and text rendering
3. **Clean slate** - Previous version exists but intentionally not referenced to avoid mental constraints
4. **Designer mindset** - Think in terms of DOM/CSS properties, Auto-layout, component states
