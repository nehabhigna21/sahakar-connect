import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/grievances", tags=["grievances"])


@router.post("", response_model=schemas.GrievanceOut)
def file_grievance(
    payload: schemas.GrievanceCreate,
    current_user: models.User = Depends(auth.require_role("customer", "worker")),
    db: Session = Depends(get_db),
):
    grievance = models.Grievance(
        filed_by_id=current_user.id,
        against_worker_id=payload.against_worker_id,
        booking_id=payload.booking_id,
        description=payload.description,
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)
    return grievance


@router.get("", response_model=list[schemas.GrievanceOut])
def list_grievances(
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """The federation dashboard's review queue, newest first."""
    return (
        db.query(models.Grievance)
        .order_by(models.Grievance.created_at.desc())
        .all()
    )


@router.post("/{grievance_id}/resolve", response_model=schemas.GrievanceOut)
def resolve_grievance(
    grievance_id: int,
    payload: schemas.GrievanceResolve,
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """A worker can only be suspended by resolving a grievance here -
    never automatically - so every suspension has a human review behind
    it."""
    grievance = (
        db.query(models.Grievance).filter(models.Grievance.id == grievance_id).first()
    )
    if grievance is None:
        raise HTTPException(status_code=404, detail="Grievance not found")
    if grievance.status != "open":
        raise HTTPException(status_code=400, detail="Grievance already resolved")
    if payload.status not in ("resolved", "dismissed"):
        raise HTTPException(status_code=400, detail="status must be resolved or dismissed")

    grievance.status = payload.status
    grievance.resolution_note = payload.resolution_note
    grievance.resolved_at = datetime.datetime.utcnow()

    if payload.suspend_worker and grievance.against_worker_id is not None:
        worker = (
            db.query(models.WorkerProfile)
            .filter(models.WorkerProfile.id == grievance.against_worker_id)
            .first()
        )
        if worker is not None:
            worker.is_suspended = True

    db.commit()
    db.refresh(grievance)
    return grievance
