"""Skeletal pose estimation via MediaPipe.

Only the skeletal landmarks are kept — no image pixels are stored once the
frame leaves this stage. That satisfies the privacy policy from the capstone
deck: *"Use skeletal tracking / face blurring. Focus on process, not identity."*
"""
from __future__ import annotations

from typing import Any

import numpy as np

from app.core.logging import get_logger
from app.vision.types import POSE_LANDMARKS, PoseFrame

log = get_logger(__name__)


class PoseEstimator:
    """Wrapper around MediaPipe's Pose solution with a graceful fallback.

    MediaPipe is optional at install time — when unavailable we return empty
    pose frames so the rest of the pipeline can still produce useful action
    signals from object detection alone.
    """

    def __init__(self, model_complexity: int = 1, min_confidence: float = 0.5) -> None:
        self._min_conf = min_confidence
        self._pose: Any | None = None
        try:
            import mediapipe as mp  # type: ignore

            self._pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=model_complexity,
                enable_segmentation=False,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=min_confidence,
            )
            log.info("pose_estimator.initialised", backend="mediapipe")
        except Exception as exc:  # pragma: no cover - env-specific
            log.warning("pose_estimator.mediapipe_unavailable", error=str(exc))

    # ------------------------------------------------------------------ API
    def estimate(self, frame_bgr: np.ndarray) -> PoseFrame:
        """Return a PoseFrame for the given BGR frame."""
        if self._pose is None or frame_bgr is None or frame_bgr.size == 0:
            return PoseFrame(landmarks=np.zeros((POSE_LANDMARKS, 3), dtype=np.float32))

        import cv2  # lazy import

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._pose.process(rgb)

        if not result.pose_landmarks:
            return PoseFrame(landmarks=np.zeros((POSE_LANDMARKS, 3), dtype=np.float32))

        h, w = frame_bgr.shape[:2]
        arr = np.array(
            [
                [lm.x * w, lm.y * h, lm.visibility]
                for lm in result.pose_landmarks.landmark
            ],
            dtype=np.float32,
        )
        avg_vis = float(arr[:, 2].mean())
        return PoseFrame(landmarks=arr, confidence=avg_vis)

    def close(self) -> None:
        if self._pose is not None:
            try:
                self._pose.close()
            except Exception:  # pragma: no cover
                pass
            self._pose = None
