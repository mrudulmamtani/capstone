"""Compliance alerts raised during monitoring."""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.session import MonitoringSession


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "alerts"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitoring_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    rule: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity, name="alert_severity", create_type=False, values_callable=lambda e: [m.value for m in e]),
        default=AlertSeverity.WARNING, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    at_s: Mapped[float] = mapped_column(Float, nullable=False)

    evidence: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )

    acknowledged: Mapped[bool] = mapped_column(default=False, nullable=False)

    session: Mapped["MonitoringSession"] = relationship(back_populates="alerts")
