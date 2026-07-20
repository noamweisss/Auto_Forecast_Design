# Architecture

The project is deliberately a small, layered Python application. Each layer
has one job, so it is easy to change the visual design without accidentally
changing data handling.

```text
main (application boundary)
  -> paths -> repository .env -> Israel clock -> logging -> validated settings
  -> data: structured fetch -> validated snapshot -> atomic store -> parse
  -> design: render-ready names, positions, and icon choices
  -> rendering: Jinja HTML/CSS + Playwright PNG screenshot
  -> delivery: save the finished image
```

## Shared project paths

`src/app_paths.py` is the one place that locates repository-owned folders. Its
paths are based on the source file's location rather than the terminal's current
working directory. Code should use `PATHS.config`, `PATHS.assets`,
`PATHS.archive`, `PATHS.output`, or `PATHS.logs` instead of creating a relative
`Path("...")` at module level.

This is analogous to a Figma file's shared styles: a single named source avoids
one screen quietly using a different value because it was opened from another
folder. Tests can still replace an individual module's directory constant when
they need an isolated temporary folder.

## Clock and settings

`src/clock.py` provides the real `Asia/Jerusalem` clock and a one-method
protocol for deterministic application tests. Parsers do not read a machine
clock: callers pass the forecast date explicitly.

`src/settings.py` reads the three committed configuration files once at the
application boundary. It validates the 15-city identity and display fields,
the 23-code Israel weather catalog (including safe icon filenames), the fixed
1080x1920 canvas, and exact agreement between configured city keys and physical
design positions. City and daily parsing receive that immutable value as an
ordinary keyword argument. There is no global settings singleton.

## Story design boundary

`config/design_tokens.json` intentionally contains only Figma source metadata,
the fixed canvas size, and the 15 city positions. Each x/y value is a physical
coordinate measured from the top-left of the Story. An `RTL` label changes text
flow later; it never mirrors that coordinate. Gradient, typography, spacing,
and logo geometry belong directly in the CSS, not in a Python token
service.

`config/00_ims_weather_codes.json` is the one catalog for supported Israel
codes, descriptions, categories, and icon filenames. A few conditions reuse
the least misleading existing illustration: snow for sleet, cloud for fog and
muggy conditions, warning for dust/sand, and frost for cold/extreme cold. These
are deliberate fallbacks, not claims that custom illustrations exist.

`src/design/render_context.py` is like a packing list checked before travel. It
turns one complete `DailyForecast` plus explicit settings and paths into frozen
template-ready text, numbers, tuples, and absolute `file:` URIs. It validates
the 15 identities, physical positions, catalog descriptions/icons, SVG map and
composite logos, and the Black/SemiBold fonts. The IMS SVG already contains its
Hebrew label; no ExtraCondensed font or replacement label is invented. Missing
files and Git LFS pointer text fail here, before a browser opens.

The header retains separate bidi-safe fields: numeric Gregorian text such as
`17/11/2025` and a Pyluach-derived Hebrew-calendar field such as
`כ״ו בחשוון התשפ״ו`. The template isolates those runs while displaying the single
verified Figma line.

## Checked Story renderer

The render context is a packing list: it contains only validated text,
coordinates, and absolute local asset addresses. Strict Jinja inserts that list
into `forecast_story.html`, while the included CSS arranges it on one literal
1080x1920 canvas. Chromium paints only that canvas, and `TemplateRenderer`
returns the resulting PNG bytes.

This is a checked browser screenshot rather than an unchecked print command.
Collectors are active before navigation; both committed fonts and every image
must decode; the canvas and page geometry must be exact; and Pillow verifies the
finished PNG. Template, temporary-file, browser, page, asset, font, layout,
screenshot, and image-format failures identify their stage. A temporary `file:`
page keeps all work local and is removed after success or failure.

