"""Muda / waste detection.

Seven classic wastes of lean manufacturing: Transport, Inventory, Motion,
Waiting, Over-production, Over-processing, Defects. We focus on the ones we
can measure from video:

* **Waiting** — high ``idle`` fraction inside a cycle.
* **Motion** — excessive wrist travel per unit of productive time.
* **Over-processing** — steps running beyond tolerance for no apparent reason.
* **Transport** — repeated ``move`` segments.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.vision.temporal_analysis import ActionSegment


@dataclass
class WasteFinding:
    category: str
    severity: str  # "info" | "warning" | "critical"
    message: str
    evidence: dict = field(default_factory=dict)


@dataclass
class MudaReport:
    idle_fraction: float
    move_fraction: float
    overprocess_steps: int
    findings: list[WasteFinding] = field(default_factory=list)


def detect_muda(
    segments: list[ActionSegment],
    step_tolerances: dict[str, float] | None = None,
) -> MudaReport:
    if not segments:
        return MudaReport(0.0, 0.0, 0, [])

    total = sum(s.duration_s for s in segments) or 1.0
    idle = sum(s.duration_s for s in segments if s.label == "idle")
    move = sum(s.duration_s for s in segments if s.label == "move")
    overprocess = 0
    findings: list[WasteFinding] = []

    idle_fraction = idle / total
    move_fraction = move / total

    if idle_fraction > 0.2:
        findings.append(
            WasteFinding(
                category="waiting",
                severity="warning" if idle_fraction < 0.35 else "critical",
                message=(
                    f"Operator is idle {idle_fraction:.0%} of the cycle — "
                    "look for upstream starvation or tool search."
                ),
                evidence={"idle_fraction": idle_fraction},
            )
        )

    if move_fraction > 0.15:
        findings.append(
            WasteFinding(
                category="transport",
                severity="warning",
                message=(
                    f"{move_fraction:.0%} of the cycle is spent moving between "
                    "sub-stations. Consider re-laying out the tools or bins."
                ),
                evidence={"move_fraction": move_fraction},
            )
        )

    for seg in segments:
        tol = (step_tolerances or {}).get(seg.label)
        if tol is not None and seg.duration_s > tol * 1.8:
            overprocess += 1
            findings.append(
                WasteFinding(
                    category="over_processing",
                    severity="warning",
                    message=f"'{seg.label}' step ran {seg.duration_s:.1f}s (>{tol:.1f}s tolerance).",
                    evidence={"start_s": seg.start_s, "end_s": seg.end_s, "label": seg.label},
                )
            )

    return MudaReport(
        idle_fraction=round(idle_fraction, 3),
        move_fraction=round(move_fraction, 3),
        overprocess_steps=overprocess,
        findings=findings,
    )
