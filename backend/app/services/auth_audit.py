from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.auth_audit_log import AuthAuditLog


def get_client_ip(request: Request | None) -> str | None:
    """
    Return the most appropriate client IP address.

    X-Forwarded-For is checked first because production
    applications are commonly placed behind a trusted proxy.
    """
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()[:64]

    real_ip = request.headers.get("x-real-ip")

    if real_ip:
        return real_ip.strip()[:64]

    if request.client is not None:
        return request.client.host[:64]

    return None


def get_user_agent(request: Request | None) -> str | None:
    """
    Return the request user-agent safely.
    """
    if request is None:
        return None

    user_agent = request.headers.get("user-agent")

    if not user_agent:
        return None

    return user_agent[:2000]


def normalise_email(email: str | None) -> str | None:
    """
    Normalise an email address before storing it.
    """
    if email is None:
        return None

    cleaned_email = str(email).strip().lower()

    return cleaned_email[:320] or None


def create_auth_audit_log(
    db: Session,
    *,
    event_type: str,
    success: bool,
    request: Request | None = None,
    user_id: UUID | str | None = None,
    email: str | None = None,
    status_code: int | None = None,
    detail: str | None = None,
) -> AuthAuditLog:
    """
    Add an authentication event to the current transaction.

    This function does not commit. The calling route controls
    whether the authentication change and audit record are
    committed together.
    """
    audit_log = AuthAuditLog(
        user_id=user_id,
        email=normalise_email(email),
        event_type=event_type.strip().lower()[:100],
        success=success,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        status_code=status_code,
        detail=detail[:4000] if detail else None,
    )

    db.add(audit_log)

    return audit_log


def create_user_auth_audit_log(
    db: Session,
    *,
    event_type: str,
    success: bool,
    user: Any,
    request: Request | None = None,
    status_code: int | None = None,
    detail: str | None = None,
) -> AuthAuditLog:
    """
    Create an audit record using a User-like object.
    """
    return create_auth_audit_log(
        db=db,
        event_type=event_type,
        success=success,
        request=request,
        user_id=getattr(user, "id", None),
        email=getattr(user, "email", None),
        status_code=status_code,
        detail=detail,
    )