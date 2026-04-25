"""Rule plugins for the real-time compliance engine.

Each rule implements :meth:`BaseRule.observe` which is called for every
action score the pipeline emits, and :meth:`BaseRule.finalise` which is
called once the session finishes. Rules are stateless w.r.t. each other —
use ``self.state`` for anything they need to remember across frames.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models.alert import AlertSeverity
from app.models.sop import SOP
from app.vision.types import ActionScore


@dataclass
class RuleResult:
    rule: str
    severity: AlertSeverity
    title: str
    message: str
    at_s: float
    evidence: dict = field(default_factory=dict)


class BaseRule(ABC):
    name: str = "base"
    severity: AlertSeverity = AlertSeverity.WARNING

    def __init__(self, sop: SOP | None = None) -> None:
        self.sop = sop
        self.state: dict = {}

    @abstractmethod
    def observe(self, score: ActionScore) -> list[RuleResult]:
        ...

    def finalise(self) -> list[RuleResult]:
        return []


# ---------------------------------------------------------------------------
# Skipped-step rule: follows the SOP step order and fires if the operator
# moves past a step without observing the expected label within tolerance.
# ---------------------------------------------------------------------------
class SkippedStepRule(BaseRule):
    name = "skipped_step"
    severity = AlertSeverity.WARNING

    def __init__(self, sop: SOP) -> None:
        super().__init__(sop)
        self.state = {"next_step": 0, "last_seen_label": None, "started_at": 0.0}

    def observe(self, score: ActionScore) -> list[RuleResult]:
        if not self.sop or not self.sop.steps:
            return []
        ns = self.state["next_step"]
        if ns >= len(self.sop.steps):
            return []
        expected = self.sop.steps[ns]
        label = score.top_label
        results: list[RuleResult] = []

        # advance when we finally see the expected label confidently
        if label == expected.action_label and score.top_score > 0.5:
            self.state["next_step"] = ns + 1
            self.state["started_at"] = score.timestamp_s
            return results

        # if we see a *later* step first, flag the skip
        upcoming = {s.action_label: s.step_index for s in self.sop.steps[ns + 1:]}
        if label in upcoming and score.top_score > 0.6:
            results.append(
                RuleResult(
                    rule=self.name,
                    severity=self.severity,
                    title=f"Skipped step: {expected.title}",
                    message=(
                        f"Operator appears to have skipped step {expected.step_index + 1} "
                        f"({expected.action_label}) and jumped to '{label}'."
                    ),
                    at_s=score.timestamp_s,
                    evidence={
                        "expected_step_index": expected.step_index,
                        "expected_label": expected.action_label,
                        "observed_label": label,
                    },
                )
            )
            # advance past the skipped step so we don't fire forever
            self.state["next_step"] = upcoming[label]
        return results


# ---------------------------------------------------------------------------
# Cycle-time drift: if the running clock exceeds 1.5× the SOP's target
# cycle time, raise a warning.
# ---------------------------------------------------------------------------
class CycleTimeDriftRule(BaseRule):
    name = "cycle_time_drift"
    severity = AlertSeverity.WARNING

    def __init__(self, sop: SOP) -> None:
        super().__init__(sop)
        self.state = {"fired": False}

    def observe(self, score: ActionScore) -> list[RuleResult]:
        if not self.sop or not self.sop.target_cycle_time_s:
            return []
        if self.state["fired"]:
            return []
        target = self.sop.target_cycle_time_s
        if score.timestamp_s > target * 1.5:
            self.state["fired"] = True
            return [
                RuleResult(
                    rule=self.name,
                    severity=AlertSeverity.CRITICAL
                    if score.timestamp_s > target * 2.0
                    else AlertSeverity.WARNING,
                    title="Cycle time drift",
                    message=(
                        f"Cycle is {score.timestamp_s:.1f}s — exceeds 1.5× the "
                        f"{target:.1f}s target."
                    ),
                    at_s=score.timestamp_s,
                    evidence={"target_s": target, "elapsed_s": score.timestamp_s},
                )
            ]
        return []


# ---------------------------------------------------------------------------
# PPE violation: fires if, at any point while the operator is working, we
# haven't seen the expected PPE (helmet / glasses / glove).
# ---------------------------------------------------------------------------
class PPEViolationRule(BaseRule):
    name = "ppe_violation"
    severity = AlertSeverity.CRITICAL

    _PPE_DETECTION_HINTS = {
        "helmet": {"helmet", "hard_hat"},
        "glasses": {"glasses", "goggles"},
        "glove": {"glove", "gloves"},
        "vest": {"vest", "high_vis"},
    }

    def __init__(self, sop: SOP, window_s: float = 5.0) -> None:
        super().__init__(sop)
        required: set[str] = set()
        for step in sop.steps:
            required.update((p.lower() for p in (step.required_ppe or [])))
        self.required = required
        self.window_s = window_s
        self.state = {"last_seen": {p: -999.0 for p in required}, "fired": set()}

    def observe(self, score: ActionScore) -> list[RuleResult]:
        if not self.required:
            return []
        detected_labels = set(
            (score.scores.get("_detections") or []) if isinstance(score.scores, dict) else []
        )
        for ppe in self.required:
            hints = self._PPE_DETECTION_HINTS.get(ppe, {ppe})
            if hints & detected_labels:
                self.state["last_seen"][ppe] = score.timestamp_s

        results: list[RuleResult] = []
        for ppe, last in self.state["last_seen"].items():
            if ppe in self.state["fired"]:
                continue
            if score.timestamp_s - last > self.window_s:
                self.state["fired"].add(ppe)
                results.append(
                    RuleResult(
                        rule=self.name,
                        severity=self.severity,
                        title=f"PPE violation: {ppe}",
                        message=f"Required '{ppe}' not detected for "
                        f"{self.window_s:.0f}s at t={score.timestamp_s:.1f}s.",
                        at_s=score.timestamp_s,
                        evidence={"ppe": ppe, "window_s": self.window_s},
                    )
                )
        return results


def default_rules(sop: SOP) -> list[BaseRule]:
    return [SkippedStepRule(sop), CycleTimeDriftRule(sop), PPEViolationRule(sop)]
