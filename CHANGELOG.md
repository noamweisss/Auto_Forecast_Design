# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added sanitized, committed IMS XML fixtures, baseline asset contracts, and an offline pull-request CI workflow.
- Added strict temporary characterization tests for parser defects F-02 and F-03; the defects remain unfixed.
- Added modest Ruff and Mypy advisory configuration for Python 3.11.
- Added `src/app_paths.py`, `docs/ARCHITECTURE.md`, and configuration contract tests as the first July 2026 refactor slice.
- Added `pyproject.toml` with the default pytest command.

- Added a concise, repository-level `AGENTS.md` for local and Codex cloud work.
- Added `docs/PROJECT_STATUS.md` as the verified implementation and restart map.
- Added `scripts/setup_codex_cloud.sh` for Linux-based cloud setup.
- Added a secret-free `.env.example` for future email configuration.

### Changed

- Anchored parser, archive, output, log, token, and icon paths to the repository instead of the shell working directory.
- Corrected README claims so unfinished rendering, email, and automation are
  clearly distinguished from implemented data work.
- Hardened Git ignore rules and documented Git LFS/publication boundaries.
- Documented that the repository has no selected software license yet.
- **Architecture Shift**: Rendering approach changed from Pillow (pixel drawing) to **HTML/CSS templates + Playwright screenshots**
  - Design now lives in HTML/CSS files that mirror the Figma layout — CSS maps nearly 1:1 to Figma properties
  - Hebrew RTL handled natively by the browser (`dir="rtl"`) — removed `python-bidi` and `arabic-reshaper` dependencies
  - Added `jinja2` and `playwright` as new dependencies
  - Updated the historical agent documentation and project plan used at the time
  - Old Pillow rendering stubs replaced with new file structure (`template_renderer.py`, `templates/`)

- **Data Pipeline (Phase 2)**: Complete implementation of weather data fetching, parsing, and archiving
  - `src/data/fetcher.py`: HTTP requests with retry logic (30s/60s delays) and multi-encoding support
  - `src/data/parser.py`: XML parsing with weather code lookup and per-city fallback logic
  - `src/data/archive.py`: 7-day rolling archive with save/load/cleanup functions
  - `src/data/models.py`: Added `internal_key` and `is_fallback` fields with validation
  - `src/delivery/file_saver.py`: Dual-format output (JPEG + PNG) with 30-day cleanup

- **Test Suite**: Automated tests covering all data pipeline modules
  - `tests/test_fetcher.py`: Retry logic, timeout handling, Hebrew encoding
  - `tests/test_archive.py`: Save, fallback, cleanup functions
  - `tests/test_parser.py`: Country/city parsing, weather codes, fallback behavior
  - `tests/test_file_saver.py`: Dual format output, cleanup

- **Manual Verification Tools**: `tests/manual/` folder
  - `export_forecast_json.py`: Script to export parsed data as readable JSON

- **Documentation**: `docs/01_phase2_data_pipeline_plan.md` with approved design decisions

### Fixed

- City name spelling consistency (Eilat not Elat, Ein Gedi not En Gedi)
- XML encoding detection for IMS Hebrew content (Windows-1255 / ISO-8859-8)
- XML declaration normalization for lxml parsing
- Replaced an emoji in the placeholder entry point that crashed on some Windows
  console encodings.

---

## [0.1.0] - 2024-12-18

### Added

- Initial project scaffolding and folder structure
- Configuration files: `cities.json`, `00_ims_weather_codes.json`
- Reference XML files in `docs/internal/reference/`
- Basic logging setup in `src/utils/logger.py`
- Date utilities in `src/utils/date_utils.py`
- Placeholder files for all modules
- Project documentation: `GEMINI.md`, `CLAUDE.md`, `00_initial_plan.md`
