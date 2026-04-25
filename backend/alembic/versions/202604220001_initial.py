"""initial schema

Revision ID: 202604220001
Revises:
Create Date: 2026-04-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "202604220001"
down_revision = None
branch_labels = None
depends_on = None


def _create_enum_if_not_exists(name: str, values: list[str]) -> None:
    """Create a PG enum via DO block to avoid DuplicateObject errors."""
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(
        sa.text(
            f"DO $$ BEGIN "
            f"CREATE TYPE {name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; "
            f"END $$"
        )
    )


user_role = postgresql.ENUM("operator", "supervisor", "engineer", "admin", name="user_role", create_type=False)
sop_status = postgresql.ENUM("draft", "review", "published", "archived", name="sop_status", create_type=False)
session_status = postgresql.ENUM("pending", "running", "completed", "failed", name="session_status", create_type=False)
alert_severity = postgresql.ENUM("info", "warning", "critical", name="alert_severity", create_type=False)


def upgrade() -> None:
    _create_enum_if_not_exists("user_role", ["operator", "supervisor", "engineer", "admin"])
    _create_enum_if_not_exists("sop_status", ["draft", "review", "published", "archived"])
    _create_enum_if_not_exists("session_status", ["pending", "running", "completed", "failed"])
    _create_enum_if_not_exists("alert_severity", ["info", "warning", "critical"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "sops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("station", sa.String(120), nullable=False, index=True),
        sa.Column("description", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sop_status, nullable=False, server_default="draft"),
        sa.Column("source_video_path", sa.String(512)),
        sa.Column("target_cycle_time_s", sa.Float()),
        sa.Column("rendered_markdown", sa.Text()),
        sa.Column("generation_metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "sop_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sop_id", sa.String(36), sa.ForeignKey("sops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("action_label", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("target_duration_s", sa.Float(), nullable=False),
        sa.Column("tolerance_s", sa.Float(), nullable=False, server_default="1.5"),
        sa.Column("clip_start_s", sa.Float()),
        sa.Column("clip_end_s", sa.Float()),
        sa.Column("clip_path", sa.String(512)),
        sa.Column("required_ppe", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "monitoring_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sop_id", sa.String(36), sa.ForeignKey("sops.id", ondelete="SET NULL"), index=True),
        sa.Column("operator_ref", sa.String(120), index=True),
        sa.Column("source_uri", sa.String(512), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False, server_default="offline"),
        sa.Column("status", session_status, nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cycle_time_s", sa.Float()),
        sa.Column("deviation_score", sa.Float()),
        sa.Column("summary", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "action_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("monitoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(64), nullable=False, index=True),
        sa.Column("start_s", sa.Float(), nullable=False),
        sa.Column("end_s", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("monitoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rule", sa.String(64), nullable=False, index=True),
        sa.Column("severity", alert_severity, nullable=False, server_default="warning"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("at_s", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("context", postgresql.JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("alerts")
    op.drop_table("action_events")
    op.drop_table("monitoring_sessions")
    op.drop_table("sop_steps")
    op.drop_table("sops")
    op.drop_table("users")
    alert_severity.drop(op.get_bind(), checkfirst=True)
    session_status.drop(op.get_bind(), checkfirst=True)
    sop_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
