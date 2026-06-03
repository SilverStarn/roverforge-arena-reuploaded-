# Capabilities

This file lists the main systems and the quickest way to verify each one.

| Capability | Primary Files | Verification |
| --- | --- | --- |
| Manual driving | `game/rendering/arena_app.py` | `python -m game.main play` |
| Startup guide and gameplay HUD | `game/rendering/hud.py` | Launch the app; press `H` or use the Guide button |
| Live metric tiles | `game/rendering/hud.py` | Watch score, beacons, step count, speed, and clearance while driving |
| Clickable gameplay controls | `game/rendering/hud.py`, `game/rendering/arena_app.py` | Use the right-side buttons for autopilot, pause, camera, reset, and debug layers |
| Autonomous control | `game/agents/grid_planner.py` | `python -m game.main play --autopilot --agent planner` |
| Pause, single-step, camera modes | `game/rendering/arena_app.py` | `P`, `N`, and `C` while the app is running |
| Smoothed chase and overhead cameras | `game/rendering/arena_app.py`, `game/rendering/settings.py` | Move the rover, then press `C` to compare camera modes |
| Themed procedural scene | `game/rendering/theme.py`, `game/rendering/geometry.py` | Launch the app and inspect floor panels, rails, obstacles, targets, and rover parts |
| Animated targets and rover feedback | `game/rendering/arena_app.py`, `game/rendering/settings.py` | Watch target beacons pulse; collide to see rover flash feedback |
| Headless evaluation | `game/core/evaluation.py`, `game/main.py` | `python -m game.main eval --episodes 20 --seed 7` |
| Sensor debug view | `game/rendering/arena_app.py` | `F2` while the app is running |
| Collision bounds debug view | `game/rendering/debug_draw.py` | `F3` while the app is running |
| Reward event debug view | `game/core/models.py`, `game/rendering/arena_app.py` | Collect a target or collide; use `F5` to toggle |
| Reward breakdown | `game/rendering/hud.py` | Watch the reward line after each simulation step |
| Episode summary | `game/rendering/hud.py`, `game/rendering/arena_app.py` | Finish or timeout an episode |
| Pathfinding debug view | `game/agents/grid_planner.py`, `game/rendering/arena_app.py` | Run autopilot and use `F4` |
| Benchmark command | `game/main.py` | `python -m game.main benchmark --steps 10000 --agent rule --render-frames 300` |
| CLI validation | `game/main.py` | Invalid zero/negative counts fail fast |
| Terminal lifecycle safety | `game/core/environment.py` | `step()` after `done` returns zero reward |
| Optional C++ scorer | `cpp/path_score.cpp`, `game/native.py` | Build the native module or use fallback status |

## Implementation Notes

- The simulation layer is independent of Panda3D and can run in automated tests or batch jobs.
- Scene styling is centralized so material choices and animation timings can be changed without touching simulation rules.
- Debug views are separate toggles so one system can be inspected at a time.
- Reward events are emitted by the simulation and reused by logs, tests, and rendering.
