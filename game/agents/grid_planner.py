"""Map-aware A* baseline agent."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
import math

from game.agents.rule_based import RuleBasedAgent
from game.core.environment import TrainingArenaEnv
from game.core.math_utils import clamp, wrap_angle
from game.core.types import ActionCommand, Observation


GridCell = tuple[int, int]
Waypoint = tuple[float, float]


@dataclass
class GridPlannerAgent:
    """Plan around known obstacles, then track waypoints with simple steering."""

    env: TrainingArenaEnv
    cell_size: float = 0.5
    replan_interval: int = 12
    waypoint_radius: float = 0.45

    def __post_init__(self) -> None:
        self._reactive = RuleBasedAgent()
        self._path: list[Waypoint] = []
        self._target_signature: tuple[tuple[float, float, bool], ...] = ()
        self._ticks_since_plan = self.replan_interval

    @property
    def path(self) -> tuple[Waypoint, ...]:
        """Current waypoint path in world coordinates."""
        return tuple(self._path)

    @property
    def ticks_since_plan(self) -> int:
        return self._ticks_since_plan

    def act(self, observation: Observation) -> ActionCommand:
        if self._needs_plan():
            self._path = self._plan_to_nearest_target()
            self._target_signature = self._signature()
            self._ticks_since_plan = 0

        self._ticks_since_plan += 1
        if self._front_blocked(observation):
            return self._reactive.act(observation)

        position = observation["position"]
        self._drop_reached_waypoints(position)
        if not self._path:
            return self._reactive.act(observation)

        return self._steer_toward(self._path[0], observation)

    def _needs_plan(self) -> bool:
        return (
            not self._path
            or self._ticks_since_plan >= self.replan_interval
            or self._signature() != self._target_signature
        )

    def _signature(self) -> tuple[tuple[float, float, bool], ...]:
        return tuple((round(t.x, 2), round(t.y, 2), t.collected) for t in self.env.targets)

    def _front_blocked(self, observation: Observation) -> bool:
        front_band = observation["sensors"][3:6]
        return min(front_band) < 0.16

    def _drop_reached_waypoints(self, position: Waypoint) -> None:
        while self._path and math.dist(position, self._path[0]) <= self.waypoint_radius:
            self._path.pop(0)

    def _steer_toward(self, waypoint: Waypoint, observation: Observation) -> ActionCommand:
        position = observation["position"]
        dx = waypoint[0] - position[0]
        dy = waypoint[1] - position[1]
        desired_heading = math.atan2(dx, dy)
        heading_error = wrap_angle(desired_heading - observation["heading"])

        throttle = 1.0
        if abs(heading_error) > 1.35:
            throttle = 0.20
        elif abs(heading_error) > 0.70:
            throttle = 0.55

        return {
            "turn": clamp(heading_error * 1.8, -1.0, 1.0),
            "throttle": throttle,
        }

    def _plan_to_nearest_target(self) -> list[Waypoint]:
        target = self.env.nearest_target()
        if target is None:
            return []

        start = self._to_cell(self.env.agent.x, self.env.agent.y)
        goal = self._nearest_valid_cell(self._to_cell(target.x, target.y))
        if goal is None:
            return []

        cells = self._a_star(start, goal)
        return [self._to_world(cell) for cell in cells[1:]]

    def _a_star(self, start: GridCell, goal: GridCell) -> list[GridCell]:
        if not self._is_valid_cell(start):
            return []

        open_heap: list[tuple[float, GridCell]] = []
        heappush(open_heap, (0.0, start))
        came_from: dict[GridCell, GridCell] = {}
        cost_so_far = {start: 0.0}
        while open_heap:
            _, current = heappop(open_heap)
            if current == goal:
                return self._reconstruct_path(came_from, current)

            for neighbor, move_cost in self._neighbors(current):
                new_cost = cost_so_far[current] + move_cost
                if neighbor in cost_so_far and new_cost >= cost_so_far[neighbor]:
                    continue

                cost_so_far[neighbor] = new_cost
                priority = new_cost + self._heuristic(neighbor, goal)
                heappush(open_heap, (priority, neighbor))
                came_from[neighbor] = current

        return []

    def _neighbors(self, cell: GridCell) -> tuple[tuple[GridCell, float], ...]:
        candidates = (
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, 1.4),
            (-1, 1, 1.4),
            (1, -1, 1.4),
            (1, 1, 1.4),
        )
        neighbors: list[tuple[GridCell, float]] = []
        for dx, dy, move_cost in candidates:
            neighbor = (cell[0] + dx, cell[1] + dy)
            if not self._is_valid_cell(neighbor):
                continue
            if dx != 0 and dy != 0:
                horizontal = (cell[0] + dx, cell[1])
                vertical = (cell[0], cell[1] + dy)
                if not self._is_valid_cell(horizontal) or not self._is_valid_cell(vertical):
                    continue
            neighbors.append((neighbor, move_cost))
        return tuple(neighbors)

    def _reconstruct_path(self, came_from: dict[GridCell, GridCell], current: GridCell) -> list[GridCell]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _nearest_valid_cell(self, cell: GridCell) -> GridCell | None:
        if self._is_valid_cell(cell):
            return cell
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    candidate = (cell[0] + dx, cell[1] + dy)
                    if self._is_valid_cell(candidate):
                        return candidate
        return None

    def _is_valid_cell(self, cell: GridCell) -> bool:
        x, y = self._to_world(cell)
        clearance_radius = self.env.config.agent_radius + 0.08
        return not self.env.collides_at(x, y, clearance_radius)

    def _to_cell(self, x: float, y: float) -> GridCell:
        cfg = self.env.config
        return (
            round((x + cfg.width / 2.0) / self.cell_size),
            round((y + cfg.depth / 2.0) / self.cell_size),
        )

    def _to_world(self, cell: GridCell) -> Waypoint:
        cfg = self.env.config
        return (
            cell[0] * self.cell_size - cfg.width / 2.0,
            cell[1] * self.cell_size - cfg.depth / 2.0,
        )

    def _heuristic(self, a: GridCell, b: GridCell) -> float:
        return math.dist(a, b)
