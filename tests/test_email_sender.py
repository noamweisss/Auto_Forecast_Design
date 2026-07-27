"""Offline contracts for SMTP configuration and forecast email delivery."""

from datetime import date
from email.message import EmailMessage
from pathlib import Path
import smtplib

import pytest

from src.delivery.email_sender import (
    EmailConfigError,
    EmailDeliveryError,
    EmailSettings,
    SmtpSecurity,
    build_forecast_message,
    default_subject,
    load_email_settings,
    send_forecast_email,
)


TARGET_DATE = date(2026, 7, 28)
VALID_ENVIRONMENT = {
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "EMAIL_ADDRESS": "forecast@example.com",
    "EMAIL_PASSWORD": "app-password",
    "RECIPIENT_EMAIL": "weissno@ims.gov.il",
}


def settings(**overrides) -> EmailSettings:
    base = {
        "server": "smtp.gmail.com",
        "port": 587,
        "username": "forecast@example.com",
        "password": "app-password",
        "sender_address": "forecast@example.com",
        "sender_name": "IMS Forecast Automation",
        "recipients": ("weissno@ims.gov.il",),
        "security": SmtpSecurity.STARTTLS,
    }
    base.update(overrides)
    return EmailSettings(**base)


class FakeSmtpClient:
    """Records the ordered SMTP conversation without opening a socket."""

    def __init__(self, *, login_error=None, send_error=None) -> None:
        self.calls: list[tuple] = []
        self.sent_messages: list[EmailMessage] = []
        self.closed = False
        self._login_error = login_error
        self._send_error = send_error

    def __enter__(self):
        self.calls.append(("enter",))
        return self

    def __exit__(self, *exception_details):
        self.closed = True
        self.calls.append(("exit",))
        return False

    def starttls(self, *, context):
        self.calls.append(("starttls", context is not None))

    def login(self, username, password):
        self.calls.append(("login", username, password))
        if self._login_error is not None:
            raise self._login_error

    def send_message(self, message):
        self.calls.append(("send_message",))
        if self._send_error is not None:
            raise self._send_error
        self.sent_messages.append(message)


def write_png(tmp_path: Path, name: str = "forecast_2026-07-28.png") -> Path:
    path = tmp_path / name
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"story bytes")
    return path


def test_valid_environment_loads_normalized_settings():
    loaded = load_email_settings(VALID_ENVIRONMENT)

    assert loaded.server == "smtp.gmail.com"
    assert loaded.port == 587
    assert loaded.username == "forecast@example.com"
    assert loaded.sender_address == "forecast@example.com"
    assert loaded.recipients == ("weissno@ims.gov.il",)
    assert loaded.security is SmtpSecurity.STARTTLS


@pytest.mark.parametrize("missing_name", sorted(VALID_ENVIRONMENT))
def test_every_required_variable_is_named_when_missing(missing_name):
    environment = {
        name: value
        for name, value in VALID_ENVIRONMENT.items()
        if name != missing_name
    }

    with pytest.raises(EmailConfigError) as raised:
        load_email_settings(environment)

    assert missing_name in str(raised.value)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("SMTP_PORT", "not-a-port"),
        ("SMTP_PORT", "0"),
        ("SMTP_PORT", "70000"),
        ("EMAIL_ADDRESS", "forecast-at-example.com"),
        ("RECIPIENT_EMAIL", "weissno@ims"),
        ("RECIPIENT_EMAIL", "weissno@ims.gov.il, broken@@example.com"),
        ("SMTP_SECURITY", "plaintext"),
    ],
)
def test_unusable_values_are_rejected_with_the_variable_name(name, value):
    environment = dict(VALID_ENVIRONMENT)
    environment[name] = value

    with pytest.raises(EmailConfigError) as raised:
        load_email_settings(environment)

    assert name in str(raised.value)


def test_several_recipients_are_split_deduplicated_and_ordered():
    environment = dict(VALID_ENVIRONMENT)
    environment["RECIPIENT_EMAIL"] = (
        " weissno@ims.gov.il; media@ims.gov.il , weissno@ims.gov.il "
    )

    loaded = load_email_settings(environment)

    assert loaded.recipients == ("weissno@ims.gov.il", "media@ims.gov.il")


@pytest.mark.parametrize(
    ("environment_overrides", "expected"),
    [
        ({"SMTP_PORT": "465"}, SmtpSecurity.SSL),
        ({"SMTP_PORT": "587"}, SmtpSecurity.STARTTLS),
        ({"SMTP_PORT": "465", "SMTP_SECURITY": "starttls"}, SmtpSecurity.STARTTLS),
        ({"SMTP_PORT": "587", "SMTP_SECURITY": "SSL"}, SmtpSecurity.SSL),
    ],
)
def test_security_follows_the_port_unless_stated(environment_overrides, expected):
    environment = dict(VALID_ENVIRONMENT)
    environment.update(environment_overrides)

    assert load_email_settings(environment).security is expected


