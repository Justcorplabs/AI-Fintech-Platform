from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy import (
    func,
    or_,
    select,
    update,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    require_permission,
)
from app.core.permissions import Permission
from app.db.database import get_db
from app.models.auth_audit_log import (
    AuthAuditLog,
)
from app.models.refresh_token import (
    RefreshToken,
)
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminUserActionResponse,
    AdminUserOut,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    AuthAuditLogOut,
)
from app.services.auth_audit import (
    create_auth_audit_log,
)


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


users_read_access = require_permission(
    Permission.USERS_READ
)

users_write_access = require_permission(
    Permission.USERS_WRITE
)

audit_read_access = require_permission(
    Permission.AUDIT_READ
)


def get_role_value(
    user: User,
) -> str:
    return (
        user.role.value
        if isinstance(user.role, UserRole)
        else str(user.role)
    )


def get_active_admin_count(
    db: Session,
) -> int:
    count = db.scalar(
        select(
            func.count(User.id)
        ).where(
            User.role == UserRole.admin,
            User.is_active.is_(True),
        )
    )

    return int(count or 0)


def revoke_active_refresh_tokens(
    db: Session,
    user_id: UUID,
    revoked_at: datetime,
) -> int:
    result = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id
            == user_id,
            RefreshToken.revoked_at.is_(
                None
            ),
        )
        .values(
            revoked_at=revoked_at
        )
    )

    return result.rowcount or 0


def get_user_for_update(
    db: Session,
    user_id: UUID,
) -> User:
    user = db.scalar(
        select(User)
        .where(
            User.id == user_id
        )
        .with_for_update()
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="User not found.",
        )

    return user


def ensure_not_self_management(
    current_user: User,
    target_user: User,
    action: str,
) -> None:
    if current_user.id == target_user.id:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                f"Administrators cannot "
                f"{action} their own account."
            ),
        )


def ensure_not_last_active_admin(
    db: Session,
    target_user: User,
) -> None:
    target_role = get_role_value(
        target_user
    )

    if (
        target_role == UserRole.admin.value
        and target_user.is_active
        and get_active_admin_count(db) <= 1
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "This action cannot be completed "
                "because it would remove the last "
                "active administrator."
            ),
        )


