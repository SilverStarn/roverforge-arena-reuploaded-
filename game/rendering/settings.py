"""Rendering configuration and lightweight UI state."""

from __future__ import annotations

from dataclasses import dataclass

from game.core import RewardEvent


Color = tuple[float, float, float, float]
CameraMode = str


@dataclass(frozen=True)
class WindowSettings:
    title: str = "RoverForge Arena"
    width: int = 1280
    height: int = 720
    background_color: Color = (0.045, 0.055, 0.065, 1.0)


@dataclass(frozen=True)
class CameraSettings:
    chase_distance: float = 8.5
    chase_offset: float = 1.8
    chase_height: float = 8.2
    look_at_height: float = 0.45
    overhead_height_scale: float = 0.95
    smoothing: float = 8.0


@dataclass(frozen=True)
class VisualSettings:
    target_bob_height: float = 0.10
    target_bob_speed: float = 2.8
    target_spin_speed: float = 80.0
    collision_flash_seconds: float = 0.35
    wheel_spin_scale: float = 120.0


@dataclass
class DebugSettings:
    sensors: bool = True
    collision_bounds: bool = True
    reward_events: bool = True
    pathfinding: bool = True

    def all_enabled(self) -> bool:
        return all(self.__dict__.values())


@dataclass
class RewardMarkerState:
    event: RewardEvent
    ttl: float = 1.6
