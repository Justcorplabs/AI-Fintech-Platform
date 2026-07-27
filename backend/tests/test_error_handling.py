import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.error_handlers import register_error_handlers
from app.core.exceptions import (
    ConflictError,
    ResourceNotFoundError,
)


class InputPayload(BaseModel):
    name: str
    amount: float


@pytest.fixture
def error_client():
    app = FastAPI()

    register_error_handlers(app)

    @app.get("/not-found")
    def not_found():
        raise ResourceNotFoundError(
            "Test resource was not found."
        )

    @app.get("/conflict")
    def conflict():
        raise ConflictError(
            "Test resource already exists.",
            details={
                "field": "email",
            },
        )

    @app.get("/forbidden")
    def forbidden():
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to perform this action."
            ),
        )

    @app.post("/validation")
    def validation(
        payload: InputPayload,
    ):
        return payload

    @app.get("/unexpected")
    def unexpected():
        raise RuntimeError(
            "Internal test failure"
        )

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        yield client


def test_controlled_not_found_error(
    error_client,
):
    request_id = "test-not-found-id"

    response = error_client.get(
        "/not-found",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 404

    assert response.headers[
        "X-Request-ID"
    ] == request_id

    assert response.json() == {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": (
                "Test resource was not found."
            ),
            "request_id": request_id,
            "details": None,
        }
    }


def test_controlled_conflict_error(
    error_client,
):
    response = error_client.get(
        "/conflict"
    )

    body = response.json()

    assert response.status_code == 409
    assert body["error"]["code"] == "CONFLICT"

    assert body["error"]["message"] == (
        "Test resource already exists."
    )

    assert body["error"]["details"] == {
        "field": "email",
    }

    assert body["error"]["request_id"]


def test_http_exception_is_standardized(
    error_client,
):
    response = error_client.get(
        "/forbidden"
    )

    body = response.json()

    assert response.status_code == 403

    assert body["error"]["code"] == (
        "PERMISSION_DENIED"
    )

    assert body["error"]["message"] == (
        "You do not have permission "
        "to perform this action."
    )

    assert body["error"]["request_id"]


def test_missing_route_is_standardized(
    error_client,
):
    response = error_client.get(
        "/route-that-does-not-exist"
    )

    body = response.json()

    assert response.status_code == 404

    assert body["error"]["code"] == (
        "RESOURCE_NOT_FOUND"
    )

    assert body["error"]["message"] == (
        "Not Found"
    )

    assert body["error"]["request_id"]


def test_validation_error_is_standardized(
    error_client,
):
    response = error_client.post(
        "/validation",
        json={
            "name": 200,
            "amount": "invalid-number",
        },
    )

    body = response.json()

    assert response.status_code == 422

    assert body["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    assert body["error"]["message"] == (
        "The request contains invalid data."
    )

    details = body["error"]["details"]

    assert isinstance(
        details,
        list,
    )

    assert details

    assert all(
        "field" in error
        and "message" in error
        and "type" in error
        for error in details
    )


def test_unexpected_error_hides_internal_details(
    error_client,
):
    response = error_client.get(
        "/unexpected"
    )

    body = response.json()

    assert response.status_code == 500

    assert body["error"]["code"] == (
        "INTERNAL_SERVER_ERROR"
    )

    assert body["error"]["message"] == (
        "An unexpected server error occurred."
    )

    assert (
        "Internal test failure"
        not in response.text
    )


def test_generated_request_id_is_returned(
    error_client,
):
    response = error_client.get(
        "/not-found"
    )

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id

    assert (
        response.json()["error"][
            "request_id"
        ]
        == request_id
    )