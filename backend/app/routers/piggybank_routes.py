from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/piggybank", tags=["piggybank"])


@router.get("/me", response_model=list[schemas.PiggybankEntryOut])
def my_ledger(
    current_user: models.User = Depends(auth.require_role("worker")),
    db: Session = Depends(get_db),
):
    profile = auth.find_worker_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    return (
        db.query(models.PiggybankEntry)
        .filter(models.PiggybankEntry.worker_id == profile.id)
        .order_by(models.PiggybankEntry.created_at.desc())
        .all()
    )
