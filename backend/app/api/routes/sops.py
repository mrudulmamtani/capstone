"""SOP CRUD + generation routes."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.sop import SOP, SOPStatus
from app.models.user import User, UserRole
from app.schemas.sop import SOPCreate, SOPGenerateRequest, SOPOut
from app.sop.generator import SOPGenerator
from app.vision.pipeline import VisionPipeline

log = get_logger(__name__)
router = APIRouter(prefix="/sops", tags=["sops"])


def _preferred_sops(sops: list[SOP]) -> list[SOP]:
    preferred: dict[tuple[str, str], SOP] = {}

    for sop in sops:
        key = (sop.title, sop.station)
        current = preferred.get(key)
        if current is None:
            preferred[key] = sop
            continue

        current_score = (len(current.steps), int(current.status == SOPStatus.PUBLISHED), current.updated_at)
        next_score = (len(sop.steps), int(sop.status == SOPStatus.PUBLISHED), sop.updated_at)
        if next_score > current_score:
            preferred[key] = sop

    return sorted(preferred.values(), key=lambda sop: sop.created_at, reverse=True)


@router.get("", response_model=list[SOPOut])
def list_sops(
    station: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SOPOut]:
    stmt = select(SOP).options(selectinload(SOP.steps)).order_by(SOP.created_at.desc())
    if station:
        stmt = stmt.where(SOP.station == station)
    sops = db.execute(stmt).scalars().all()
    return [SOPOut.model_validate(s) for s in _preferred_sops(sops)]


@router.get("/{sop_id}", response_model=SOPOut)
def get_sop(sop_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> SOPOut:
    sop = db.execute(
        select(SOP).options(selectinload(SOP.steps)).where(SOP.id == sop_id)
    ).scalar_one_or_none()
    if not sop:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SOP not found")
    return SOPOut.model_validate(sop)


@router.post("", response_model=SOPOut, status_code=status.HTTP_201_CREATED)
def create_sop(
    payload: SOPCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ENGINEER, UserRole.ADMIN)),
) -> SOPOut:
    sop = SOP(title=payload.title, station=payload.station, description=payload.description)
    db.add(sop)
    db.commit()
    db.refresh(sop)
    return SOPOut.model_validate(sop)


@router.post("/{sop_id}/publish", response_model=SOPOut)
def publish_sop(
    sop_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.SUPERVISOR, UserRole.ENGINEER, UserRole.ADMIN)),
) -> SOPOut:
    sop = db.get(SOP, sop_id)
    if not sop:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SOP not found")
    sop.status = SOPStatus.PUBLISHED
    db.commit()
    db.refresh(sop)
    return SOPOut.model_validate(sop)


@router.post("/upload-video")
def upload_video(
    file: Annotated[UploadFile, File(...)],
    _: User = Depends(require_role(UserRole.ENGINEER, UserRole.ADMIN)),
) -> dict:
    """Upload a reference video to ``data/videos/``."""
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing filename")
    target = settings.video_dir / file.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": str(target), "size": target.stat().st_size}


@router.post("/generate", response_model=SOPOut, status_code=status.HTTP_201_CREATED)
def generate_sop(
    payload: SOPGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ENGINEER, UserRole.ADMIN)),
) -> SOPOut:
    """Run the Phase-1 pipeline on ``source_video_path`` and persist the SOP."""
    src = Path(payload.source_video_path)
    if not src.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Video not found: {src}")

    pipeline = VisionPipeline()
    result = pipeline.run_batch(src, build_heatmap=True)
    generator = SOPGenerator()
    sop, stats = generator.generate(
        db,
        title=payload.title,
        station=payload.station,
        description=payload.description,
        pipeline_result=result,
        required_ppe=payload.required_ppe,
    )
    log.info("sop.generate.api", sop_id=sop.id, stats=stats.__dict__)
    return SOPOut.model_validate(sop)
