from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.sop import SOPStatus


class SOPStepOut(BaseModel):
    id: str
    step_index: int
    action_label: str
    title: str
    instruction: str
    target_duration_s: float
    tolerance_s: float
    clip_start_s: float | None = None
    clip_end_s: float | None = None
    clip_path: str | None = None
    required_ppe: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SOPOut(BaseModel):
    id: str
    title: str
    station: str
    description: str | None = None
    version: int
    status: SOPStatus
    target_cycle_time_s: float | None = None
    rendered_markdown: str | None = None
    steps: list[SOPStepOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SOPCreate(BaseModel):
    title: str
    station: str
    description: str | None = None


class SOPGenerateRequest(BaseModel):
    """Kick off the Phase-1 pipeline against an uploaded/known video."""

    title: str
    station: str
    source_video_path: str
    description: str | None = None
    required_ppe: list[str] = Field(default_factory=list)