@router.get(
    "/users",
    response_model=list[AdminUserOut],
)
def get_users(
    role: UserRole | None = Query(
        default=None
    ),
    is_active: bool | None = Query(
        default=None
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        users_read_access
    ),
):
    query = select(User)

    if role is not None:
        query = query.where(
            User.role == role
        )

    if is_active is not None:
        query = query.where(
            User.is_active == is_active
        )

    if search:
        cleaned_search = (
            search.strip()
        )

        search_pattern = (
            f"%{cleaned_search}%"
        )

        query = query.where(
            or_(
                User.email.ilike(
                    search_pattern
                ),
                User.full_name.ilike(
                    search_pattern
                ),
                User.organisation.ilike(
                    search_pattern
                ),
            )
        )

    query = (
        query.order_by(
            User.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserActionResponse,
)
def update_user_role(
    user_id: UUID,
    payload: AdminUserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        users_write_access
    ),
):
    current_time = datetime.now(
        timezone.utc
    )

    try:
        target_user = (
            get_user_for_update(
                db=db,
                user_id=user_id,
            )
        )

        ensure_not_self_management(
            current_user=current_user,
            target_user=target_user,
            action="change the role of",
        )

        previous_role = get_role_value(
            target_user
        )

        new_role = payload.role.value

        if previous_role == new_role:
            return AdminUserActionResponse(
                message=(
                    "The user already has "
                    f"the {new_role} role."
                ),
                revoked_sessions=0,
                user=target_user,
            )

        if (
            previous_role
            == UserRole.admin.value
            and new_role
            != UserRole.admin.value
        ):
            ensure_not_last_active_admin(
                db=db,
                target_user=target_user,
            )

        target_user.role = payload.role

        revoked_sessions = (
            revoke_active_refresh_tokens(
                db=db,
                user_id=target_user.id,
                revoked_at=current_time,
            )
        )

        create_auth_audit_log(
            db=db,
            event_type=(
                "admin_user_role_updated"
            ),
            success=True,
            request=request,
            user_id=target_user.id,
            email=target_user.email,
            status_code=status.HTTP_200_OK,
            detail=(
                f"Administrator "
                f"{current_user.email} changed "
                f"the user's role from "
                f"{previous_role} to {new_role}. "
                f"Revoked {revoked_sessions} "
                f"active refresh-token "
                f"session(s)."
            ),
        )

        db.commit()
        db.refresh(target_user)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The user role could not "
                "be updated."
            ),
        )

    return AdminUserActionResponse(
        message=(
            f"User role changed to "
            f"{new_role}."
        ),
        revoked_sessions=revoked_sessions,
        user=target_user,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserActionResponse,
)
def update_user_status(
    user_id: UUID,
    payload: AdminUserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        users_write_access
    ),
):
    current_time = datetime.now(
        timezone.utc
    )

    try:
        target_user = (
            get_user_for_update(
                db=db,
                user_id=user_id,
            )
        )

        ensure_not_self_management(
            current_user=current_user,
            target_user=target_user,
            action="change the status of",
        )

        if (
            target_user.is_active
            == payload.is_active
        ):
            status_name = (
                "active"
                if payload.is_active
                else "disabled"
            )

            return AdminUserActionResponse(
                message=(
                    f"The user is already "
                    f"{status_name}."
                ),
                revoked_sessions=0,
                user=target_user,
            )

        if (
            target_user.is_active
            and not payload.is_active
        ):
            ensure_not_last_active_admin(
                db=db,
                target_user=target_user,
            )

        target_user.is_active = (
            payload.is_active
        )

        revoked_sessions = 0

        if not payload.is_active:
            revoked_sessions = (
                revoke_active_refresh_tokens(
                    db=db,
                    user_id=target_user.id,
                    revoked_at=current_time,
                )
            )

        else:
            target_user.failed_login_attempts = 0
            target_user.locked_until = None

        new_status = (
            "active"
            if payload.is_active
            else "disabled"
        )

        create_auth_audit_log(
            db=db,
            event_type=(
                "admin_user_status_updated"
            ),
            success=True,
            request=request,
            user_id=target_user.id,
            email=target_user.email,
            status_code=status.HTTP_200_OK,
            detail=(
                f"Administrator "
                f"{current_user.email} changed "
                f"the user's account status "
                f"to {new_status}. "
                f"Revoked {revoked_sessions} "
                f"active refresh-token "
                f"session(s)."
            ),
        )

        db.commit()
        db.refresh(target_user)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The user account status "
                "could not be updated."
            ),
        )

    return AdminUserActionResponse(
        message=(
            f"User account is now "
            f"{new_status}."
        ),
        revoked_sessions=revoked_sessions,
        user=target_user,
    )


@router.get(
    "/audit-logs",
    response_model=list[AuthAuditLogOut],
)
def get_auth_audit_logs(
    event_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    success: bool | None = Query(
        default=None
    ),
    email: str | None = Query(
        default=None,
        min_length=1,
        max_length=320,
    ),
    user_id: UUID | None = Query(
        default=None
    ),
    ip_address: str | None = Query(
        default=None,
        min_length=1,
        max_length=64,
    ),
    created_after: datetime | None = Query(
        default=None
    ),
    created_before: datetime | None = Query(
        default=None
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        audit_read_access
    ),
):
    query = select(
        AuthAuditLog
    )

    if event_type:
        query = query.where(
            AuthAuditLog.event_type
            == event_type.strip().lower()
        )

    if success is not None:
        query = query.where(
            AuthAuditLog.success
            == success
        )

    if email:
        email_pattern = (
            f"%{email.strip().lower()}%"
        )

        query = query.where(
            AuthAuditLog.email.ilike(
                email_pattern
            )
        )

    if user_id is not None:
        query = query.where(
            AuthAuditLog.user_id
            == user_id
        )

    if ip_address:
        query = query.where(
            AuthAuditLog.ip_address
            == ip_address.strip()
        )

    if created_after is not None:
        query = query.where(
            AuthAuditLog.created_at
            >= created_after
        )

    if created_before is not None:
        query = query.where(
            AuthAuditLog.created_at
            <= created_before
        )

    query = (
        query.order_by(
            AuthAuditLog.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )