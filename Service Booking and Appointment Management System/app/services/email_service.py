from __future__ import annotations
from email.message import EmailMessage
import smtplib
from app.config import settings


class EmailService:
    sent_messages: list[dict[str, str]] = []

    @classmethod
    def send_email(cls, to_email: str, subject: str, body: str) -> dict[str, str]:
        message = {"to": to_email, "subject": subject, "body": body}
        cls.sent_messages.append(message)

        if settings.smtp_host:
            email_message = EmailMessage()
            email_message["Subject"] = subject
            email_message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            email_message["To"] = to_email
            email_message.set_content(body)

            try:
                if settings.smtp_use_tls:
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                        smtp.starttls()
                        if settings.smtp_username and settings.smtp_password:
                            smtp.login(settings.smtp_username, settings.smtp_password)
                        smtp.send_message(email_message)
                else:
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                        if settings.smtp_username and settings.smtp_password:
                            smtp.login(settings.smtp_username, settings.smtp_password)
                        smtp.send_message(email_message)
            except Exception as exc:
                # Keep the in-memory record for diagnostics, but propagate the failure so callers know the send failed.
                raise RuntimeError(f"Failed to send email to {to_email}: {exc}") from exc

        return message

    @classmethod
    def clear_sent_messages(cls) -> None:
        cls.sent_messages.clear()
