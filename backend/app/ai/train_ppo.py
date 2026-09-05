"""Train the dispatch-weight-tuning agent.

Both PPO and SAC point at the same DispatchWeightEnv, so swapping between
them is just picking the algorithm - the environment, observation, and
reward stay identical.

Usage:
    python -m app.ai.train_ppo --algo ppo --timesteps 200000
    python -m app.ai.train_ppo --algo sac --timesteps 200000
"""

import argparse
from pathlib import Path

from stable_baselines3 import PPO, SAC
from stable_baselines3.common.env_util import make_vec_env

from .dispatch_env import DispatchWeightEnv

MODELS_DIR = Path(__file__).parent / "models"
ALGOS = {"ppo": PPO, "sac": SAC}


def train(algo: str, timesteps: int) -> Path:
    if algo not in ALGOS:
        raise ValueError(f"algo must be one of {list(ALGOS)}")

    # PPO is on-policy and benefits from parallel rollout collection; SAC
    # is off-policy (replay buffer) so a single env is enough.
    env = make_vec_env(DispatchWeightEnv, n_envs=4) if algo == "ppo" else DispatchWeightEnv()
    model = ALGOS[algo]("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=timesteps)

    MODELS_DIR.mkdir(exist_ok=True)
    out_path = MODELS_DIR / f"{algo}_dispatch.zip"
    model.save(out_path)
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=list(ALGOS), default="ppo")
    parser.add_argument("--timesteps", type=int, default=200_000)
    args = parser.parse_args()

    path = train(args.algo, args.timesteps)
    print(f"Saved model to {path}")
