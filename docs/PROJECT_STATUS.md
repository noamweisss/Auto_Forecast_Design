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
| Data models | Implemented | Forecast objects and validation exist in `src/data/models.py`. |
| IMS fetching | Implemented | Country and city XML can be downloaded with retry and encoding handling. |
| XML parsing | Implemented | XML is converted to forecast objects using committed city and weather-code data. |
| Archive | Implemented | XML snapshots and fallback helpers exist. Generated archives stay untracked. |
| Design assets | Available | Figma-derived tokens, fonts, icons, logos, and map assets are committed. |
| Design helpers | Partial | `src/design/tokens.py` and icon descriptions still contain stubs. |
| HTML/CSS template | Placeholder | The 1080x1920 canvas exists, but it contains placeholder text rather than the design. |
| Playwright renderer | Placeholder | `TemplateRenderer.render()` raises `NotImplementedError`. |
| Image saving | Implemented | Pillow images can be saved as JPEG and PNG. |
| Email delivery | Placeholder | Configuration validation exists, but message construction and sending are stubs. |
| Main workflow | Placeholder | `python -m src.main` explains the intended flow but does not run it. |
| Automation | Not started | `.github/workflows/` contains no production workflow. |

## Verification snapshot

The last known green test run was 54 tests passing on 2026-07-15.

On 2026-07-20, a fresh baseline could not reach the tests on the local Windows
machine:

- The checked-in `.venv` launcher points to a removed Microsoft Store Python.
- The current bundled Codex Python runtime does not include pytest.

That is an environment failure, not evidence that the tests or application code
failed. A fresh local environment or `scripts/setup_codex_cloud.sh` should be
used before the next implementation task. Do not commit `.venv`.

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

## Source-of-truth order

When files disagree, use this order:

1. Current source code and tests.
2. `AGENTS.md` and this page.
3. `README.md`.
4. Historical plans and changelog entries.

Update this page whenever a layer changes between implemented, partial, and
placeholder.
