# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added real SMTP delivery in `src/delivery/email_sender.py`: validated
  environment settings, port-derived STARTTLS or implicit SSL, a UTF-8 Hebrew
  message naming the forecast date, the PNG attachment, and readable
  configuration and delivery errors.
- Added a `--email` flag to `python -m src.main` that validates credentials
  before any fetching or rendering, sends only after the PNG is published, and
  exits 8 on a delivery failure while still reporting the saved file.
- Added `.github/workflows/daily_forecast.yml`, which generates the live Story
  and emails it at 06:30 Israel time. The schedule fires at 03:30 and 04:30 UTC
  and an `Asia/Jerusalem` gate keeps only the 06:xx firing, so summer and winter
  offsets both work; manual runs skip the gate and choose source, date, and send.
- Added offline contracts for email configuration, message construction, the
  ordered SMTP conversation, failure translation, the `--email` command boundary,
  and the scheduled workflow file. No test opens a socket.
- Added an Apache License 2.0 `LICENSE` file and recorded the license in
  `README.md` and `.agents/AGENTS.md`.
- Added one thin `generate_forecast_image()` application workflow and a real
  `python -m src.main` CLI that connect exact-date source selection, parsing,
  Story context, Chromium rendering, and one local PNG.
- Added deterministic offline fixture mode from committed sanitized IMS-shaped
  XML, plus live IMS mode with per-feed archive fallback and no date shifting.
- Added a browser-marked vertical integration test from the committed XML
  fixtures through Playwright and the atomic output file.
- Added the complete RTL 1080x1920 Story HTML/CSS and a deterministic Jinja +
  Playwright renderer that returns validated PNG bytes and reports failures by
  template, browser, asset, font, layout, screenshot, or PNG stage.
- Added structural and real-Chromium renderer tests, including physical city,
  map, description, logo, font, image, bidi, repeatability, and failure checks.
- Added an ignored frozen-reference visual diagnostic helper that writes a
  render, 50/50 overlay, amplified difference, and metrics for human review.
- Added a pull-request `render-smoke` CI job that hydrates Git LFS assets,
  installs Chromium, and runs the browser-marked renderer tests without skips.
- Added a frozen 1080x1920 Figma Story export, its sanitized matching forecast
  fixture, exact source/asset hashes, and an offline visual-review guide.
- Added a test-only fixture builder that turns the sanitized reference JSON
  into the real `DailyForecast` and Story render context without IMS or Figma.
- Added a frozen, validated Story render context with exact header fields, 15 ordered city labels, physical positions, local asset URIs, and derived fallback state.
- Added Pyluach-based Hebrew-calendar formatting for the approved `כ״ו בחשוון התשפ״ו` header text.
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

- Added short docstrings to the public data-boundary and render-context types
  (`ForecastSnapshot`, `ForecastProvenance`, `FetchFailure`, `FetchResult`,
  `StoryCity`, `StoryAssets`, `StoryRenderContext`) and the `DailyForecast`
  city lookups, so each type states its contract at the point of use.
- Added a `.coderabbit.yaml` that disables the docstring-coverage pre-merge
  check: the project documents its public surface on purpose and keeps small
  private helpers uncommented, which a blanket coverage percentage penalizes.
- Added a concise, repository-level `AGENTS.md` for local and Codex cloud work.
- Added `docs/PROJECT_STATUS.md` as the verified implementation and restart map.
- Added `scripts/setup_codex_cloud.sh` for Linux-based cloud setup.
- Added a secret-free `.env.example` for future email configuration.

### Changed

- Marked email delivery and daily automation as implemented in `README.md`,
  `docs/PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`, and `.agents/AGENTS.md`, and
  recorded the remaining manual step: add the two repository secrets, merge the
  workflow to the default branch, and confirm the first real send.
- Expanded `.env.example` with the optional `SMTP_USERNAME`, `SMTP_SECURITY`, and
  `EMAIL_SENDER_NAME` variables and a default recipient.
- Documentation hygiene pass: moved the superseded initial plans and the
  refactor audit into `docs/history/` (with a README explaining they are
  historical), moved `AGENTS.md` to `.agents/AGENTS.md` as the single source of
  truth for agent guidance, and refreshed stale docstrings/comments in
  `email_sender.py`, `tests/__init__.py`, and `requirements.txt`.
- Accepted the observed official IMS morning and evening feed envelopes through
  strict product-shape checks while keeping exact-date and 15-city publication
  requirements unchanged.
- Replaced the old global Pillow/JPEG/PNG saver helpers with one canonical
  `save_forecast_png()` boundary that validates and atomically replaces a
  hydrated 1080x1920 PNG.
- Extended the pull-request Chromium smoke job to run the full fixture-to-PNG
  application path as well as renderer tests.
- Matched city 402's Story-only Hebrew display label to Figma's visible
  `תל אביב`. Its stable ID, `tel_aviv` key, English/source identity
  `Tel Aviv - Yafo`, and IMS forecast data are unchanged.
- Hydrated and verified committed Git LFS assets in pull-request CI and Codex
  cloud setup before Python installation or offline tests.
- Consolidated all 23 supported Israel weather descriptions and icon filenames into one validated catalog, including documented deliberate icon reuse.
- Reduced structured design JSON to Figma metadata, the fixed 1080x1920 canvas, and 15 top-left physical city positions.
- Removed the duplicate icon mapping and unimplemented design-token accessor modules; future visual styling belongs in HTML/CSS.
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

- Treated an empty or whitespace-only IMS success body as a structured `DECODE`
  fetch failure instead of letting it raise an uncaught error, so the documented
  fetch contract and archive fallback still hold.
- Rejected empty Hebrew country text at the `CountryForecast` model boundary and
  rejected duplicate exact-date `TimeUnitData` in country and city parsing, so
  malformed source data fails loudly rather than silently taking the first match.
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
