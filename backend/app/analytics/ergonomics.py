"""Lightweight ergonomic risk scoring from pose data.

We approximate a RULA-style quick score from wrist/elbow/shoulder angles
aggregated across a session. A full RULA/REBA assessment would require
side-view cameras and manual scoring; this gives an *indicative* score good
enough to flag problematic stations for human review.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ErgonomicsReport:
    sample_count: int
    mean_shoulder_abduction_deg: float
    mean_elbow_flexion_deg: float
    reach_percentile_95: float
    score: int  # 1 (low risk) … 7 (high risk)
    hotspots: list[dict] = field(default_factory=list)


def analyse_ergonomics(
    pose_landmark_frames: list[np.ndarray],
    frame_size: tuple[int, int] | None = None,
) -> ErgonomicsReport:
    """Aggregate ergonomic risk indicators.

    ``pose_landmark_frames`` is a list of (33, 3) landmark arrays as produced
    by :class:`app.vision.pose_estimation.PoseEstimator`.
    """
    if not pose_landmark_frames:
        return ErgonomicsReport(0, 0.0, 0.0, 0.0, 1, [])

    shoulder_angles: list[float] = []
    elbow_angles: list[float] = []
    reaches: list[float] = []

    for lm in pose_landmark_frames:
        if lm is None or lm.size == 0 or len(lm) < 17:
            continue
        # right side (MediaPipe indices): shoulder=12, elbow=14, wrist=16, hip=24
        rs = lm[12][:2]
        re = lm[14][:2]
        rw = lm[16][:2]
        rh = lm[24][:2] if len(lm) > 24 else rs

        shoulder_angles.append(_angle(rh, rs, re))
        elbow_angles.append(_angle(rs, re, rw))
        reaches.append(float(np.linalg.norm(rw - rs)))

    n = len(shoulder_angles)
    if n == 0:
        return ErgonomicsReport(0, 0.0, 0.0, 0.0, 1, [])

    mean_shoulder = float(np.mean(shoulder_angles))
    mean_elbow = float(np.mean(elbow_angles))
    p95_reach = float(np.percentile(reaches, 95))

    score = 1
    hotspots: list[dict] = []
    if mean_shoulder > 60:
        score += 2
        hotspots.append(
            {
                "area": "shoulder",
                "message": f"Mean shoulder abduction {mean_shoulder:.0f}° — "
                "operator is reaching above recommended 60°.",
            }
        )
    if mean_shoulder > 90:
        score += 1
    if mean_elbow < 60 or mean_elbow > 135:
        score += 1
        hotspots.append(
            {
                "area": "elbow",
                "message": f"Mean elbow flexion {mean_elbow:.0f}° outside the 60-135° comfort band.",
            }
        )
    if frame_size and p95_reach > 0.55 * frame_size[0]:
        score += 2
        hotspots.append(
            {
                "area": "reach",
                "message": "95th-percentile reach exceeds 55% of frame width — "
                "consider moving the bin closer to the operator.",
            }
        )

    return ErgonomicsReport(
        sample_count=n,
        mean_shoulder_abduction_deg=round(mean_shoulder, 1),
        mean_elbow_flexion_deg=round(mean_elbow, 1),
        reach_percentile_95=round(p95_reach, 1),
        score=min(7, score),
        hotspots=hotspots,
    )


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return the angle ABC in degrees."""
    ba = a - b
    bc = c - b
    denom = (np.linalg.norm(ba) * np.linalg.norm(bc)) or 1.0
    cosine = float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))
