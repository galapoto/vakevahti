import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings
from app.services.report_email_delivery import ReportEmailClaim


class SmtpConfigurationError(RuntimeError):
    """Raised when SMTP delivery was enabled without the required configuration."""


def _validate(settings: Settings) -> None:
    if not settings.report_email_from.strip():
        raise SmtpConfigurationError("REPORT_EMAIL_FROM is required for email delivery.")
    if not settings.smtp_host.strip():
        raise SmtpConfigurationError("SMTP_HOST is required for email delivery.")
    if settings.smtp_ssl and settings.smtp_starttls:
        raise SmtpConfigurationError("SMTP_SSL and SMTP_STARTTLS cannot both be enabled.")


def _message(settings: Settings, claim: ReportEmailClaim) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.report_email_from.strip()
    message["To"] = ", ".join(claim.recipient_emails)
    message["Subject"] = claim.subject
    message.set_content(claim.body_text)
    message.add_alternative(claim.body_html, subtype="html")
    return message


def _send_sync(settings: Settings, claim: ReportEmailClaim) -> None:
    _validate(settings)
    message = _message(settings, claim)
    timeout = settings.smtp_timeout_seconds

    if settings.smtp_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=timeout,
            context=context,
        ) as client:
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as client:
        client.ehlo()
        if settings.smtp_starttls:
            context = ssl.create_default_context()
            client.starttls(context=context)
            client.ehlo()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password)
        client.send_message(message)


async def send_report_email(settings: Settings, claim: ReportEmailClaim) -> None:
    """Send a report email without blocking the application's asyncio loop."""

    await asyncio.to_thread(_send_sync, settings, claim)
