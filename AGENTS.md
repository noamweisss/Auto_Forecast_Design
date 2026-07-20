# AGENTS.md

This is the shared operating guide for humans and coding agents working in this
repository. Keep it short, factual, and updated when the real workflow changes.

## Mission

Build an automated daily forecast-image generator for the Israel
Meteorological Service (IMS) media team. The first product milestone is one
correct local 1080x1920 Instagram Story image generated from real IMS data.

The maintainer is a designer learning software development. Prefer readable,
well-named code and explain decisions in plain language. Use HTML/CSS and Figma
or DOM analogies when they genuinely clarify a Python concept.

## Read first

1. `docs/PROJECT_STATUS.md` - verified implementation state and next milestone.
2. `README.md` - setup and project overview.
3. The source and tests relevant to the task.

Source code and tests are authoritative. Historical plans describe intent and
may be stale.

## Current reality

- Data models, IMS XML fetching, parsing, archiving, and image file saving are
  implemented and covered by tests.
- `src/main.py` is still a placeholder; it does not run the advertised pipeline.
- The validated Story render context, HTML/CSS template, and checked Playwright
  PNG renderer are implemented and covered by structural and browser tests.
- The data, renderer, and saver are not connected by one application workflow yet.
- Email delivery still contains stubs.
- No production GitHub Actions workflow exists yet.
- Figma-derived tokens and local design assets are committed, so ordinary work
  must not require live Figma access.

Do not describe the project as end-to-end functional until the source proves it.

## Setup and checks

Use Python 3.11 or newer.

Local setup:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Activate `.venv` in the normal way for your shell, or call its Python executable
directly. Do not commit the environment directory.

Codex cloud setup:

```bash
bash scripts/setup_codex_cloud.sh
```

Fast repository test command:

```bash
python -m pytest tests -q -p no:cacheprovider
```

Full local entry point:

```bash
python -m src.main
```

The entry point currently prints a placeholder message. Treat that as known
unfinished behavior, not a successful forecast-generation run.

## Project map

```text
src/data/       Fetch, parse, model, and archive IMS XML
src/design/     Validated, template-ready Story context and asset addresses
src/rendering/  Jinja2 template plus Playwright screenshot pipeline
src/delivery/   Image saving and future email delivery
src/utils/      Logging and date helpers
config/         City, weather-code, and Figma-derived design data
assets/         Fonts, logos, map, and weather icons via Git LFS
tests/          Automated tests; tests/manual contains optional helpers
```

## Engineering rules

- Make the smallest coherent change that advances the requested milestone.
- Prefer clarity over clever abstractions. Explain why non-obvious logic exists.
- Preserve Hebrew as UTF-8. Use browser-native RTL with `dir="rtl"` for layouts.
- Keep modules single-purpose: data, design, rendering, delivery, and orchestration.
- Keep network and email calls mocked in automated tests.
- Never depend on ignored files for normal tests or basic repository orientation.
- Do not assume Figma, Gmail, IMS network access, or local MCP servers are
  available in Codex cloud.
- Never commit `.env`, credentials, generated forecasts, fetched XML archives,
  logs, caches, or private notes under `docs/internal/`.
- Update `CHANGELOG.md` and `docs/PROJECT_STATUS.md` when implementation status
  materially changes.

## Completion standard

Before declaring a code change complete:

1. Run the focused tests for the files changed.
2. Run the fast repository test command when dependencies are available.
3. Report any skipped check and the exact environment reason.
4. Confirm `git status` contains only intentional changes.
5. For rendering changes, inspect the actual 1080x1920 output at normal size;
   passing unit tests alone is not visual acceptance.

Avoid broad refactors, dependency upgrades, live email, deployment, or long
visual-optimization cycles unless the task explicitly includes them.

## Git and publication

- Keep `main` stable. Use short-lived topic branches.
- Use commit messages in the form `<type>: <description>`.
- Git LFS is required for fonts and image assets.
- The repository currently has no declared software license. Do not claim one
  or add one without the owner's decision.
- Codex cloud receives committed repository files, not this machine's ignored
  files or local tool configuration. Put durable project guidance here.
