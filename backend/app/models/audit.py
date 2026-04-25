"""Audit log — tracks every privacy-sensitive access to raw footage."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey


class AuditLog(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "audit_log"

    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )
