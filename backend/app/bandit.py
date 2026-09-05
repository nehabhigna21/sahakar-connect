import random
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from . import models
from .ai import policy


@dataclass
class MatchResult:
    """A dispatch decision plus the plain-language reason behind it, so
    the worker app can show a 'why you were matched' screen instead of a
    black-box assignment."""

    worker: "models.WorkerProfile | None"
    reason: str

# Rating at or above this counts as a "success" for the Bernoulli bandit.
SUCCESS_THRESHOLD = 4


def get_or_create_arm(
    db: Session, worker_id: int, category_id: int, zone: str
) -> models.BanditArm:
    arm = (
        db.query(models.BanditArm)
        .filter(
            models.BanditArm.worker_id == worker_id,
            models.BanditArm.category_id == category_id,
            models.BanditArm.zone == zone,
        )
        .first()
    )
    if arm is None:
        arm = models.BanditArm(
            worker_id=worker_id,
            category_id=category_id,
            zone=zone,
            alpha=1.0,
            beta=1.0,
        )
        db.add(arm)
        db.flush()
    return arm


def apply_historic_counts(
    db: Session,
    worker_id: int,
    category_id: int,
    zone: str,
    successes: int,
    failures: int,
) -> models.BanditArm:
    """Replace priors with 1 + historic counts (manual seed)."""
    if successes < 0 or failures < 0:
        raise ValueError("successes and failures must be >= 0")
    arm = get_or_create_arm(db, worker_id, category_id, zone)
    arm.alpha = 1.0 + successes
    arm.beta = 1.0 + failures
    return arm


def record_reward(db: Session, booking: models.Booking, rating: int) -> None:
    if booking.worker_id is None:
        return
    arm = get_or_create_arm(
        db, booking.worker_id, booking.category_id, booking.zone
    )
    if rating >= SUCCESS_THRESHOLD:
        arm.alpha += 1.0
    else:
        arm.beta += 1.0


def seed_from_reviews(db: Session, reset: bool = True) -> tuple[int, int]:
    """Rebuild arms from completed bookings that already have reviews."""
    if reset:
        db.query(models.BanditArm).delete()
        db.flush()

    rows = (
        db.query(models.Booking, models.Review)
        .join(models.Review, models.Review.booking_id == models.Booking.id)
        .filter(
            models.Booking.status == "completed",
            models.Booking.worker_id.isnot(None),
        )
        .all()
    )

    counts: dict[tuple[int, int, str], dict[str, int]] = defaultdict(
        lambda: {"successes": 0, "failures": 0}
    )
    for booking, review in rows:
        key = (booking.worker_id, booking.category_id, booking.zone)
        if review.rating >= SUCCESS_THRESHOLD:
            counts[key]["successes"] += 1
        else:
            counts[key]["failures"] += 1

    for (worker_id, category_id, zone), c in counts.items():
        apply_historic_counts(
            db,
            worker_id,
            category_id,
            zone,
            c["successes"],
            c["failures"],
        )

    return len(counts), len(rows)


def _skill_names(skills: str) -> set[str]:
    return {part.strip().lower() for part in skills.split(",") if part.strip()}


def eligible_workers(
    db: Session, category: models.ServiceCategory, zone: str
) -> list[models.WorkerProfile]:
    workers = (
        db.query(models.WorkerProfile)
        .filter(
            models.WorkerProfile.is_available.is_(True),
            models.WorkerProfile.is_suspended.is_(False),
            models.WorkerProfile.zone == zone,
        )
        .all()
    )
    name = category.name.strip().lower()
    return [w for w in workers if name in _skill_names(w.skills)]


def pick_worker(
    db: Session,
    category: models.ServiceCategory,
    zone: str,
    lat: float = 0.0,
    lng: float = 0.0,
    is_emergency: bool = False,
) -> MatchResult:
    """Picks a worker for this booking. Uses the trained RL dispatch-weight
    policy when a model is available (see app/ai/policy.py); otherwise
    falls back to Thompson sampling over historic rating success."""
    candidates = eligible_workers(db, category, zone)
    if not candidates:
        return MatchResult(
            None,
            f"No available, skill-matched workers found in {zone} for {category.name}.",
        )

    rl_result = policy.score_candidates(db, candidates, category, zone, lat, lng, is_emergency)
    if rl_result is not None:
        scores, weights = rl_result
        idx = max(range(len(candidates)), key=lambda i: scores[i])
        best = candidates[idx]
        reason = (
            f"Matched in {zone} on skill fit for {category.name} using the RL-tuned "
            f"dispatch policy (distance={weights[0]:.2f}, idle-time={weights[1]:.2f}, "
            f"rating={weights[2]:.2f}, skill={weights[3]:.2f}) among {len(candidates)} "
            "available worker(s)."
        )
        return MatchResult(best, reason)

    best = None
    best_theta = -1.0
    for worker in candidates:
        arm = get_or_create_arm(db, worker.id, category.id, zone)
        theta = random.betavariate(arm.alpha, arm.beta)
        if theta > best_theta:
            best_theta = theta
            best = worker

    reason = (
        f"Matched in {zone} on skill fit for {category.name}, among "
        f"{len(candidates)} available worker(s) - selected by a fairness-weighted "
        f"lottery over track record (quality score {best_theta:.2f}) rather than "
        "always picking the single top-rated worker."
    )
    return MatchResult(best, reason)
