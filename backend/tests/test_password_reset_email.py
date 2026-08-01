import smtplib
from pathlib import Path

import pytest

from app.core.config import settings
from app.services.email import (
    password_reset,
)
from app.services.email.password_reset import (
    PasswordResetEmailError,
    build_password_reset_message,
    send_password_reset_email,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)


def configure_test_smtp(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "SMTP_HOST",
        "smtp.example.test",
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PORT",
        587,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_USERNAME",
        "smtp-user",
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PASSWORD",
        "smtp-password",
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_EMAIL",
        "no-reply@example.test",
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_NAME",
        "JustCorp Talent AI",
    )

    monkeypatch.setattr(
        settings,
        "SMTP_USE_TLS",
        True,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_TIMEOUT_SECONDS",
        15,
    )


def test_build_password_reset_message():
    message = build_password_reset_message(
        recipient_email=(
            "candidate@example.test"
        ),
        recipient_name="Test Candidate",
        reset_url=(
            "https://example.test/"
            "reset-password?token=secure-token"
        ),
        expires_minutes=30,
    )

    assert (
        message["To"]
        == "candidate@example.test"
    )

    assert (
        "Reset your JustCorp Talent AI "
        "password"
        in message["Subject"]
    )

    plain_text = message.get_body(
        preferencelist=("plain",)
    ).get_content()

    assert "Test Candidate" in plain_text
    assert "secure-token" in plain_text
    assert "30 minutes" in plain_text


def test_send_password_reset_email_uses_tls_and_auth(
    monkeypatch,
):
    configure_test_smtp(monkeypatch)

    captured = {}

    class FakeSMTP:
        def __init__(
            self,
            host,
            port,
            timeout,
        ):
            captured["host"] = host
            captured["port"] = port
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

        def ehlo(self):
            captured["ehlo"] = (
                captured.get("ehlo", 0)
                + 1
            )

        def starttls(self, context):
            captured["tls"] = (
                context is not None
            )

        def login(
            self,
            username,
            password,
        ):
            captured["login"] = (
                username,
                password,
            )

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(
        password_reset.smtplib,
        "SMTP",
        FakeSMTP,
    )

    send_password_reset_email(
        recipient_email=(
            "candidate@example.test"
        ),
        recipient_name="Test Candidate",
        reset_url=(
            "https://example.test/"
            "reset-password?token=secure-token"
        ),
        expires_minutes=30,
    )

    assert (
        captured["host"]
        == "smtp.example.test"
    )

    assert captured["port"] == 587
    assert captured["timeout"] == 15
    assert captured["tls"] is True

    assert captured["login"] == (
        "smtp-user",
        "smtp-password",
    )

    assert (
        captured["message"]["To"]
        == "candidate@example.test"
    )


def test_email_delivery_errors_are_wrapped(
    monkeypatch,
):
    configure_test_smtp(monkeypatch)

    class FailingSMTP:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            raise smtplib.SMTPException(
                "SMTP unavailable"
            )

    monkeypatch.setattr(
        password_reset.smtplib,
        "SMTP",
        FailingSMTP,
    )

    with pytest.raises(
        PasswordResetEmailError
    ):
        send_password_reset_email(
            recipient_email=(
                "candidate@example.test"
            ),
            recipient_name=None,
            reset_url=(
                "https://example.test/"
                "reset-password?token=token"
            ),
            expires_minutes=30,
        )


def test_auth_route_uses_email_delivery():
    source = (
        PROJECT_ROOT
        / "backend"
        / "app"
        / "api"
        / "routes"
        / "auth.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "PASSWORD_RESET_EMAIL_ENABLED"
        in source
    )

    assert (
        "send_password_reset_email"
        in source
    )

    assert (
        "PasswordResetEmailError"
        in source
    )


def test_render_reset_url_targets_resume_frontend():
    source = (
        PROJECT_ROOT
        / "render.yaml"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "https://justcorplabs-resume-"
        "intelligence.vercel.app"
        in source
    )

    assert (
        "PASSWORD_RESET_EMAIL_ENABLED"
        in source
    )
