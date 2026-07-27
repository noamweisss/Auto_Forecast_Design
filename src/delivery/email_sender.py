"""Send one finished forecast Story PNG to the media team over SMTP.

Configuration is read once from environment variables (loaded from the
repository ``.env`` locally, or from GitHub Actions secrets in the daily
workflow). Nothing here reads a clock or a config file directly: the caller
passes the forecast date, and the SMTP client is an ordinary injected argument
so the automated suite never opens a socket.

Required environment variables:
    SMTP_SERVER      Mail host, for example ``smtp.gmail.com``.
    SMTP_PORT        Mail port; 587 means STARTTLS and 465 means implicit SSL.
    EMAIL_ADDRESS    Sender mailbox, also used as the SMTP username.
    EMAIL_PASSWORD   App password for that mailbox, never a normal password.
    RECIPIENT_EMAIL  One address, or several separated by commas/semicolons.

Optional environment variables:
    SMTP_USERNAME    SMTP login when it differs from EMAIL_ADDRESS.
    SMTP_SECURITY    ``starttls`` or ``ssl``; defaults from the port.
    EMAIL_SENDER_NAME  Display name shown before the sender address.

Security note:
    Never commit ``.env``. Gmail app passwords are created at
    https://myaccount.google.com/apppasswords and are revocable.
"""

from dataclasses import dataclass
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr
from enum import Enum
import logging
import os
from pathlib import Path
import smtplib
import ssl
from typing import Callable, Mapping


logger = logging.getLogger(__name__)

_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_RECIPIENT_SEPARATORS = (",", ";")


class EmailConfigError(RuntimeError):
    """Email configuration is missing or cannot be used as written."""


class EmailDeliveryError(RuntimeError):
    """A configured message could not be built or handed to the mail server."""


class SmtpSecurity(str, Enum):
    """How the connection to the mail server is protected."""

    STARTTLS = "starttls"
    SSL = "ssl"


@dataclass(frozen=True)
class EmailSettings:
    """Everything needed to send one forecast email, validated at load time."""

    server: str
    port: int
    username: str
    password: str
    sender_address: str
    sender_name: str
    recipients: tuple[str, ...]
    security: SmtpSecurity
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class EmailDeliveryResult:
    """What was actually sent, for logging and command-line output."""

    recipients: tuple[str, ...]
    subject: str
    attachment_name: str
    attachment_bytes: int


SmtpClientFactory = Callable[[EmailSettings], smtplib.SMTP]


def load_email_settings(
    environment: Mapping[str, str] | None = None,
) -> EmailSettings:
    """Read and validate email configuration, naming every unusable value."""
    values = os.environ if environment is None else environment

    server = _required_text(values, "SMTP_SERVER")
    sender_address = _required_address(values, "EMAIL_ADDRESS")
    password = _required_text(values, "EMAIL_PASSWORD")
    port = _required_port(values, "SMTP_PORT")
    recipients = _required_recipients(values, "RECIPIENT_EMAIL")
    username = (values.get("SMTP_USERNAME") or sender_address).strip()
    sender_name = (values.get("EMAIL_SENDER_NAME") or "").strip()

    return EmailSettings(
        server=server,
        port=port,
        username=username,
        password=password,
        sender_address=sender_address,
        sender_name=sender_name,
        recipients=recipients,
        security=_resolve_security(values, port),
    )


def send_forecast_email(
    image_path: Path,
    *,
    settings: EmailSettings,
    target_date: date,
    subject: str | None = None,
    body: str | None = None,
    smtp_client_factory: SmtpClientFactory | None = None,
) -> EmailDeliveryResult:
    """Attach one published forecast PNG and deliver it to every recipient."""
    if not isinstance(settings, EmailSettings):
        raise EmailDeliveryError("settings must be validated EmailSettings")
    if not isinstance(target_date, date):
        raise EmailDeliveryError("target_date must be a date")

    attachment = _read_attachment(Path(image_path))
    message = build_forecast_message(
        attachment_bytes=attachment,
        attachment_name=Path(image_path).name,
        settings=settings,
        target_date=target_date,
        subject=subject,
        body=body,
    )

    factory = smtp_client_factory or _open_smtp_client
    try:
        with factory(settings) as client:
            if settings.security is SmtpSecurity.STARTTLS:
                client.starttls(context=ssl.create_default_context())
            client.login(settings.username, settings.password)
            client.send_message(message)
    except smtplib.SMTPAuthenticationError as error:
        raise EmailDeliveryError(
            f"{settings.server} rejected the credentials for "
            f"{settings.username}: {error}"
        ) from error
    except smtplib.SMTPException as error:
        raise EmailDeliveryError(f"SMTP delivery to {settings.server} failed: {error}") from error
    except (OSError, ssl.SSLError) as error:
        raise EmailDeliveryError(
            f"Could not reach {settings.server}:{settings.port}: {error}"
        ) from error

    result = EmailDeliveryResult(
        recipients=settings.recipients,
        subject=str(message["Subject"]),
        attachment_name=Path(image_path).name,
        attachment_bytes=len(attachment),
    )
    logger.info(
        "Sent %s (%s bytes) to %s",
        result.attachment_name,
        result.attachment_bytes,
        ", ".join(result.recipients),
    )
    return result


