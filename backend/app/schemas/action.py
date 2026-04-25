from __future__ import annotations

from pydantic import BaseModel, Field


class ActionEventOut(BaseModel):
    id: str
    step_index: int
    label: str
    start_s: float
    end_s: float
    confidence: float
    metadata: dict = Field(default_factory=dict, alias="metadata_blob")

    model_config = {"from_attributes": True, "populate_by_name": True}
