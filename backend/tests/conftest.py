from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_current_user,
    require_permission,
)
from app.core.permissions import Permission
from app.db.database import get_db
from app.models.user import UserRole


@pytest.fixture
def user_factory():
    """
    Create lightweight authenticated-user objects without
    inserting records into the database.
    """

    def create_user(
        role: UserRole,
        *,
        is_active: bool = True,
    ):
        return SimpleNamespace(
            id=uuid4(),
            email=f"{role.value}@test.com",
            full_name=f"Test {role.value.title()}",
            role=role,
            is_active=is_active,
            organisation="JustCorp Test",
        )

    return create_user


@pytest.fixture
def permission_client_factory(
    user_factory,
):
    """
    Build a minimal FastAPI application protected by the
    real require_permission dependency.

    This verifies 200, 401, and 403 permission behaviour
    without calling PostgreSQL, fraud models, or AI services.
    """

    clients: list[TestClient] = []

    def create_client(
        permission: Permission,
        *,
        role: UserRole | None = None,
        authenticated: bool = True,
    ) -> TestClient:
        test_app = FastAPI()

        permission_dependency = (
            require_permission(permission)
        )

        @test_app.get("/probe")
        def permission_probe(
            current_user=Depends(
                permission_dependency
            ),
        ):
            role_value = (
                current_user.role.value
                if isinstance(
                    current_user.role,
                    UserRole,
                )
                else str(current_user.role)
            )

            return {
                "authenticated": True,
                "role": role_value,
                "permission": permission.value,
            }

        # Prevent unauthenticated tests from creating
        # a real database session.
        test_app.dependency_overrides[
            get_db
        ] = lambda: None

        if authenticated:
            if role is None:
                raise ValueError(
                    "A role is required for "
                    "authenticated test clients."
                )

            test_user = user_factory(
                role
            )

            test_app.dependency_overrides[
                get_current_user
            ] = lambda: test_user

        client = TestClient(
            test_app
        )

        clients.append(client)

        return client

    yield create_client

    for client in clients:
        client.close()


def _normalise_path(
    path: str,
) -> str:
    """
    Normalise route paths for reliable comparison.
    """
    cleaned = "/" + str(path).strip("/")

    return (
        "/"
        if cleaned == "/"
        else cleaned
    )


def _route_candidate_paths(
    route: APIRoute,
) -> set[str]:
    """
    Return every path representation available on a
    FastAPI route.
    """
    candidates: set[str] = set()

    for attribute in (
        "path",
        "path_format",
    ):
        value = getattr(
            route,
            attribute,
            None,
        )

        if value:
            candidates.add(
                _normalise_path(value)
            )

    return candidates


def _permissions_from_callable(
    dependency_callable,
) -> set[Permission]:
    """
    Extract Permission values captured by the closure
    created by require_permission().
    """
    permissions: set[Permission] = set()

    closure = getattr(
        dependency_callable,
        "__closure__",
        None,
    )

    if not closure:
        return permissions

    for cell in closure:
        try:
            value = cell.cell_contents

        except ValueError:
            continue

        if isinstance(
            value,
            Permission,
        ):
            permissions.add(value)

    return permissions


def _walk_dependencies(
    dependency,
) -> set[Permission]:
    """
    Recursively inspect a FastAPI dependency tree.
    """
    permissions = (
        _permissions_from_callable(
            dependency.call
        )
    )

    for child_dependency in (
        dependency.dependencies
    ):
        permissions.update(
            _walk_dependencies(
                child_dependency
            )
        )

    return permissions


def _extract_route_permissions(
    route: APIRoute,
) -> set[Permission]:
    """
    Extract every Permission dependency attached to a route.
    """
    permissions: set[Permission] = set()

    for dependency in (
        route.dependant.dependencies
    ):
        permissions.update(
            _walk_dependencies(
                dependency
            )
        )

    return permissions


def _route_matches(
    route: APIRoute,
    expected_path: str,
    requested_method: str,
) -> bool:
    """
    Match either a fully registered application path or a
    source-router path without the /api/v1 prefix.
    """
    if (
        requested_method
        not in route.methods
    ):
        return False

    full_path = _normalise_path(
        expected_path
    )

    local_path = full_path

    if full_path.startswith(
        "/api/v1/"
    ):
        local_path = _normalise_path(
            full_path.removeprefix(
                "/api/v1"
            )
        )

    expected_paths = {
        full_path,
        local_path,
    }

    return bool(
        _route_candidate_paths(route)
        & expected_paths
    )


def _verify_openapi_registration(
    path: str,
    method: str,
) -> None:
    """
    Confirm that the route is actually registered on the
    main FastAPI application.
    """
    from app.main import app

    normalised_path = _normalise_path(
        path
    )

    openapi_schema = app.openapi()

    registered_paths = (
        openapi_schema.get(
            "paths",
            {},
        )
    )

    path_definition = (
        registered_paths.get(
            normalised_path
        )
    )

    if path_definition is None:
        available_paths = "\n".join(
            sorted(
                registered_paths.keys()
            )
        )

        raise AssertionError(
            f"Route is not registered in OpenAPI: "
            f"{method} {normalised_path}\n\n"
            f"Available paths:\n"
            f"{available_paths}"
        )

    if (
        method.lower()
        not in path_definition
    ):
        available_methods = ", ".join(
            sorted(
                path_definition.keys()
            )
        )

        raise AssertionError(
            f"Method {method} is not registered "
            f"for {normalised_path}. "
            f"Available methods: "
            f"{available_methods}"
        )


def _project_source_routes():
    """
    Yield routes directly from each project router.

    This provides a stable fallback when a FastAPI version
    represents included application routes differently.
    """
    from app.api.routes import (
        admin,
        auth,
        fraud,
        recruitment,
    )

    project_routers = (
        auth.router,
        fraud.router,
        recruitment.router,
        admin.router,
    )

    for project_router in (
        project_routers
    ):
        for route in (
            project_router.routes
        ):
            if isinstance(
                route,
                APIRoute,
            ):
                yield route


def get_route_permissions(
    path: str,
    method: str,
) -> set[Permission]:
    """
    Return the Permission values attached to a registered
    application route.

    The function first verifies registration through
    OpenAPI, then examines both the included application
    routes and the original source routers.
    """
    from app.main import app

    requested_method = (
        method.upper()
    )

    normalised_path = (
        _normalise_path(path)
    )

    _verify_openapi_registration(
        path=normalised_path,
        method=requested_method,
    )

    # First inspect routes registered directly on the
    # main FastAPI application.
    for route in app.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        if _route_matches(
            route=route,
            expected_path=normalised_path,
            requested_method=requested_method,
        ):
            return (
                _extract_route_permissions(
                    route
                )
            )

    # Fall back to the original source routers. Their
    # paths normally omit the global /api/v1 prefix.
    for route in (
        _project_source_routes()
    ):
        if _route_matches(
            route=route,
            expected_path=normalised_path,
            requested_method=requested_method,
        ):
            return (
                _extract_route_permissions(
                    route
                )
            )

    raise AssertionError(
        f"Registered route was found in OpenAPI, "
        f"but its dependency route could not be "
        f"resolved: "
        f"{requested_method} {normalised_path}"
    )