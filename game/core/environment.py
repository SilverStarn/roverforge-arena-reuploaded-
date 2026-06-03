"""Deterministic 2D simulation layer used by renderers, agents, and CLI tools."""

from __future__ import annotations

import math
import random
from typing import Any

from game.core.actions import normalize_action
from game.core.config import ArenaConfig
from game.core.constants import SENSOR_ANGLES_DEGREES
from game.core.math_utils import clamp, wrap_angle
from game.core.models import AgentState, RectObstacle, RewardEvent, StepResult, Target
from game.core.types import Action, Observation
from game.native import score_path


class TrainingArenaEnv:
    """Fixed-step rover arena with a gym-like Python API."""

    def __init__(self, config: ArenaConfig | None = None):
        self.config = config or ArenaConfig()
        self.obstacles: list[RectObstacle] = []
        self.targets: list[Target] = []
        self.agent = AgentState(0.0, 0.0)
        self.steps = 0
        self.total_reward = 0.0
        self.collision_count = 0
        self.last_reward_breakdown: dict[str, float] = {}
        self.last_reward_events: list[RewardEvent] = []
        self.episode_done = False
        self.terminal_reason = "running"
        self.seed = self.config.seed
        self.reset(self.config.seed)

    def reset(self, seed: int | None = None) -> Observation:
        self.seed = self.config.seed if seed is None else seed
        rng = random.Random(self.seed)
        self.obstacles = self._generate_obstacles(rng)
        self.targets = self._generate_targets(rng)
        self.agent = AgentState(0.0, -self.config.depth / 2.0 + 1.8, 0.0, 0.0)
        self.steps = 0
        self.total_reward = 0.0
        self.collision_count = 0
        self.last_reward_breakdown = {}
        self.last_reward_events = []
        self.episode_done = False
        self.terminal_reason = "running"
        return self.observe()

    def step(self, action: Action) -> StepResult:
        if self.episode_done:
            return self._terminal_step_result()

        command = normalize_action(action)
        previous_distance = self._nearest_target_distance()

        self.steps += 1
        self.agent.heading = wrap_angle(
            self.agent.heading
            + command["turn"] * self.config.turn_speed * self.config.step_seconds
        )
        self.agent.speed = command["throttle"] * self.config.move_speed

        dx = math.sin(self.agent.heading) * self.agent.speed * self.config.step_seconds
        dy = math.cos(self.agent.heading) * self.agent.speed * self.config.step_seconds
        next_x = self.agent.x + dx
        next_y = self.agent.y + dy

        reward_breakdown = {
            "time": -0.01,
            "progress": 0.0,
            "collision": 0.0,
            "target": 0.0,
            "success": 0.0,
        }
        reward_events: list[RewardEvent] = []
        reward = reward_breakdown["time"]
        collided = self.collides_at(next_x, next_y, self.config.agent_radius)
        if collided:
            self.collision_count += 1
            self.agent.speed = 0.0
            reward_breakdown["collision"] = -0.35
            reward += reward_breakdown["collision"]
            reward_events.append(self._reward_event("collision", reward_breakdown["collision"]))
        else:
            self.agent.x = next_x
            self.agent.y = next_y

        reward_breakdown["progress"] = self._progress_reward(previous_distance)
        reward += reward_breakdown["progress"]
        collected = self._collect_targets()
        if collected:
            reward_breakdown["target"] = float(collected)
            reward += reward_breakdown["target"]
            reward_events.append(self._reward_event(f"target x{collected}", reward_breakdown["target"]))

        success = self.remaining_targets == 0
        timed_out = self.steps >= self.config.max_steps and not success
        done = success or timed_out
        if success:
            reward_breakdown["success"] = 5.0
            reward += reward_breakdown["success"]
            reward_events.append(self._reward_event("episode success", reward_breakdown["success"]))

        if done:
            self.episode_done = True
            self.terminal_reason = "success" if success else "timeout"

        self.total_reward += reward
        self.last_reward_breakdown = reward_breakdown
        self.last_reward_events = reward_events
        info: dict[str, object] = {
            "collided": collided,
            "collected": collected,
            "remaining_targets": self.remaining_targets,
            "total_reward": self.total_reward,
            "steps": self.steps,
            "success": success,
            "timed_out": timed_out,
            "terminal_reason": self.terminal_reason,
            "reward_breakdown": reward_breakdown,
            "reward_events": reward_events,
        }
        return StepResult(self.observe(), reward, done, info, reward_breakdown, reward_events)

    @property
    def remaining_targets(self) -> int:
        return sum(1 for target in self.targets if not target.collected)

    @property
    def completion_ratio(self) -> float:
        if not self.targets:
            return 1.0
        return 1.0 - self.remaining_targets / len(self.targets)

    def observe(self) -> Observation:
        sensors = tuple(self._scan_distance(math.radians(angle)) for angle in SENSOR_ANGLES_DEGREES)
        target_delta = self.target_delta_agent_frame()
        return {
            "position": (self.agent.x, self.agent.y),
            "heading": self.agent.heading,
            "speed": self.agent.speed,
            "step": self.steps,
            "sensors": sensors,
            "sensor_angles": SENSOR_ANGLES_DEGREES,
            "sensor_range": self.config.sensor_range,
            "target_delta": target_delta,
            "target_angle": math.atan2(target_delta[0], target_delta[1]),
            "targets_remaining": self.remaining_targets,
            "completion_ratio": self.completion_ratio,
            "path_score": score_path(sensors, target_delta),
            "collisions": self.collision_count,
            "episode_done": self.episode_done,
            "terminal_reason": self.terminal_reason,
            "last_reward_breakdown": self.last_reward_breakdown,
            "last_reward_events": self.last_reward_events,
        }

    def level_snapshot(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "config": self.config,
            "obstacles": list(self.obstacles),
            "targets": list(self.targets),
        }

    def active_targets(self) -> list[Target]:
        return [target for target in self.targets if not target.collected]

    def nearest_target(self) -> Target | None:
        active_targets = self.active_targets()
        if not active_targets:
            return None
        return min(
            active_targets,
            key=lambda target: math.dist((self.agent.x, self.agent.y), (target.x, target.y)),
        )

    def inside_bounds(self, x: float, y: float, radius: float) -> bool:
        return (
            -self.config.width / 2.0 + radius <= x <= self.config.width / 2.0 - radius
            and -self.config.depth / 2.0 + radius <= y <= self.config.depth / 2.0 - radius
        )

    def collides_at(self, x: float, y: float, radius: float) -> bool:
        if not self.inside_bounds(x, y, radius):
            return True
        return any(obstacle.intersects_circle(x, y, radius) for obstacle in self.obstacles)

    def target_delta_agent_frame(self) -> tuple[float, float]:
        target = self.nearest_target()
        if target is None:
            return (0.0, 0.0)

        world_dx = target.x - self.agent.x
        world_dy = target.y - self.agent.y
        sin_h = math.sin(-self.agent.heading)
        cos_h = math.cos(-self.agent.heading)
        local_x = world_dx * cos_h - world_dy * sin_h
        local_y = world_dx * sin_h + world_dy * cos_h
        return (local_x, local_y)

    def _generate_obstacles(self, rng: random.Random) -> list[RectObstacle]:
        obstacles: list[RectObstacle] = []
        attempts = 0
        while len(obstacles) < self.config.obstacle_count and attempts < 400:
            attempts += 1
            width = rng.uniform(1.1, 2.8)
            depth = rng.uniform(0.9, 2.2)
            x = rng.uniform(-self.config.width / 2.0 + width, self.config.width / 2.0 - width)
            y = rng.uniform(-self.config.depth / 2.0 + depth, self.config.depth / 2.0 - depth)
            obstacle = RectObstacle(x, y, width, depth, rng.uniform(0.7, 1.9))
            if self._reserved_start_area(obstacle.x, obstacle.y, 2.5):
                continue
            if any(obstacle.padded_overlaps(existing, 0.8) for existing in obstacles):
                continue
            obstacles.append(obstacle)
        return obstacles

    def _generate_targets(self, rng: random.Random) -> list[Target]:
        targets: list[Target] = []
        attempts = 0
        while len(targets) < self.config.target_count and attempts < 400:
            attempts += 1
            x = rng.uniform(-self.config.width / 2.0 + 1.0, self.config.width / 2.0 - 1.0)
            y = rng.uniform(-self.config.depth / 2.0 + 1.0, self.config.depth / 2.0 - 1.0)
            if self._reserved_start_area(x, y, 2.3):
                continue
            if self.collides_at(x, y, self.config.target_radius + 0.35):
                continue
            if any(math.dist((x, y), (target.x, target.y)) < 1.5 for target in targets):
                continue
            targets.append(Target(x, y))
        return targets

    def _reserved_start_area(self, x: float, y: float, radius: float) -> bool:
        start = (0.0, -self.config.depth / 2.0 + 1.8)
        return math.dist((x, y), start) < radius

    def _collect_targets(self) -> int:
        collected = 0
        for target in self.targets:
            if target.collected:
                continue
            if math.dist((self.agent.x, self.agent.y), (target.x, target.y)) <= (
                self.config.target_radius + self.config.agent_radius
            ):
                target.collected = True
                collected += 1
        return collected

    def _reward_event(self, label: str, value: float) -> RewardEvent:
        return RewardEvent(
            label=label,
            value=value,
            step=self.steps,
            position=(self.agent.x, self.agent.y),
        )

    def _terminal_step_result(self) -> StepResult:
        info: dict[str, object] = {
            "already_done": True,
            "success": self.remaining_targets == 0,
            "timed_out": self.terminal_reason == "timeout",
            "terminal_reason": self.terminal_reason,
            "remaining_targets": self.remaining_targets,
            "total_reward": self.total_reward,
            "steps": self.steps,
            "reward_breakdown": {},
            "reward_events": [],
        }
        return StepResult(self.observe(), 0.0, True, info, {}, [])

    def _nearest_target_distance(self) -> float | None:
        distances = [
            math.dist((self.agent.x, self.agent.y), (target.x, target.y))
            for target in self.active_targets()
        ]
        return min(distances) if distances else None

    def _progress_reward(self, previous_distance: float | None) -> float:
        if previous_distance is None:
            return 0.0
        current_distance = self._nearest_target_distance()
        if current_distance is None:
            return 0.0
        progress = previous_distance - current_distance
        return clamp(progress * 0.08, -0.04, 0.06)

    def _scan_distance(self, angle_offset: float) -> float:
        angle = self.agent.heading + angle_offset
        distance = self.config.sensor_step
        while distance <= self.config.sensor_range:
            x = self.agent.x + math.sin(angle) * distance
            y = self.agent.y + math.cos(angle) * distance
            if self.collides_at(x, y, self.config.agent_radius):
                return distance / self.config.sensor_range
            distance += self.config.sensor_step
        return 1.0
