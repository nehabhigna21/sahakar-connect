import collections
import datetime

from sqlalchemy.orm import Session

from . import models

# A week gets this many guaranteed "baseline" shifts before any demand-driven
# extras are added - the guarantee against idle days.
MIN_BASELINE_SHIFTS_PER_WEEK = 3
# ...and never more than this many total - the guarantee against overload.
MAX_SHIFTS_PER_WEEK = 6

MEDIUM_DEMAND_THRESHOLD = 4
HIGH_DEMAND_THRESHOLD = 10


def _demand_level(count: float) -> str:
    if count >= HIGH_DEMAND_THRESHOLD:
        return "high"
    if count >= MEDIUM_DEMAND_THRESHOLD:
        return "medium"
    return "low"


def recompute_demand_forecasts(db: Session) -> int:
    """Rebuild demand_forecasts from historical booking counts, grouped by
    zone/category/day-of-week. Heuristic prototype: real usage would swap
    this for a proper time-series model without touching its callers."""
    counts: dict[tuple[str, int, int], int] = collections.Counter()
    for booking in db.query(models.Booking).all():
        when = booking.scheduled_at or booking.created_at
        if when is None:
            continue
        counts[(booking.zone, booking.category_id, when.weekday())] += 1

    db.query(models.DemandForecast).delete()
    db.flush()

    written = 0
    for (zone, category_id, day_of_week), n in counts.items():
        db.add(
            models.DemandForecast(
                zone=zone,
                category_id=category_id,
                day_of_week=day_of_week,
                predicted_bookings=float(n),
                demand_level=_demand_level(n),
            )
        )
        written += 1
    return written


def _worker_categories(db: Session, worker: models.WorkerProfile) -> list[models.ServiceCategory]:
    names = {part.strip().lower() for part in worker.skills.split(",") if part.strip()}
    if not names:
        return []
    return [
        c
        for c in db.query(models.ServiceCategory).all()
        if c.name.strip().lower() in names
    ]


def generate_baseline_shifts(
    db: Session, week_start: datetime.date
) -> list[models.WorkerShift]:
    """Assign each available worker a spread of shifts across their skilled
    zone/category's highest-demand days for the week starting week_start (a
    Monday), guaranteeing at least MIN_BASELINE_SHIFTS_PER_WEEK and never
    more than MAX_SHIFTS_PER_WEEK.

    Cold start (no forecast data yet) still guarantees the baseline floor
    by cycling through weekdays for the worker's own zone/skills - the
    guarantee matters even before any booking history exists.
    """
    week_end = week_start + datetime.timedelta(days=7)
    db.query(models.WorkerShift).filter(
        models.WorkerShift.shift_date >= datetime.datetime.combine(week_start, datetime.time.min),
        models.WorkerShift.shift_date < datetime.datetime.combine(week_end, datetime.time.min),
    ).delete()
    db.flush()

    forecasts = db.query(models.DemandForecast).all()
    workers = (
        db.query(models.WorkerProfile)
        .filter(models.WorkerProfile.is_available.is_(True))
        .all()
    )

    created: list[models.WorkerShift] = []
    for worker in workers:
        categories = _worker_categories(db, worker)
        if not categories:
            continue
        category_ids = {c.id for c in categories}

        candidates = sorted(
            (f for f in forecasts if f.zone == worker.zone and f.category_id in category_ids),
            key=lambda f: f.predicted_bookings,
            reverse=True,
        )

        used_days: set[int] = set()
        assigned = 0
        for forecast in candidates:
            if assigned >= MAX_SHIFTS_PER_WEEK or forecast.day_of_week in used_days:
                continue
            shift_date = week_start + datetime.timedelta(days=forecast.day_of_week)
            created.append(
                models.WorkerShift(
                    worker_id=worker.id,
                    zone=forecast.zone,
                    category_id=forecast.category_id,
                    shift_date=datetime.datetime.combine(shift_date, datetime.time.min),
                    is_baseline=assigned < MIN_BASELINE_SHIFTS_PER_WEEK,
                )
            )
            used_days.add(forecast.day_of_week)
            assigned += 1

        # Cold start / sparse-forecast fallback: keep filling weekdays with the
        # worker's own zone and first skill category until the floor is hit.
        fallback_category_id = categories[0].id
        day_of_week = 0
        while assigned < MIN_BASELINE_SHIFTS_PER_WEEK and day_of_week < 7:
            if day_of_week not in used_days:
                shift_date = week_start + datetime.timedelta(days=day_of_week)
                created.append(
                    models.WorkerShift(
                        worker_id=worker.id,
                        zone=worker.zone,
                        category_id=fallback_category_id,
                        shift_date=datetime.datetime.combine(shift_date, datetime.time.min),
                        is_baseline=True,
                    )
                )
                used_days.add(day_of_week)
                assigned += 1
            day_of_week += 1

    db.add_all(created)
    return created
