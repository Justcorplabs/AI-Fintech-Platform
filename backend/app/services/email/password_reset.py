import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

from app.core.config import settings


class PasswordResetEmailError(
    RuntimeError
):
    """Raised when reset email delivery fails."""


def build_password_reset_message(
    recipient_email: str,
    recipient_name: str | None,
    reset_url: str,
    expires_minutes: int,
) -> EmailMessage:
    safe_name = escape(
        recipient_name or "there"
    )

    safe_url = escape(
        reset_url,
        quote=True,
    )

    message = EmailMessage()

    message["Subject"] = (
        "Reset your JustCorp Talent AI password"
    )

    message["From"] = formataddr(
        (
            settings.SMTP_FROM_NAME,
            settings.SMTP_FROM_EMAIL,
        )
    )

    message["To"] = recipient_email

    message.set_content(
        f"""Hello {recipient_name or "there"},

A password reset was requested for your
JustCorp Talent AI account.

Use the following secure link to reset your password:

{reset_url}

This link expires in {expires_minutes} minutes
and can only be used once.

If you did not request this reset, you can
ignore this email.

JustCorp Talent AI
"""
    )

    message.add_alternative(
        f"""<!doctype html>
<html lang="en">
  <body style="font-family: Arial, sans-serif; color: #0f172a;">
    <h2>Reset your password</h2>

    <p>Hello {safe_name},</p>

    <p>
      A password reset was requested for your
      JustCorp Talent AI account.
    </p>

    <p>
      <a
        href="{safe_url}"
        style="
          display: inline-block;
          padding: 12px 18px;
          background: #7c3aed;
          color: #ffffff;
          text-decoration: none;
          border-radius: 7px;
          font-weight: 600;
        "
      >
        Reset password
      </a>
    </p>

    <p>
      This link expires in
      {expires_minutes} minutes and can only
      be used once.
    </p>

    <p>
      If you did not request this reset,
      you can ignore this email.
    </p>
  </body>
</html>
""",
        subtype="html",
    )

    return message


def send_password_reset_email(
    recipient_email: str,
    recipient_name: str | None,
    reset_url: str,
    expires_minutes: int,
) -> None:
    message = build_password_reset_message(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        reset_url=reset_url,
        expires_minutes=expires_minutes,
    )

    try:
        with smtplib.SMTP(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=(
                settings
                .SMTP_TIMEOUT_SECONDS
            ),
        ) as smtp:
            smtp.ehlo()

            if settings.SMTP_USE_TLS:
                smtp.starttls(
                    context=(
                        ssl.create_default_context()
                    )
                )

                smtp.ehlo()

            if settings.SMTP_USERNAME:
                smtp.login(
                    settings.SMTP_USERNAME,
                    settings.SMTP_PASSWORD,
                )

            smtp.send_message(message)

    except (
        OSError,
        smtplib.SMTPException,
    ) as exc:
        raise PasswordResetEmailError(
            "Password-reset email delivery failed."
        ) from exc
