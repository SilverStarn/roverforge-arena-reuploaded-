"""Action normalization for manual controls and AI policies."""

from __future__ import annotations

from collections.abc import Mapping
import math

from game.core.math_utils import clamp
from game.core.types import Action, ActionCommand


ACTION_TABLE: dict[int, tuple[float, float]] = {
    0: (0.0, 1.0),   # forward
    1: (-1.0, 0.70), # forward-left
    2: (1.0, 0.70),  # forward-right
    3: (-1.0, 0.0),  # rotate left
    4: (1.0, 0.0),   # rotate right
    5: (0.0, 0.0),   # coast/stop
}


def normalize_action(action: Action) -> ActionCommand:
    """Convert an integer or mapping action into clamped turn/throttle values."""
    if isinstance(action, int):
        turn, throttle = ACTION_TABLE.get(action, ACTION_TABLE[5])
        return {"turn": turn, "throttle": throttle}

    if isinstance(action, Mapping):
        return {
            "turn": clamp(_finite_float(action.get("turn", 0.0)), -1.0, 1.0),
            "throttle": clamp(_finite_float(action.get("throttle", 0.0)), -1.0, 1.0),
        }

    return {"turn": 0.0, "throttle": 0.0}


def _finite_float(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0
