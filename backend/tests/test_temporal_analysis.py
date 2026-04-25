"""Unit tests for the temporal action localiser."""
from __future__ import annotations

from app.vision.temporal_analysis import TemporalActionLocalizer
from app.vision.types import ActionScore


def _mk_scores(labels: list[str], fps: int = 10) -> list[ActionScore]:
    return [
        ActionScore(frame_index=i, timestamp_s=i / fps, scores={l: 0.9})
        for i, l in enumerate(labels)
    ]


def test_localises_monotonic_run():
    tal = TemporalActionLocalizer(window_size=3, min_segment_s=0.2)
    scores = _mk_scores(["pick"] * 20)
    segs = tal.localize(scores)
    assert len(segs) == 1
    assert segs[0].label == "pick"
    assert segs[0].duration_s > 1.5


def test_smooths_short_noise():
    tal = TemporalActionLocalizer(window_size=5, min_segment_s=0.5)
    labels = ["pick"] * 10 + ["screw"] + ["pick"] * 10
    segs = tal.localize(_mk_scores(labels))
    # Noise burst should be absorbed into the surrounding 'pick' run.
    assert [s.label for s in segs] == ["pick"]


def test_detects_transition():
    tal = TemporalActionLocalizer(window_size=3, min_segment_s=0.2)
    labels = ["pick"] * 10 + ["place"] * 10 + ["screw"] * 10
    segs = tal.localize(_mk_scores(labels))
    assert [s.label for s in segs] == ["pick", "place", "screw"]
