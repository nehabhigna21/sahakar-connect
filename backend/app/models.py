import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class Federation(Base):
    """A Labour Cooperative Federation/Society - the org an admin manages."""

    __tablename__ = "federations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)

    workers = relationship("WorkerProfile", back_populates="federation")


class ServiceCategory(Base):
    """A type of gig: electrician, plumber, cleaner, caregiver, etc."""

    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    base_price = Column(Float, default=300.0)


class User(Base):
    """Every person who can log in: customer, worker, or federation admin."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "customer" | "worker" | "admin"
    language_pref = Column(String, default="en")  # "en" | "hi"
    address = Column(String, default="")
    household_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    worker_profile = relationship(
        "WorkerProfile", back_populates="user", uselist=False
    )


class WorkerProfile(Base):
    """Extra data attached to a User with role='worker'."""

    __tablename__ = "worker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    federation_id = Column(Integer, ForeignKey("federations.id"), nullable=True)
    skills = Column(String, default="")  # comma-separated ServiceCategory names
    verification_status = Column(String, default="pending")  # pending|verified|rejected
    certification_note = Column(String, default="")
    eshram_id = Column(String, default="")  # e-Shram / NSDC registration number
    is_suspended = Column(Boolean, default=False)
    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    insurance_enrolled = Column(Boolean, default=False)
    welfare_fund_contributed = Column(Float, default=0.0)
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    zone = Column(String, default="Zone-1")
    is_available = Column(Boolean, default=True)

    # Patronage-dividend "piggybank": voluntary co-op equity stake.
    # Enrolled workers get a cut of each completed job's price credited
    # to piggybank_balance, tracked transaction-by-transaction below.
    piggybank_enrolled = Column(Boolean, default=False)
    piggybank_balance = Column(Float, default=0.0)

    user = relationship("User", back_populates="worker_profile")
    federation = relationship("Federation", back_populates="workers")


class Booking(Base):
    """One request from a customer for a service, moving through a lifecycle."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("worker_profiles.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    zone = Column(String, default="Zone-1")
    is_emergency = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, nullable=True)
    # pending -> matched -> in_progress -> completed  (or cancelled at any point)
    status = Column(String, default="pending")
    price = Column(Float, default=0.0)
    # Plain-language record of how the worker was picked, shown to the
    # worker as "why you were matched" - filled in at match time.
    match_reason = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Payment(Base):
    """A mock payment record - no real gateway, just an invoice trail."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    # Flat fee, not a percentage cut - same amount regardless of job price.
    platform_fee = Column(Float, default=0.0)
    worker_payout = Column(Float, default=0.0)
    status = Column(String, default="paid")  # paid | pending
    invoice_note = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Grievance(Base):
    """A complaint filed by a customer or worker, reviewed by a federation
    admin. A worker can only be suspended through resolving one of these -
    never automatically - so every suspension has a human decision behind
    it."""

    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)
    filed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    against_worker_id = Column(Integer, ForeignKey("worker_profiles.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    description = Column(String, nullable=False)
    # open -> resolved | dismissed
    status = Column(String, default="open")
    resolution_note = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class PiggybankEntry(Base):
    """One patronage-dividend credit into a worker's equity ledger.

    balance_after records the running total at that point, so the ledger
    is a readable audit trail rather than just a derived sum.
    """

    __tablename__ = "piggybank_entries"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("worker_profiles.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BanditArm(Base):
    """Thompson-sampling stats for one worker in one category and zone.

    alpha / beta start at 1 (uniform prior). Historic jobs bump them:
    rating >= 4 adds to alpha, otherwise beta.
    """

    __tablename__ = "bandit_arms"
    __table_args__ = (
        UniqueConstraint(
            "worker_id", "category_id", "zone", name="uq_bandit_arm_context"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("worker_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    zone = Column(String, nullable=False)
    alpha = Column(Float, default=1.0, nullable=False)
    beta = Column(Float, default=1.0, nullable=False)


class DemandForecast(Base):
    """Predicted demand for a zone/category on a given day-of-week.

    Rebuilt from historical booking counts (a prototype heuristic, not a
    live ML pipeline) and used to plan worker shifts ahead of time so
    workers get routed toward where jobs are actually expected.
    """

    __tablename__ = "demand_forecasts"
    __table_args__ = (
        UniqueConstraint(
            "zone", "category_id", "day_of_week", name="uq_forecast_context"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    zone = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    predicted_bookings = Column(Float, default=0.0, nullable=False)
    demand_level = Column(String, default="low", nullable=False)  # low | medium | high
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class WorkerShift(Base):
    """One assigned 'active day' for a worker in a zone/category.

    Guaranteeing a minimum number of these per week - spread across the
    worker's highest-demand zone/category combos, capped so nobody is
    overloaded - is how income volatility gets smoothed into a steady
    baseline: not idle too long, not overloaded either.
    """

    __tablename__ = "worker_shifts"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("worker_profiles.id"), nullable=False)
    zone = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    shift_date = Column(DateTime, nullable=False)
    is_baseline = Column(Boolean, default=True, nullable=False)  # guaranteed floor slot vs demand-driven extra
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
