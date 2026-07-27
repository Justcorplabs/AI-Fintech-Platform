import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.exceptions import AppException
from app.schemas.common import ErrorBody, ErrorResponse


logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


STATUS_CODE_ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "PERMISSION_DENIED",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "FILE_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


STATUS_CODE_MESSAGES: dict[int, str] = {
    400: "The request could not be processed.",
    401: "Authentication is required.",
    403: "You do not have permission to perform this action.",
    404: "The requested resource was not found.",
    405: "The requested HTTP method is not allowed.",
    409: "The request conflicts with the current resource state.",
    413: "The request body is too large.",
    415: "The request uses an unsupported media type.",
    422: "The request contains invalid data.",
    429: "Too many requests. Try again later.",
    500: "An unexpected server error occurred.",
    502: "An upstream service returned an invalid response.",
    503: "The service is temporarily unavailable.",
}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assign a request identifier to every HTTP request.

    A client-supplied request ID is preserved when present.
    Otherwise, a UUID is generated.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        request_id = (
            request.headers.get(
                REQUEST_ID_HEADER
            )
            or str(uuid4())
        )

        request.state.request_id = request_id

        response = await call_next(
            request
        )

        response.headers[
            REQUEST_ID_HEADER
        ] = request_id

        return response


def get_request_id(
    request: Request,
) -> str:
    """Retrieve or generate the request identifier."""

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id:
        return str(request_id)

    return str(uuid4())


def create_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build the standard API error response."""

    request_id = get_request_id(
        request
    )

    response_headers = dict(
        headers or {}
    )

    response_headers[
        REQUEST_ID_HEADER
    ] = request_id

    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=request_id,
            details=details,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(
            mode="json"
        ),
        headers=response_headers,
    )


async def app_exception_handler(
    request: Request,
    exception: AppException,
) -> JSONResponse:
    """Handle controlled application exceptions."""

    return create_error_response(
        request=request,
        status_code=exception.status_code,
        code=exception.code,
        message=exception.message,
        details=exception.details,
        headers=exception.headers,
    )


async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI and Starlette HTTP exceptions."""

    status_code = exception.status_code

    code = STATUS_CODE_ERROR_CODES.get(
        status_code,
        "HTTP_ERROR",
    )

    details: Any | None = None

    if isinstance(
        exception.detail,
        str,
    ):
        message = exception.detail

    else:
        message = STATUS_CODE_MESSAGES.get(
            status_code,
            "The request could not be completed.",
        )
        details = exception.detail

    headers = dict(
        exception.headers or {}
    )

    return create_error_response(
        request=request,
        status_code=status_code,
        code=code,
        message=message,
        details=details,
        headers=headers,
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic and request-validation errors without
    returning potentially sensitive raw input values.
    """

    validation_details: list[
        dict[str, str]
    ] = []

    for error in exception.errors():
        location = ".".join(
            str(item)
            for item in error.get(
                "loc",
                ()
            )
        )

        validation_details.append(
            {
                "field": location,
                "message": error.get(
                    "msg",
                    "Invalid value.",
                ),
                "type": error.get(
                    "type",
                    "validation_error",
                ),
            }
        )

    return create_error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message=(
            "The request contains invalid data."
        ),
        details=validation_details,
    )


async def rate_limit_exception_handler(
    request: Request,
    exception: RateLimitExceeded,
) -> JSONResponse:
    """Handle SlowAPI rate-limit errors."""

    detail = getattr(
        exception,
        "detail",
        None,
    )

    message = (
        str(detail)
        if detail
        else "Too many requests. Try again later."
    )

    return create_error_response(
        request=request,
        status_code=429,
        code="RATE_LIMIT_EXCEEDED",
        message=message,
    )


async def database_exception_handler(
    request: Request,
    exception: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle unexpected database errors without exposing
    SQL statements or database credentials.
    """

    request_id = get_request_id(
        request
    )

    logger.exception(
        "Database error. request_id=%s",
        request_id,
        exc_info=exception,
    )

    return create_error_response(
        request=request,
        status_code=503,
        code="DATABASE_UNAVAILABLE",
        message=(
            "The database service is temporarily unavailable."
        ),
    )


async def unexpected_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions without exposing internal
    stack traces to API clients.
    """

    request_id = get_request_id(
        request
    )

    logger.exception(
        "Unhandled application error. request_id=%s",
        request_id,
        exc_info=exception,
    )

    return create_error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message=(
            "An unexpected server error occurred."
        ),
    )


def register_error_handlers(
    app: FastAPI,
) -> None:
    """Register request-ID middleware and error handlers."""

    app.add_middleware(
        RequestIDMiddleware
    )

    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        RateLimitExceeded,
        rate_limit_exception_handler,
    )

    app.add_exception_handler(
        SQLAlchemyError,
        database_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )