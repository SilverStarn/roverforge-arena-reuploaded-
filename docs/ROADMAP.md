# Roadmap

This backlog groups possible improvements by system area. Items are intentionally small enough to
be implemented and reviewed independently.

## Current Pass

- Started item 21 by moving rendering settings into `game/rendering/settings.py`.
- Completed item 41 by moving HUD text management into `game/rendering/hud.py`.
- Started item 22 with a short episode summary after success or timeout.
- Added startup guidance and reward breakdown text to make manual play understandable.
- Completed item 24 with smoothed chase and overhead camera movement.
- Completed item 27 with collision flash feedback on the rover.
- Started item 28 by centralizing scene colors and materials in `game/rendering/theme.py`.
- Added a graphics pass for floor panels, wall rails, obstacle detail, animated target beacons,
  rover body parts, wheel motion, and additional lighting.
- Added live HUD metric tiles and clickable controls for core gameplay and debug state.
- Added rendered-pose interpolation so movement and camera tracking are smoother without changing
  fixed-step simulation behavior.

## Simulation

1. Add episode scenario presets with different arena sizes, obstacle counts, and target layouts.
2. Add moving obstacles with deterministic paths.
3. Add one-way hazard zones that penalize traversal without ending the episode.
4. Add per-target reward weights so some targets are higher priority.
5. Add configurable spawn regions for agent, targets, and obstacles.
6. Add environment serialization to save and replay generated levels.
7. Add deterministic replay files that record seed, actions, and episode outcome.
8. Add reward profiles for sparse, shaped, and collision-heavy training runs.
9. Add a separate terminal penalty for timeouts.
10. Add collision cooldown so repeated wall contact is not over-counted every frame.

## Agents

11. Add a waypoint-following agent that consumes an externally supplied route.
12. Add a frontier-exploration agent that prioritizes unknown/open space.
13. Add an agent comparison command that runs multiple policies over the same seed set.
14. Add planner diagnostics with expanded node count and path cost.
15. Add a behavior tree agent for clearer decision tracing.
16. Add manual action recording so human play can be replayed as an episode.
17. Add a keyboard-to-action adapter test suite.
18. Add configurable planner cell size from the CLI.
19. Add path smoothing after A* to reduce zig-zag motion.
20. Add policy hooks for external ML agents without importing a training framework.

## Rendering And UX

21. Split Panda3D app state, HUD, input, camera, and scene construction into separate modules.
22. Add a compact episode summary overlay after success or timeout.
23. Add a minimap-style overhead inset.
24. Add smoother chase camera interpolation.
25. Add a free-look inspection camera.
26. Add target collection animations.
27. Add collision flash feedback on the rover.
28. Add debug color themes for light and dark backgrounds.
29. Add line thickness scaling for debug overlays at different zoom levels.
30. Add a small FPS and frame-time overlay that can be toggled.

## CLI And Data

31. Add CSV export in addition to JSONL.
32. Add aggregate evaluation output as JSON for scripts.
33. Add seed range syntax such as `--seed-range 10:50`.
34. Add a `replay` command that consumes recorded action files.
35. Add a `snapshot` command that writes a level description to disk.
36. Add benchmark warmup steps before timing.
37. Add percentile timing metrics for benchmark output.
38. Add command presets for common local checks.
39. Add machine-readable version and config output.
40. Add CLI tests for each command's main output shape.

## Code Quality

41. Move HUD code out of `ArenaApp`.
42. Move camera logic out of `ArenaApp`.
43. Move input bindings out of `ArenaApp`.
44. Add typed observation models to replace raw dictionaries.
45. Add stricter typing for reward info fields.
46. Add unit tests for pathfinding corner cases.
47. Add tests for terminal timeout behavior.
48. Add rendering smoke tests for debug-layer toggles.
49. Add a small architecture decision record for the optional C++ boundary.
50. Add packaging checks for the console script entry point.