def test_separate_smtp_username_overrides_the_sender_login():
    environment = dict(VALID_ENVIRONMENT)
    environment["SMTP_USERNAME"] = "relay-user"

    assert load_email_settings(environment).username == "relay-user"


def test_message_carries_hebrew_text_and_the_png_attachment(tmp_path):
    image_path = write_png(tmp_path)

    message = build_forecast_message(
        attachment_bytes=image_path.read_bytes(),
        attachment_name=image_path.name,
        settings=settings(),
        target_date=TARGET_DATE,
    )

    assert message["Subject"] == "תחזית יומית - 28/07/2026"
    assert message["To"] == "weissno@ims.gov.il"
    assert message["From"] == "IMS Forecast Automation <forecast@example.com>"

    body = message.get_body(preferencelist=("plain",))
    assert body is not None
    assert "השירות המטאורולוגי הישראלי" in body.get_content()

    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_content_type() == "image/png"
    assert attachments[0].get_filename() == image_path.name
    assert attachments[0].get_payload(decode=True) == image_path.read_bytes()


def test_subject_uses_the_forecast_date_not_the_send_date():
    assert default_subject(date(2026, 1, 3)) == "תחזית יומית - 03/01/2026"


def test_successful_send_follows_starttls_login_send_and_close(tmp_path):
    image_path = write_png(tmp_path)
    client = FakeSmtpClient()

    result = send_forecast_email(
        image_path,
        settings=settings(),
        target_date=TARGET_DATE,
        smtp_client_factory=lambda _: client,
    )

    assert [call[0] for call in client.calls] == [
        "enter",
        "starttls",
        "login",
        "send_message",
        "exit",
    ]
    assert client.calls[2] == ("login", "forecast@example.com", "app-password")
    assert client.closed is True
    assert result.recipients == ("weissno@ims.gov.il",)
    assert result.subject == "תחזית יומית - 28/07/2026"
    assert result.attachment_name == image_path.name
    assert result.attachment_bytes == image_path.stat().st_size


def test_implicit_ssl_connections_never_call_starttls(tmp_path):
    image_path = write_png(tmp_path)
    client = FakeSmtpClient()

    send_forecast_email(
        image_path,
        settings=settings(port=465, security=SmtpSecurity.SSL),
        target_date=TARGET_DATE,
        smtp_client_factory=lambda _: client,
    )

    assert [call[0] for call in client.calls] == [
        "enter",
        "login",
        "send_message",
        "exit",
    ]


@pytest.mark.parametrize(
    ("client_kwargs", "expected_text"),
    [
        (
            {"login_error": smtplib.SMTPAuthenticationError(535, b"bad password")},
            "rejected the credentials",
        ),
        (
            {"send_error": smtplib.SMTPRecipientsRefused({"weissno@ims.gov.il": (550, b"no")})},
            "SMTP delivery to smtp.gmail.com failed",
        ),
        ({"send_error": OSError("connection reset")}, "Could not reach smtp.gmail.com:587"),
    ],
)
def test_server_failures_become_readable_delivery_errors(
    tmp_path,
    client_kwargs,
    expected_text,
):
    image_path = write_png(tmp_path)
    client = FakeSmtpClient(**client_kwargs)

    with pytest.raises(EmailDeliveryError) as raised:
        send_forecast_email(
            image_path,
            settings=settings(),
            target_date=TARGET_DATE,
            smtp_client_factory=lambda _: client,
        )

    assert expected_text in str(raised.value)


@pytest.mark.parametrize(
    ("filename", "content", "expected_text"),
    [
        ("forecast.txt", b"not an image", "must be a PNG file"),
        ("forecast_2026-07-28.png", b"", "is empty"),
    ],
)
def test_unusable_attachments_fail_before_any_connection(
    tmp_path,
    filename,
    content,
    expected_text,
):
    image_path = tmp_path / filename
    image_path.write_bytes(content)

    def refuse_connection(_):
        pytest.fail("the attachment must be checked before connecting")

    with pytest.raises(EmailDeliveryError) as raised:
        send_forecast_email(
            image_path,
            settings=settings(),
            target_date=TARGET_DATE,
            smtp_client_factory=refuse_connection,
        )

    assert expected_text in str(raised.value)


def test_missing_attachment_file_is_reported_as_a_delivery_error(tmp_path):
    with pytest.raises(EmailDeliveryError) as raised:
        send_forecast_email(
            tmp_path / "forecast_2026-07-28.png",
            settings=settings(),
            target_date=TARGET_DATE,
            smtp_client_factory=lambda _: FakeSmtpClient(),
        )

    assert "Could not read" in str(raised.value)
