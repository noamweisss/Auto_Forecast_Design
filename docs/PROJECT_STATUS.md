# Project Status

Last reviewed: 2026-07-20

This page is the practical restart map for someone returning to the repository
after a long gap. It separates executable code from plans and placeholders.

## The short version

The project can turn one validated Story packing list into a checked 1080x1920
PNG. It still does not run the full path from real IMS data through rendering
and saving. That one local real-data image is the next milestone; email and
scheduled automation come later.

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
| Design assets | Validated | The complete SVG map/logos, 23 catalog-selected icons, and Black/SemiBold fonts are checked before rendering. |
| Story render context | Implemented | One frozen packing list supplies exact header text, 15 physical city positions, temperatures, icon/file URIs, and fallback state. |
| Frozen visual reference | Available | A verified 1080x1920 Figma export, sanitized matching forecast, and exact metadata/hashes provide an offline target without live Figma access. |
| HTML/CSS template | Implemented | Literal RTL HTML/CSS reproduces the frozen Story geometry with physical top-left city coordinates and committed local assets. |
| Playwright renderer | Implemented | A strict Jinja render becomes a checked 1080x1920 PNG; browser, page, asset, font, layout, screenshot, and PNG failures are actionable. |
| Image saving | Implemented | Pillow images can be saved as JPEG and PNG. |
| Email delivery | Placeholder | Configuration validation exists, but message construction and sending are stubs. |
| Main workflow | Placeholder | `python -m src.main` explains the intended flow but does not run it. |
| Automation | Partial | Pull requests run offline tests plus a real-Chromium render smoke job. No daily production workflow exists. |

## Verification snapshot

On 2026-07-20, the full suite passed 197 tests with no expected failures.
The normal passing regressions for F-02 and F-03 prove exact-date fallback and
complete 15-city output. The run used the isolated audit environment and a
writable pytest temporary directory, including 8 browser tests with installed
Chromium. The frozen reference, rendered PNG, overlay, and amplified difference
were inspected at normal size. The visual gate passed: canvas, orientation,
map, logos, city relationships, Hebrew, numeric bidi, and hierarchy had no hard
blocker. Small glyph and SVG edge differences were accepted as cross-engine
antialiasing. Reference dimensions, bytes, SHA-256, matching fixture, and local
asset hashes remain enforced offline.
The Story deliberately uses Figma's visible Hebrew label `תל אביב` for city
402. Its stable ID, `tel_aviv` internal key, English/source identity
`Tel Aviv - Yafo`, and IMS forecast data remain unchanged.

## Recommended next milestone

Produce one real-data local image before building email or scheduling:

1. Connect the existing data pipeline to the renderer for one explicit date.
2. Pass the returned PNG into the existing local image-saving boundary.
3. Run that orchestration from `python -m src.main` without email or scheduling.
4. Inspect the resulting 1080x1920 real-data image at normal size against the frozen
   reference.

This is intentionally one product milestone rather than a request to finish the
entire delivery system.

## Codex cloud readiness

The repository now keeps remote work reproducible through:

- A committed root `AGENTS.md` with exact checks and completion rules.
- `scripts/setup_codex_cloud.sh` for Python dependencies and Chromium.
- `.env.example` with names only and no credentials.
- Git LFS rules plus setup/CI hydration checks for fonts and binary design
  assets.
- A pull-request render-smoke job that installs Chromium and cannot silently
  skip browser-marked renderer tests.
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
The design boundary now also produces one validated Story render context. It
uses the verified 1080x1920 canvas, keeps all city x/y coordinates physical
from the top-left (never RTL-mirrored), formats the exact Hebrew-calendar
header, and refuses missing or unhydrated local assets before a browser opens.
The repository now also carries the exact Figma node `1:2` export and matching
sanitized mock forecast as an offline visual oracle. The checked renderer uses
that context to produce deterministic PNG bytes and refuses incomplete browser
state, assets, fonts, or geometry. This makes layout work reproducible without
claiming that the mock values are a real IMS forecast. The remaining boundary
is application orchestration. See [Architecture](ARCHITECTURE.md).

## Source-of-truth order

When files disagree, use this order:

1. Current source code and tests.
2. `AGENTS.md` and this page.
3. `README.md`.
4. Historical plans and changelog entries.

Update this page whenever a layer changes between implemented, partial, and
placeholder.
