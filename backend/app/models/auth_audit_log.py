import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.database import Base


class AuthAuditLog(Base):
    __tablename__ = "auth_audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    email = Column(
        String(320),
        nullable=True,
        index=True,
    )

    event_type = Column(
        String(100),
        nullable=False,
        index=True,
    )

    success = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    ip_address = Column(
        String(64),
        nullable=True,
        index=True,
    )

    user_agent = Column(
        Text,
        nullable=True,
    )

    status_code = Column(
        Integer,
        nullable=True,
    )

    detail = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )