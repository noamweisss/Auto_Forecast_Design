# Architecture

A small, layered Python application. Each layer has one job, so the visual
design can change without touching data handling.

```text
main (CLI boundary)
  -> paths -> repository .env -> Israel clock -> logging -> validated settings
  -> application: fixture/live candidates -> exact-date parse
  -> design: render-ready names, positions, and icon choices
  -> rendering: Jinja HTML/CSS + Playwright PNG screenshot
  -> delivery: atomically publish one checked PNG
```

## Paths, clock, and settings

`src/app_paths.py` is the single place that locates repository folders, keyed to
the source tree rather than the terminal's working directory. Code uses
`PATHS.config`, `PATHS.assets`, `PATHS.archive`, `PATHS.output`, `PATHS.logs`,
or `PATHS.ims_fixtures` instead of a relative `Path("...")`. Tests can still
point an individual module at a temporary folder.

`src/clock.py` provides the real `Asia/Jerusalem` clock plus a one-method
protocol for deterministic tests. Parsers never read a machine clock; callers
pass the forecast date explicitly.

`src/settings.py` reads the three committed config files once at the boundary
and validates them: the 15-city identity and display fields, the 23-code Israel
weather catalog (with safe icon filenames), the fixed 1080x1920 canvas, and
exact agreement between configured city keys and design positions. That
immutable value is passed as an ordinary argument — there is no global
singleton.

## Story design boundary

`config/design_tokens.json` holds only Figma source metadata, the canvas size,
and the 15 city positions. Each x/y is a physical coordinate from the top-left;
an `RTL` label changes text flow but never mirrors a coordinate. Gradient,
typography, spacing, and logo geometry live in the CSS, not in Python.

`config/00_ims_weather_codes.json` is the one catalog for supported codes,
descriptions, categories, and icon filenames. A few conditions reuse the least
misleading existing illustration (snow for sleet, cloud for fog/muggy, warning
for dust/sand, frost for cold) — deliberate fallbacks, not claims that custom
art exists.

`src/design/render_context.py` is a packing list checked before travel. It turns
one complete `DailyForecast` plus settings and paths into frozen, template-ready
text, numbers, tuples, and absolute `file:` URIs, validating the 15 identities,
positions, catalog descriptions/icons, SVG map, composite logos, and fonts.
Missing files and Git LFS pointer text fail here, before a browser opens. The
header keeps separate bidi-safe fields — Gregorian text like `17/11/2025` and a
Pyluach Hebrew-calendar field like `כ״ו בחשוון התשפ״ו` — while displaying the
single verified Figma line.

## Checked Story renderer

Strict Jinja inserts the render context into `forecast_story.html`; the CSS
arranges it on one literal 1080x1920 canvas. This is a *checked* screenshot, not
an unchecked print: collectors are active before navigation, both fonts and
every image must decode, canvas and page geometry must be exact, and Pillow
verifies the finished PNG. Each failure stage (template, temp file, browser,
page, asset, font, layout, screenshot, image format) is named. A temporary
`file:` page keeps all work local and is removed afterward.

The page is globally RTL, but Figma's x/y values are physical from the canvas
top-left, so CSS uses literal `left`/`top` with explicit flex child order for
RTL, LTR, and top-to-bottom city groups. The map wrapper describes the SVG's
inner visible path; the unmodified 555x1517 SVG viewport is offset by 10.8px.
Figma's gradient starts before the measured line, so the CSS stop is `-62.599%`
rather than a positive on-canvas stop.

## Offline visual reference

`docs/design-reference/` holds the exact 1x export of Figma node `1:2`, its
source and asset hashes, and a beginner-readable visual policy.
`tests/fixtures/render/forecast_story_reference.json` holds sanitized mock
values for the same date, text, 15 cities, temperatures, and icon — not a real
IMS forecast. Tests build that JSON into a real `DailyForecast` and
`StoryRenderContext`, so renderer work compares like with like without IMS,
Figma, or a network. The PNG is the frozen target; the HTML/CSS is the editable
source. `python -m tests.story_visual` writes an ignored render, overlay,
amplified difference, and JSON metrics under `test-results/story-visual/` to
help a human find discrepancies — no similarity number replaces the normal-size
visual gate.

## Snapshots and provenance

`src/data/snapshots.py` names the two feed types and three sources and defines
immutable records for source XML facts and parsed provenance. A snapshot is a
sealed, time-stamped copy of one feed; its factory verifies the feed root, IMS
issue time, every advertised forecast date, and the aware fetch time before
assigning a deterministic ID.

`src/data/fetcher.py` returns decoded XML or a structured failure; injected HTTP
and sleep functions exercise retries, encoding, and failure reasons offline.

`src/data/archive.py` stores each validated snapshot as its own atomic UTF-8
JSON envelope. Lookup uses the stored feed, fetch time, and exact forecast-date
set, so filenames never decide usefulness; legacy date-named XML is ignored for
lacking trustworthy metadata.

`src/data/parser.py` accepts preferred-first snapshot sequences, ignores
wrong-feed or wrong-date snapshots, and validates publishable values: nonempty
Hebrew country text; valid temperatures, a known weather code, and valid
optional humidity/wind per city. One bad city may use the next exact-date
snapshot without moving the other 14. The key rule: yesterday's download may
supply tomorrow's forecast (its source date is still tomorrow), but yesterday's
values may never be relabelled as tomorrow.

`src/data/models.py` is the final gate before rendering. Country and city
provenance is required, Hebrew country text must be nonempty, a `DailyForecast`
must hold exactly 15 unique cities, and every component date must equal the
requested date. Fallback flags are read-only properties derived from provenance.

## One source-to-PNG application

`src/application.py` is a thin coordinator. Fixture mode reads the two committed
sanitized XML samples, seals them with one fixed Israel timestamp, and never
touches HTTP or archives. Live mode finds exact-date archive candidates before
fetching each feed, saves every structurally valid response, and places a live
candidate first only when it advertises the requested date; archives follow
newest-first and may replace only unusable values for that same date. No
cleanup, email, scheduling, or nearby-date selection enters this path.

Both modes then share the same parser, context adapter, Chromium renderer, and
`save_forecast_png()` boundary. The saver validates 1080x1920 PNG bytes, writes
and fsyncs a temporary file beside the final path, and atomically replaces it, so
a same-date rerun publishes one complete `forecast_YYYY-MM-DD.png` or preserves
the previous one. `src/main.py` parses arguments before side effects, reads the
Israel clock once, and maps configuration, source, forecast, render, and output
failures to stable exit codes. IMS overwrites the same public files with morning
and evening editions; the snapshot boundary recognizes only the observed
envelopes and still requires the requested date and all 15 cities.

## Import safety

Library modules obtain standard loggers without configuring them. `main()` loads
only the repository `.env` (without overriding existing process values) and then
configures console/file logging. Importing any module does not create `logs/`,
write files, or load a `.env` from the working directory.
