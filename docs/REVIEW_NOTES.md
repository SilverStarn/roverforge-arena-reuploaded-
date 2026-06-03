# Review Notes

These notes capture a few edge cases and design decisions that are easy to miss during a quick read.

## Fixed Edge Cases

| Area | Issue | Current Behavior |
| --- | --- | --- |
| Episode lifecycle | Repeated `step()` calls after success could change totals. | Terminal episodes return `done=True`, zero reward, and no new events. |
| CLI validation | Zero or negative counts are not meaningful for eval/benchmark commands. | Positive integer validation is applied at argument parsing. |
| Autopilot configuration | Agent selection used to be implicit in the app. | `--agent` is available for play, eval, and benchmark. |
| Planner movement | Diagonal A* moves could pass between blocked adjacent cells. | Diagonal neighbors are rejected when either side cell is blocked. |
| Metrics | Episode rows needed enough context for agent comparisons. | JSONL rows include timeout, terminal reason, target counts, completion, reward, and collisions. |
| Input handling | Non-finite action values could cross the policy boundary. | Bad action values normalize to zero turn/throttle. |
| Config handling | Invalid arena dimensions and counts were accepted. | `ArenaConfig` validates dimensions, counts, and sensor ranges. |

## Verification Commands

```powershell
.\.venv\Scripts\python -m unittest discover -v
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m compileall -q game tests
.\.venv\Scripts\python -m game.main eval --episodes 5 --seed 7 --max-steps 900
.\.venv\Scripts\python -m game.main benchmark --steps 1000 --seed 7 --agent rule
.\.venv\Scripts\python -m game.main benchmark --steps 100 --seed 7 --agent planner --render-frames 5
```

## Boundaries

- Simulation rules live in `game/core`.
- Agent policies live in `game/agents`.
- Panda3D-specific code lives in `game/rendering`.
- The native scorer is optional and must not be required for normal Python execution.
