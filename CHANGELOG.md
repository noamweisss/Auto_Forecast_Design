# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Data Pipeline (Phase 2)**: Complete implementation of weather data fetching, parsing, and archiving
  - `src/data/fetcher.py`: HTTP requests with retry logic (30s/60s delays) and multi-encoding support
  - `src/data/parser.py`: XML parsing with weather code lookup and per-city fallback logic
  - `src/data/archive.py`: 7-day rolling archive with save/load/cleanup functions
  - `src/data/models.py`: Added `internal_key` and `is_fallback` fields with validation
  - `src/delivery/file_saver.py`: Dual-format output (JPEG + PNG) with 30-day cleanup

- **Test Suite**: 59 automated tests covering all data pipeline modules
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
