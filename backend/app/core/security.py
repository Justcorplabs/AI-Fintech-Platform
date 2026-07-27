import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.core.config import settings


pwd_context = CryptContext(
    schemes=[
        "bcrypt_sha256",
        "bcrypt",
    ],
    deprecated="auto",
)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return pwd_context.verify(
            plain_password,
            hashed_password,
        )
    except (UnknownHashError, ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)

    expiry_duration = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    expire = now + expiry_duration

    payload = data.copy()
    payload.update(
        {
            "iat": now,
            "nbf": now,
            "exp": expire,
            "jti": str(uuid4()),
            "token_type": "access",
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)

    expiry_duration = expires_delta or timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    expire = now + expiry_duration

    payload = data.copy()
    payload.update(
        {
            "iat": now,
            "nbf": now,
            "exp": expire,
            "jti": str(uuid4()),
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
        },
    )

    if payload.get("token_type") != "access":
        raise JWTError("Invalid token type.")

    if not payload.get("sub"):
        raise JWTError("Token subject is missing.")

    if not payload.get("jti"):
        raise JWTError("Token identifier is missing.")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
        },
    )

    if payload.get("token_type") != "refresh":
        raise JWTError("Invalid token type.")

    if not payload.get("sub"):
        raise JWTError("Token subject is missing.")

    if not payload.get("jti"):
        raise JWTError("Token identifier is missing.")

    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Backwards-compatible access-token helper.

    Authentication dependencies should use decode_access_token()
    so invalid tokens raise a proper authentication error.
    """
    try:
        return decode_access_token(token)
    except JWTError:
        return None