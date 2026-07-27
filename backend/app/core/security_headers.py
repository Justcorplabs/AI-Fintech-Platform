from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add defensive HTTP security headers to every API response.

    These headers help reduce risks related to:
    - MIME-type sniffing
    - Clickjacking
    - Referrer information leakage
    - Unnecessary browser permissions
    - Unsafe content loading
    - Insecure cross-origin resource handling
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = (
            "nosniff"
        )

        response.headers["X-Frame-Options"] = (
            "DENY"
        )

        response.headers["Referrer-Policy"] = (
            "strict-origin-when-cross-origin"
        )

        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        response.headers[
            "Cross-Origin-Opener-Policy"
        ] = "same-origin"

        response.headers[
            "Cross-Origin-Resource-Policy"
        ] = "same-site"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "connect-src 'self' http: https: ws: wss:"
        )

        if request.url.scheme == "https":
            response.headers[
                "Strict-Transport-Security"
            ] = (
                "max-age=31536000; "
                "includeSubDomains"
            )

        if "Server" in response.headers:
            del response.headers["Server"]

        return response