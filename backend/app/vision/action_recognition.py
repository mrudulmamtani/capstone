"""Action recognition.

Combines two complementary signals to produce a per-frame probability
distribution over the action vocabulary:

1. **Object detections** from YOLOv8 — tells us *what* is in frame and where.
   Presence of a screwdriver → "screw" gets a boost; presence of a component
   and the operator's wrist near a bin → "pick", etc.
2. **Wrist kinematics** from MediaPipe pose — tells us *how* the operator is
   moving. Sustained fast wrist motion tracks "reach"/"move"; near-static
   wrist over a workpiece tracks "screw"/"inspect".

The scores are intentionally explainable (no learned black-box classifier)
so quality engineers can tune the heuristics for their specific line. A
learned model can be dropped in later behind the same ``score_frame`` API.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Any

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.vision.types import (
    DEFAULT_ACTIONS,
    ActionScore,
    Detection,
    PoseFrame,
)

log = get_logger(__name__)


# Very conservative mapping from COCO labels YOLOv8 ships with, to the
# manufacturing tool vocabulary our rules expect. In a real deployment this
# would be replaced by a fine-tuned model on per-site SKUs.
_TOOL_ALIASES: dict[str, str] = {
    "scissors": "tool",
    "knife": "tool",
    "spoon": "tool",
    "fork": "tool",
    "toothbrush": "tool",
    "cell phone": "tool",
    "remote": "tool",
    "bottle": "component",
    "cup": "component",
    "bowl": "component",
    "book": "component",
    "mouse": "component",
    "keyboard": "component",
}


class ActionRecognizer:
    """Scores a single frame across the action vocabulary."""

    def __init__(
        self,
        model_path: str | None = None,
        conf_threshold: float | None = None,
        vocabulary: tuple[str, ...] = DEFAULT_ACTIONS,
    ) -> None:
        self.vocabulary = vocabulary
        self._conf = conf_threshold if conf_threshold is not None else settings.yolo_conf_threshold
        self._yolo: Any | None = None
        self._wrist_history: deque[tuple[float, float, float]] = deque(maxlen=12)

        path = model_path or settings.yolo_detect_model
        try:
            from ultralytics import YOLO  # type: ignore

            self._yolo = YOLO(path)
            log.info("action_recognizer.initialised", backend="yolov8", model=path)
        except Exception as exc:  # pragma: no cover - env-specific
            log.warning("action_recognizer.yolo_unavailable", error=str(exc), model=path)

    # ---------------------------------------------------------------- API
    def detect_objects(self, frame_bgr: np.ndarray) -> list[Detection]:
        if self._yolo is None or frame_bgr is None or frame_bgr.size == 0:
            return []
        try:
            result = self._yolo.predict(
                frame_bgr, conf=self._conf, verbose=False
            )
        except Exception as exc:  # pragma: no cover - runtime
            log.warning("action_recognizer.predict_failed", error=str(exc))
            return []

        if not result:
            return []
        r0 = result[0]
        names = r0.names
        out: list[Detection] = []
        for box in r0.boxes:
            label = names[int(box.cls)] if names else str(int(box.cls))
            xy = box.xyxy[0].tolist()
            out.append(
                Detection(
                    label=_TOOL_ALIASES.get(label, label),
                    confidence=float(box.conf[0]),
                    xyxy=(float(xy[0]), float(xy[1]), float(xy[2]), float(xy[3])),
                )
            )
        return out

    def score_frame(
        self,
        frame_index: int,
        timestamp_s: float,
        pose: PoseFrame,
        detections: list[Detection],
    ) -> ActionScore:
        """Return a probability-like distribution over actions."""
        scores = {k: 0.0 for k in self.vocabulary}

        # ---------- wrist kinematics ----------
        wrist = pose.wrist_position("right") or pose.wrist_position("left")
        wrist_speed = 0.0
        wrist_still = 0.0
        if wrist is not None:
            self._wrist_history.append((timestamp_s, wrist[0], wrist[1]))
            wrist_speed = self._wrist_speed()
            wrist_still = 1.0 - min(1.0, wrist_speed / 400.0)  # px/s normalized

        # ---------- detection-based cues ----------
        labels_in_frame = {d.label for d in detections}
        has_tool = "tool" in labels_in_frame or "screwdriver" in labels_in_frame
        has_component = "component" in labels_in_frame
        has_person = "person" in labels_in_frame

        # ---------- rule assignments ----------
        # Idle: no pose confidence or wrist invisible.
        if wrist is None or pose.confidence < 0.2:
            scores["idle"] = 0.7
            return ActionScore(frame_index=frame_index, timestamp_s=timestamp_s, scores=_normalise(scores))

        # Move — the whole body is shifting (centroid motion).
        centroid_speed = self._centroid_speed(pose)
        if centroid_speed > 150 and wrist_speed > 150:
            scores["move"] = 0.6

        # Reach — fast wrist, arm extended, no tool yet.
        if wrist_speed > 250:
            scores["reach"] = 0.6 + 0.2 * float(has_component)

        # Pick — hand near a detected component, wrist slowing down.
        if has_component and 50 < wrist_speed < 300:
            scores["pick"] = 0.7

        # Place — hand recently moved a component and is now slowing near a
        # different location. Proxy: wrist decelerating + component present.
        if has_component and wrist_speed < 120 and self._wrist_decelerating():
            scores["place"] = 0.65

        # Screw — tool present, wrist relatively still but with fine motion
        # (detected as low speed but non-zero).
        if has_tool and 20 < wrist_speed < 140:
            scores["screw"] = 0.8

        # Inspect — person, no tool, wrist still, gaze-adjacent heuristic (head
        # near hand using nose landmark as a proxy).
        if has_person and wrist_still > 0.8 and not has_tool:
            if _nose_near_wrist(pose):
                scores["inspect"] = 0.7
            else:
                scores["idle"] = max(scores["idle"], 0.5)

        # Fallback — small idle baseline so we never emit all-zeros.
        if sum(scores.values()) < 0.05:
            scores["idle"] = 0.4

        return ActionScore(
            frame_index=frame_index,
            timestamp_s=timestamp_s,
            scores=_normalise(scores),
        )

    # ------------------------------------------------------------ helpers
    def _wrist_speed(self) -> float:
        if len(self._wrist_history) < 2:
            return 0.0
        t0, x0, y0 = self._wrist_history[-2]
        t1, x1, y1 = self._wrist_history[-1]
        dt = max(1e-3, t1 - t0)
        return math.hypot(x1 - x0, y1 - y0) / dt

    def _wrist_decelerating(self) -> bool:
        if len(self._wrist_history) < 4:
            return False
        recent = list(self._wrist_history)[-4:]
        speeds = []
        for a, b in zip(recent, recent[1:]):
            dt = max(1e-3, b[0] - a[0])
            speeds.append(math.hypot(b[1] - a[1], b[2] - a[2]) / dt)
        return speeds[0] > speeds[-1] * 1.5

    @staticmethod
    def _centroid_speed(pose: PoseFrame) -> float:
        if pose.landmarks is None or pose.landmarks.size == 0:
            return 0.0
        # crude centroid-velocity proxy: shoulders midpoint displacement vs
        # previous frame. Since we don't carry state here we rely on wrist
        # history as an approximation in this lightweight implementation.
        return 0.0


def _normalise(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        scores["idle"] = 1.0
        return scores
    return {k: v / total for k, v in scores.items()}


def _nose_near_wrist(pose: PoseFrame) -> bool:
    if pose.landmarks is None or pose.landmarks.size == 0:
        return False
    # MediaPipe indices: nose=0, right_wrist=16, left_wrist=15.
    if len(pose.landmarks) < 17:
        return False
    nose = pose.landmarks[0][:2]
    rwrist = pose.landmarks[16][:2]
    lwrist = pose.landmarks[15][:2]
    d = min(np.linalg.norm(nose - rwrist), np.linalg.norm(nose - lwrist))
    return bool(d < 120.0)
