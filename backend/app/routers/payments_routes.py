from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/me", response_model=list[schemas.PaymentOut])
def my_payments(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Customers see their invoices; workers see their payout breakdown."""
    query = db.query(models.Payment).join(
        models.Booking, models.Payment.booking_id == models.Booking.id
    )
    if current_user.role == "customer":
        query = query.filter(models.Booking.customer_id == current_user.id)
    elif current_user.role == "worker":
        profile = auth.find_worker_profile(db, current_user.id)
        if profile is None:
            return []
        query = query.filter(models.Booking.worker_id == profile.id)

    return query.order_by(models.Payment.created_at.desc()).all()
