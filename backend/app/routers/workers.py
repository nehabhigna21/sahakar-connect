from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas, verification
from ..database import get_db

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/me", response_model=schemas.WorkerProfileOut)
def read_my_profile(
    current_user: models.User = Depends(auth.require_role("worker")),
    db: Session = Depends(get_db),
):
    profile = auth.find_worker_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")
    return profile


@router.patch("/me", response_model=schemas.WorkerProfileOut)
def update_my_profile(
    payload: schemas.WorkerProfileUpdate,
    current_user: models.User = Depends(auth.require_role("worker")),
    db: Session = Depends(get_db),
):
    profile = auth.find_worker_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/{worker_id}/verify", response_model=schemas.WorkerProfileOut)
def verify_worker(
    worker_id: int,
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Run the e-Shram/NSDC check against the worker's submitted ID and
    update their verification status accordingly."""
    profile = (
        db.query(models.WorkerProfile)
        .filter(models.WorkerProfile.id == worker_id)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    verified, note = verification.run_mock_eshram_check(profile)
    profile.verification_status = "verified" if verified else "rejected"
    profile.certification_note = note

    db.commit()
    db.refresh(profile)
    return profile
