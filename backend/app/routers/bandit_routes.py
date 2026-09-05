from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, bandit, models, schemas
from ..database import get_db

router = APIRouter(prefix="/bandit", tags=["bandit"])


@router.get("/arms", response_model=list[schemas.BanditArmOut])
def list_arms(
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(models.BanditArm).all()


@router.post("/arms", response_model=schemas.BanditArmOut)
def set_arm_from_counts(
    payload: schemas.BanditArmManual,
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    worker = (
        db.query(models.WorkerProfile)
        .filter(models.WorkerProfile.id == payload.worker_id)
        .first()
    )
    if worker is None:
        raise HTTPException(status_code=400, detail="Unknown worker_id")
    category = (
        db.query(models.ServiceCategory)
        .filter(models.ServiceCategory.id == payload.category_id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=400, detail="Unknown category_id")

    try:
        arm = bandit.apply_historic_counts(
            db,
            payload.worker_id,
            payload.category_id,
            payload.zone,
            payload.successes,
            payload.failures,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    db.refresh(arm)
    return arm


@router.post("/seed-from-history", response_model=schemas.BanditSeedResult)
def seed_from_history(
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Rebuild every arm from completed bookings that already have reviews."""
    arms_written, jobs_counted = bandit.seed_from_reviews(db, reset=True)
    db.commit()
    return schemas.BanditSeedResult(
        arms_written=arms_written, jobs_counted=jobs_counted
    )
