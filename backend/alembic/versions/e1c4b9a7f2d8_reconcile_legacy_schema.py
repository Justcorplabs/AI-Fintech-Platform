"""Reconcile legacy schema with current models.

Revision ID: e1c4b9a7f2d8
Revises: b7dad0f55492
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e1c4b9a7f2d8"
down_revision: Union[str, Sequence[str], None] = "b7dad0f55492"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = postgresql.ENUM(
    "admin",
    "analyst",
    "recruiter",
    "viewer",
    name="userrole",
    create_type=False,
)


def _validate_existing_data() -> None:
    """Stop before destructive constraints are applied."""

    bind = op.get_bind()

    violations = bind.execute(
        sa.text(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE role IS NULL
                ) AS null_roles,
                COUNT(*) FILTER (
                    WHERE is_active IS NULL
                ) AS null_active_flags,
                COUNT(*) FILTER (
                    WHERE created_at IS NULL
                ) AS null_created_dates
            FROM users
            """
        )
    ).mappings().one()

    oversized_ip_addresses = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM auth_audit_logs
            WHERE ip_address IS NOT NULL
              AND char_length(ip_address) > 64
            """
        )
    ).scalar_one()

    problems = []

    if violations["null_roles"]:
        problems.append(
            f"{violations['null_roles']} users have NULL roles"
        )

    if violations["null_active_flags"]:
        problems.append(
            f"{violations['null_active_flags']} users have NULL is_active values"
        )

    if violations["null_created_dates"]:
        problems.append(
            f"{violations['null_created_dates']} users have NULL created_at values"
        )

    if oversized_ip_addresses:
        problems.append(
            f"{oversized_ip_addresses} audit IP addresses exceed 64 characters"
        )

    if problems:
        raise RuntimeError(
            "Legacy schema reconciliation blocked: "
            + "; ".join(problems)
        )


def upgrade() -> None:
    """Align the legacy database with current SQLAlchemy models."""

    _validate_existing_data()

    op.alter_column(
        "auth_audit_logs",
        "ip_address",
        existing_type=sa.String(length=100),
        type_=sa.String(length=64),
        existing_nullable=True,
    )

    op.create_index(
        op.f("ix_auth_audit_logs_success"),
        "auth_audit_logs",
        ["success"],
        unique=False,
    )

    op.alter_column(
        "users",
        "role",
        existing_type=user_role_enum,
        nullable=False,
    )

    op.alter_column(
        "users",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
    )

    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_server_default=sa.text("now()"),
        nullable=False,
    )


def downgrade() -> None:
    """Restore the legacy column and index definitions."""

    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_server_default=sa.text("now()"),
        nullable=True,
    )

    op.alter_column(
        "users",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=True,
    )

    op.alter_column(
        "users",
        "role",
        existing_type=user_role_enum,
        nullable=True,
    )

    op.drop_index(
        op.f("ix_auth_audit_logs_success"),
        table_name="auth_audit_logs",
    )

    op.alter_column(
        "auth_audit_logs",
        "ip_address",
        existing_type=sa.String(length=64),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
