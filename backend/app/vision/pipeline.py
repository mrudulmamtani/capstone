"""Top-level orchestrator that wires every CV stage together.

Two entry points:

* :meth:`VisionPipeline.run_batch` — processes a whole video file, returns
  segments + heatmap. Used by the Phase-1 "generate SOP from gold-standard"
  flow and by Phase-2 ergonomic analysis.
* :meth:`VisionPipeline.iter_stream` — generator yielding per-frame
  :class:`ActionScore` objects. Used by Phase-3 real-time compliance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.privacy.face_blur import FaceAnonymizer
from app.streaming.rtsp_reader import VideoReader
from app.vision.action_recognition import ActionRecognizer
from app.vision.heatmap import HeatmapBuilder
from app.vision.pose_estimation import PoseEstimator
from app.vision.temporal_analysis import ActionSegment, TemporalActionLocalizer
from app.vision.types import ActionScore

log = get_logger(__name__)


@dataclass
class FrameContext:
    frame_index: int
    timestamp_s: float
    image: np.ndarray
    score: ActionScore | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    source: str
    duration_s: float
    frame_count: int
    segments: list[ActionSegment]
    heatmap_path: Path | None = None
    per_frame_scores: list[ActionScore] = field(default_factory=list)


class VisionPipeline:
    def __init__(
        self,
        action_recognizer: ActionRecognizer | None = None,
        pose_estimator: PoseEstimator | None = None,
        temporal_localizer: TemporalActionLocalizer | None = None,
        face_blur: FaceAnonymizer | None = None,
    ) -> None:
        self.action_recognizer = action_recognizer or ActionRecognizer()
        self.pose_estimator = pose_estimator or PoseEstimator()
        self.temporal_localizer = temporal_localizer or TemporalActionLocalizer()
        self.face_blur = face_blur

    # ------------------------------------------------------------ streaming
    def iter_stream(
        self,
        source: str | Path,
        target_fps: int | None = None,
        heatmap: HeatmapBuilder | None = None,
    ) -> Iterator[ActionScore]:
        """Yield :class:`ActionScore` objects per frame from a live stream."""
        target = target_fps or settings.pipeline_target_fps
        reader = VideoReader(source, target_fps=target)

        for frame in reader:
            img = frame.image
            if self.face_blur is not None:
                img = self.face_blur.blur(img)

            pose = self.pose_estimator.estimate(img)
            dets = self.action_recognizer.detect_objects(img)
            score = self.action_recognizer.score_frame(
                frame_index=frame.index,
                timestamp_s=frame.timestamp_s,
                pose=pose,
                detections=dets,
            )
            if heatmap is not None and pose.landmarks is not None:
                heatmap.add_pose(pose.landmarks)
            yield score

    # --------------------------------------------------------------- batch
    def run_batch(
        self,
        source: str | Path,
        build_heatmap: bool = True,
        heatmap_path: Path | None = None,
    ) -> PipelineResult:
        """Process a whole video and return segments + heatmap."""
        target = settings.pipeline_target_fps

        reader = VideoReader(source, target_fps=target)

        heatmap_builder: HeatmapBuilder | None = None
        scores: list[ActionScore] = []
        width = height = 0
        frame_count = 0
        last_ts = 0.0

        for frame in reader:
            img = frame.image
            if frame_count == 0:
                height, width = img.shape[:2]
                if build_heatmap:
                    heatmap_builder = HeatmapBuilder(width=width, height=height)

            if self.face_blur is not None:
                img = self.face_blur.blur(img)

            pose = self.pose_estimator.estimate(img)
            dets = self.action_recognizer.detect_objects(img)
            score = self.action_recognizer.score_frame(
                frame_index=frame.index,
                timestamp_s=frame.timestamp_s,
                pose=pose,
                detections=dets,
            )
            scores.append(score)

            if heatmap_builder is not None and pose.landmarks is not None:
                heatmap_builder.add_pose(pose.landmarks)

            frame_count += 1
            last_ts = frame.timestamp_s

        segments = self.temporal_localizer.localize(scores)

        heat_path: Path | None = None
        if heatmap_builder is not None:
            target_path = heatmap_path or (settings.heatmap_dir / f"{Path(source).stem}.png")
            try:
                heat_path = heatmap_builder.save_png(target_path)
            except Exception as exc:  # pragma: no cover - IO
                log.warning("pipeline.heatmap_save_failed", error=str(exc))

        result = PipelineResult(
            source=str(source),
            duration_s=last_ts,
            frame_count=frame_count,
            segments=segments,
            heatmap_path=heat_path,
            per_frame_scores=scores,
        )
        log.info(
            "pipeline.batch_complete",
            source=str(source),
            frames=frame_count,
            segments=len(segments),
            duration_s=round(last_ts, 2),
        )
        return result
