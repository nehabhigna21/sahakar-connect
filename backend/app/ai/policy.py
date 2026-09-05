"""Bridges the trained dispatch-weight-tuning model into live dispatch.

Turns real booking/worker state into the same observation shape
DispatchWeightEnv trains on, feeds it to the trained model, and returns
per-candidate composite scores using the weights it outputs.

If no trained model file exists yet (or it fails to load for any
reason - missing stable-baselines3/torch, corrupt file, shape
mismatch from a stale model), score_candidates() returns None and the
caller falls back to its own scoring. RL should never be a hard
dependency for dispatch to work.

Mirrors dispatch_env.py's CATEGORIES/MAX_IDLE_HOURS rather than
importing it, so the main API doesn't need gymnasium installed just to
boot - keep these in sync by hand if the env's constants change.
"""

import datetime
import math
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from .. import models

CATEGORIES = ["electrician", "plumber", "cleaner", "caregiver"]
MAX_IDLE_HOURS = 24.0
# Distances beyond this are treated as "as far as it gets" for scoring -
# tune to whatever a realistic zone spans.
MAX_DISTANCE_KM = 25.0

MODELS_DIR = Path(__file__).parent / "models"
# Tried in order; first one found on disk wins.
_MODEL_CANDIDATES = [("ppo_dispatch.zip", "PPO"), ("sac_dispatch.zip", "SAC")]

_model = None
_model_load_attempted = False


def _load_model():
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True

    for filename, algo_name in _MODEL_CANDIDATES:
        path = MODELS_DIR / filename
        if not path.exists():
            continue
        try:
            from stable_baselines3 import PPO, SAC

            algo_cls = PPO if algo_name == "PPO" else SAC
            _model = algo_cls.load(str(path))
            break
        except Exception:
            _model = None
    return _model


def idle_hours(db: Session, worker_id: int) -> float:
    """Hours since this worker's most recent booking - the best live
    proxy for 'idle time' available without a dedicated tracking
    column. Never having had a booking counts as maximally idle."""
    last = (
        db.query(models.Booking)
        .filter(models.Booking.worker_id == worker_id)
        .order_by(models.Booking.created_at.desc())
        .first()
    )
    if last is None:
        return MAX_IDLE_HOURS
    delta = datetime.datetime.utcnow() - last.created_at
    return min(MAX_IDLE_HOURS, max(0.0, delta.total_seconds() / 3600.0))


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _distance_score(worker: models.WorkerProfile, lat: float, lng: float) -> float:
    km = _haversine_km(worker.lat, worker.lng, lat, lng)
    return max(0.0, 1.0 - min(km, MAX_DISTANCE_KM) / MAX_DISTANCE_KM)


def _category_index(category_name: str) -> float:
    name = category_name.strip().lower()
    if name in CATEGORIES:
        return CATEGORIES.index(name) / (len(CATEGORIES) - 1)
    # Outside the trained set - neutral placeholder rather than a
    # misleading guess at which of the 4 it's "closest" to.
    return 0.5


def score_candidates(
    db: Session,
    candidates: list[models.WorkerProfile],
    category: models.ServiceCategory,
    zone: str,
    lat: float,
    lng: float,
    is_emergency: bool,
) -> tuple[list[float], np.ndarray] | None:
    """Returns (per-candidate composite scores, the 4 weights used) if a
    trained model is available, else None."""
    model = _load_model()
    if model is None or not candidates:
        return None

    idle = np.array([idle_hours(db, w.id) for w in candidates])
    ratings = np.array([(w.rating_avg or 0.0) for w in candidates]) / 5.0
    distances = np.array([_distance_score(w, lat, lng) for w in candidates])
    # Candidates are already filtered to a skill match; production has
    # no graded proficiency field, so treat every match as top-tier.
    skill = np.ones(len(candidates))

    total_workers = max(
        db.query(models.WorkerProfile).filter(models.WorkerProfile.zone == zone).count(), 1
    )
    now = datetime.datetime.utcnow()
    hour_of_day = now.hour + now.minute / 60.0
    demand_factor = max(0.0, 1.0 - abs(hour_of_day - 13) / 13)
    idle_norm = idle / MAX_IDLE_HOURS

    obs = np.array(
        [
            len(candidates) / total_workers,
            idle_norm.mean(),
            idle_norm.std(),
            idle_norm.max(),
            idle_norm.mean(),  # no separate "all workers" pool live - reuse eligible pool
            idle_norm.std(),
            demand_factor,
            _category_index(category.name),
            float(is_emergency),
            ratings.mean() if len(ratings) else 0.0,
            1.0,
            hour_of_day / 24.0,
            now.weekday() / 6.0,
        ],
        dtype=np.float32,
    )

    action, _ = model.predict(obs, deterministic=True)
    weights = np.clip(action, 0.0, 1.0)
    total = float(weights.sum())
    weights = weights if total > 0 else np.full(4, 0.25, dtype=np.float32)
    weights = weights / weights.sum()

    scores = (
        weights[0] * distances
        + weights[1] * idle_norm
        + weights[2] * ratings
        + weights[3] * skill
    )
    return scores.tolist(), weights
