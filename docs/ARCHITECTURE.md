# Architecture

The project is deliberately a small, layered Python application. Each layer
has one job, so it is easy to change the visual design without accidentally
changing data handling.

```text
main (future CLI)
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

## Current boundary

Slice 0 establishes safe shared paths, sanitized production-shaped IMS fixtures,
configuration and asset contracts, and offline PR CI. Its parser contracts keep
two audit defects visible as strict temporary expected failures: F-02 chooses
the first fallback date from multi-date XML, and F-03 can silently return fewer
than the configured 15 cities after invalid optional data. The parser and
renderer are still separate, and the renderer/main workflow remain placeholders.
The next data slice should fix those parser contracts and make snapshot and
fallback provenance explicit before connecting an image pipeline.
