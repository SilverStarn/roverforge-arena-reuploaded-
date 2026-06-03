"""Procedural Panda3D geometry helpers."""

from __future__ import annotations

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    NodePath,
)

from game.rendering.theme import THEME


Color = tuple[float, float, float, float]
BoxSize = tuple[float, float, float]


def make_box(name: str, size: BoxSize, color: Color) -> NodePath:
    """Create a simple box with per-face normals and a flat color."""
    width, depth, height = size
    hx = width / 2.0
    hy = depth / 2.0
    z0 = 0.0
    z1 = height

    faces = (
        (((-hx, -hy, z0), (-hx, hy, z0), (hx, hy, z0), (hx, -hy, z0)), (0, 0, -1)),
        (((-hx, -hy, z1), (hx, -hy, z1), (hx, hy, z1), (-hx, hy, z1)), (0, 0, 1)),
        (((-hx, -hy, z0), (hx, -hy, z0), (hx, -hy, z1), (-hx, -hy, z1)), (0, -1, 0)),
        (((hx, -hy, z0), (hx, hy, z0), (hx, hy, z1), (hx, -hy, z1)), (1, 0, 0)),
        (((hx, hy, z0), (-hx, hy, z0), (-hx, hy, z1), (hx, hy, z1)), (0, 1, 0)),
        (((-hx, hy, z0), (-hx, -hy, z0), (-hx, -hy, z1), (-hx, hy, z1)), (-1, 0, 0)),
    )

    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(vertex_data, "vertex")
    normal = GeomVertexWriter(vertex_data, "normal")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)

    row = 0
    for corners, face_normal in faces:
        for corner in corners:
            vertex.addData3(*corner)
            normal.addData3(*face_normal)
            color_writer.addData4(*color)
        triangles.addVertices(row, row + 1, row + 2)
        triangles.addVertices(row, row + 2, row + 3)
        row += 4

    geom = Geom(vertex_data)
    geom.addPrimitive(triangles)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)


def make_cylinder(
    name: str,
    radius: float,
    height: float,
    color: Color,
    segments: int = 32,
) -> NodePath:
    """Create a vertical cylinder with simple top, bottom, and side faces."""
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(vertex_data, "vertex")
    normal = GeomVertexWriter(vertex_data, "normal")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)

    # Side vertices.
    for z in (0.0, height):
        for index in range(segments):
            angle = math.tau * index / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertex.addData3(x, y, z)
            normal.addData3(math.cos(angle), math.sin(angle), 0)
            color_writer.addData4(*color)

    for index in range(segments):
        next_index = (index + 1) % segments
        bottom_a = index
        bottom_b = next_index
        top_a = index + segments
        top_b = next_index + segments
        triangles.addVertices(bottom_a, bottom_b, top_b)
        triangles.addVertices(bottom_a, top_b, top_a)

    top_center = segments * 2
    vertex.addData3(0, 0, height)
    normal.addData3(0, 0, 1)
    color_writer.addData4(*color)
    bottom_center = top_center + 1
    vertex.addData3(0, 0, 0)
    normal.addData3(0, 0, -1)
    color_writer.addData4(*color)

    for index in range(segments):
        next_index = (index + 1) % segments
        triangles.addVertices(top_center, index + segments, next_index + segments)
        triangles.addVertices(bottom_center, next_index, index)

    geom = Geom(vertex_data)
    geom.addPrimitive(triangles)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)


def make_grid(
    name: str,
    width: float,
    depth: float,
    spacing: float = 1.0,
    color: Color = THEME.grid,
) -> NodePath:
    lines = LineSegs(name)
    lines.setThickness(1.0)
    lines.setColor(*color)

    x = -width / 2.0
    while x <= width / 2.0 + 0.001:
        lines.moveTo(x, -depth / 2.0, 0.025)
        lines.drawTo(x, depth / 2.0, 0.025)
        x += spacing

    y = -depth / 2.0
    while y <= depth / 2.0 + 0.001:
        lines.moveTo(-width / 2.0, y, 0.026)
        lines.drawTo(width / 2.0, y, 0.026)
        y += spacing

    return NodePath(lines.create())
