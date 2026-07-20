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

These checks establish trustworthy source history only. Storing a snapshot does
not mean every country or city value is publishable. Forecast models still allow
optional provenance as a migration bridge; Slice 2B must connect selected
snapshots to parsing and enforce value/provenance truthfulness.

## Import safety

Library modules obtain standard Python loggers without configuring them.
`main()` explicitly loads only the repository `.env` without overriding an
existing process value, then configures console/file logging. Importing data or
delivery modules does not create `logs/`, write files, or load a `.env` from the
current working directory.

## Current boundary

Slice 2A validates acquisition and snapshot storage without changing parser
fallback or value behavior. Two audit defects remain visible as strict
temporary expected failures: F-02 chooses the first fallback date from
multi-date XML, and F-03 can silently return fewer than the configured 15
cities after invalid optional data. The renderer and end-to-end workflow remain
placeholders. Slice 2B should fix those parser contracts, consume validated
snapshot candidates, and populate truthful fallback provenance before an image
pipeline is connected.
