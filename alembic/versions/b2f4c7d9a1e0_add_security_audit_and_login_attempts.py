"""add security audit and login attempts

Revision ID: b2f4c7d9a1e0
Revises: aa90557ef712
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f4c7d9a1e0"
down_revision: Union[str, Sequence[str], None] = "aa90557ef712"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"], unique=False)
    op.create_index(
        "ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False
    )
    op.create_index(
        "ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False
    )

    op.create_table(
        "login_attempts",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_attempts_email", "login_attempts", ["email"], unique=False)
    op.create_index(
        "ix_login_attempts_locked_until",
        "login_attempts",
        ["locked_until"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_occurred_at",
        "login_attempts",
        ["occurred_at"],
        unique=False,
    )

    op.create_table(
        "error_traces",
        sa.Column("error_type", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=False),
        sa.Column("method", sa.String(length=12), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_error_traces_actor_id", "error_traces", ["actor_id"], unique=False
    )
    op.create_index(
        "ix_error_traces_created_at", "error_traces", ["created_at"], unique=False
    )
    op.create_index(
        "ix_error_traces_error_type", "error_traces", ["error_type"], unique=False
    )
    op.create_index("ix_error_traces_path", "error_traces", ["path"], unique=False)
    op.create_index(
        "ix_error_traces_request_id", "error_traces", ["request_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_error_traces_request_id", table_name="error_traces")
    op.drop_index("ix_error_traces_path", table_name="error_traces")
    op.drop_index("ix_error_traces_error_type", table_name="error_traces")
    op.drop_index("ix_error_traces_created_at", table_name="error_traces")
    op.drop_index("ix_error_traces_actor_id", table_name="error_traces")
    op.drop_table("error_traces")

    op.drop_index("ix_login_attempts_occurred_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_locked_until", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email", table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
