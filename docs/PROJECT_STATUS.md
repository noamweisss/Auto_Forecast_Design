# Project Status

Last reviewed: 2026-07-27

This is the restart map for anyone returning to the repository after a gap. It
separates working code from plans and placeholders. When files disagree, trust
source code and tests first, then `.agents/AGENTS.md` and this page, then `README.md`,
then historical plans and the changelog.

## The short version

One command turns exact-date IMS data into one atomic 1080x1920 PNG, and
optionally emails it:

```bash
python -m src.main --source fixture           # deterministic offline demo
python -m src.main --source live              # current official IMS feeds
python -m src.main --source live --email      # also send the saved PNG
```

Fixture mode proves the whole path offline with committed sample data. Live mode
fetches the real country and city feeds and applies the same exact-date and
15-city rules. `.github/workflows/daily_forecast.yml` runs the live command with
`--email` at 06:30 Israel time.

## Layer-by-layer state

| Layer | State | Meaning |
| --- | --- | --- |
| Shared paths (`src/app_paths.py`) | Implemented | Repository paths are anchored to the source tree, not the shell directory. |
| Clock + settings boundary | Implemented | `main()` sets up paths, `.env`, Israel time, logging, and one immutable settings load. |
| Data models | Implemented | Every value carries source provenance; a daily forecast needs one date and 15 unique cities. |
| IMS fetching | Implemented | Returns decoded XML or a structured failure with its exact attempt count. |
| XML parsing | Implemented | Resolves ordered snapshots for one exact date; incomplete or invalid data fails the whole forecast. |
| Snapshots + store | Implemented | IMS feeds are sealed with issue/fetch time and atomically stored as UTF-8 JSON, selected by metadata within a seven-day window. |
| Design assets + context | Implemented | The SVG map/logos, catalog icons, and fonts are checked, then packed into one frozen render context. |
| Visual reference | Available | A committed 1080x1920 Figma export of node `1:2` plus a sanitized matching forecast give an offline target without live Figma. |
| HTML/CSS template + renderer | Implemented | Strict Jinja fills the RTL template; Playwright checks fonts, images, geometry, and PNG dimensions before output. |
| Image saving | Implemented | Validated PNG bytes are published through a flushed, fsynced temporary file and atomic replace. |
| Email delivery | Implemented | Validated SMTP settings, a Hebrew UTF-8 message, and the PNG attachment are sent through STARTTLS or implicit SSL; the SMTP client is injected, so tests stay offline. |
| Automation | Implemented | PRs run offline tests plus a real-Chromium render smoke test. A scheduled workflow generates and emails the Story at 06:30 Israel time across both national offsets. |

## Verification

On 2026-07-20 the offline suite passed (232 passed, 9 skipped) with `ruff` and
`mypy src` clean. The browser render path is covered by the fixture-to-PNG smoke
test, which runs against real Chromium in CI.

The 2026-07-27 delivery work adds offline contracts for SMTP configuration,
message construction, connection ordering, failure translation, the command-line
`--email` boundary, and the scheduled workflow file. No automated test opens a
socket, so the first real send is still a manual verification step: run the
workflow by hand from the Actions tab and confirm the message arrives.

Automated contracts guard exact reference bytes, dimensions, provenance
metadata, fixture content, and hydrated asset hashes. They do not replace human
visual review: after renderer changes, open the actual 1080x1920 output at
normal size and compare it with `docs/design-reference/`.

The Story deliberately shows Figma's visible Hebrew label `תל אביב` for city
402. Its stable ID, `tel_aviv` internal key, `Tel Aviv - Yafo` English identity,
and IMS data are unchanged.

## Recommended next milestone

Put the daily routine into real service:

1. Add the `EMAIL_ADDRESS` and `EMAIL_PASSWORD` repository secrets. Every other
   email variable has a working default in the workflow.
2. Merge the workflow to `main`. GitHub only runs scheduled workflows from the
   default branch, so a topic branch never fires at 06:30.
3. Trigger the workflow by hand from the Actions tab and confirm the message
   arrives before relying on the schedule.
4. Watch the first winter-time run: the schedule fires at 03:30 and 04:30 UTC
   and the Israel-hour gate keeps whichever one is 06:30 locally.
5. Refine the live design later if the media team wants visual changes.

## Codex cloud readiness

Remote work stays reproducible through a committed `.agents/AGENTS.md`,
`scripts/setup_codex_cloud.sh`, `.env.example` (names only), Git LFS rules with
setup/CI hydration checks, a render-smoke CI job that cannot silently skip
browser tests, and ignore rules for generated forecasts, fetched XML,
credentials, caches, and local environments.

Cloud agents work from committed assets and `config/design_tokens.json`. Live
Figma, Gmail, and IMS network access are optional, not baseline assumptions.

Update this page whenever a layer moves between implemented, partial, and
placeholder.
