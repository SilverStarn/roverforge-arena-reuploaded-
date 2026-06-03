"""Core simulation API for RoverForge Arena."""

from game.core.config import ArenaConfig
from game.core.environment import TrainingArenaEnv
from game.core.evaluation import average_metric, run_episode
from game.core.math_utils import clamp, wrap_angle
from game.core.models import AgentState, RectObstacle, RewardEvent, StepResult, Target
from game.core.types import Action, EpisodeMetrics, Observation

__all__ = [
    "Action",
    "AgentState",
    "ArenaConfig",
    "EpisodeMetrics",
    "Observation",
    "RectObstacle",
    "RewardEvent",
    "StepResult",
    "Target",
    "TrainingArenaEnv",
    "average_metric",
    "clamp",
    "run_episode",
    "wrap_angle",
]
