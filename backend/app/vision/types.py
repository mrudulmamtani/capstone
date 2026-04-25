"""Shared typed containers used across the vision pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# 33-point MediaPipe body landmark set.
POSE_LANDMARKS = 33

# Core action vocabulary — matches the capstone deck ("Pick / Place / Screw").
# Extended with adjacent manufacturing primitives so the pipeline covers a
# fuller assembly cycle end-to-end.
DEFAULT_ACTIONS: tuple[str, ...] = (
    "idle",
    "reach",
    "pick",
    "place",
    "screw",
    "inspect",
    "move",
)


@dataclass
class Detection:
    """Bounding box detection from YOLO."""

    label: str
    confidence: float
    xyxy: tuple[float, float, float, float]

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.xyxy
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


@dataclass
class PoseFrame:
    """Per-frame pose estimation result."""

    landmarks: np.ndarray  # shape (N, 3): x, y, visibility
    confidence: float = 0.0

    def wrist_position(self, side: str = "right") -> tuple[float, float] | None:
        idx = 16 if side == "right" else 15
        if self.landmarks is None or len(self.landmarks) <= idx:
            return None
        x, y, vis = self.landmarks[idx]
        if vis < 0.3:
            return None
        return float(x), float(y)


@dataclass
class ActionScore:
    """Per-frame probability distribution over the action vocabulary."""

    frame_index: int
    timestamp_s: float
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def top_label(self) -> str:
        if not self.scores:
            return "idle"
        return max(self.scores.items(), key=lambda kv: kv[1])[0]

    @property
    def top_score(self) -> float:
        if not self.scores:
            return 0.0
        return max(self.scores.values())
