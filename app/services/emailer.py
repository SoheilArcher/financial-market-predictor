from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_ready() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def _send_email_sync(to_email: str, subject: str, text: str, html: str | None = None) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to_email
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_email(to_email: str, subject: str, text: str, html: str | None = None) -> bool:
    if not _smtp_ready():
        logger.warning("SMTP is not configured. Email to %s was not sent. Body: %s", to_email, text)
        return False
    await asyncio.to_thread(_send_email_sync, to_email, subject, text, html)
    return True


async def send_verification_email(to_email: str, verify_url: str) -> bool:
    subject = "Verify your Market AI email"
    text = f"Welcome to Market AI.\n\nPlease verify your email:\n{verify_url}\n\nThis link expires soon."
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.7">
      <h2>Market AI email verification</h2>
      <p>Please verify your email address to activate your account.</p>
      <p><a href="{verify_url}">Verify email</a></p>
      <p>If the button does not work, open this link:</p>
      <p>{verify_url}</p>
    </div>
    """
    return await send_email(to_email, subject, text, html)
