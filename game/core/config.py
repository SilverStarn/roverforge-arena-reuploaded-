"""Configuration values for deterministic arena simulations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArenaConfig:
    width: float = 22.0
    depth: float = 16.0
    max_steps: int = 900
    step_seconds: float = 1.0 / 30.0
    move_speed: float = 4.2
    turn_speed: float = 2.8
    agent_radius: float = 0.38
    target_radius: float = 0.55
    sensor_range: float = 6.0
    sensor_step: float = 0.18
    obstacle_count: int = 10
    target_count: int = 5
    seed: int = 7

    def __post_init__(self) -> None:
        positive_fields = {
            "width": self.width,
            "depth": self.depth,
            "max_steps": self.max_steps,
            "step_seconds": self.step_seconds,
            "move_speed": self.move_speed,
            "turn_speed": self.turn_speed,
            "agent_radius": self.agent_radius,
            "target_radius": self.target_radius,
            "sensor_range": self.sensor_range,
            "sensor_step": self.sensor_step,
            "target_count": self.target_count,
        }
        for name, value in positive_fields.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if self.obstacle_count < 0:
            raise ValueError("obstacle_count must be zero or greater")
        if self.sensor_step > self.sensor_range:
            raise ValueError("sensor_step must be less than or equal to sensor_range")
        if self.width <= self.agent_radius * 4 or self.depth <= self.agent_radius * 4:
            raise ValueError("arena dimensions are too small for the configured agent radius")
