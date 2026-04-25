"""Tests for the real-time compliance rule plugins."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.alerts.rules import (
    CycleTimeDriftRule,
    PPEViolationRule,
    SkippedStepRule,
    default_rules,
)
from app.vision.types import ActionScore


# ---------------------------------------------------------------------------
# Lightweight SOP/SOPStep stand-ins so rules can be exercised without a DB.
# ---------------------------------------------------------------------------
@dataclass
class _Step:
    step_index: int
    action_label: str
    title: str = ""
    required_ppe: list[str] = field(default_factory=list)


@dataclass
class _SOP:
    id: str
    steps: list[_Step]
    target_cycle_time_s: float = 0.0


def _score(label: str, t: float, confidence: float = 0.9) -> ActionScore:
    return ActionScore(
        frame_index=int(t * 10),
        timestamp_s=t,
        scores={label: confidence},
    )


# ---------------------------------------------------------------------------
# Skipped-step rule
# ---------------------------------------------------------------------------
def test_skipped_step_fires_when_operator_jumps_ahead():
    sop = _SOP(
        id="sop-skip",
        steps=[
            _Step(0, "pick", "Pick"),
            _Step(1, "place", "Place"),
            _Step(2, "screw", "Screw"),
        ],
    )
    rule = SkippedStepRule(sop)

    # Watch pick complete, then straight to screw — skipping place
    rule.observe(_score("pick", 0.5, 0.9))
    results = rule.observe(_score("screw", 1.0, 0.9))

    assert len(results) == 1
    assert results[0].rule == "skipped_step"
    assert "place" in results[0].evidence["expected_label"]


def test_skipped_step_silent_on_happy_path():
    sop = _SOP(
        id="sop-happy",
        steps=[_Step(0, "pick", "Pick"), _Step(1, "place", "Place")],
    )
    rule = SkippedStepRule(sop)
    r1 = rule.observe(_score("pick", 0.1, 0.9))
    r2 = rule.observe(_score("place", 1.1, 0.9))
    assert r1 == []
    assert r2 == []


# ---------------------------------------------------------------------------
# Cycle-time drift rule
# ---------------------------------------------------------------------------
def test_cycle_time_drift_fires_once_above_1_5x():
    sop = _SOP(id="sop-ct", steps=[], target_cycle_time_s=10.0)
    rule = CycleTimeDriftRule(sop)

    assert rule.observe(_score("pick", 5.0)) == []
    assert rule.observe(_score("pick", 12.0)) == []   # still below 1.5×
    fired = rule.observe(_score("pick", 16.0))         # 16 > 15 = 1.5 * 10
    assert len(fired) == 1
    # but only once — state flag prevents re-firing
    assert rule.observe(_score("pick", 20.0)) == []


def test_cycle_time_drift_escalates_above_2x():
    sop = _SOP(id="sop-ct2", steps=[], target_cycle_time_s=10.0)
    rule = CycleTimeDriftRule(sop)
    fired = rule.observe(_score("pick", 22.0))  # > 2× target
    assert len(fired) == 1
    # Severity should be CRITICAL (enum string value "critical")
    assert str(fired[0].severity.value).lower() == "critical"


def test_cycle_time_drift_quiet_without_target():
    sop = _SOP(id="sop-no-target", steps=[], target_cycle_time_s=0.0)
    rule = CycleTimeDriftRule(sop)
    assert rule.observe(_score("pick", 99.0)) == []


# ---------------------------------------------------------------------------
# PPE violation rule
# ---------------------------------------------------------------------------
def test_ppe_violation_fires_when_helmet_never_seen():
    sop = _SOP(
        id="sop-ppe",
        steps=[_Step(0, "pick", "Pick", required_ppe=["helmet"])],
    )
    rule = PPEViolationRule(sop, window_s=3.0)
    # Never observe a helmet detection → fire after window expires
    rule.observe(_score("pick", 1.0))
    fired = rule.observe(_score("pick", 5.0))
    assert len(fired) == 1
    assert fired[0].evidence["ppe"] == "helmet"


def test_ppe_violation_silent_if_nothing_required():
    sop = _SOP(id="sop-none", steps=[_Step(0, "pick", "Pick", required_ppe=[])])
    rule = PPEViolationRule(sop, window_s=1.0)
    assert rule.observe(_score("pick", 10.0)) == []


# ---------------------------------------------------------------------------
# default_rules wiring
# ---------------------------------------------------------------------------
def test_default_rules_returns_all_three_types():
    sop = _SOP(
        id="sop-default",
        steps=[_Step(0, "pick", "Pick", required_ppe=["helmet"])],
        target_cycle_time_s=5.0,
    )
    rules = default_rules(sop)
    names = {r.name for r in rules}
    assert names == {"skipped_step", "cycle_time_drift", "ppe_violation"}
