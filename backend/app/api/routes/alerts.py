"""Alert listing + acknowledgement."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    session_id: str | None = None,
    acknowledged: bool | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AlertOut]:
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    if session_id:
        stmt = stmt.where(Alert.session_id == session_id)
    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged == acknowledged)
    return [AlertOut.model_validate(a) for a in db.execute(stmt).scalars().all()]


@router.post("/{alert_id}/ack", response_model=AlertOut)
def acknowledge(
    alert_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AlertOut:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)
