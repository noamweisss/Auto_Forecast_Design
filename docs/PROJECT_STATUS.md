# Project Status

Last reviewed: 2026-07-20

This page is the practical restart map for someone returning to the repository
after a long gap. It separates executable code from plans and placeholders.

## The short version

The project has a useful data foundation, but it does not yet generate a
forecast image. The next milestone is one correct local 1080x1920 image made
from real IMS data. Email and scheduled automation come later.

## Layer-by-layer state

| Layer | State | What that means |
| --- | --- | --- |
| Shared paths | Implemented | `src/app_paths.py` anchors repository paths so commands do not depend on the shell directory. |
| Clock and settings boundary | Implemented | `main()` establishes paths, local `.env`, Israel time, logging, and one validated immutable settings load in that order. |
| Data models | Implemented | Every country/city value has required source provenance; a daily forecast is rejected unless it has one date and 15 unique cities. |
| IMS fetching | Implemented | Country and city acquisition returns either decoded XML or a structured failure with its exact attempt count. |
| XML parsing | Implemented | Ordered snapshots are resolved for one exact date. Each city may independently fall back, but incomplete or invalid data fails the whole forecast. |
| Validated snapshots | Implemented | IMS XML can be sealed with its real issue time, fetch time, feed, and complete forecast-date set. This proves source structure, not publishability. |
| Snapshot store | Implemented | Valid snapshots are atomically stored as UTF-8 JSON and selected by metadata within an explicit seven-day window. |
| Design assets | Available | Figma-derived tokens, fonts, icons, logos, and map assets are committed. |
| Design helpers | Partial | `src/design/tokens.py` and icon descriptions still contain stubs. |
| HTML/CSS template | Placeholder | The 1080x1920 canvas exists, but it contains placeholder text rather than the design. |
| Playwright renderer | Placeholder | `TemplateRenderer.render()` raises `NotImplementedError`. |
| Image saving | Implemented | Pillow images can be saved as JPEG and PNG. |
| Email delivery | Placeholder | Configuration validation exists, but message construction and sending are stubs. |
| Main workflow | Placeholder | `python -m src.main` explains the intended flow but does not run it. |
| Automation | Not started | `.github/workflows/` contains no production workflow. |

## Verification snapshot

On 2026-07-20, the offline suite passed 140 tests with no expected failures.
The normal passing regressions for F-02 and F-03 prove exact-date fallback and
complete 15-city output. The run used the isolated audit environment and a
writable pytest temporary directory. Rendering output was not inspected because
this slice does not implement or change rendering.

## Recommended next milestone

Produce one real local image before building email or scheduling:

1. Implement and test the design-token accessors.
2. Complete weather-code-to-icon descriptions and paths.
3. Turn `forecast_story.html` and `.css` into the real RTL design using the
   committed tokens and assets.
4. Implement `TemplateRenderer.render()` with Jinja2 and Playwright.
5. Connect the existing data pipeline to the renderer for one date.
6. Inspect the resulting 1080x1920 image at normal size.

This is intentionally one product milestone rather than a request to finish the
entire delivery system.

## Codex cloud readiness

The repository now keeps remote work reproducible through:

- A committed root `AGENTS.md` with exact checks and completion rules.
- `scripts/setup_codex_cloud.sh` for Python dependencies and Chromium.
- `.env.example` with names only and no credentials.
- Git LFS rules for fonts and binary design assets.
- Ignore rules for generated forecasts, fetched XML, credentials, caches, local
  environments, private journals, and machine-specific agent files.

Cloud agents should work from committed assets and `config/design_tokens.json`.
Live Figma, Gmail, IMS network access, and local MCP servers are optional task
capabilities, not baseline assumptions.

## Refactor progress

The July 2026 refactor now has a trustworthy data boundary: structured fetch
failures, validated time-stamped IMS snapshots, atomic JSON records, exact-date
archive lookup, strict parsing, and required provenance. F-02 and F-03 are
repaired. An older *download* may safely help when its multi-day XML still
contains the exact future day requested. Values for yesterday are never renamed
as today's forecast.
Rendering is still unimplemented. See [Architecture](ARCHITECTURE.md) for the
current boundary.

## Source-of-truth order

When files disagree, use this order:

1. Current source code and tests.
2. `AGENTS.md` and this page.
3. `README.md`.
4. Historical plans and changelog entries.

Update this page whenever a layer changes between implemented, partial, and
placeholder.
