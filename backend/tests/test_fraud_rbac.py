import pytest

from app.core.permissions import Permission
from app.models.user import UserRole
from tests.conftest import (
    get_route_permissions,
)


FRAUD_ROUTE_PERMISSIONS = [
    (
        "POST",
        "/api/v1/fraud/predict",
        Permission.FRAUD_ANALYZE,
    ),
    (
        "GET",
        "/api/v1/fraud/transactions",
        Permission.FRAUD_READ,
    ),
    (
        "GET",
        "/api/v1/fraud/model/metadata",
        Permission.FRAUD_READ,
    ),
    (
        "GET",
        (
            "/api/v1/fraud/transactions/"
            "{transaction_id}"
        ),
        Permission.FRAUD_READ,
    ),
    (
        "PATCH",
        (
            "/api/v1/fraud/transactions/"
            "{transaction_id}/review"
        ),
        Permission.FRAUD_ANALYZE,
    ),
    (
        "GET",
        "/api/v1/fraud/stats",
        Permission.FRAUD_READ,
    ),
]


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "expected_permission",
    ),
    FRAUD_ROUTE_PERMISSIONS,
)
def test_fraud_routes_use_expected_permissions(
    method,
    path,
    expected_permission,
):
    permissions = (
        get_route_permissions(
            path,
            method,
        )
    )

    assert permissions == {
        expected_permission
    }


@pytest.mark.parametrize(
    "role",
    [
        UserRole.admin,
        UserRole.analyst,
        UserRole.viewer,
    ],
)
def test_fraud_read_allowed_roles(
    permission_client_factory,
    role,
):
    client = (
        permission_client_factory(
            Permission.FRAUD_READ,
            role=role,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 200

    assert response.json() == {
        "authenticated": True,
        "role": role.value,
        "permission": (
            Permission.FRAUD_READ.value
        ),
    }


def test_recruiter_cannot_read_fraud(
    permission_client_factory,
):
    client = (
        permission_client_factory(
            Permission.FRAUD_READ,
            role=UserRole.recruiter,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "You do not have permission "
            "to perform this action."
        )
    }


@pytest.mark.parametrize(
    "role",
    [
        UserRole.admin,
        UserRole.analyst,
    ],
)
def test_fraud_analysis_allowed_roles(
    permission_client_factory,
    role,
):
    client = (
        permission_client_factory(
            Permission.FRAUD_ANALYZE,
            role=role,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role",
    [
        UserRole.viewer,
        UserRole.recruiter,
    ],
)
def test_fraud_analysis_denied_roles(
    permission_client_factory,
    role,
):
    client = (
        permission_client_factory(
            Permission.FRAUD_ANALYZE,
            role=role,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "permission",
    [
        Permission.FRAUD_READ,
        Permission.FRAUD_ANALYZE,
    ],
)
def test_fraud_permissions_require_authentication(
    permission_client_factory,
    permission,
):
    client = (
        permission_client_factory(
            permission,
            authenticated=False,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Authentication credentials "
            "could not be validated."
        )
    }

    assert (
        response.headers[
            "www-authenticate"
        ]
        == "Bearer"
    )