def build_forecast_message(
    *,
    attachment_bytes: bytes,
    attachment_name: str,
    settings: EmailSettings,
    target_date: date,
    subject: str | None = None,
    body: str | None = None,
) -> EmailMessage:
    """Build one UTF-8 Hebrew message carrying the forecast PNG as an attachment."""
    message = EmailMessage()
    message["From"] = (
        formataddr((settings.sender_name, settings.sender_address))
        if settings.sender_name
        else settings.sender_address
    )
    message["To"] = ", ".join(settings.recipients)
    message["Subject"] = subject or default_subject(target_date)
    message.set_content(body or default_body(target_date), charset="utf-8")
    message.add_attachment(
        attachment_bytes,
        maintype="image",
        subtype="png",
        filename=attachment_name,
    )
    return message


def default_subject(target_date: date) -> str:
    """Hebrew subject naming the forecast date, not the send date."""
    return f"תחזית יומית - {target_date.strftime('%d/%m/%Y')}"


def default_body(target_date: date) -> str:
    """Hebrew body text for the automated daily delivery."""
    return f"""שלום,

מצורפת תחזית מזג האוויר היומית לתאריך {target_date.strftime('%d/%m/%Y')}
לפרסום ברשתות החברתיות.

בברכה,
מערכת התחזית האוטומטית
השירות המטאורולוגי הישראלי
"""


def _open_smtp_client(settings: EmailSettings) -> smtplib.SMTP:
    if settings.security is SmtpSecurity.SSL:
        return smtplib.SMTP_SSL(
            settings.server,
            settings.port,
            timeout=settings.timeout_seconds,
            context=ssl.create_default_context(),
        )
    return smtplib.SMTP(settings.server, settings.port, timeout=settings.timeout_seconds)


def _read_attachment(image_path: Path) -> bytes:
    if image_path.suffix.lower() != ".png":
        raise EmailDeliveryError(f"Attachment must be a PNG file; got {image_path.name}")
    try:
        attachment = image_path.read_bytes()
    except OSError as error:
        raise EmailDeliveryError(f"Could not read {image_path}: {error}") from error
    if not attachment:
        raise EmailDeliveryError(f"Attachment {image_path} is empty")
    if len(attachment) > _MAX_ATTACHMENT_BYTES:
        raise EmailDeliveryError(
            f"Attachment {image_path.name} is {len(attachment)} bytes, "
            f"above the {_MAX_ATTACHMENT_BYTES}-byte limit"
        )
    return attachment


def _required_text(values: Mapping[str, str], name: str) -> str:
    value = (values.get(name) or "").strip()
    if not value:
        raise EmailConfigError(f"{name} must be set to a nonempty value")
    return value


def _required_address(values: Mapping[str, str], name: str) -> str:
    value = _required_text(values, name)
    if not _looks_like_address(value):
        raise EmailConfigError(f"{name} must be one email address; got {value!r}")
    return value


def _required_port(values: Mapping[str, str], name: str) -> int:
    raw = _required_text(values, name)
    try:
        port = int(raw)
    except ValueError as error:
        raise EmailConfigError(f"{name} must be a whole number; got {raw!r}") from error
    if not 1 <= port <= 65535:
        raise EmailConfigError(f"{name} must be between 1 and 65535; got {port}")
    return port


def _required_recipients(values: Mapping[str, str], name: str) -> tuple[str, ...]:
    raw = _required_text(values, name)
    for separator in _RECIPIENT_SEPARATORS[1:]:
        raw = raw.replace(separator, _RECIPIENT_SEPARATORS[0])

    recipients: list[str] = []
    for candidate in raw.split(_RECIPIENT_SEPARATORS[0]):
        address = candidate.strip()
        if not address:
            continue
        if not _looks_like_address(address):
            raise EmailConfigError(f"{name} contains an invalid address: {address!r}")
        if address not in recipients:
            recipients.append(address)

    if not recipients:
        raise EmailConfigError(f"{name} must contain at least one email address")
    return tuple(recipients)


def _resolve_security(values: Mapping[str, str], port: int) -> SmtpSecurity:
    raw = (values.get("SMTP_SECURITY") or "").strip().lower()
    if not raw:
        return SmtpSecurity.SSL if port == 465 else SmtpSecurity.STARTTLS
    try:
        return SmtpSecurity(raw)
    except ValueError as error:
        allowed = ", ".join(item.value for item in SmtpSecurity)
        raise EmailConfigError(
            f"SMTP_SECURITY must be one of {allowed}; got {raw!r}"
        ) from error


def _looks_like_address(value: str) -> bool:
    """Accept a single ``local@domain.tld`` address without spaces or extra @."""
    if value != value.strip() or any(character.isspace() for character in value):
        return False
    local, separator, domain = value.partition("@")
    if not separator or not local or "@" in domain:
        return False
    labels = domain.split(".")
    return len(labels) >= 2 and all(label for label in labels)
