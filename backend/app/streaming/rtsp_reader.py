"""Generic video source reader — local file, HTTP, or RTSP."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class Frame:
    index: int
    timestamp_s: float
    image: np.ndarray


class VideoReader:
    """Iterable reader that decodes an RTSP/HTTP URL or a local video file.

    Decimates to ``target_fps`` so the downstream CV stages have a predictable
    budget. On RTSP it transparently retries on transient failures so a brief
    network blip doesn't kill a monitoring session.
    """

    def __init__(
        self,
        source: str | Path,
        target_fps: int = 10,
        max_retries: int = 5,
        retry_delay_s: float = 1.0,
    ) -> None:
        self.source = str(source)
        self.target_fps = max(1, int(target_fps))
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s

    # --------------------------------------------------------------- helpers
    def _open(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source!r}")
        return cap

    # ------------------------------------------------------------------- API
    def __iter__(self) -> Iterator[Frame]:
        retries = 0
        cap = self._open()
        native_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, int(round(native_fps / self.target_fps)))
        log.info(
            "video_reader.open",
            source=self.source,
            native_fps=native_fps,
            target_fps=self.target_fps,
            step=step,
        )

        frame_index = 0
        emitted = 0
        try:
            while True:
                ok, img = cap.read()
                if not ok or img is None:
                    if self._is_stream() and retries < self.max_retries:
                        retries += 1
                        log.warning("video_reader.reconnect", attempt=retries)
                        cap.release()
                        time.sleep(self.retry_delay_s)
                        cap = self._open()
                        continue
                    break
                retries = 0
                if frame_index % step == 0:
                    ts = emitted / self.target_fps
                    yield Frame(index=emitted, timestamp_s=ts, image=img)
                    emitted += 1
                frame_index += 1
        finally:
            cap.release()

    def _is_stream(self) -> bool:
        s = self.source.lower()
        return s.startswith(("rtsp://", "http://", "https://"))
