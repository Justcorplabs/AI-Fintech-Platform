from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.core.rbac import ROLE_PERMISSIONS
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User, UserRole


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="Bearer authentication",
    description=(
        "Enter the JWT access token returned by the login endpoint."
    ),
)


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials could not be validated.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT access token and return the authenticated user.
    """

    if credentials is None:
        raise credentials_exception()

    if credentials.scheme.lower() != "bearer":
        raise credentials_exception()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))

    except (JWTError, ValueError, TypeError, KeyError):
        raise credentials_exception()

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled.",
        )

    return user


def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    """
    Restrict an endpoint to one or more roles.

    Example:
        Depends(require_roles(UserRole.ADMIN))
    """

    allowed_role_values = {
        role.value
        for role in allowed_roles
    }

    def role_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:

        current_role = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )

        if current_role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action."
                ),
            )

        return current_user

    return role_dependency


def require_permission(
    permission: Permission,
) -> Callable:
    """
    Restrict an endpoint to users whose role contains
    the required permission.

    Example:
        Depends(require_permission(Permission.JOBS_WRITE))
    """

    def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:

        current_role = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role)
        )

        permissions = ROLE_PERMISSIONS.get(
            current_role,
            set(),
        )

        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action."
                ),
            )

        return current_user

    return permission_dependency