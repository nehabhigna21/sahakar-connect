from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, forecast, models, schemas
from ..database import get_db

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/demand", response_model=list[schemas.DemandForecastOut])
def list_demand_forecasts(
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(models.DemandForecast).all()


@router.post("/recompute", response_model=schemas.ScheduleGenerateResult)
def recompute_and_schedule(
    payload: schemas.ScheduleGenerateRequest,
    _: models.User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Rebuild demand forecasts from booking history, then (re)generate the
    given week's worker shifts from those forecasts - the two always run
    together so shifts never drift from stale forecast data."""
    if payload.week_start.weekday() != 0:
        raise HTTPException(status_code=400, detail="week_start must be a Monday")

    forecasts_written = forecast.recompute_demand_forecasts(db)
    shifts = forecast.generate_baseline_shifts(db, payload.week_start)
    db.commit()
    return schemas.ScheduleGenerateResult(
        forecasts_recomputed=forecasts_written, shifts_created=len(shifts)
    )


@router.get("/shifts", response_model=list[schemas.WorkerShiftOut])
def list_shifts(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Admins see every shift; workers see only their own."""
    if current_user.role == "admin":
        return db.query(models.WorkerShift).all()

    profile = auth.find_worker_profile(db, current_user.id)
    if profile is None:
        return []
    return (
        db.query(models.WorkerShift)
        .filter(models.WorkerShift.worker_id == profile.id)
        .order_by(models.WorkerShift.shift_date.asc())
        .all()
    )
