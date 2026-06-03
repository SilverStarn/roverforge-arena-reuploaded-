"""Reactive sensor-driven baseline agent."""

from __future__ import annotations

from dataclasses import dataclass

from game.core.math_utils import clamp
from game.core.types import ActionCommand, Observation


@dataclass
class RuleBasedAgent:
    """Follow target direction while steering away from blocked sensor rays."""

    avoid_gain: float = 1.45
    target_gain: float = 1.25
    front_stop: float = 0.22
    slow_zone: float = 0.38

    def act(self, observation: Observation) -> ActionCommand:
        sensors = tuple(float(value) for value in observation["sensors"])
        target_angle = float(observation["target_angle"])
        center = len(sensors) // 2
        front_band = sensors[max(0, center - 1) : center + 2]
        front = min(front_band)
        left_clearance = sum(sensors[:center])
        right_clearance = sum(sensors[center + 1 :])

        target_turn = clamp(target_angle * self.target_gain, -1.0, 1.0)
        avoid_turn = self._avoidance_turn(front, left_clearance, right_clearance)

        return {
            "turn": clamp(target_turn + avoid_turn * self.avoid_gain * (1.0 - front), -1.0, 1.0),
            "throttle": self._throttle(target_angle, front),
        }

    def _avoidance_turn(self, front: float, left_clearance: float, right_clearance: float) -> float:
        if front >= self.slow_zone:
            return 0.0
        return -1.0 if left_clearance > right_clearance else 1.0

    def _throttle(self, target_angle: float, front: float) -> float:
        if abs(target_angle) > 1.7:
            return 0.25
        if front < self.front_stop:
            return 0.0
        if front < self.slow_zone:
            return 0.35
        return 1.0
