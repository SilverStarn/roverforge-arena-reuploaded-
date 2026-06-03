"""Agent construction helpers for CLI and app entry points."""

from __future__ import annotations

from game.agents.grid_planner import GridPlannerAgent
from game.agents.random_agent import RandomAgent
from game.agents.rule_based import RuleBasedAgent
from game.core.environment import TrainingArenaEnv
from game.core.types import Agent


AGENT_CHOICES = ("planner", "rule", "random")


def make_agent(name: str, env: TrainingArenaEnv, seed: int = 0) -> Agent:
    if name == "random":
        return RandomAgent(seed=seed)
    if name == "rule":
        return RuleBasedAgent()
    if name == "planner":
        return GridPlannerAgent(env)
    raise ValueError(f"Unknown agent '{name}'. Expected one of: {', '.join(AGENT_CHOICES)}")
