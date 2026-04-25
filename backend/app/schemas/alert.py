from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.alert import AlertSeverity


class AlertOut(BaseModel):
    id: str
    session_id: str
    rule: str
    severity: AlertSeverity
    title: str
    message: str
    at_s: float
    acknowledged: bool
    evidence: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}
