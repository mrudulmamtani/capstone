"""Tests for the SOP generator against the offline stub LLM."""
from __future__ import annotations

from app.sop.generator import SOPGenerator, _suggest_tolerance, summarise_segments
from app.sop.llm import StubLLMClient
from app.vision.pipeline import PipelineResult
from app.vision.temporal_analysis import ActionSegment


def _seg(
    label: str,
    start_s: float,
    end_s: float,
    per_frame_labels: list[str] | None = None,
) -> ActionSegment:
    fc = max(1, int((end_s - start_s) * 10))
    return ActionSegment(
        label=label,
        start_s=start_s,
        end_s=end_s,
        confidence=0.9,
        frame_count=fc,
        per_frame_labels=per_frame_labels or [label] * fc,
    )


def _fake_pipeline_result(segments: list[ActionSegment]) -> PipelineResult:
    return PipelineResult(
        source="tests://demo.mp4",
        duration_s=segments[-1].end_s if segments else 0.0,
        frame_count=sum(s.frame_count for s in segments),
        segments=segments,
        heatmap_path=None,
        per_frame_scores=[],
    )


def test_generate_persists_sop_with_ordered_steps(db):
    segments = [
        _seg("idle", 0.0, 1.0),      # filtered out
        _seg("pick", 1.0, 3.0),
        _seg("place", 3.0, 5.0),
        _seg("screw", 5.0, 8.0),
    ]
    result = _fake_pipeline_result(segments)

    gen = SOPGenerator(llm=StubLLMClient(), min_step_duration_s=0.5)
    sop, stats = gen.generate(
        db,
        title="Assembly – Station 3",
        station="S3",
        pipeline_result=result,
        description="Door handle assembly.",
        required_ppe=["glasses", "glove"],
    )

    assert sop.id is not None
    assert sop.title == "Assembly – Station 3"
    assert sop.station == "S3"
    # idle filtered; three real steps remain
    assert len(sop.steps) == 3
    assert [s.action_label for s in sop.steps] == ["pick", "place", "screw"]
    # step indices are assigned in order
    assert [s.step_index for s in sop.steps] == [0, 1, 2]
    # target cycle time sums non-idle steps
    assert abs(sop.target_cycle_time_s - 7.0) < 1e-6
    # markdown rendered and includes the title
    assert sop.rendered_markdown is not None
    assert "Assembly – Station 3" in sop.rendered_markdown
    # generation metadata captures provider + counts
    assert sop.generation_metadata["llm_provider"] == "stub"
    assert sop.generation_metadata["segment_count"] == len(segments)

    # stats mirror reality
    assert stats.total_steps == len(segments)
    assert stats.kept_steps == 3
    assert stats.llm_provider == "stub"


def test_short_segments_are_filtered(db):
    segments = [
        _seg("pick", 0.0, 0.1),   # below 0.5s floor
        _seg("place", 0.1, 2.0),
    ]
    result = _fake_pipeline_result(segments)
    gen = SOPGenerator(llm=StubLLMClient(), min_step_duration_s=0.5)
    sop, stats = gen.generate(
        db,
        title="Short filter",
        station="S1",
        pipeline_result=result,
    )
    assert [s.action_label for s in sop.steps] == ["place"]
    assert stats.kept_steps == 1


def test_ppe_is_propagated_to_every_step(db):
    segments = [_seg("pick", 0.0, 2.0), _seg("screw", 2.0, 4.0)]
    result = _fake_pipeline_result(segments)
    gen = SOPGenerator(llm=StubLLMClient())
    sop, _ = gen.generate(
        db,
        title="PPE test",
        station="S2",
        pipeline_result=result,
        required_ppe=["helmet", "glasses"],
    )
    for step in sop.steps:
        assert step.required_ppe == ["helmet", "glasses"]


def test_stub_markdown_has_step_headings(db):
    segments = [
        _seg("pick", 0.0, 1.0),
        _seg("place", 1.0, 2.0),
        _seg("screw", 2.0, 5.0),
    ]
    result = _fake_pipeline_result(segments)
    gen = SOPGenerator(llm=StubLLMClient())
    sop, _ = gen.generate(
        db, title="Markdown shape", station="S1", pipeline_result=result
    )
    md = sop.rendered_markdown or ""
    assert "## Procedure" in md
    assert "### Step 1" in md
    assert "### Step 3" in md
    assert "Safety & quality" in md


def test_suggest_tolerance_tracks_label_stability():
    # Fully stable labels → tight tolerance (~duration * 0.2, floored at 0.8)
    stable = ActionSegment(
        label="pick",
        start_s=0.0,
        end_s=2.0,
        confidence=0.95,
        frame_count=20,
        per_frame_labels=["pick"] * 20,
    )
    tight = _suggest_tolerance(stable)

    # Shaky — same length, but only 50% agreement → 1.5× widening kicks in
    shaky = ActionSegment(
        label="pick",
        start_s=0.0,
        end_s=2.0,
        confidence=0.6,
        frame_count=20,
        per_frame_labels=["pick"] * 10 + ["reach"] * 10,
    )
    loose = _suggest_tolerance(shaky)
    assert loose > tight


def test_summarise_segments_empty():
    assert summarise_segments([]) == {"total": 0}


def test_summarise_segments_computes_means():
    segments = [
        _seg("idle", 0.0, 2.0),
        _seg("pick", 2.0, 4.0),
        _seg("place", 4.0, 6.0),
        _seg("screw", 6.0, 10.0),
    ]
    summary = summarise_segments(segments)
    assert summary["total"] == 4
    assert summary["non_idle"] == 3
    # mean of 2.0, 2.0, 4.0
    assert abs(summary["mean_step_s"] - (8 / 3)) < 1e-6
    assert summary["max_step_s"] == 4.0
    assert set(summary["labels"]) == {"idle", "pick", "place", "screw"}
