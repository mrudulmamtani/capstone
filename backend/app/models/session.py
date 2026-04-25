"""Monitoring sessions — one per live feed or uploaded run."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.action import ActionEvent
    from app.models.alert import Alert
    from app.models.sop import SOP


class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MonitoringSession(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "monitoring_sessions"

    sop_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sops.id", ondelete="SET NULL"), index=True
    )
    operator_ref: Mapped[str | None] = mapped_column(String(120), index=True)

    source_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="offline", nullable=False)

    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status", create_type=False, values_callable=lambda e: [m.value for m in e]),
        default=SessionStatus.PENDING, nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cycle_time_s: Mapped[float | None] = mapped_column(Float)
    deviation_score: Mapped[float | None] = mapped_column(Float)

    summary: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )

    sop: Mapped["SOP | None"] = relationship(back_populates="sessions")
    actions: Mapped[list["ActionEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
