# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated daily weather forecast image generator for the Israel Meteorological Service (IMS) Media Team. The system fetches forecast data from IMS XML sources, generates designed images (starting with 1080x1920 Instagram Story format), and emails them to the media team for social media distribution.

**Developer Context:** The primary developer is a designer with web development background (HTML/CSS/JavaScript), not a professional programmer. Code must be clear, well-documented, and debuggable by someone learning to code.

## Data Sources

### IMS Weather Forecast XML Files

Both XML files contain Hebrew text - encoding handling is critical:

- **Country forecast:** https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml
- **Cities forecast:** https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml

### Weather Code Reference

Weather condition codes and their Hebrew/English translations are documented in `docs/00_ims_weather_codes.json`. This file includes:
- Israel-specific forecast codes (23 codes)
- Worldwide forecast codes (31 codes)
- Wind direction mappings
- Categories: severe weather, precipitation, clouds, clear, visibility, wind, temperature, conditions

## Design System

The layout design is in Figma using Auto-layout Frames and Multi-State Components. Access via Figma MCP:
- **Figma URL:** https://www.figma.com/design/YVPUc24KCJIFrHpoXKrHz7/Story-Layout-V2.0?node-id=1-2&m=dev
- **Approach:** Designer thinks in DOM/CSS terms - implementations should mirror this mental model
- Use Figma MCP remote server (configured in VS Code) to accurately replicate designs

## Assets Structure

All design assets are in `assets/`:
- `Fonts/` - Typography assets
- `Logos/` - IMS branding
- `Weather_Icons/` - Weather condition icons

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

## Important Constraints

1. **No blind AI generation** - Developer must understand all code for debugging
2. **Hebrew encoding** - Critical for XML parsing and text rendering
3. **Clean slate** - Previous version exists but intentionally not referenced to avoid mental constraints
4. **Designer mindset** - Think in terms of DOM/CSS properties, Auto-layout, component states
