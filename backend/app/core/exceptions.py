from typing import Any


class AppException(Exception):
    """
    Base application exception.

    Every controlled application error should inherit from
    this class so the API returns a consistent response.
    """

    def __init__(
        self,
        *,
        message: str,
        status_code: int = 400,
        code: str = "APPLICATION_ERROR",
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers or {}


class BadRequestError(AppException):
    def __init__(
        self,
        message: str = "The request could not be processed.",
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=400,
            code="BAD_REQUEST",
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(
        self,
        message: str = (
            "Authentication credentials could not be validated."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            details=details,
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )


class PermissionDeniedError(AppException):
    def __init__(
        self,
        message: str = (
            "You do not have permission to perform this action."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
            code="PERMISSION_DENIED",
            details=details,
        )


class ResourceNotFoundError(AppException):
    def __init__(
        self,
        message: str = "The requested resource was not found.",
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            details=details,
        )


class ConflictError(AppException):
    def __init__(
        self,
        message: str = (
            "The request conflicts with the current resource state."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=409,
            code="CONFLICT",
            details=details,
        )


class FileTooLargeError(AppException):
    def __init__(
        self,
        message: str = (
            "The uploaded file exceeds the permitted size."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=413,
            code="FILE_TOO_LARGE",
            details=details,
        )


class UnsupportedFileTypeError(AppException):
    def __init__(
        self,
        message: str = (
            "The uploaded file type is not supported."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=415,
            code="UNSUPPORTED_FILE_TYPE",
            details=details,
        )


class ServiceUnavailableError(AppException):
    def __init__(
        self,
        message: str = (
            "A required service is temporarily unavailable."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            code="SERVICE_UNAVAILABLE",
            details=details,
        )


class ModelUnavailableError(AppException):
    def __init__(
        self,
        message: str = (
            "The machine-learning model is currently unavailable."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            code="MODEL_UNAVAILABLE",
            details=details,
        )


class ExternalServiceError(AppException):
    def __init__(
        self,
        message: str = (
            "An external service could not complete the request."
        ),
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=502,
            code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )