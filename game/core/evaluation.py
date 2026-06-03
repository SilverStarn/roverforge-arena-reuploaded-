"""Headless episode execution and metric helpers."""

from __future__ import annotations

from collections.abc import Iterable

from game.core.environment import TrainingArenaEnv
from game.core.types import Agent, EpisodeMetrics


def run_episode(
    env: TrainingArenaEnv,
    agent: Agent,
    seed: int | None = None,
    max_steps: int | None = None,
) -> EpisodeMetrics:
    observation = env.reset(seed)
    reward_total = 0.0
    limit = max_steps or env.config.max_steps

    for _ in range(limit):
        result = env.step(agent.act(observation))
        observation = result.observation
        reward_total += result.reward
        if result.done:
            break

    return {
        "seed": env.seed,
        "steps": env.steps,
        "reward": reward_total,
        "success": env.remaining_targets == 0,
        "timed_out": env.terminal_reason == "timeout",
        "terminal_reason": env.terminal_reason,
        "completion": env.completion_ratio,
        "collisions": env.collision_count,
        "collected_targets": len(env.targets) - env.remaining_targets,
        "remaining_targets": env.remaining_targets,
        "target_count": len(env.targets),
    }


def average_metric(rows: Iterable[EpisodeMetrics], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return sum(values) / len(values) if values else 0.0
