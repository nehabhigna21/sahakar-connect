from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, bandit, models, payments, piggybank, schemas
from ..database import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=schemas.BookingOut)
def create_booking(
    payload: schemas.BookingCreate,
    current_user: models.User = Depends(auth.require_role("customer")),
    db: Session = Depends(get_db),
):
    category = (
        db.query(models.ServiceCategory)
        .filter(models.ServiceCategory.id == payload.category_id)
        .first()
    )
    if category is None:
        raise HTTPException(status_code=400, detail="Unknown category")

    booking = models.Booking(
        customer_id=current_user.id,
        category_id=category.id,
        lat=payload.lat,
        lng=payload.lng,
        zone=payload.zone,
        is_emergency=payload.is_emergency,
        scheduled_at=payload.scheduled_at,
        status="pending",
        price=category.base_price,
    )

    match = bandit.pick_worker(
        db,
        category,
        payload.zone,
        lat=payload.lat,
        lng=payload.lng,
        is_emergency=payload.is_emergency,
    )
    booking.match_reason = match.reason
    if match.worker is not None:
        booking.worker_id = match.worker.id
        booking.status = "matched"

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("", response_model=list[schemas.BookingOut])
def list_my_bookings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Booking)
    if current_user.role == "customer":
        query = query.filter(models.Booking.customer_id == current_user.id)
    elif current_user.role == "worker":
        profile = auth.find_worker_profile(db, current_user.id)
        if profile is None:
            return []
        query = query.filter(models.Booking.worker_id == profile.id)
    return query.order_by(models.Booking.created_at.desc()).all()


@router.post("/{booking_id}/complete", response_model=schemas.BookingOut)
def complete_booking(
    booking_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if current_user.role == "customer" and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if current_user.role == "worker":
        profile = auth.find_worker_profile(db, current_user.id)
        if profile is None or booking.worker_id != profile.id:
            raise HTTPException(status_code=403, detail="Not your booking")

    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is cancelled")

    booking.status = "completed"
    payments.create_payment(db, booking)
    piggybank.credit_patronage(db, booking)
    db.commit()
    db.refresh(booking)
    return booking
