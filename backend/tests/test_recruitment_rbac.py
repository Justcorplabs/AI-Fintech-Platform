import pytest

from app.core.permissions import Permission
from app.models.user import UserRole
from tests.conftest import (
    get_route_permissions,
)


RECRUITMENT_ROUTE_PERMISSIONS = [
    (
        "POST",
        "/api/v1/recruitment/jobs",
        Permission.JOBS_WRITE,
    ),
    (
        "GET",
        "/api/v1/recruitment/jobs",
        Permission.JOBS_READ,
    ),
    (
        "DELETE",
        (
            "/api/v1/recruitment/jobs/"
            "{job_id}"
        ),
        Permission.JOBS_WRITE,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "review-resume"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "rewrite-cv"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "build-resume"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "download-cv-docx"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "download-application-pack-docx"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "POST",
        (
            "/api/v1/recruitment/"
            "upload-cv/{job_id}"
        ),
        Permission.RECRUITMENT_WRITE,
    ),
    (
        "GET",
        (
            "/api/v1/recruitment/"
            "applications/{job_id}"
        ),
        Permission.RECRUITMENT_READ,
    ),
    (
        "PATCH",
        (
            "/api/v1/recruitment/"
            "applications/"
            "{application_id}/status"
        ),
        Permission.RECRUITMENT_WRITE,
    ),
    (
        "DELETE",
        (
            "/api/v1/recruitment/"
            "applications/"
            "{application_id}"
        ),
        Permission.RECRUITMENT_WRITE,
    ),
    (
        "GET",
        (
            "/api/v1/recruitment/"
            "dashboard"
        ),
        Permission.RECRUITMENT_READ,
    ),
]


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "expected_permission",
    ),
    RECRUITMENT_ROUTE_PERMISSIONS,
)
def test_recruitment_routes_use_expected_permissions(
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
        UserRole.recruiter,
        UserRole.viewer,
    ],
)
@pytest.mark.parametrize(
    "permission",
    [
        Permission.JOBS_READ,
        Permission.RECRUITMENT_READ,
    ],
)
def test_recruitment_read_allowed_roles(
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

    assert response.status_code == 200


@pytest.mark.parametrize(
    "role",
    [
        UserRole.admin,
        UserRole.recruiter,
    ],
)
@pytest.mark.parametrize(
    "permission",
    [
        Permission.JOBS_WRITE,
        Permission.RECRUITMENT_WRITE,
    ],
)
def test_recruitment_write_allowed_roles(
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

    assert response.status_code == 200


@pytest.mark.parametrize(
    "permission",
    [
        Permission.JOBS_READ,
        Permission.JOBS_WRITE,
        Permission.RECRUITMENT_READ,
        Permission.RECRUITMENT_WRITE,
    ],
)
def test_analyst_cannot_access_recruitment(
    permission_client_factory,
    permission,
):
    client = (
        permission_client_factory(
            permission,
            role=UserRole.analyst,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "permission",
    [
        Permission.JOBS_WRITE,
        Permission.RECRUITMENT_WRITE,
    ],
)
def test_viewer_cannot_modify_recruitment(
    permission_client_factory,
    permission,
):
    client = (
        permission_client_factory(
            permission,
            role=UserRole.viewer,
        )
    )

    response = client.get(
        "/probe"
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "permission",
    [
        Permission.JOBS_READ,
        Permission.JOBS_WRITE,
        Permission.RECRUITMENT_READ,
        Permission.RECRUITMENT_WRITE,
    ],
)
def test_recruitment_permissions_require_authentication(
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