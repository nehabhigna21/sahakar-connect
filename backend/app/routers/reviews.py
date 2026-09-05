from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, bandit, models, schemas
from ..database import get_db

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=schemas.ReviewOut)
def create_review(
    payload: schemas.ReviewCreate,
    current_user: models.User = Depends(auth.require_role("customer")),
    db: Session = Depends(get_db),
):
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1-5")

    booking = (
        db.query(models.Booking).filter(models.Booking.id == payload.booking_id).first()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="Booking must be completed first")

    existing = (
        db.query(models.Review)
        .filter(models.Review.booking_id == booking.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Review already exists")

    review = models.Review(
        booking_id=booking.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)

    bandit.record_reward(db, booking, payload.rating)

    if booking.worker_id is not None:
        worker = (
            db.query(models.WorkerProfile)
            .filter(models.WorkerProfile.id == booking.worker_id)
            .first()
        )
        if worker is not None:
            total = worker.rating_avg * worker.rating_count + payload.rating
            worker.rating_count += 1
            worker.rating_avg = total / worker.rating_count

    db.commit()
    db.refresh(review)
    return review
