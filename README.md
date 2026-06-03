# RoverForge Arena

RoverForge Arena is a Panda3D simulation where a rover navigates a warehouse-style arena, avoids
obstacles, collects targets, and records episode metrics. The simulation can run with a Panda3D
window for interactive inspection or headlessly for batch evaluation.


## Features

- Manual driving and autonomous control.
- Deterministic `reset(seed)` / `step(action)` simulation API.
- Headless evaluation with JSONL metrics.
- Sensor, collision-bound, reward-event, and pathfinding debug views.
- Short episode summary after success or timeout.
- Startup guide, live metric tiles, and clickable gameplay controls.
- Simulation and render benchmark commands.
- Optional C++ scorer loaded behind a Python fallback.
- Themed procedural arena with materials, lighting, animated targets, rover detail, and collision feedback.
- No external asset downloads are required.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Run the interactive simulation:

```powershell
.\.venv\Scripts\python -m game.main play
```

Start with autonomous control enabled:

```powershell
.\.venv\Scripts\python -m game.main play --autopilot --agent planner
```

Run headless evaluation episodes:

```powershell
.\.venv\Scripts\python -m game.main eval --episodes 20 --seed 7
```

Compare against the reactive policy:

```powershell
.\.venv\Scripts\python -m game.main eval --episodes 20 --seed 7 --agent rule
```

Run a simulation benchmark:

```powershell
.\.venv\Scripts\python -m game.main benchmark --steps 10000 --agent rule
```

Measure rendered frame rate as well:

```powershell
.\.venv\Scripts\python -m game.main benchmark --steps 10000 --agent planner --render-frames 300
```

Run tests:

```powershell
.\.venv\Scripts\python -m unittest discover -v
```

Run lint after installing optional dev tools:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m ruff check .
```

## Controls

- `W/S`: forward and reverse
- `A/D`: turn
- `Tab`: toggle autopilot
- `H`: show or hide the guide
- `Enter` or `Got it`: dismiss the guide
- `P`: pause or resume simulation
- `N`: advance one simulation step while paused
- `C`: switch chase/overhead camera
- `Space`: new seeded arena
- `F1`: toggle all debug views
- `F2`: toggle sensor rays
- `F3`: toggle collision bounds
- `F4`: toggle planner path
- `F5`: toggle reward events
- `Esc`: quit

## Project Structure

```text
game/
  core/            Simulation config, models, environment, evaluation helpers
  agents/          Grid-planning, reactive, and random policies
  rendering/       Panda3D app, HUD, camera, debug views, geometry, visual theme
  main.py          CLI commands for play, eval, and benchmark
  native.py        Optional C++ loader with Python fallback
cpp/
  path_score.cpp   Native path scoring implementation
docs/
  ARCHITECTURE.md
  CAPABILITIES.md
  REVIEW_NOTES.md
  ROADMAP.md
  RUNBOOK.md
  GITHUB_WORKFLOW.md
tests/
  test_cli.py
  test_hud.py
  test_simulation.py
```

After installing the project in editable mode, the CLI is also available as `roverforge`.

## Optional C++ Build

The project runs without compiling C++. When CMake and a C++ compiler are available:

```powershell
cmake -S cpp -B cpp/build
cmake --build cpp/build --config Release
```

The Python loader looks for `cpp/build/Release/arena_native.dll` on Windows. You can also set an
explicit native library path with `PANDA_ARENA_NATIVE`.

## Notes

- The simulation is deterministic for a given seed.
- Rendering is isolated from simulation rules so batch evaluation can run without a window.
- Visual styling is centralized in `game/rendering/theme.py` and `game/rendering/settings.py`.
- Gameplay HUD buttons mirror the keyboard controls for autopilot, pause, camera, reset, and debug layers.
- `planner`, `rule`, and `random` agents can be selected from the CLI.
- Terminal episodes are safe to call again; a post-terminal `step()` returns zero reward.
