import hashlib
import logging
from typing import Final

from fastapi import Request
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import decode_access_token


logger = logging.getLogger(__name__)


AUTH_LOGIN_LIMIT: Final[str] = "5/minute"
AUTH_REGISTER_LIMIT: Final[str] = "3/minute"
AUTH_REFRESH_LIMIT: Final[str] = "10/minute"
AUTH_FORGOT_PASSWORD_LIMIT: Final[str] = "3/15minutes"
AUTH_RESET_PASSWORD_LIMIT: Final[str] = "5/15minutes"

FRAUD_PREDICTION_LIMIT: Final[str] = "60/minute"

RESUME_AI_LIMIT: Final[str] = "30/minute"
CANDIDATE_SCORING_LIMIT: Final[str] = "20/minute"


def client_ip_key(request: Request) -> str:
    """
    Generate an IP-based rate-limit key.

    In production, configure Uvicorn to trust proxy headers
    only from known reverse proxies.
    """
    client_ip = get_remote_address(request)
    return f"ip:{client_ip}"


def authenticated_user_key(request: Request) -> str:
    """
    Generate a stable per-user rate-limit key from an access token.

    Invalid or missing access tokens fall back to the client IP.
    Authentication dependencies remain responsible for rejecting
    invalid credentials.
    """
    authorization = request.headers.get(
        "Authorization",
        "",
    )

    scheme, separator, token = authorization.partition(" ")

    if (
        separator
        and scheme.lower() == "bearer"
        and token.strip()
    ):
        try:
            payload = decode_access_token(token.strip())

            user_id = str(
                payload.get("sub", "")
            ).strip()

            if user_id:
                return f"user:{user_id}"

        except (
            JWTError,
            ValueError,
            TypeError,
            KeyError,
        ):
            logger.debug(
                "Rate-limit key fell back to IP because "
                "the access token could not be decoded."
            )

    return client_ip_key(request)


def anonymous_token_key(request: Request) -> str:
    """
    Generate an anonymous key without retaining raw credentials.

    This can be used for endpoints limited by an authorization
    header rather than an authenticated user.
    """
    authorization = request.headers.get(
        "Authorization",
        "",
    ).strip()

    if authorization:
        token_digest = hashlib.sha256(
            authorization.encode("utf-8")
        ).hexdigest()

        return f"token:{token_digest}"

    return client_ip_key(request)


limiter = Limiter(
    key_func=client_ip_key,
    headers_enabled=True,
    strategy="fixed-window",
    storage_uri="memory://",
    key_prefix="sentinel-ai",
)