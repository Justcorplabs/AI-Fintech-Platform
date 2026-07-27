from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.admin import (
    ensure_not_last_active_admin,
    ensure_not_self_management,
)
from app.core.permissions import Permission
from app.models.user import UserRole
from tests.conftest import (
    get_route_permissions,
)


ADMIN_ROUTE_PERMISSIONS = [
    (
        "GET",
        "/api/v1/admin/users",
        Permission.USERS_READ,
    ),
    (
        "PATCH",
        (
            "/api/v1/admin/users/"
            "{user_id}/role"
        ),
        Permission.USERS_WRITE,
    ),
    (
        "PATCH",
        (
            "/api/v1/admin/users/"
            "{user_id}/status"
        ),
        Permission.USERS_WRITE,
    ),
    (
        "GET",
        "/api/v1/admin/audit-logs",
        Permission.AUDIT_READ,
    ),
]


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "expected_permission",
    ),
    ADMIN_ROUTE_PERMISSIONS,
)
def test_admin_routes_use_expected_permissions(
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
    "permission",
    [
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.AUDIT_READ,
    ],
)
def test_admin_has_administration_permissions(
    permission_client_factory,
    permission,
):
    client = (
        permission_client_factory(
            permission,
            role=UserRole.admin,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role",
    [
        UserRole.analyst,
        UserRole.recruiter,
        UserRole.viewer,
    ],
)
@pytest.mark.parametrize(
    "permission",
    [
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.AUDIT_READ,
    ],
)
def test_non_admin_roles_are_denied(
    permission_client_factory,
    role,
    permission,
):
    client = (
        permission_client_factory(
            permission,
            role=role,
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
    "permission",
    [
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.AUDIT_READ,
    ],
)
def test_admin_permissions_require_authentication(
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


def test_admin_cannot_change_own_role():
    administrator_id = uuid4()

    current_user = SimpleNamespace(
        id=administrator_id,
        role=UserRole.admin,
    )

    target_user = SimpleNamespace(
        id=administrator_id,
        role=UserRole.admin,
    )

    with pytest.raises(
        HTTPException
    ) as error:
        ensure_not_self_management(
            current_user=current_user,
            target_user=target_user,
            action="change the role of",
        )

    assert (
        error.value.status_code
        == 400
    )

    assert error.value.detail == (
        "Administrators cannot change "
        "the role of their own account."
    )


def test_admin_cannot_disable_own_account():
    administrator_id = uuid4()

    current_user = SimpleNamespace(
        id=administrator_id,
        role=UserRole.admin,
    )

    target_user = SimpleNamespace(
        id=administrator_id,
        role=UserRole.admin,
    )

    with pytest.raises(
        HTTPException
    ) as error:
        ensure_not_self_management(
            current_user=current_user,
            target_user=target_user,
            action="change the status of",
        )

    assert (
        error.value.status_code
        == 400
    )

    assert error.value.detail == (
        "Administrators cannot change "
        "the status of their own account."
    )


def test_last_active_admin_is_protected():
    class FakeSession:
        def scalar(
            self,
            statement,
        ):
            return 1

    target_user = SimpleNamespace(
        id=uuid4(),
        role=UserRole.admin,
        is_active=True,
    )

    with pytest.raises(
        HTTPException
    ) as error:
        ensure_not_last_active_admin(
            db=FakeSession(),
            target_user=target_user,
        )

    assert (
        error.value.status_code
        == 409
    )

    assert error.value.detail == (
        "This action cannot be completed "
        "because it would remove the last "
        "active administrator."
    )


def test_admin_change_allowed_when_another_admin_exists():
    class FakeSession:
        def scalar(
            self,
            statement,
        ):
            return 2

    target_user = SimpleNamespace(
        id=uuid4(),
        role=UserRole.admin,
        is_active=True,
    )

    # The function should return normally when two
    # or more active administrators exist.
    ensure_not_last_active_admin(
        db=FakeSession(),
        target_user=target_user,
    )