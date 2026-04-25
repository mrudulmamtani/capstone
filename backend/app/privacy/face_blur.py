"""Face anonymisation.

The capstone's privacy mitigation is "use skeletal tracking / face blurring".
This stage runs *before* any frame is persisted or sent to the UI. It uses
OpenCV's Haar cascade because it's dependency-free and fast enough for
realtime; a stronger alternative (e.g. RetinaFace) can replace this class
without touching callers.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)


class FaceAnonymizer:
    def __init__(self, cascade_path: Path | None = None, kernel_size: int = 35) -> None:
        self._kernel = max(3, kernel_size | 1)  # force odd
        path = cascade_path or Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(str(path))
        if self._cascade.empty():  # pragma: no cover
            log.warning("face_anonymizer.cascade_missing", path=str(path))

    def blur(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Return a copy of ``frame_bgr`` with every detected face blurred."""
        if frame_bgr is None or frame_bgr.size == 0 or self._cascade.empty():
            return frame_bgr

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(40, 40)
        )
        if len(faces) == 0:
            return frame_bgr

        out = frame_bgr.copy()
        for (x, y, w, h) in faces:
            roi = out[y:y + h, x:x + w]
            if roi.size == 0:
                continue
            blurred = cv2.GaussianBlur(roi, (self._kernel, self._kernel), 0)
            out[y:y + h, x:x + w] = blurred
        return out
