import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: str  # "customer" | "worker" | "admin"
    language_pref: str = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    language_pref: str
    address: str
    household_verified: bool

    class Config:
        from_attributes = True  # lets us build this straight from a User ORM object


class UserAddressUpdate(BaseModel):
    address: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Worker ----------

class WorkerProfileUpdate(BaseModel):
    skills: Optional[str] = None  # comma-separated
    federation_id: Optional[int] = None
    certification_note: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    zone: Optional[str] = None
    is_available: Optional[bool] = None
    insurance_enrolled: Optional[bool] = None
    piggybank_enrolled: Optional[bool] = None
    eshram_id: Optional[str] = None


class WorkerProfileOut(BaseModel):
    id: int
    user_id: int
    federation_id: Optional[int]
    skills: str
    verification_status: str
    certification_note: str
    eshram_id: str
    is_suspended: bool
    rating_avg: float
    rating_count: int
    insurance_enrolled: bool
    welfare_fund_contributed: float
    lat: float
    lng: float
    zone: str
    is_available: bool
    piggybank_enrolled: bool
    piggybank_balance: float

    class Config:
        from_attributes = True


# ---------- Bookings ----------

class BookingCreate(BaseModel):
    category_id: int
    lat: float
    lng: float
    zone: str
    is_emergency: bool = False
    scheduled_at: Optional[datetime.datetime] = None


class BookingOut(BaseModel):
    id: int
    customer_id: int
    worker_id: Optional[int]
    category_id: int
    lat: float
    lng: float
    zone: str
    is_emergency: bool
    scheduled_at: Optional[datetime.datetime]
    status: str
    price: float
    match_reason: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Payments ----------

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: float
    platform_fee: float
    worker_payout: float
    status: str
    invoice_note: str

    class Config:
        from_attributes = True


# ---------- Reviews ----------

class ReviewCreate(BaseModel):
    booking_id: int
    rating: int
    comment: str = ""


class ReviewOut(BaseModel):
    id: int
    booking_id: int
    rating: int
    comment: str

    class Config:
        from_attributes = True


# ---------- Service categories / federations ----------

class ServiceCategoryOut(BaseModel):
    id: int
    name: str
    base_price: float

    class Config:
        from_attributes = True


class FederationOut(BaseModel):
    id: int
    name: str
    region: str

    class Config:
        from_attributes = True


class ServiceCategoryCreate(BaseModel):
    name: str
    base_price: float = 300.0


class FederationCreate(BaseModel):
    name: str
    region: str


# ---------- Grievances ----------

class GrievanceCreate(BaseModel):
    description: str
    against_worker_id: Optional[int] = None
    booking_id: Optional[int] = None


class GrievanceOut(BaseModel):
    id: int
    filed_by_id: int
    against_worker_id: Optional[int]
    booking_id: Optional[int]
    description: str
    status: str
    resolution_note: str
    created_at: datetime.datetime
    resolved_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class GrievanceResolve(BaseModel):
    status: str  # "resolved" | "dismissed"
    resolution_note: str = ""
    suspend_worker: bool = False


# ---------- Piggybank ----------

class PiggybankEntryOut(BaseModel):
    id: int
    worker_id: int
    booking_id: int
    amount: float
    balance_after: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Bandit ----------

class BanditArmOut(BaseModel):
    id: int
    worker_id: int
    category_id: int
    zone: str
    alpha: float
    beta: float

    class Config:
        from_attributes = True


class BanditArmManual(BaseModel):
    """Set an arm from historic success/fail counts (not live JSON reviews)."""

    worker_id: int
    category_id: int
    zone: str
    successes: int
    failures: int


class BanditSeedResult(BaseModel):
    arms_written: int
    jobs_counted: int


# ---------- Demand forecasting / shift scheduling ----------

class DemandForecastOut(BaseModel):
    id: int
    zone: str
    category_id: int
    day_of_week: int
    predicted_bookings: float
    demand_level: str

    class Config:
        from_attributes = True


class WorkerShiftOut(BaseModel):
    id: int
    worker_id: int
    zone: str
    category_id: int
    shift_date: datetime.datetime
    is_baseline: bool

    class Config:
        from_attributes = True


class ScheduleGenerateRequest(BaseModel):
    week_start: datetime.date  # must be a Monday


class ScheduleGenerateResult(BaseModel):
    forecasts_recomputed: int
    shifts_created: int
