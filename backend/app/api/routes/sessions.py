"""Monitoring session routes."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerts.engine import ComplianceEngine
from app.api.deps import get_current_user
from app.api.routes.monitor import publish_event
from app.core.logging import get_logger
from app.db.session import SessionLocal, get_db
from app.models.action import ActionEvent
from app.models.session import MonitoringSession, SessionStatus
from app.models.sop import SOP
from app.models.user import User
from app.schemas.session import SessionCreate, SessionOut, SessionSummary
from app.sop.comparator import GoldenBatchComparator
from app.vision.pipeline import VisionPipeline

log = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def list_sessions(
    sop_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SessionOut]:
    stmt = select(MonitoringSession).order_by(MonitoringSession.created_at.desc())
    if sop_id:
        stmt = stmt.where(MonitoringSession.sop_id == sop_id)
    rows = db.execute(stmt).scalars().all()
    return [SessionOut.model_validate(s) for s in rows]


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SessionOut:
    if payload.sop_id and not db.get(SOP, payload.sop_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SOP not found")

    session = MonitoringSession(
        sop_id=payload.sop_id,
        operator_ref=payload.operator_ref,
        source_uri=payload.source_uri,
        mode=payload.mode,
        status=SessionStatus.PENDING,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    bg.add_task(_run_session, session.id)
    return SessionOut.model_validate(session)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> SessionOut:
    s = db.get(MonitoringSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return SessionOut.model_validate(s)


@router.get("/{session_id}/summary", response_model=SessionSummary)
def session_summary(
    session_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> SessionSummary:
    s = db.get(MonitoringSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return SessionSummary(
        session_id=s.id,
        total_steps=int(s.summary.get("total_steps", 0)),
        matched_steps=int(s.summary.get("matched_steps", 0)),
        skipped_steps=list(s.summary.get("skipped_steps", [])),
        extra_steps=list(s.summary.get("extra_steps", [])),
        cycle_time_s=float(s.cycle_time_s or 0),
        target_cycle_time_s=s.summary.get("target_cycle_time_s"),
        deviation_score=float(s.deviation_score or 0),
        alerts=int(s.summary.get("alerts", 0)),
    )


# ----------------------------------------------------- background execution
def _run_session(session_id: str) -> None:
    """Run the batch pipeline + compliance engine for a session."""
    db = SessionLocal()
    try:
        sess = db.get(MonitoringSession, session_id)
        if not sess:
            log.warning("session.run.missing", session_id=session_id)
            return
        sess.status = SessionStatus.RUNNING
        sess.started_at = datetime.now(timezone.utc)
        db.commit()

        pipeline = VisionPipeline()
        result = pipeline.run_batch(sess.source_uri, build_heatmap=True)

        # persist action events
        for i, seg in enumerate(result.segments):
            if seg.label == "idle":
                continue
            db.add(
                ActionEvent(
                    session_id=sess.id,
                    step_index=i,
                    label=seg.label,
                    start_s=seg.start_s,
                    end_s=seg.end_s,
                    confidence=seg.confidence,
                )
            )

        summary: dict = {}
        alerts = 0
        if sess.sop_id:
            sop = db.get(SOP, sess.sop_id)
            if sop is not None:
                cmp = GoldenBatchComparator().compare(sop, result.segments)
                summary = {
                    "total_steps": cmp.total_steps,
                    "matched_steps": cmp.matched,
                    "skipped_steps": cmp.skipped,
                    "extra_steps": cmp.extra,
                    "out_of_order": cmp.out_of_order,
                    "target_cycle_time_s": cmp.target_cycle_time_s,
                    "heatmap_path": str(result.heatmap_path) if result.heatmap_path else None,
                }
                sess.cycle_time_s = cmp.cycle_time_s
                sess.deviation_score = cmp.deviation_score

                engine = ComplianceEngine(sop)
                for ev in engine.run(
                    result.per_frame_scores, db=db, session=sess
                ):
                    asyncio.run(publish_event(sess.id, {"kind": ev.kind, **ev.payload}))
                    if ev.kind == "alert":
                        alerts += 1

        sess.status = SessionStatus.COMPLETED
        sess.completed_at = datetime.now(timezone.utc)
        sess.summary = {**summary, "alerts": alerts}
        db.commit()
        log.info("session.run.complete", session_id=sess.id, alerts=alerts)
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("session.run.failed", session_id=session_id, error=str(exc))
        sess = db.get(MonitoringSession, session_id)
        if sess:
            sess.status = SessionStatus.FAILED
            db.commit()
    finally:
        db.close()
