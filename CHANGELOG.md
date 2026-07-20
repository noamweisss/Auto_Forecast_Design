# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added structured IMS fetch results with explicit retryable failure kinds, exact attempt counts, and offline-injected request/sleep boundaries.
- Added validated snapshot construction from IMS issue time, forecast dates, feed identity, fetch time, and a deterministic content-based ID.
- Added an atomic UTF-8 JSON snapshot store with metadata-based seven-day lookup and cleanup.
- Added an Israel-aware application clock and a small snapshot/provenance vocabulary for later fallback work.
- Added one validated, immutable settings load for cities, Israel weather codes, and design tokens, including cross-file city-position checks.
- Added import-safety and outside-repository subprocess coverage, plus `tzdata` for reliable `Asia/Jerusalem` support on Windows and minimal environments.
- Added sanitized, committed IMS XML fixtures, baseline asset contracts, and an offline pull-request CI workflow.
- Added normal regression coverage for exact-date fallback (F-02) and complete 15-city output after invalid optional data (F-03).
- Added modest Ruff and Mypy advisory configuration for Python 3.11.
- Added `src/app_paths.py`, `docs/ARCHITECTURE.md`, and configuration contract tests as the first July 2026 refactor slice.
- Added `pyproject.toml` with the default pytest command.

- Added a concise, repository-level `AGENTS.md` for local and Codex cloud work.
- Added `docs/PROJECT_STATUS.md` as the verified implementation and restart map.
- Added `scripts/setup_codex_cloud.sh` for Linux-based cloud setup.
- Added a secret-free `.env.example` for future email configuration.

### Changed

- Replaced date-named XML archive behavior with sealed snapshot records; legacy `.xml` archives are deliberately ignored rather than assigned invented metadata.
- Archive lookup now requires the requested forecast date inside validated snapshot metadata and returns newest matching records as archive sources.
- Replaced loose-XML parser inputs with preferred-first validated snapshot sequences and exact-date selection.
- Logging and `.env` loading now happen explicitly in `main()`; importing library modules no longer creates log files or loads environment files.
- Made country/city provenance required, and derive fallback state from the recorded source selection instead of a separate mutable flag.
- Updated the manual JSON exporter to use structured fetching, snapshot construction/storage, exact-date parsing, and per-value provenance.
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

- Fixed F-02: an older snapshot may supply values only for the exact requested date; another day's values are never relabelled.
- Fixed F-03: invalid city data now falls back per city or raises one actionable error instead of returning fewer than 15 configured cities.
- Reject missing/duplicate configured cities, invalid temperatures, unknown weather codes, malformed humidity/wind, and missing Hebrew country text.
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
