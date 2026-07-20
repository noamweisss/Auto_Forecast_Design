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
the Israel weather-code descriptions, and exact agreement between configured
city keys and design positions. City and daily parsing receive that immutable
value as an ordinary keyword argument. There is no global settings singleton.

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

The data layer now fetches, seals, stores, and parses exact-date snapshots into
one complete provenance-backed forecast. F-02 and F-03 are normal passing
regressions: fallback never selects another XML date, and invalid optional data
cannot produce a 14-city result. The renderer and end-to-end workflow remain
placeholders; `src/main.py` still does not run this data path.
