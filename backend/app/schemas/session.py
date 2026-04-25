from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.session import SessionStatus


class SessionCreate(BaseModel):
    sop_id: str | None = None
    operator_ref: str | None = None
    source_uri: str
    mode: str = "offline"


class SessionOut(BaseModel):
    id: str
    sop_id: str | None
    operator_ref: str | None
    source_uri: str
    mode: str
    status: SessionStatus
    started_at: datetime | None
    completed_at: datetime | None
    cycle_time_s: float | None
    deviation_score: float | None

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    """Aggregated stats used by the dashboard."""

    session_id: str
    total_steps: int
    matched_steps: int
    skipped_steps: list[str] = Field(default_factory=list)
    extra_steps: list[str] = Field(default_factory=list)
    cycle_time_s: float
    target_cycle_time_s: float | None = None
    deviation_score: float
    alerts: int
