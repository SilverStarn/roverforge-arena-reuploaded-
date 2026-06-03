"""Line-based debug drawing helpers for Panda3D scenes."""

from __future__ import annotations

import math

from panda3d.core import LineSegs, PandaNode


Color = tuple[float, float, float, float]
Point2 = tuple[float, float]


def rectangle_outline(
    name: str,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    z: float,
    color: Color,
    thickness: float = 2.0,
) -> PandaNode:
    lines = LineSegs(name)
    lines.setThickness(thickness)
    lines.setColor(*color)
    lines.moveTo(min_x, min_y, z)
    lines.drawTo(max_x, min_y, z)
    lines.drawTo(max_x, max_y, z)
    lines.drawTo(min_x, max_y, z)
    lines.drawTo(min_x, min_y, z)
    return lines.create()


def circle_outline(
    name: str,
    x: float,
    y: float,
    radius: float,
    z: float,
    color: Color,
    segments: int = 40,
    thickness: float = 2.0,
) -> PandaNode:
    lines = LineSegs(name)
    lines.setThickness(thickness)
    lines.setColor(*color)

    for index in range(segments + 1):
        angle = math.tau * index / segments
        px = x + math.cos(angle) * radius
        py = y + math.sin(angle) * radius
        if index == 0:
            lines.moveTo(px, py, z)
        else:
            lines.drawTo(px, py, z)

    return lines.create()


def polyline(
    name: str,
    points: list[Point2] | tuple[Point2, ...],
    z: float,
    color: Color,
    thickness: float = 3.0,
) -> PandaNode:
    lines = LineSegs(name)
    lines.setThickness(thickness)
    lines.setColor(*color)

    if not points:
        return lines.create()

    first = points[0]
    lines.moveTo(first[0], first[1], z)
    for point in points[1:]:
        lines.drawTo(point[0], point[1], z)

    return lines.create()


def reward_marker(
    name: str,
    x: float,
    y: float,
    value: float,
    z: float = 0.12,
) -> PandaNode:
    color = (0.16, 0.95, 0.52, 1.0) if value >= 0.0 else (1.0, 0.26, 0.23, 1.0)
    height = 1.1 if value >= 0.0 else 0.7

    lines = LineSegs(name)
    lines.setThickness(3.0)
    lines.setColor(*color)
    lines.moveTo(x, y, z)
    lines.drawTo(x, y, z + height)
    lines.moveTo(x - 0.22, y, z + height)
    lines.drawTo(x + 0.22, y, z + height)
    lines.moveTo(x, y - 0.22, z + height)
    lines.drawTo(x, y + 0.22, z + height)
    return lines.create()
