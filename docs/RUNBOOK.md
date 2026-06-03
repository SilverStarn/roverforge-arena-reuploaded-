# Development Runbook

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Common Commands

Manual play:

```powershell
.\.venv\Scripts\python -m game.main play
```

Autonomous run:

```powershell
.\.venv\Scripts\python -m game.main play --autopilot --agent planner
```

Headless evaluation:

```powershell
.\.venv\Scripts\python -m game.main eval --episodes 50 --seed 7 --jsonl episode_logs/planner.jsonl
```

Benchmark:

```powershell
.\.venv\Scripts\python -m game.main benchmark --steps 10000 --agent rule --render-frames 300
```

Tests:

```powershell
.\.venv\Scripts\python -m unittest discover -v
```

## Debug View Controls

- `H`: show or hide the guide
- `Enter`: dismiss the guide
- `P`: pause or resume simulation
- `N`: advance one simulation step while paused
- `C`: switch chase/overhead camera
- `F1`: all debug views
- `F2`: sensor rays
- `F3`: collision bounds
- `F4`: planner path
- `F5`: reward events

## Evaluation Output

The evaluation command reports success rate, average completion, reward, and collisions. Use JSONL
output when comparing agents across seeds or attaching run artifacts to a pull request.

## Benchmark Output

The benchmark reports:

- `target_fps`: fixed simulation rate configured by `ArenaConfig.step_seconds`
- `throughput_fps`: how many simulation steps the CPU completed per second
- `avg_step_ms`: average CPU time per simulation step
- `max_step_ms`: slowest measured simulation step
- `render fps`: optional measured Panda3D frame loop rate when `--render-frames` is provided
