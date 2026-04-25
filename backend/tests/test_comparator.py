"""Tests for Golden Batch comparator (Needleman-Wunsch alignment)."""
from __future__ import annotations

from dataclasses import dataclass

from app.sop.comparator import GoldenBatchComparator, _align
from app.vision.temporal_analysis import ActionSegment


# ---------------------------------------------------------------------------
# Lightweight SOP/SOPStep stand-ins so we can unit-test the comparator without
# bringing up a database session. The comparator only reads ``.id``,
# ``.steps``, ``.target_cycle_time_s`` on SOP and ``.action_label``,
# ``.step_index``, ``.target_duration_s``, ``.tolerance_s`` on steps.
# ---------------------------------------------------------------------------
@dataclass
class _FakeStep:
    step_index: int
    action_label: str
    target_duration_s: float
    tolerance_s: float = 1.0


@dataclass
class _FakeSOP:
    id: str
    steps: list[_FakeStep]
    target_cycle_time_s: float = 0.0


def _seg(label: str, start_s: float, end_s: float, confidence: float = 0.9) -> ActionSegment:
    return ActionSegment(
        label=label,
        start_s=start_s,
        end_s=end_s,
        confidence=confidence,
        frame_count=max(1, int((end_s - start_s) * 10)),
        per_frame_labels=[label] * max(1, int((end_s - start_s) * 10)),
    )


# ---------------------------------------------------------------------------
# Alignment primitive — pure function, easy to characterise directly.
# ---------------------------------------------------------------------------
def test_align_identical_sequences():
    a = ["pick", "place", "screw"]
    b = ["pick", "place", "screw"]
    pairs = _align(a, b)
    assert pairs == [(0, 0), (1, 1), (2, 2)]


def test_align_detects_skip():
    # "place" is missing from observed
    pairs = _align(["pick", "place", "screw"], ["pick", "screw"])
    # One gap on the observed side
    assert (1, None) in pairs
    # And both real matches survive
    assert (0, 0) in pairs


def test_align_detects_extra():
    # Extra "inspect" inserted by trainee
    pairs = _align(["pick", "screw"], ["pick", "inspect", "screw"])
    # One gap on the expected side
    assert any(p[0] is None and p[1] is not None for p in pairs)


# ---------------------------------------------------------------------------
# GoldenBatchComparator behaviour against small fixtures.
# ---------------------------------------------------------------------------
def test_perfect_run_is_zero_deviation():
    sop = _FakeSOP(
        id="sop-1",
        steps=[
            _FakeStep(0, "pick", 2.0, 0.5),
            _FakeStep(1, "place", 2.0, 0.5),
            _FakeStep(2, "screw", 3.0, 1.0),
        ],
        target_cycle_time_s=7.0,
    )
    observed = [
        _seg("pick", 0.0, 2.0),
        _seg("place", 2.0, 4.0),
        _seg("screw", 4.0, 7.0),
    ]

    cmp = GoldenBatchComparator().compare(sop, observed)

    assert cmp.total_steps == 3
    assert cmp.matched == 3
    assert cmp.skipped == []
    assert cmp.extra == []
    assert cmp.deviation_score == 0.0
    assert all(s.status == "match" for s in cmp.per_step)
    assert all(s.within_tolerance for s in cmp.per_step)


def test_skipped_step_is_penalised():
    sop = _FakeSOP(
        id="sop-2",
        steps=[
            _FakeStep(0, "pick", 2.0),
            _FakeStep(1, "place", 2.0),
            _FakeStep(2, "screw", 3.0),
        ],
        target_cycle_time_s=7.0,
    )
    # Operator skipped "place"
    observed = [
        _seg("pick", 0.0, 2.0),
        _seg("screw", 2.0, 5.0),
    ]

    cmp = GoldenBatchComparator().compare(sop, observed)

    assert "place" in cmp.skipped
    assert cmp.matched == 2
    assert cmp.deviation_score > 0.0
    # "missing" entry surfaces in per-step detail
    statuses = [s.status for s in cmp.per_step]
    assert "missing" in statuses


def test_extra_action_is_penalised():
    sop = _FakeSOP(
        id="sop-3",
        steps=[
            _FakeStep(0, "pick", 2.0),
            _FakeStep(1, "screw", 3.0),
        ],
        target_cycle_time_s=5.0,
    )
    # Operator added an extra "inspect"
    observed = [
        _seg("pick", 0.0, 2.0),
        _seg("inspect", 2.0, 3.0),
        _seg("screw", 3.0, 6.0),
    ]

    cmp = GoldenBatchComparator().compare(sop, observed)

    assert "inspect" in cmp.extra
    assert cmp.deviation_score > 0.0


def test_idle_segments_are_ignored():
    sop = _FakeSOP(
        id="sop-4",
        steps=[_FakeStep(0, "pick", 2.0), _FakeStep(1, "place", 2.0)],
        target_cycle_time_s=4.0,
    )
    observed = [
        _seg("idle", 0.0, 1.0),   # should be filtered out
        _seg("pick", 1.0, 3.0),
        _seg("idle", 3.0, 3.5),   # also filtered
        _seg("place", 3.5, 5.5),
    ]

    cmp = GoldenBatchComparator().compare(sop, observed)

    assert cmp.matched == 2
    assert cmp.extra == []  # idle doesn't become "extra"


def test_cycle_time_drift_contributes_to_deviation():
    sop = _FakeSOP(
        id="sop-5",
        steps=[_FakeStep(0, "pick", 2.0, 0.5), _FakeStep(1, "place", 2.0, 0.5)],
        target_cycle_time_s=4.0,
    )
    # Operator took 2× the target cycle time
    observed = [
        _seg("pick", 0.0, 4.0),
        _seg("place", 4.0, 8.0),
    ]

    cmp = GoldenBatchComparator().compare(sop, observed)

    # Cycle time drift is a fraction of the total deviation score
    assert cmp.deviation_score > 0.0
    assert cmp.cycle_time_s > cmp.target_cycle_time_s
    # Per-step detail flags the tolerance breach
    assert not all(s.within_tolerance for s in cmp.per_step)
