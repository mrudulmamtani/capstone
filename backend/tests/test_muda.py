"""Tests for the Muda / waste detector."""
from __future__ import annotations

from app.analytics.muda import WasteFinding, detect_muda
from app.vision.temporal_analysis import ActionSegment


def _seg(label: str, start_s: float, end_s: float) -> ActionSegment:
    return ActionSegment(
        label=label,
        start_s=start_s,
        end_s=end_s,
        confidence=0.9,
        frame_count=max(1, int((end_s - start_s) * 10)),
        per_frame_labels=[label] * max(1, int((end_s - start_s) * 10)),
    )


def test_empty_input_returns_empty_report():
    rep = detect_muda([])
    assert rep.idle_fraction == 0.0
    assert rep.move_fraction == 0.0
    assert rep.overprocess_steps == 0
    assert rep.findings == []


def test_high_idle_fraction_flags_waiting():
    segments = [
        _seg("idle", 0.0, 6.0),  # 60% idle
        _seg("pick", 6.0, 8.0),
        _seg("screw", 8.0, 10.0),
    ]
    rep = detect_muda(segments)

    assert rep.idle_fraction >= 0.55
    categories = [f.category for f in rep.findings]
    assert "waiting" in categories
    waiting = next(f for f in rep.findings if f.category == "waiting")
    # 60% idle should be the critical threshold, not just warning
    assert waiting.severity == "critical"


def test_moderate_idle_is_warning_not_critical():
    segments = [
        _seg("idle", 0.0, 2.5),  # 25% idle — above warning, below critical
        _seg("pick", 2.5, 5.0),
        _seg("place", 5.0, 7.5),
        _seg("screw", 7.5, 10.0),
    ]
    rep = detect_muda(segments)
    waiting = next((f for f in rep.findings if f.category == "waiting"), None)
    assert waiting is not None
    assert waiting.severity == "warning"


def test_high_move_fraction_flags_transport():
    segments = [
        _seg("pick", 0.0, 2.0),
        _seg("move", 2.0, 4.0),  # 40% move
        _seg("screw", 4.0, 5.0),
    ]
    rep = detect_muda(segments)

    assert rep.move_fraction > 0.15
    assert any(f.category == "transport" for f in rep.findings)


def test_over_processing_flagged_when_step_exceeds_tolerance():
    segments = [
        _seg("pick", 0.0, 1.0),   # within tolerance
        _seg("screw", 1.0, 10.0),  # 9s where tolerance is 2s → 4.5× → over
    ]
    tolerances = {"pick": 2.0, "screw": 2.0}
    rep = detect_muda(segments, step_tolerances=tolerances)

    assert rep.overprocess_steps >= 1
    assert any(f.category == "over_processing" for f in rep.findings)


def test_findings_include_evidence_payload():
    segments = [
        _seg("idle", 0.0, 4.0),
        _seg("pick", 4.0, 5.0),
    ]
    rep = detect_muda(segments)
    waiting = next(f for f in rep.findings if f.category == "waiting")
    assert isinstance(waiting, WasteFinding)
    assert "idle_fraction" in waiting.evidence
    assert 0.0 <= waiting.evidence["idle_fraction"] <= 1.0


def test_clean_run_produces_no_findings():
    segments = [
        _seg("pick", 0.0, 1.0),
        _seg("place", 1.0, 2.0),
        _seg("screw", 2.0, 5.0),
    ]
    # No idle, no move, no tolerances provided
    rep = detect_muda(segments)
    assert rep.findings == []
    assert rep.overprocess_steps == 0
