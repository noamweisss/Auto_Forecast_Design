"""Offline contracts for the scheduled daily forecast-email workflow.

The workflow file cannot be executed here, so these tests guard the parts that
silently break a 06:30 Israel delivery: the UTC cron pair, the Israel-hour gate,
hydrated LFS assets, a real browser, and the credential names the sender reads.
"""

import re

from src.app_paths import PATHS
from src.delivery.email_sender import load_email_settings


DAILY_WORKFLOW = PATHS.root / ".github" / "workflows" / "daily_forecast.yml"
REQUIRED_ENVIRONMENT_NAMES = (
    "SMTP_SERVER",
    "SMTP_PORT",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "RECIPIENT_EMAIL",
)


def _workflow_text() -> str:
    return DAILY_WORKFLOW.read_text(encoding="utf-8")


def test_schedule_covers_both_israel_offsets_and_keeps_only_the_six_oclock_run():
    text = _workflow_text()

    # 03:30 UTC is 06:30 IDT (summer) and 04:30 UTC is 06:30 IST (winter).
    assert 'cron: "30 3,4 * * *"' in text
    assert 'ZoneInfo("Asia/Jerusalem")' in text
    assert "israel_now.hour == 6" in text
    assert 'EVENT_NAME"] != "schedule"' in text
    assert "should_run={str(should_run).lower()}" in text
    assert "steps.gate.outputs.should_run == 'true'" in text


def test_manual_runs_can_choose_source_date_and_whether_to_send():
    text = _workflow_text()

    assert "workflow_dispatch:" in text
    assert "options: [live, fixture]" in text
    assert "forecast_date:" in text
    assert "send_email:" in text
    assert "${{ inputs.source || 'live' }}" in text
    assert "github.event_name == 'schedule' && 'true' || inputs.send_email" in text


def test_scheduled_run_generates_live_data_and_emails_it():
    text = _workflow_text()

    assert "arguments=(--source \"$SOURCE\")" in text
    assert "arguments+=(--email)" in text
    assert 'python -m src.main "${arguments[@]}"' in text
    assert "continue-on-error" not in text


def test_runner_hydrates_assets_and_installs_a_real_browser():
    text = _workflow_text()

    assert "        with:\n          lfs: true" in text
    assert "git lfs fsck" in text
    assert "python -m pip install -r requirements.txt" in text
    assert "python -m playwright install --with-deps chromium" in text
    assert text.index("git lfs fsck") < text.index('python -m src.main "${arguments[@]}"')


def test_every_credential_the_sender_requires_is_supplied_from_secrets():
    text = _workflow_text()

    for name in REQUIRED_ENVIRONMENT_NAMES:
        assert re.search(rf"^\s+{name}: \$\{{\{{ secrets\.", text, flags=re.MULTILINE), name

    # Only the two genuinely secret values must be configured by hand; the rest
    # fall back so a run cannot fail on an unset host, port, or recipient.
    assert "secrets.EMAIL_ADDRESS }}" in text
    assert "secrets.EMAIL_PASSWORD }}" in text
    assert "secrets.SMTP_SERVER || 'smtp.gmail.com'" in text
    assert "secrets.SMTP_PORT || '587'" in text
    assert "secrets.RECIPIENT_EMAIL || 'weissno@ims.gov.il'" in text


def test_workflow_defaults_alone_load_valid_email_settings():
    """The fallbacks plus the two secrets are enough for the sender to run."""
    text = _workflow_text()
    defaults = dict(re.findall(r"secrets\.(\w+) \|\| '([^']+)'", text))

    settings = load_email_settings(
        {
            "SMTP_SERVER": defaults["SMTP_SERVER"],
            "SMTP_PORT": defaults["SMTP_PORT"],
            "RECIPIENT_EMAIL": defaults["RECIPIENT_EMAIL"],
            "EMAIL_ADDRESS": "configured-sender@example.com",
            "EMAIL_PASSWORD": "configured-app-password",
        }
    )

    assert settings.recipients == ("weissno@ims.gov.il",)
    assert settings.server == "smtp.gmail.com"
    assert settings.port == 587


def test_no_credential_is_committed_in_the_workflow_file():
    text = _workflow_text()

    # Every credential must arrive through ${{ secrets.* }}, never as a literal.
    assert not re.search(r"EMAIL_PASSWORD:[ \t]+[^$\n]", text)
    assert not re.search(r"EMAIL_ADDRESS:[ \t]+[^$\n]", text)
