from sqlalchemy.orm import Session

from . import models

# Flat fee per completed job - not a percentage cut. A worker on a
# Rs.5000 job and one on a Rs.300 job pay the same amount, so the fee
# share shrinks as the job gets bigger, unlike a commission.
PLATFORM_FLAT_FEE = 49.0


def create_payment(db: Session, booking: models.Booking) -> models.Payment:
    """Create (or return the existing) payment for a completed booking,
    with the platform fee and worker payout broken out explicitly."""
    existing = (
        db.query(models.Payment)
        .filter(models.Payment.booking_id == booking.id)
        .first()
    )
    if existing is not None:
        return existing

    fee = min(PLATFORM_FLAT_FEE, booking.price)
    payout = round(booking.price - fee, 2)

    payment = models.Payment(
        booking_id=booking.id,
        amount=booking.price,
        platform_fee=fee,
        worker_payout=payout,
        status="paid",
        invoice_note=(
            f"Flat platform fee of Rs.{fee:.2f} - worker keeps Rs.{payout:.2f}"
        ),
    )
    db.add(payment)
    return payment
