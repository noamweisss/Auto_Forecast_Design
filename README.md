# IMS Auto Forecast Design

An automated system to generate and deliver daily weather forecast images for the Israel Meteorological Service (IMS) media team.

![Project Status](https://img.shields.io/badge/Status-Early_Development-orange)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## About This Project

**Created by Noam Weiss, IMS Media Team.**

This project was born out of a need to automate the manual daily task of creating designed weather maps for our social media channels. However, it serves a dual purpose: it is also a personal learning journey.

I am a designer by trade, not a professional developer. My background is in visual design and web concepts (HTML/CSS), and I approach this project with a "Design-First" mindset—thinking in terms of Figma frames, auto-layouts, and components.

**Built with AI Agents**
This software is being built in collaboration with AI agents (Claude Code & Gemini CLI). Unlike my previous attempts where I let AI generate code blindly, this project is built on a strict philosophy: **"Clarity over Cleverness."** 
*   I use AI to help bridge the gap between design concepts and Python logic.
*   I review and understand every line of code to ensure I can debug and maintain it myself.
*   We prioritize strict documentation and professional engineering standards to ensure the system is robust and educational.

## Overview

The system runs automatically every morning via GitHub Actions to:
1.  **Fetch** official weather forecast XML data from IMS servers.
2.  **Render** a high-quality, branded weather map image (1080x1920 for Instagram Stories) using an HTML/CSS template (mirroring the Figma design) and Playwright for screenshot capture.
3.  **Deliver** the generated image via email to the media team for distribution.

## Key Features

*   **Automated Data Fetching**: Retrieves `isr_country.xml` and `isr_cities.xml` from IMS.
*   **Design-First Rendering**: Design lives in an HTML/CSS template that mirrors the Figma design system. Jinja2 injects forecast data, Playwright screenshots the result.
*   **Hebrew Support**: Full RTL support handled natively by the browser via `dir="rtl"` — no manual BiDi libraries needed.
*   **Resilience**: 7-day local archive of XML data for fallback if fetching fails.
*   **Email Delivery**: SMTP integration to send results directly to the media team.

## Tech Stack

*   **Language**: Python 3.11+
*   **Core Libraries**:
    *   `Jinja2`: HTML template engine for injecting forecast data.
    *   `Playwright`: Headless browser for HTML → image screenshots.
    *   `Pillow`: Image format conversion (JPEG/PNG saving).
    *   `lxml`: XML parsing.
    *   `requests`: HTTP data fetching.
*   **Automation**: GitHub Actions (Daily Cron).

## Getting Started

### Prerequisites

*   Python 3.11 or higher installed.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/noamweiss/Auto_Forecast_Design.git
    cd Auto_Forecast_Design
    ```

2.  **Set up a virtual environment**:
    ```bash
    python -m venv venv
    
    # Windows
    .\venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright's browser** (one-time setup):
    ```bash
    playwright install chromium
    ```

5.  **Configuration**:
    *   Ensure `config/design_tokens.json` exists (contains Figma design values).
    *   Create a `.env` file for secrets like email credentials.

### Usage

To run the full forecast generation pipeline:

```bash
python -m src.main
```

By default, this will:
1. Fetch the latest data.
2. Generate the image.
3. Save it to the `output/` directory.
4. (Optionally) Send the email if configured.

### Running Tests

The project uses `pytest` for testing.

```bash
python -m pytest tests/
```

To run with coverage:

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Documentation

*   [**Initial Project Plan**](docs/00_initial_plan.md): Comprehensive architecture and detailed goals.
*   [**Folder Structure**](docs/01_folder_structure.md): Detailed map of the project layout.
*   [**CLAUDE.md**](CLAUDE.md): AI Assistant context and development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
