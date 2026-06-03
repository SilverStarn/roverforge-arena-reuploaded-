"""Data models for the headless simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

from game.core.types import Observation


@dataclass(frozen=True)
class RectObstacle:
    x: float
    y: float
    width: float
    depth: float
    height: float = 1.2

    @property
    def min_x(self) -> float:
        return self.x - self.width / 2.0

    @property
    def max_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def min_y(self) -> float:
        return self.y - self.depth / 2.0

    @property
    def max_y(self) -> float:
        return self.y + self.depth / 2.0

    def intersects_circle(self, x: float, y: float, radius: float) -> bool:
        closest_x = min(max(x, self.min_x), self.max_x)
        closest_y = min(max(y, self.min_y), self.max_y)
        dx = x - closest_x
        dy = y - closest_y
        return dx * dx + dy * dy <= radius * radius

    def padded_overlaps(self, other: "RectObstacle", padding: float) -> bool:
        return not (
            self.max_x + padding < other.min_x
            or self.min_x - padding > other.max_x
            or self.max_y + padding < other.min_y
            or self.min_y - padding > other.max_y
        )


@dataclass
class Target:
    x: float
    y: float
    collected: bool = False


@dataclass
class AgentState:
    x: float
    y: float
    heading: float = 0.0
    speed: float = 0.0


@dataclass(frozen=True)
class RewardEvent:
    label: str
    value: float
    step: int
    position: tuple[float, float]


@dataclass
class StepResult:
    observation: Observation
    reward: float
    done: bool
    info: dict[str, object] = field(default_factory=dict)
    reward_breakdown: dict[str, float] = field(default_factory=dict)
    reward_events: list[RewardEvent] = field(default_factory=list)
