"""Standard Operating Procedure models.

An ``SOP`` is the top-level document for a workstation/task (e.g. "Assembly of
door handle at Station 3"). It owns ordered ``SOPStep`` rows which come
directly from the CV pipeline's action localisation.
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.session import MonitoringSession


class SOPStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SOP(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "sops"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    station: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[SOPStatus] = mapped_column(
        SAEnum(SOPStatus, name="sop_status", create_type=False, values_callable=lambda e: [m.value for m in e]),
        default=SOPStatus.DRAFT, nullable=False
    )

    source_video_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_cycle_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    # The fully-rendered, human-readable SOP (LLM output).
    rendered_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Arbitrary metadata produced during generation (model versions, confidence, etc.).
    generation_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=False
    )

    steps: Mapped[list["SOPStep"]] = relationship(
        back_populates="sop",
        order_by="SOPStep.step_index",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["MonitoringSession"]] = relationship(back_populates="sop")


class SOPStep(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "sop_steps"

    sop_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sops.id", ondelete="CASCADE"), index=True, nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    action_label: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)

    target_duration_s: Mapped[float] = mapped_column(Float, nullable=False)
    tolerance_s: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)

    clip_start_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    clip_end_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    clip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    required_ppe: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default="[]", nullable=False
    )

    sop: Mapped[SOP] = relationship(back_populates="steps")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SOPStep {self.step_index}:{self.action_label}>"
