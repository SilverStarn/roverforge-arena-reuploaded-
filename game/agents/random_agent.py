"""Random baseline policy."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from game.core.types import Observation


@dataclass
class RandomAgent:
    """Baseline policy useful for comparing evaluation results."""

    seed: int = 0
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def act(self, _observation: Observation) -> int:
        return self._rng.randrange(0, 6)
