from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Standard structure for one API error."""

    code: str = Field(
        ...,
        examples=["RESOURCE_NOT_FOUND"],
    )
    message: str
    request_id: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Standard error response returned by the API."""

    error: ErrorBody


class MessageResponse(BaseModel):
    """Standard response for simple successful operations."""

    message: str