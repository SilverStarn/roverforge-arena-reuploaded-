"""Legacy import shim for simulation classes."""

from game.core import (  # noqa: F401
    ArenaConfig,
    RectObstacle,
    RewardEvent,
    StepResult,
    Target,
    TrainingArenaEnv,
    average_metric,
    clamp,
    run_episode,
    wrap_angle,
)
from game.core.actions import ACTION_TABLE  # noqa: F401
from game.core.constants import SENSOR_ANGLES_DEGREES  # noqa: F401
from game.core.models import AgentState  # noqa: F401
