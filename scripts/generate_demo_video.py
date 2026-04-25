"""Generate a synthetic assembly-line demo video.

This script produces a short MP4 that contains a stick-figure operator moving
through the pick -> place -> screw cycle several times. It lets you exercise
the full vision pipeline end-to-end without needing a real CCTV feed.

Usage::

    python scripts/generate_demo_video.py \
        --output data/videos/demo.mp4 \
        --cycles 4 \
        --fps 20 \
        --width 960 \
        --height 540

The generated video is deliberately stylised — we are not trying to fool the
YOLO detector (which won't fire on a stick figure anyway). The point is to
exercise the *structural* pipeline: frame reading, pose estimation,
temporal smoothing, segmentation, SOP generation.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np

# ----------------------------------------------------------------- phases
# Each phase defines how long it lasts (seconds) and where the operator's
# right hand should be relative to the canvas. The vision pipeline will see
# these as distinct kinematic patterns.
_PHASES = [
    ("reach", 0.7, lambda t, w, h: (0.15 + 0.50 * t * w, 0.45 * h)),
    ("pick", 0.5, lambda t, w, h: (0.65 * w, 0.45 * h + 0.05 * math.sin(12 * t) * h)),
    ("move", 0.6, lambda t, w, h: (0.65 * w - 0.30 * t * w, 0.35 * h)),
    ("place", 0.5, lambda t, w, h: (0.35 * w, 0.40 * h + 0.02 * math.sin(8 * t) * h)),
    ("screw", 1.2, lambda t, w, h: (0.35 * w + 0.01 * math.sin(40 * t) * w, 0.40 * h)),
    ("inspect", 0.5, lambda t, w, h: (0.35 * w, 0.30 * h)),
    ("idle", 0.4, lambda t, w, h: (0.40 * w, 0.55 * h)),
]


def _draw_operator(canvas: np.ndarray, hand: tuple[float, float]) -> None:
    h, w = canvas.shape[:2]
    # ---------- background bench ----------
    cv2.rectangle(canvas, (0, int(h * 0.65)), (w, h), (48, 48, 56), -1)
    cv2.rectangle(canvas, (int(w * 0.08), int(h * 0.63)), (int(w * 0.28), int(h * 0.70)),
                  (140, 120, 70), -1)  # bin
    cv2.rectangle(canvas, (int(w * 0.55), int(h * 0.62)), (int(w * 0.70), int(h * 0.66)),
                  (80, 80, 160), -1)   # fixture

    # ---------- stick operator ----------
    head_c = (int(w * 0.30), int(h * 0.20))
    cv2.circle(canvas, head_c, int(h * 0.05), (240, 220, 190), -1)
    torso_top = (head_c[0], head_c[1] + int(h * 0.05))
    torso_bot = (head_c[0], int(h * 0.60))
    cv2.line(canvas, torso_top, torso_bot, (80, 120, 220), 6)
    # legs
    cv2.line(canvas, torso_bot, (torso_bot[0] - 40, int(h * 0.75)), (40, 40, 90), 6)
    cv2.line(canvas, torso_bot, (torso_bot[0] + 40, int(h * 0.75)), (40, 40, 90), 6)
    # left arm rests
    cv2.line(canvas, torso_top, (torso_top[0] - 60, int(h * 0.50)), (80, 120, 220), 6)

    # right arm follows the scripted hand
    hx, hy = int(hand[0]), int(hand[1])
    elbow = (
        (torso_top[0] + hx) // 2,
        (torso_top[1] + hy) // 2 - 20,
    )
    cv2.line(canvas, torso_top, elbow, (80, 120, 220), 6)
    cv2.line(canvas, elbow, (hx, hy), (80, 120, 220), 6)
    cv2.circle(canvas, (hx, hy), 12, (60, 200, 90), -1)  # hand marker


def _render_overlay(canvas: np.ndarray, phase: str, cycle: int, t_cycle: float) -> None:
    h, w = canvas.shape[:2]
    cv2.rectangle(canvas, (0, 0), (w, 40), (20, 20, 28), -1)
    cv2.putText(
        canvas,
        f"demo cycle {cycle + 1}   phase={phase:>8s}   t={t_cycle:5.2f}s",
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (220, 220, 230),
        1,
        cv2.LINE_AA,
    )


def generate(
    output: Path,
    *,
    cycles: int = 4,
    fps: int = 20,
    width: int = 960,
    height: int = 540,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"OpenCV could not open video writer for {output}")

    cycle_duration = sum(p[1] for p in _PHASES)
    total_frames = int(cycles * cycle_duration * fps)
    frame_idx = 0

    try:
        for cycle in range(cycles):
            t_cycle = 0.0
            for phase, duration, pos_fn in _PHASES:
                n = max(1, int(duration * fps))
                for k in range(n):
                    t_phase = k / max(1, n - 1) if n > 1 else 0.0
                    hand = pos_fn(t_phase, width, height)

                    canvas = np.full((height, width, 3), (18, 18, 24), dtype=np.uint8)
                    _draw_operator(canvas, hand)
                    _render_overlay(canvas, phase, cycle, t_cycle + k / fps)

                    writer.write(canvas)
                    frame_idx += 1
                t_cycle += duration
    finally:
        writer.release()

    print(f"Wrote {frame_idx} frames ({frame_idx / fps:.1f}s) to {output}", file=sys.stderr)
    return output


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate a synthetic demo video.")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("data/videos/demo.mp4"),
        help="Where to write the MP4 (parent dirs are created).",
    )
    ap.add_argument("--cycles", type=int, default=4, help="How many pick/place/screw cycles.")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--height", type=int, default=540)
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    out = generate(
        args.output,
        cycles=args.cycles,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    print(str(out))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
