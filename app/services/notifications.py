import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("smartdesk.notifications")


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    reply_to: Optional[str] = None


def send_email(message: EmailMessage) -> None:
    """Placeholder email sender. Replace with real SMTP or provider integration."""
    logger.info("Sending email to %s with subject %s", message.to, message.subject)
    logger.debug("Email body: %s", message.body)


def send_verification_email(*, email: str, token: str) -> None:
    verification_link = f"https://smartdesk.local/auth/verify?token={token}"
    body = (
        "Welcome to SmartDesk!\n\n"
        "Please confirm your email address to activate your account by visiting: "
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    send_email(
        EmailMessage(
            to=email,
            subject="Verify your SmartDesk account",
            body=body,
        )
    )
