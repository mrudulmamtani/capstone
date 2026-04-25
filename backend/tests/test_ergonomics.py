"""Tests for the RULA-style ergonomic scorer."""
from __future__ import annotations

import numpy as np

from app.analytics.ergonomics import analyse_ergonomics, _angle


def _landmarks(
    shoulder=(0.5, 0.5),
    elbow=(0.5, 0.65),
    wrist=(0.5, 0.8),
    hip=(0.5, 0.9),
) -> np.ndarray:
    """Build a 33×3 landmark array with only the indices we score populated."""
    lm = np.zeros((33, 3), dtype=float)
    lm[:, 2] = 0.9  # visibility
    lm[12] = [*shoulder, 0.9]
    lm[14] = [*elbow, 0.9]
    lm[16] = [*wrist, 0.9]
    lm[24] = [*hip, 0.9]
    return lm


def test_empty_pose_frames_return_safe_score():
    rep = analyse_ergonomics([])
    assert rep.sample_count == 0
    assert rep.score == 1
    assert rep.hotspots == []


def test_neutral_posture_scores_low():
    # Arm hanging down, elbow gently flexed — baseline posture.
    frames = [_landmarks() for _ in range(5)]
    rep = analyse_ergonomics(frames)
    assert rep.sample_count == 5
    assert rep.score <= 2  # no major hotspots


def test_shoulder_abduction_raises_score():
    # Arm extended laterally: elbow far to the side of the shoulder
    raised = [
        _landmarks(
            shoulder=(0.5, 0.5),
            elbow=(0.9, 0.5),   # way out to the side → big shoulder angle
            wrist=(1.0, 0.5),
        )
        for _ in range(5)
    ]
    rep = analyse_ergonomics(raised)
    assert rep.mean_shoulder_abduction_deg > 60
    assert rep.score >= 3
    assert any(h["area"] == "shoulder" for h in rep.hotspots)


def test_elbow_outside_comfort_band_is_flagged():
    # Hyper-extended elbow (nearly straight → angle close to 180)
    straight = [
        _landmarks(
            shoulder=(0.5, 0.5),
            elbow=(0.5, 0.65),
            wrist=(0.5, 0.8),  # perfectly collinear with shoulder & elbow
        )
        for _ in range(5)
    ]
    rep = analyse_ergonomics(straight)
    # Collinear shoulder-elbow-wrist → ~180°, outside 60-135° comfort band
    assert rep.mean_elbow_flexion_deg > 135
    assert rep.score > 1
    assert any(h["area"] == "elbow" for h in rep.hotspots)


def test_score_is_clamped_to_7():
    # Combine extreme shoulder + reach to push score past 7
    extreme = [
        _landmarks(
            shoulder=(0.1, 0.5),
            elbow=(0.9, 0.3),
            wrist=(1.5, 0.1),   # way out of frame
        )
        for _ in range(3)
    ]
    rep = analyse_ergonomics(extreme, frame_size=(1.0, 1.0))
    assert rep.score <= 7  # must be clamped


def test_angle_helper_is_correct():
    # Right angle: a=(1,0), b=(0,0), c=(0,1) → 90°
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([0.0, 1.0])
    assert abs(_angle(a, b, c) - 90.0) < 1e-4

    # Straight line: a=(-1,0), b=(0,0), c=(1,0) → 180°
    assert abs(_angle(np.array([-1.0, 0.0]), b, np.array([1.0, 0.0])) - 180.0) < 1e-4
