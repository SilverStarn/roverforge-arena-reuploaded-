"""Panda3D rendering package."""

from __future__ import annotations

from typing import Any

__all__ = ["ArenaApp"]


def __getattr__(name: str) -> Any:
    if name == "ArenaApp":
        from game.rendering.arena_app import ArenaApp

        return ArenaApp
    raise AttributeError(name)
