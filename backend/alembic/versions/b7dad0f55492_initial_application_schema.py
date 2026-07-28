"""Initial legacy application schema.

Revision ID: b7dad0f55492
Revises:
Create Date: 2026-07-28 14:51:25.514481
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7dad0f55492"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


application_status_enum = postgresql.ENUM(
    "uploaded",
    "parsed",
    "scored",
    "shortlisted",
    "rejected",
    name="applicationstatus",
    create_type=False,
)

fraud_status_enum = postgresql.ENUM(
    "pending",
    "flagged",
    "cleared",
    "investigating",
    name="fraudstatus",
    create_type=False,
)

user_role_enum = postgresql.ENUM(
    "admin",
    "analyst",
    "recruiter",
    "viewer",
    name="userrole",
    create_type=False,
)


def upgrade() -> None:
    """Create the legacy schema that predates Alembic."""

    bind = op.get_bind()

    application_status_enum.create(bind, checkfirst=True)
    fraud_status_enum.create(bind, checkfirst=True)
    user_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "cv_applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_post_id", sa.UUID(), nullable=False),
        sa.Column("candidate_name", sa.String(), nullable=True),
        sa.Column("candidate_email", sa.String(), nullable=True),
        sa.Column("cv_filename", sa.String(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column(
            "extracted_skills",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
        sa.Column("experience_years", sa.Float(), nullable=True),
        sa.Column("education_level", sa.String(), nullable=True),
        sa.Column(
            "parsed_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("llm_reasoning", sa.Text(), nullable=True),
        sa.Column(
            "status",
            application_status_enum,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "scored_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "job_posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "required_skills",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
        sa.Column(
            "required_experience_years",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column("organisation", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "transaction_ref",
            sa.String(),
            nullable=False,
        ),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=True,
        ),
        sa.Column("merchant_name", sa.String(), nullable=True),
        sa.Column(
            "merchant_category",
            sa.String(),
            nullable=True,
        ),
        sa.Column("card_type", sa.String(), nullable=True),
        sa.Column(
            "transaction_hour",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "distance_from_home",
            sa.Float(),
            nullable=True,
        ),
        sa.Column("is_foreign", sa.Boolean(), nullable=True),
        sa.Column("fraud_score", sa.Float(), nullable=True),
        sa.Column("is_fraud", sa.Boolean(), nullable=True),
        sa.Column(
            "status",
            fraud_status_enum,
            nullable=True,
        ),
        sa.Column(
            "shap_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_transactions_transaction_ref"),
        "transactions",
        ["transaction_ref"],
        unique=True,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column(
            "hashed_password",
            sa.String(),
            nullable=False,
        ),
        # These columns were nullable in the legacy database.
        sa.Column("role", user_role_enum, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("organisation", sa.String(), nullable=True),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "auth_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "success",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        # The legacy database used 100 characters.
        sa.Column(
            "ip_address",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_auth_audit_logs_created_at"),
        "auth_audit_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_audit_logs_email"),
        "auth_audit_logs",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_audit_logs_event_type"),
        "auth_audit_logs",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_audit_logs_ip_address"),
        "auth_audit_logs",
        ["ip_address"],
        unique=False,
    )
    # The legacy database did not contain ix_auth_audit_logs_success.
    op.create_index(
        op.f("ix_auth_audit_logs_user_id"),
        "auth_audit_logs",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_password_reset_tokens_expires_at"),
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_token_hash"),
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_used_at"),
        "password_reset_tokens",
        ["used_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"),
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "jti",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "replaced_by_jti",
            sa.String(length=36),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_refresh_tokens_expires_at"),
        "refresh_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_jti"),
        "refresh_tokens",
        ["jti"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_tokens_revoked_at"),
        "refresh_tokens",
        ["revoked_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"),
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "transaction_audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "transaction_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_transaction_audit_events_transaction_id"),
        "transaction_audit_events",
        ["transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the initial legacy application schema."""

    op.drop_index(
        op.f("ix_transaction_audit_events_transaction_id"),
        table_name="transaction_audit_events",
    )
    op.drop_table("transaction_audit_events")

    op.drop_index(
        op.f("ix_refresh_tokens_user_id"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_token_hash"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_revoked_at"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_jti"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_expires_at"),
        table_name="refresh_tokens",
    )
    op.drop_table("refresh_tokens")

    op.drop_index(
        op.f("ix_password_reset_tokens_user_id"),
        table_name="password_reset_tokens",
    )
    op.drop_index(
        op.f("ix_password_reset_tokens_used_at"),
        table_name="password_reset_tokens",
    )
    op.drop_index(
        op.f("ix_password_reset_tokens_token_hash"),
        table_name="password_reset_tokens",
    )
    op.drop_index(
        op.f("ix_password_reset_tokens_expires_at"),
        table_name="password_reset_tokens",
    )
    op.drop_table("password_reset_tokens")

    op.drop_index(
        op.f("ix_auth_audit_logs_user_id"),
        table_name="auth_audit_logs",
    )
    op.drop_index(
        op.f("ix_auth_audit_logs_ip_address"),
        table_name="auth_audit_logs",
    )
    op.drop_index(
        op.f("ix_auth_audit_logs_event_type"),
        table_name="auth_audit_logs",
    )
    op.drop_index(
        op.f("ix_auth_audit_logs_email"),
        table_name="auth_audit_logs",
    )
    op.drop_index(
        op.f("ix_auth_audit_logs_created_at"),
        table_name="auth_audit_logs",
    )
    op.drop_table("auth_audit_logs")

    op.drop_index(
        op.f("ix_users_email"),
        table_name="users",
    )
    op.drop_table("users")

    op.drop_index(
        op.f("ix_transactions_transaction_ref"),
        table_name="transactions",
    )
    op.drop_table("transactions")

    op.drop_table("job_posts")
    op.drop_table("cv_applications")

    bind = op.get_bind()

    user_role_enum.drop(bind, checkfirst=True)
    fraud_status_enum.drop(bind, checkfirst=True)
    application_status_enum.drop(bind, checkfirst=True)
