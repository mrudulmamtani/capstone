"""Auto-SOP generation.

Takes a :class:`PipelineResult` from the vision pipeline and turns it into
a persisted :class:`SOP` with ordered :class:`SOPStep` children, including
the rendered markdown document produced by the LLM.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.sop import SOP, SOPStatus, SOPStep
from app.sop.llm import LLMClient, get_llm_client
from app.vision.pipeline import PipelineResult
from app.vision.temporal_analysis import ActionSegment

log = get_logger(__name__)


_SYSTEM_PROMPT = (
    "You are a senior manufacturing engineer writing a Standard Operating "
    "Procedure. You receive a structured JSON description of a gold-standard "
    "operator's actions extracted from video. Produce a clear, numbered, "
    "auditable SOP in Markdown. Each step must describe: what the operator "
    "does, how long it should take, and what 'done' looks like. Be concrete "
    "and avoid filler. Include a short Safety & Quality section."
)


@dataclass
class GenerationStats:
    total_steps: int
    kept_steps: int
    target_cycle_time_s: float
    llm_provider: str


class SOPGenerator:
    def __init__(
        self,
        llm: LLMClient | None = None,
        idle_label: str = "idle",
        min_step_duration_s: float = 0.6,
    ) -> None:
        self.llm = llm or get_llm_client()
        self.idle_label = idle_label
        self.min_step_duration_s = min_step_duration_s

    # ---------------------------------------------------------------- main
    def generate(
        self,
        db: Session,
        *,
        title: str,
        station: str,
        pipeline_result: PipelineResult,
        description: str | None = None,
        required_ppe: list[str] | None = None,
    ) -> tuple[SOP, GenerationStats]:
        steps = self._filter_steps(pipeline_result.segments)
        target_cycle = sum(s.duration_s for s in steps)

        payload = {
            "title": title,
            "station": station,
            "description": description or "",
            "required_ppe": required_ppe or [],
            "target_cycle_time_s": target_cycle,
            "steps": [
                {
                    "label": s.label,
                    "start_s": round(s.start_s, 3),
                    "end_s": round(s.end_s, 3),
                    "target_duration_s": round(s.duration_s, 3),
                    "tolerance_s": round(_suggest_tolerance(s), 2),
                    "confidence": round(s.confidence, 3),
                }
                for s in steps
            ],
        }

        markdown = self.llm.complete(
            system=_SYSTEM_PROMPT,
            user=(
                "Generate the SOP for the following gold-standard reference. "
                "Respond with Markdown only, no preface.\n\n"
                f"<payload>{json.dumps(payload)}</payload>"
            ),
            max_tokens=2000,
        )

        sop = SOP(
            title=title,
            station=station,
            description=description,
            status=SOPStatus.DRAFT,
            source_video_path=pipeline_result.source,
            target_cycle_time_s=target_cycle,
            rendered_markdown=markdown,
            generation_metadata={
                "llm_provider": self.llm.provider,
                "frame_count": pipeline_result.frame_count,
                "duration_s": pipeline_result.duration_s,
                "segment_count": len(pipeline_result.segments),
            },
        )

        for i, seg in enumerate(steps):
            step = SOPStep(
                step_index=i,
                action_label=seg.label,
                title=_step_title(seg.label, i),
                instruction=_step_instruction(seg.label),
                target_duration_s=round(seg.duration_s, 3),
                tolerance_s=round(_suggest_tolerance(seg), 2),
                clip_start_s=round(seg.start_s, 3),
                clip_end_s=round(seg.end_s, 3),
                required_ppe=required_ppe or [],
            )
            sop.steps.append(step)

        db.add(sop)
        db.commit()
        db.refresh(sop)

        stats = GenerationStats(
            total_steps=len(pipeline_result.segments),
            kept_steps=len(steps),
            target_cycle_time_s=target_cycle,
            llm_provider=self.llm.provider,
        )
        log.info("sop.generated", sop_id=sop.id, **stats.__dict__)
        return sop, stats

    # --------------------------------------------------------------- helpers
    def _filter_steps(self, segments: list[ActionSegment]) -> list[ActionSegment]:
        return [
            s
            for s in segments
            if s.label != self.idle_label and s.duration_s >= self.min_step_duration_s
        ]


def _suggest_tolerance(seg: ActionSegment) -> float:
    """Suggest a step tolerance from the per-frame label confidence stability."""
    base = max(0.8, seg.duration_s * 0.2)
    # Use per-frame label agreement as a proxy for process variance.
    same = sum(1 for l in seg.per_frame_labels if l == seg.label)
    agreement = same / max(1, len(seg.per_frame_labels))
    if agreement < 0.8:
        base *= 1.5
    return round(base, 2)


def _step_title(label: str, i: int) -> str:
    nice = {
        "reach": "Reach for component",
        "pick": "Pick up component",
        "place": "Place into fixture",
        "screw": "Fasten with tool",
        "inspect": "Inspect",
        "move": "Move to next station",
    }.get(label, label.title())
    return f"Step {i + 1}: {nice}"


def _step_instruction(label: str) -> str:
    return {
        "reach": "Extend the dominant arm toward the component bin. Keep shoulders square to the bench.",
        "pick": "Grasp the component firmly between thumb and forefinger; lift without dragging.",
        "place": "Align the component with the fixture keyway and set it down — do not press.",
        "screw": "Engage the tool, keep the bit perpendicular, drive until torque clicks.",
        "inspect": "Visually confirm seating and orientation before releasing.",
        "move": "Shift weight to the opposite foot and pivot toward the next sub-station.",
        "idle": "Pause. No action required.",
    }.get(label, "Follow the reference clip.")


def summarise_segments(segments: list[ActionSegment]) -> dict:
    """Small aggregate useful for the UI."""
    if not segments:
        return {"total": 0}
    durations = [s.duration_s for s in segments if s.label != "idle"]
    return {
        "total": len(segments),
        "non_idle": len(durations),
        "mean_step_s": statistics.mean(durations) if durations else 0,
        "max_step_s": max(durations) if durations else 0,
        "labels": sorted({s.label for s in segments}),
    }
