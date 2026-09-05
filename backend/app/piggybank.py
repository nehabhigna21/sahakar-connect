from sqlalchemy.orm import Session

from . import models

# Share of a completed job's price credited to an enrolled worker's
# equity ledger. Kept separate from the platform fee - this comes out
# of the co-op's margin, not the worker's take-home.
PATRONAGE_RATE = 0.05


def credit_patronage(db: Session, booking: models.Booking) -> models.PiggybankEntry | None:
    """Credit the patronage dividend for one completed booking, if the
    assigned worker is enrolled. Returns the new ledger entry, or None
    if there's no worker or the worker hasn't opted in."""
    if booking.worker_id is None:
        return None

    worker = (
        db.query(models.WorkerProfile)
        .filter(models.WorkerProfile.id == booking.worker_id)
        .first()
    )
    if worker is None or not worker.piggybank_enrolled:
        return None

    amount = round(booking.price * PATRONAGE_RATE, 2)
    worker.piggybank_balance += amount

    entry = models.PiggybankEntry(
        worker_id=worker.id,
        booking_id=booking.id,
        amount=amount,
        balance_after=worker.piggybank_balance,
    )
    db.add(entry)
    return entry