The page is globally RTL, but Figma's city, map, description, and logo x/y
values are physical coordinates from the canvas top-left. CSS therefore uses
literal `left` and `top` for those elements and explicit flex child order for
RTL, LTR, and top-to-bottom city groups. The map wrapper describes the SVG's
inner visible path; the unmodified 555x1517 SVG viewport is offset by 10.8px.
Figma's gradient start lies before the measured gradient line, so the equivalent
CSS stop is `-62.599%` rather than a positive on-canvas stop.

## Offline visual reference

`docs/design-reference/` contains the exact 1x export of Figma node `1:2`, its
source and asset hashes, and a beginner-readable visual policy. The matching
`tests/fixtures/render/forecast_story_reference.json` contains sanitized mock
values for the same date, text, 15 cities, temperature ranges, and weather icon.
It is deliberately not described as a real IMS forecast.

Tests can build that JSON into the real `DailyForecast` and
`StoryRenderContext`, so renderer work can compare like with like without IMS,
Figma, credentials, or another network service. The PNG is the frozen target
appearance; HTML/CSS is the editable implementation source.

The automated contracts guard exact bytes, dimensions, provenance metadata,
fixture content, and hydrated asset hashes. They do not replace human visual
review. After renderer changes, the actual 1080x1920 output must still be
opened at normal size and compared with the reference.

`python -m tests.story_visual` writes one ignored render, 50/50 overlay,
amplified pixel difference, and JSON metrics under `test-results/story-visual/`.
Those files help a human find discrepancies; no similarity number replaces the
normal-size visual gate.

## Snapshots and provenance

`src/data/snapshots.py` names the two feed types and three possible sources, and
defines immutable records for source XML facts and parsed forecast provenance.
A snapshot is a sealed, time-stamped copy of one IMS feed. Its factory verifies
the expected feed root, the IMS issue time, every advertised forecast date, and
the aware fetch time before assigning a deterministic ID.

`src/data/fetcher.py` returns either decoded XML or a structured failure. Tests
inject the HTTP and sleep functions, so retries, encoding, and failure reasons
are exercised without network calls or real waiting.

`src/data/archive.py` stores each validated snapshot as its own UTF-8 JSON
envelope and publishes it atomically. Lookup uses the stored feed, fetch time,
and exact forecast-date set; filenames do not decide whether a record is useful.
Legacy date-named XML files are ignored because they lack trustworthy issue and
fetch metadata.

`src/data/parser.py` accepts preferred-first snapshot sequences. It ignores
wrong-feed snapshots and snapshots without the requested date, then validates
publishable values. Country text must include a nonempty Hebrew description.
Every configured city must have valid temperatures and a known weather code;
present humidity and wind values must also be valid. One bad city may use the
next exact-date snapshot without moving the other 14 cities to that source.

This distinction matters: an XML file downloaded yesterday can contain a
forecast for tomorrow. Using tomorrow's entry from that older download is safe
because its source date remains tomorrow. Taking yesterday's values and merely
labelling them as tomorrow is prohibited.

`src/data/models.py` is the final data gate before future rendering. Country and
city provenance is required. A `DailyForecast` must contain exactly 15 unique
cities, and every component date must equal the requested date. Fallback flags
are read-only properties derived from provenance, so a value cannot claim to be
live while its recorded source says otherwise.

## Import safety

Library modules obtain standard Python loggers without configuring them.
`main()` explicitly loads only the repository `.env` without overriding an
existing process value, then configures console/file logging. Importing data or
delivery modules does not create `logs/`, write files, or load a `.env` from the
current working directory.

## Current boundary

The data layer fetches, seals, stores, and parses exact-date snapshots into one
complete provenance-backed forecast. The design layer validates and packs that
forecast; the HTML/CSS and checked Chromium renderer produce PNG bytes; and the
frozen offline package provides the exact visual target and matching mock
context. The end-to-end application workflow remains unfinished: `src/main.py`
still does not connect data, rendering, and saving.
