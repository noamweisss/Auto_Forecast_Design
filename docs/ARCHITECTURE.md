# Architecture

The project is deliberately a small, layered Python application. Each layer
has one job, so it is easy to change the visual design without accidentally
changing data handling.

```text
main (application boundary)
  -> paths -> repository .env -> Israel clock -> logging -> validated settings
  -> data: fetch, archive, parse, validate
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
Forecast models temporarily allow optional provenance. This is a migration
bridge only: Slice 2 still needs to extract metadata, select valid archives,
populate provenance, and enforce truthful fallback behavior.

## Import safety

Library modules obtain standard Python loggers without configuring them.
`main()` explicitly loads only the repository `.env` without overriding an
existing process value, then configures console/file logging. Importing data or
delivery modules does not create `logs/`, write files, or load a `.env` from the
current working directory.

## Current boundary

Slice 1 makes time, configuration, and source vocabulary explicit without
changing fallback selection. Two audit defects remain visible as strict
temporary expected failures: F-02 chooses the first fallback date from
multi-date XML, and F-03 can silently return fewer than the configured 15
cities after invalid optional data. The renderer and end-to-end workflow remain
placeholders. Slice 2 should fix those parser contracts and populate truthful
snapshot/fallback provenance before an image pipeline is connected.
