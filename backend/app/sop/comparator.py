"""Golden Batch comparator.

Aligns a trainee's action sequence against the published SOP and scores the
deviation — skipped steps, extra steps, out-of-order steps, and duration
anomalies. The alignment uses Needleman-Wunsch (global sequence alignment)
on action labels; duration comparisons are per-matched-step.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.sop import SOP
from app.vision.temporal_analysis import ActionSegment


@dataclass
class StepCompare:
    step_index: int
    expected_label: str
    actual_label: str | None
    expected_duration_s: float
    actual_duration_s: float | None
    within_tolerance: bool
    status: str  # "match" | "missing" | "extra" | "mislabel"


@dataclass
class SessionComparison:
    sop_id: str
    total_steps: int
    matched: int
    skipped: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    out_of_order: int = 0
    cycle_time_s: float = 0.0
    target_cycle_time_s: float = 0.0
    deviation_score: float = 0.0
    per_step: list[StepCompare] = field(default_factory=list)


class GoldenBatchComparator:
    def compare(
        self,
        sop: SOP,
        observed: list[ActionSegment],
    ) -> SessionComparison:
        expected = [s for s in sop.steps]
        observed_nonidle = [o for o in observed if o.label != "idle"]

        # ------- sequence alignment ---------------------------------------
        alignment = _align(
            [s.action_label for s in expected],
            [o.label for o in observed_nonidle],
        )

        matched = 0
        skipped: list[str] = []
        extra: list[str] = []
        per_step: list[StepCompare] = []
        out_of_order = 0
        last_matched_index = -1

        for pair in alignment:
            e_idx, o_idx = pair
            if e_idx is None and o_idx is not None:
                extra.append(observed_nonidle[o_idx].label)
                per_step.append(
                    StepCompare(
                        step_index=-1,
                        expected_label="-",
                        actual_label=observed_nonidle[o_idx].label,
                        expected_duration_s=0.0,
                        actual_duration_s=observed_nonidle[o_idx].duration_s,
                        within_tolerance=False,
                        status="extra",
                    )
                )
            elif o_idx is None and e_idx is not None:
                skipped.append(expected[e_idx].action_label)
                per_step.append(
                    StepCompare(
                        step_index=expected[e_idx].step_index,
                        expected_label=expected[e_idx].action_label,
                        actual_label=None,
                        expected_duration_s=expected[e_idx].target_duration_s,
                        actual_duration_s=None,
                        within_tolerance=False,
                        status="missing",
                    )
                )
            else:
                assert e_idx is not None and o_idx is not None
                exp_step = expected[e_idx]
                obs_seg = observed_nonidle[o_idx]
                within = (
                    abs(obs_seg.duration_s - exp_step.target_duration_s)
                    <= exp_step.tolerance_s
                )
                status = (
                    "match"
                    if obs_seg.label == exp_step.action_label
                    else "mislabel"
                )
                if status == "match":
                    matched += 1
                if e_idx < last_matched_index:
                    out_of_order += 1
                last_matched_index = max(last_matched_index, e_idx)

                per_step.append(
                    StepCompare(
                        step_index=exp_step.step_index,
                        expected_label=exp_step.action_label,
                        actual_label=obs_seg.label,
                        expected_duration_s=exp_step.target_duration_s,
                        actual_duration_s=obs_seg.duration_s,
                        within_tolerance=within,
                        status=status,
                    )
                )

        cycle = sum(o.duration_s for o in observed_nonidle)
        target = sop.target_cycle_time_s or sum(s.target_duration_s for s in expected)

        # ------------------------------------------ composite deviation
        dev = 0.0
        dev += 0.4 * (len(skipped) / max(1, len(expected)))
        dev += 0.25 * (len(extra) / max(1, len(expected)))
        dev += 0.15 * (out_of_order / max(1, len(expected)))
        if target > 0:
            dev += 0.2 * min(1.0, abs(cycle - target) / target)
        dev = round(min(1.0, dev), 3)

        return SessionComparison(
            sop_id=sop.id,
            total_steps=len(expected),
            matched=matched,
            skipped=skipped,
            extra=extra,
            out_of_order=out_of_order,
            cycle_time_s=round(cycle, 3),
            target_cycle_time_s=round(target, 3),
            deviation_score=dev,
            per_step=per_step,
        )


# ----------------------------------------------- Needleman-Wunsch alignment
def _align(
    a: list[str],
    b: list[str],
    *,
    match: int = 2,
    mismatch: int = -1,
    gap: int = -2,
) -> list[tuple[int | None, int | None]]:
    """Return an alignment as a list of (a_idx, b_idx) pairs.

    ``None`` on one side denotes a gap (missing step or extra step).
    """
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = match if a[i - 1] == b[j - 1] else mismatch
            dp[i][j] = max(
                dp[i - 1][j - 1] + s,
                dp[i - 1][j] + gap,
                dp[i][j - 1] + gap,
            )

    # trace back
    i, j = n, m
    pairs: list[tuple[int | None, int | None]] = []
    while i > 0 and j > 0:
        s = match if a[i - 1] == b[j - 1] else mismatch
        if dp[i][j] == dp[i - 1][j - 1] + s:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + gap:
            pairs.append((i - 1, None))
            i -= 1
        else:
            pairs.append((None, j - 1))
            j -= 1
    while i > 0:
        pairs.append((i - 1, None))
        i -= 1
    while j > 0:
        pairs.append((None, j - 1))
        j -= 1
    pairs.reverse()
    return pairs
