"""Individual action events emitted by the vision pipeline."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.session import MonitoringSession


class ActionEvent(UUIDPrimaryKey, TimestampMixin, Base):
    """A localized action in time.

    Produced by the temporal action localizer after aggregating per-frame
    detections. One ``ActionEvent`` ≈ one step of work.
    """

    __tablename__ = "action_events"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("monitoring_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    end_s: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Per-frame supporting signals (pose summary, detected objects, etc.).
    metadata_blob: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}", nullable=False
    )

    session: Mapped["MonitoringSession"] = relationship(back_populates="actions")

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)
