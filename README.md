# IMS Auto Forecast Design

An in-progress system for generating daily, branded weather-forecast images for
the Israel Meteorological Service (IMS) media team.

> **Current status:** one thin application and CLI connect exact-date IMS-shaped
> source data to the checked HTML/CSS + Playwright renderer and one atomic local
> PNG. Fixture mode is fully offline sample data; live mode uses real IMS data.

## What this project is for

The goal is to replace a manual social-media production task with a clear,
maintainable workflow:

1. Fetch official IMS country and city forecast XML.
2. Parse Hebrew forecast data into Python objects.
3. Inject that data into an RTL HTML/CSS design.
4. Capture a 1080x1920 image with Playwright.
5. Atomically save one canonical PNG.
6. Eventually deliver the result automatically.

The project is design-first. Its maintainer works primarily in Figma, HTML, and
CSS and is using this repository to learn software development, so readability
and debuggability matter more than clever abstractions.

## What works today

- IMS XML fetching with retries and Hebrew encoding fallbacks.
- Parsing country and city forecasts into Python data models.
- Weather-code and city configuration loading inside the parser.
- Validated snapshot archiving and exact-date fallback selection.
- Validation and atomic saving of one canonical 1080x1920 PNG.
- Automated tests for the implemented data and file-saving layers.
- Committed Figma-derived design tokens, fonts, logos, map, and weather icons.
- A validated Story render context plus the complete 1080x1920 RTL HTML/CSS design.
- A deterministic Playwright renderer that rejects missing assets, fonts, browser
  errors, wrong layout geometry, and invalid PNG output.
- A frozen reference fixture and ignored visual-comparison helper for normal-size
  design review.
- A real `python -m src.main` command with deterministic fixture and live IMS
  source modes, exact-date fallback provenance, stable exits, and one local PNG.
- A browser-marked vertical test from committed IMS XML fixtures through the
  complete application and atomic saver.
- SMTP delivery of the finished PNG through `python -m src.main --email`.
- A daily GitHub Actions workflow that generates and emails the Story at 06:30
  Israel time.

## What is unfinished

- The daily workflow has never run against a real mailbox; it needs the
  `EMAIL_ADDRESS` and `EMAIL_PASSWORD` repository secrets before its first send.
- The first live output is workable, but future visual refinements remain a
  design choice rather than a blocker for the local generator.

See [Project Status](docs/PROJECT_STATUS.md) for the verified layer-by-layer map
and the recommended restart point.

## Technology

- Python 3.11+
- `requests` and `lxml` for IMS data
- Jinja2 for HTML templating
- Playwright for browser screenshots
- Pillow for final PNG validation
- pytest for automated tests

Hebrew layout is handled by the browser with `dir="rtl"`; the XML pipeline uses
explicit encodings because the IMS feeds may not arrive as UTF-8.

## Local setup

Clone the repository, then create an isolated Python environment:

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install Python dependencies and Chromium:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Run the tests:

```bash
python -m pytest tests -q -p no:cacheprovider
```

Generate a deterministic offline demo from the two committed sanitized
production-shaped XML samples:

```bash
python -m src.main --source fixture
```

That fixture is local sample data, not today's forecast. Generate from real IMS
data for the Israel run-start date with:

```bash
python -m src.main --source live
```

Request an explicit exact date or repository-root-relative output directory with:

```bash
python -m src.main --source live --date 2026-07-20
python -m src.main --source fixture --output-dir test-results/forecast-demo
```

The command never selects a nearby date. A successful run writes one absolute
`forecast_YYYY-MM-DD.png` path.

Add `--email` to also send that PNG to `RECIPIENT_EMAIL`:

```bash
python -m src.main --source live --email
```

The SMTP configuration is validated before any fetching or rendering, so a
missing credential fails in seconds with exit code 3. A send failure after the
PNG was already saved exits with code 8 and still reports the saved file.

## Daily email workflow

`.github/workflows/daily_forecast.yml` runs `python -m src.main --source live
--email` every morning at 06:30 Israel time and keeps the PNG as a run artifact
for 14 days.

GitHub cron is UTC only and Israel switches between UTC+3 and UTC+2, so the
schedule fires at both 03:30 and 04:30 UTC; the first step drops whichever
firing is not 06:xx in Jerusalem. Scheduled workflows only run from the default
branch, so this file has to be on `main` before the first delivery.

Add these repository secrets under Settings, Secrets and variables, Actions:

| Secret | Required | Default if unset |
| --- | --- | --- |
| `EMAIL_ADDRESS` | Yes | none, the run fails |
| `EMAIL_PASSWORD` | Yes | none, the run fails |
| `RECIPIENT_EMAIL` | No | `weissno@ims.gov.il` |
| `SMTP_SERVER` | No | `smtp.gmail.com` |
| `SMTP_PORT` | No | `587` |
| `EMAIL_SENDER_NAME` | No | `IMS Forecast Automation` |

For Gmail, `EMAIL_PASSWORD` must be an app password from
https://myaccount.google.com/apppasswords, not the account password.

Run it by hand from the Actions tab first. Manual runs skip the clock gate and
let you choose the source, an exact date, and whether to send the email.

Renderer work can create the ignored frozen-reference diagnostics with:

```bash
python -m tests.story_visual
```

Open the resulting files under `test-results/story-visual/` at normal size;
their metrics support human review and are not a pass/fail similarity score.

## Codex cloud setup

Codex cloud needs only committed repository content; it cannot see this
machine's `.env`, virtual environment, private notes, or local integrations.

In the Codex environment settings:

1. Select Python 3.11 or newer.
2. Use this setup command:

   ```bash
   bash scripts/setup_codex_cloud.sh
   ```

3. Leave agent internet access off unless a task specifically needs live IMS or
   Figma access. The existing automated tests should not require the network.
4. Add real SMTP credentials as environment settings only when a task actually
   sends mail. Never commit them.

The setup script installs Python dependencies and the Playwright Chromium
browser while setup-time internet access is available.

## Repository guidance

- [AGENTS.md](.agents/AGENTS.md) is the durable guide for local and cloud coding agents.
- [Project Status](docs/PROJECT_STATUS.md) is the current implementation map.
- [Architecture](docs/ARCHITECTURE.md) explains the current small-layer structure and shared paths.
- [docs/history/](docs/history/) holds the superseded initial plans and refactor audit for context only.

Historical plans can drift. Prefer current source code, tests, `.agents/AGENTS.md`, and
the project-status page when they disagree.

## Secrets, generated files, and assets

- Copy `.env.example` to `.env` for local email configuration. The daily
  workflow reads the same variable names from repository secrets.
- `.env`, generated images, downloaded XML, logs, caches, and private internal
  notes are intentionally ignored by Git.
- Fonts and image assets are stored through Git LFS. Install Git LFS before
  cloning if your Git client does not include it.

## License

Licensed under the [Apache License 2.0](LICENSE). You may use, modify, and
redistribute the code under its terms; it also includes an explicit patent grant.
Copyright 2026 Noam Weiss.
