"""Shared typing contracts for simulation and agents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, TypedDict


ActionCommand = dict[str, float]
Action = int | Mapping[str, float]
Observation = dict[str, Any]


class Agent(Protocol):
    def act(self, observation: Observation) -> Action:
        """Return the next action for the provided observation."""


class EpisodeMetrics(TypedDict):
    seed: int
    steps: int
    reward: float
    success: bool
    timed_out: bool
    terminal_reason: str
    completion: float
    collisions: int
    collected_targets: int
    remaining_targets: int
    target_count: int
