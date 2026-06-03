"""Shared visual styling for the Panda3D scene."""

from __future__ import annotations

from dataclasses import dataclass

from panda3d.core import Material, NodePath


Color = tuple[float, float, float, float]


@dataclass(frozen=True)
class VisualTheme:
    floor: Color = (0.105, 0.125, 0.135, 1.0)
    floor_panel: Color = (0.145, 0.165, 0.175, 1.0)
    grid: Color = (0.28, 0.34, 0.36, 1.0)
    lane: Color = (0.86, 0.70, 0.30, 1.0)
    start_pad: Color = (0.12, 0.36, 0.48, 1.0)
    wall: Color = (0.36, 0.40, 0.43, 1.0)
    wall_accent: Color = (0.86, 0.70, 0.30, 1.0)
    obstacle: Color = (0.50, 0.39, 0.25, 1.0)
    obstacle_cap: Color = (0.62, 0.50, 0.32, 1.0)
    obstacle_stripe: Color = (0.95, 0.72, 0.22, 1.0)
    target: Color = (0.14, 0.92, 0.54, 1.0)
    target_core: Color = (0.65, 1.00, 0.78, 1.0)
    target_pad: Color = (0.08, 0.38, 0.27, 1.0)
    rover_body: Color = (0.10, 0.42, 0.78, 1.0)
    rover_panel: Color = (0.15, 0.58, 0.96, 1.0)
    rover_accent: Color = (0.98, 0.76, 0.30, 1.0)
    rover_dark: Color = (0.05, 0.07, 0.08, 1.0)
    rover_light: Color = (0.92, 0.96, 1.0, 1.0)
    sensor_glow: Color = (0.10, 0.78, 0.86, 1.0)
    collision_flash: Color = (1.0, 0.28, 0.20, 1.0)
    path: Color = (0.95, 0.82, 0.22, 1.0)
    ui_panel: Color = (0.030, 0.045, 0.052, 0.82)
    ui_panel_soft: Color = (0.055, 0.072, 0.078, 0.74)
    ui_panel_active: Color = (0.120, 0.360, 0.480, 0.86)
    ui_panel_positive: Color = (0.080, 0.380, 0.270, 0.86)
    ui_panel_warning: Color = (0.510, 0.390, 0.150, 0.88)
    ui_panel_danger: Color = (0.520, 0.120, 0.100, 0.88)
    ui_text: Color = (0.920, 0.960, 0.980, 1.0)
    ui_muted: Color = (0.700, 0.800, 0.830, 1.0)


THEME = VisualTheme()


def apply_material(
    node: NodePath,
    color: Color,
    *,
    specular: tuple[float, float, float, float] = (0.22, 0.24, 0.25, 1.0),
    shininess: float = 20.0,
) -> NodePath:
    material = Material()
    material.setDiffuse(color)
    material.setAmbient(tuple(channel * 0.55 for channel in color[:3]) + (color[3],))
    material.setSpecular(specular)
    material.setShininess(shininess)
    node.setMaterial(material, 1)
    node.setColor(*color)
    return node
