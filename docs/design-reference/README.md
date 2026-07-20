# Frozen Story design reference

This folder lets a first-time contributor understand and check the target
Instagram Story without opening Figma.

## What each file means

- `forecast-story-node-1-2.png` is the frozen target appearance exported at 1x
  from Figma node `1:2` (`Instagram Story 01`).
- `forecast-story-node-1-2.metadata.json` records the precise source, export
  dimensions and hash, matching fixture, and hashes of the local assets used by
  the Story.
- `../../tests/fixtures/render/forecast_story_reference.json` contains the
  sanitized mock date, text, temperatures, weather code, and 15 cities visible
  in that design. It is not a real IMS forecast.

The PNG is the comparison target. HTML/CSS will be the editable source of the
implementation; contributors should not try to edit the PNG itself.

This package records a visual engineering reference. It is not a statement of
legal artwork approval or asset-license provenance. The repository still has
no selected software license.

## Deliberate Tel Aviv display label

The Story follows the visible Figma label `תל אביב` for city `402`. This is a
presentation choice for the Story only. The stable city ID `402`, internal key
`tel_aviv`, English and source identity `Tel Aviv - Yafo`, and the forecast
values all keep their full meaning. The shorter label does not alter IMS source
forecast data.

## Offline rule

Ordinary development and automated tests must work without Figma. Figma is
needed only when the owner deliberately refreshes this frozen package. The
committed PNG, JSON fixture, metadata, fonts, logos, map, and weather icon are
the complete offline reference.

## What may differ

When rendering the matching reference fixture, no differences are allowed
without updating this package as an explicit design decision.

When deliberately rendering another forecast, only content may differ:

- the date and country text;
- city temperatures;
- weather conditions and their icons.

The 1080x1920 canvas, background, map and city geometry, typography, logos, and
RTL/LTR/TTB relationships remain governed by this reference.

Passing tests is not visual acceptance. After any renderer or CSS change, open
the full 1080x1920 result and inspect it at normal size against this PNG.

## Deliberately refreshing the reference

1. Export Figma file `YVPUc24KCJIFrHpoXKrHz7`, node `1:2`, at exactly 1x.
2. Replace the PNG and its matching sanitized fixture together as one design
   decision. Do not recompress or resize the export.
3. Recompute the PNG and asset byte counts and SHA-256 hashes in the metadata.
4. Run the focused reference tests and the full offline test suite.
5. Inspect the new reference and a matching render at normal size.
6. Explain the visual change and why it was intentional in the pull request.
