"""Ergonomic / reach heatmaps.

Aggregates wrist and nose positions across a session to produce a density map
that surfaces where an operator spends most of their reach. Used by the
Phase-2 deliverable ("generate heatmaps to visualise where operators stand
and reach most frequently").
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)


class HeatmapBuilder:
    """Accumulate 2D points into a smoothed density map."""

    def __init__(self, width: int, height: int, sigma: float = 20.0) -> None:
        self.width = int(width)
        self.height = int(height)
        self.sigma = sigma
        self._acc = np.zeros((self.height, self.width), dtype=np.float32)

    def add_point(self, x: float, y: float, weight: float = 1.0) -> None:
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.width and 0 <= yi < self.height:
            self._acc[yi, xi] += weight

    def add_pose(self, landmarks: np.ndarray) -> None:
        if landmarks is None or landmarks.size == 0:
            return
        # wrists, elbows, shoulders — the bits that matter for reach fatigue
        for idx in (11, 12, 13, 14, 15, 16):
            if idx >= len(landmarks):
                continue
            x, y, vis = landmarks[idx]
            if vis > 0.3:
                self.add_point(float(x), float(y), weight=float(vis))

    def build(self) -> np.ndarray:
        """Return a float32 heatmap normalised to [0, 1]."""
        try:
            from scipy.ndimage import gaussian_filter  # type: ignore

            smoothed = gaussian_filter(self._acc, sigma=self.sigma)
        except Exception:  # pragma: no cover - scipy optional
            smoothed = self._acc
        peak = smoothed.max()
        return (smoothed / peak).astype(np.float32) if peak > 0 else smoothed

    def save_png(self, path: Path, colormap: str = "hot") -> Path:
        """Render the heatmap as a PNG with a matplotlib colormap."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        grid = self.build()
        path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 8 * self.height / self.width))
        ax.imshow(grid, cmap=colormap, interpolation="bilinear")
        ax.axis("off")
        fig.tight_layout(pad=0)
        fig.savefig(path, dpi=120, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        return path
