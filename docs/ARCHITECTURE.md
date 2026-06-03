# Architecture

## Overview

The project separates simulation from rendering so AI evaluation can run headlessly while Panda3D
handles only the interactive visualization.

```text
CLI / Panda3D app
        |
        v
TrainingArenaEnv.reset(seed)
TrainingArenaEnv.step(action)
        |
        v
observations + rewards + episode metrics
```

## Simulation Layer

`game/core/environment.py` owns deterministic world generation, target collection, collision checks,
range sensor scans, reward shaping, and episode termination.

The environment intentionally resembles common reinforcement learning APIs:

- `reset(seed)` creates a reproducible arena.
- `step(action)` advances the simulation by one fixed timestep.
- `observation` contains position, heading, sensor distances, target direction, and progress.
- `reward` encourages target collection, forward progress, and obstacle avoidance.
- `reward_events` records notable reward changes such as collisions, target collection, and success.
- `done` marks success or timeout.

## Rendering Layer

`game/rendering/arena_app.py` is a Panda3D `ShowBase` application. It builds the arena from
procedural meshes, syncs visual nodes from the simulation state, and exposes layered debug views.

The scene uses `game/rendering/theme.py` for shared material colors and `game/rendering/settings.py`
for window, camera, debug, and animation settings. Arena floors, wall rails, obstacle caps, target
beacons, rover parts, wheel motion, target idle animation, and collision flash feedback all live in
the rendering layer.

`game/rendering/hud.py` owns gameplay overlay formatting and DirectGUI widgets. It exposes testable
formatting helpers for progress, reward deltas, metric tiles, and button labels while `ArenaApp`
wires those widgets to the same callbacks used by keyboard input.

Rendered rover motion uses interpolation between fixed simulation steps. The simulation state stays
deterministic, while visuals, camera tracking, wheel motion, and debug overlays update smoothly on
each rendered frame.

The Panda3D layer does not own game rules. This keeps automated evaluation, tests, and future AI
training integrations independent from the graphics window.

## Debug Views

Debug rendering lives in `game/rendering/debug_draw.py` and is consumed by `ArenaApp`.

- Sensor rays show local range readings from the current observation.
- Collision bounds show the agent radius, target collection radius, and obstacle rectangles.
- Reward events show a short text feed plus world-space markers for notable reward changes.
- Pathfinding shows the current A* waypoint path when autopilot is enabled.

The renderer also supports pause, single-step, chase camera, and overhead camera modes so reviewers
can inspect simulation state without changing the deterministic core loop.

## Agent Layer

`game/agents/` includes three baselines:

- `GridPlannerAgent`: map-aware A* planner that tracks waypoints around obstacles.
- `RuleBasedAgent`: follows target direction while steering away from blocked sensor rays.
- `RandomAgent`: provides a simple comparison baseline for evaluation.

## Native C++ Boundary

`game/native.py` tries to load the optional `arena_native` shared library. If unavailable, it uses a
matching Python implementation. This lets the project run on machines without C++ tools while still
keeping a clear native extension boundary.

## Performance Notes

- The simulation uses fixed timesteps for stable behavior across hardware.
- Procedural geometry avoids runtime asset download and licensing concerns.
- Render styling is centralized to keep scene polish consistent as new objects are added.
- Headless evaluation bypasses Panda3D rendering for faster batch runs.
- Sensor rays use inexpensive 2D sampling suitable for this arena size.
- `benchmark` reports CPU step timing and can optionally measure rendered frame FPS.
