# IMS Auto Forecast Design - GEMINI Context

## Project Overview

This project is an **automated daily weather forecast image generator** for the Israel Meteorological Service (IMS) Media Team. It fetches XML data from IMS servers, generates a stylized weather map image (currently for Instagram Stories), and emails it to the media team.

**Key Technologies:** Python 3.11+, Pillow (Image Generation), lxml (Parsing), GitHub Actions (Automation).

## Current Status

🚧 **Early Development / Scaffolding Phase**

The project structure, planning documents, and dependency lists are in place. The core logic in `src/main.py` is currently a placeholder. Implementation of the fetching, parsing, and rendering modules is the immediate next step.

## Key Documentation

*   **`docs/00_initial_plan.md`**: The comprehensive project plan. **Read this first** to understand the architecture, data flow, and specific goals.
*   **`CLAUDE.md`**: Contains critical instructions regarding design philosophy ("Clarity over cleverness"), Hebrew text handling, and the "Design-first" approach mirroring Figma.
*   **`config/design_tokens.json`**: The single source of truth for design values (colors, fonts, positions), extracted from Figma.

## Development Setup

1.  **Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    ```

2.  **Run (Current Placeholder):**
    ```bash
    python -m src.main
    ```

3.  **Run Tests:**
    ```bash
    python -m pytest tests/
    ```

## Architecture & Data Flow

1.  **Fetcher (`src/data/fetcher.py`):** Downloads `isr_country.xml` and `isr_cities.xml`.
2.  **Parser (`src/data/parser.py`):** Converts XML to Python objects (`DailyForecast`, `CityForecast`). Handles Hebrew encoding.
3.  **Renderer (`src/rendering/`):** Uses `Pillow` to draw the image.
    *   Reads layout from `config/design_tokens.json`.
    *   Handles RTL Hebrew text using `python-bidi` and `arabic-reshaper`.
4.  **Delivery (`src/delivery/`):** Saves JPEG/PNG and sends via SMTP.

## Core Conventions

*   **Design-First:** The code structure should mirror the Figma design. If a value exists in Figma (position, color, font), it belongs in `design_tokens.json`, not hardcoded in Python.
*   **Hebrew Handling:** Always ensure proper UTF-8 encoding and use the provided text utility functions for correct RTL display.
*   **Simplicity:** The primary developer is a designer learning code. Code must be readable, explicit, and well-documented. Avoid complex abstractions where simple functions suffice.
*   **Immutability:** Input data (XML) -> Pure Function (Renderer) -> Output Image.
