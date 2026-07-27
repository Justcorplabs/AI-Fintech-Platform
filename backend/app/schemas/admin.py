from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
)

from app.models.user import UserRole


class AdminUserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    organisation: str | None = None
    failed_login_attempts: int
    locked_until: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class AdminUserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserActionResponse(BaseModel):
    message: str
    revoked_sessions: int
    user: AdminUserOut


class AuthAuditLogOut(BaseModel):
    id: UUID
    user_id: UUID | None = None
    email: str | None = None
    event_type: str
    success: bool
    ip_address: str | None = None
    user_agent: str | None = None
    status_code: int | None = None
    detail: str | None = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )