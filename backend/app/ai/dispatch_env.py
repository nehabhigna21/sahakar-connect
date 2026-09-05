"""Synthetic training environment for the Fair-Dispatch weight-tuning agent.

The agent doesn't pick a worker directly - that needs a variable-size or
masked discrete action space, which is a lot more to get right in a short
build. Instead it outputs continuous weights
[w_distance, w_idle_time, w_rating, w_skill] that a simple scoring rule
uses to pick the best eligible worker for each incoming booking. That
keeps the action space small and continuous (works for both PPO and SAC)
and slots on top of the existing bandit/ILP dispatch logic instead of
replacing it.

Design notes (v2 - fixes a reward-shaping bug found in v1):

v1 rewarded fairness only through the *population* idle-time spread at
the end of each step - a signal several steps removed from the actual
pick, and much weaker than the immediate, same-step reward for picking a
close/well-rated worker. The agent unsurprisingly learned to ignore
idle-time and rating almost entirely and chase distance alone. v2 gives a
direct, same-step reward for picking whoever's been idle the longest
(on equal footing with match quality), and keeps the population-spread
term only as a secondary regularizer.

v2 also adds: graded skill proficiency (not just a yes/no skill match),
a job-duration/"busy" mechanic so a worker can't be handed back-to-back
jobs instantly (the actual mechanism behind "not overloaded"), and an
emergency-job quality boost so the trained policy learns to prioritize
speed/reliability on urgent jobs without a hardcoded rule.

No real traffic is used - each episode simulates one day of bookings
against a synthetic pool of workers, loosely shaped like the live
ServiceCategory / WorkerProfile data.
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces

CATEGORIES = ["electrician", "plumber", "cleaner", "caregiver"]
N_WORKERS = 15
BOOKINGS_PER_EPISODE = 60
MAX_IDLE_HOURS = 24.0
JOB_DURATION_RANGE = (0.5, 3.0)  # hours a worker is occupied after being matched

# Reward weights, deliberately kept on comparable 0-1 scales so no one
# factor can dominate just by having a bigger natural range than the
# others (that's what broke v1).
QUALITY_WEIGHT = 1.0
FAIRNESS_WEIGHT = 1.0  # equal footing with quality - this is the v1 fix
EMERGENCY_QUALITY_BOOST = 0.5
GLOBAL_SPREAD_WEIGHT = 0.3  # secondary regularizer, not the primary fairness signal
UNMATCHED_PENALTY = 1.5


class DispatchWeightEnv(gym.Env):
    """One step = one incoming booking. Action = dispatch-scoring weights."""

    metadata = {"render_modes": []}

    def __init__(self, seed: int | None = None):
        super().__init__()
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(13,), dtype=np.float32)
        self._rng = np.random.default_rng(seed)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)

        self.workers = [
            {
                # Graded proficiency per skill (0.5-1.0), not just yes/no.
                "skills": {
                    c: float(self._rng.uniform(0.5, 1.0))
                    for c in self._rng.choice(
                        CATEGORIES, size=int(self._rng.integers(1, 3)), replace=False
                    )
                },
                "idle_hours": float(self._rng.uniform(0, MAX_IDLE_HOURS)),
                "rating": float(self._rng.uniform(3.0, 5.0)),
                "busy_until": 0.0,  # clock hour they're free again; 0 = free now
            }
            for _ in range(N_WORKERS)
        ]
        self.step_count = 0
        # A continuous clock (hours since episode start), not wrapped -
        # lets "busy until" comparisons work cleanly across day boundaries.
        self.clock = float(self._rng.uniform(0, 24))
        self._new_booking()
        return self._obs(), {}

    def step(self, action):
        weights = np.clip(np.asarray(action, dtype=np.float32), 0.0, 1.0)
        total = float(weights.sum())
        weights = (
            weights / total if total > 0 else np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)
        )

        eligible = self._eligible()
        chosen = None
        reward = 0.0

        if not eligible:
            reward -= UNMATCHED_PENALTY
        else:
            category = self.booking["category"]
            # Redrawn per booking: same worker is a different distance from
            # each new job.
            distances = self._rng.uniform(0.0, 1.0, size=len(eligible))
            distance_scores = 1.0 - distances
            idle_scores = np.array([w["idle_hours"] for w in eligible]) / MAX_IDLE_HOURS
            rating_scores = np.array([w["rating"] for w in eligible]) / 5.0
            skill_scores = np.array(
                [(w["skills"][category] - 0.5) / 0.5 for w in eligible]
            )

            scores = (
                weights[0] * distance_scores
                + weights[1] * idle_scores
                + weights[2] * rating_scores
                + weights[3] * skill_scores
            )
            chosen_idx = int(np.argmax(scores))
            chosen = eligible[chosen_idx]

            quality = float(
                (distance_scores[chosen_idx] + rating_scores[chosen_idx] + skill_scores[chosen_idx])
                / 3.0
            )
            emergency_mult = 1.0 + EMERGENCY_QUALITY_BOOST * float(self.booking["is_emergency"])
            reward += QUALITY_WEIGHT * emergency_mult * quality
            # Direct, same-step credit for picking whoever's been waiting
            # longest - this is what actually teaches idle-time fairness,
            # instead of hoping the delayed population-spread term does it.
            reward += FAIRNESS_WEIGHT * float(idle_scores[chosen_idx])

            duration = float(self._rng.uniform(*JOB_DURATION_RANGE))
            chosen["busy_until"] = self.clock + duration
            chosen["idle_hours"] = 0.0

        gap = self._new_booking()  # advances the clock, queues the next booking
        for w in self.workers:
            if w is chosen:
                continue
            if w["busy_until"] <= self.clock:
                w["idle_hours"] = min(MAX_IDLE_HOURS, w["idle_hours"] + gap)
            else:
                w["idle_hours"] = 0.0  # mid-job: busy, not idle

        idle_spread = float(np.std([w["idle_hours"] for w in self.workers]))
        reward -= GLOBAL_SPREAD_WEIGHT * (idle_spread / MAX_IDLE_HOURS)

        self.step_count += 1
        terminated = self.step_count >= BOOKINGS_PER_EPISODE
        return self._obs(), reward, terminated, False, {}

    def _new_booking(self) -> float:
        """Queue the next booking and return the (simulated) hours until it
        arrived - used both to advance the clock and to age every worker's
        idle time."""
        self.booking = {
            "category": self._rng.choice(CATEGORIES),
            "is_emergency": bool(self._rng.random() < 0.1),
        }
        # Crude demand curve: busiest around 1pm, quietest at 1am - shorter
        # gaps between bookings when demand is high.
        hour_of_day = self.clock % 24.0
        demand_factor = np.clip(1.0 - abs(hour_of_day - 13) / 13, 0.0, 1.0)
        gap = float(max(0.05, self._rng.exponential(0.5 + (1 - demand_factor))))
        self.clock += gap
        return gap

    def _eligible(self):
        category = self.booking["category"]
        return [
            w
            for w in self.workers
            if category in w["skills"] and w["busy_until"] <= self.clock
        ]

    def _obs(self):
        eligible = self._eligible()
        category = self.booking["category"]
        hour_of_day = self.clock % 24.0
        day_of_week = int(self.clock // 24) % 7
        demand_factor = np.clip(1.0 - abs(hour_of_day - 13) / 13, 0.0, 1.0)

        if eligible:
            idle = np.array([w["idle_hours"] for w in eligible])
            ratings = np.array([w["rating"] for w in eligible])
            skills = np.array([(w["skills"][category] - 0.5) / 0.5 for w in eligible])
        else:
            idle = np.array([0.0])
            ratings = np.array([0.0])
            skills = np.array([0.0])

        all_idle = np.array([w["idle_hours"] for w in self.workers])

        return np.array(
            [
                len(eligible) / N_WORKERS,
                idle.mean() / MAX_IDLE_HOURS,
                idle.std() / MAX_IDLE_HOURS,
                idle.max() / MAX_IDLE_HOURS,  # worst-case wait among eligible workers
                all_idle.mean() / MAX_IDLE_HOURS,  # system-wide fairness context
                all_idle.std() / MAX_IDLE_HOURS,
                demand_factor,
                CATEGORIES.index(category) / (len(CATEGORIES) - 1),
                float(self.booking["is_emergency"]),
                ratings.mean() / 5.0,
                skills.mean(),
                hour_of_day / 24.0,
                day_of_week / 6.0,
            ],
            dtype=np.float32,
        )
