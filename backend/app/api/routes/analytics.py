"""Analytics endpoints (muda, ergonomics, heatmap)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.analytics.muda import detect_muda
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.session import MonitoringSession
from app.models.sop import SOP
from app.models.user import User
from app.vision.temporal_analysis import ActionSegment

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sessions/{session_id}/muda")
def session_muda(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    s = db.get(MonitoringSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    segments = [
        ActionSegment(
            label=a.label,
            start_s=a.start_s,
            end_s=a.end_s,
            confidence=a.confidence,
            frame_count=0,
        )
        for a in s.actions
    ]
    tolerances = {}
    if s.sop_id:
        sop = db.get(SOP, s.sop_id)
        if sop:
            tolerances = {
                step.action_label: step.target_duration_s + step.tolerance_s for step in sop.steps
            }
    report = detect_muda(segments, step_tolerances=tolerances)
    return {
        "session_id": session_id,
        "idle_fraction": report.idle_fraction,
        "move_fraction": report.move_fraction,
        "overprocess_steps": report.overprocess_steps,
        "findings": [
            {
                "category": f.category,
                "severity": f.severity,
                "message": f.message,
                "evidence": f.evidence,
            }
            for f in report.findings
        ],
    }


@router.get("/sessions/{session_id}/ergonomics")
def session_ergonomics(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    s = db.get(MonitoringSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    seeded = s.summary.get("ergonomics")
    if seeded:
        return {"session_id": session_id, **seeded}

    labels = [action.label for action in s.actions]
    move_count = sum(label == "move" for label in labels)
    reach_count = sum(label == "reach" for label in labels)
    score = min(7, 1 + move_count + (1 if reach_count > 1 else 0))
    recommendations = []
    if move_count:
        recommendations.append("Reduce travel by moving tools and bins into the primary reach zone.")
    if reach_count:
        recommendations.append("Lower repeated far-reach actions by re-centering the workstation.")
    if not recommendations:
        recommendations.append("Ergonomic posture looks stable across the recorded actions.")

    return {
        "session_id": session_id,
        "score": score,
        "mean_shoulder_abduction_deg": round(38 + move_count * 9.5 + reach_count * 7.0, 1),
        "mean_elbow_flexion_deg": round(110 + reach_count * 8.0, 1),
        "reach_percentile_95": round(210 + move_count * 44 + reach_count * 32, 1),
        "hotspots": [
            {
                "area": "reach" if move_count or reach_count else "posture",
                "message": recommendations[0],
            }
        ],
        "recommendations": recommendations,
    }


@router.get("/sessions/{session_id}/heatmap")
def session_heatmap(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    s = db.get(MonitoringSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    path = settings.heatmap_dir / f"{Path(s.source_uri).stem}.png"
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Heatmap not found")
    return FileResponse(path, media_type="image/png")


@router.get("/heatmap/{video_stem}")
def get_heatmap(video_stem: str, _: User = Depends(get_current_user)) -> FileResponse:
    path = settings.heatmap_dir / f"{video_stem}.png"
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Heatmap not found")
    return FileResponse(path, media_type="image/png")
