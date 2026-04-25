"""Computer vision pipeline.

The pipeline is split into composable stages that each take a frame (or a
batch of frames) and add signals to a shared ``FrameContext`` dictionary. The
orchestrator in :mod:`app.vision.pipeline` runs them in order so each stage
can be mocked out for unit tests.
"""
from app.vision.action_recognition import ActionRecognizer  # noqa: F401
from app.vision.heatmap import HeatmapBuilder  # noqa: F401
from app.vision.pipeline import FrameContext, VisionPipeline  # noqa: F401
from app.vision.pose_estimation import PoseEstimator  # noqa: F401
from app.vision.temporal_analysis import (  # noqa: F401
    ActionSegment,
    TemporalActionLocalizer,
)
