# GitHub Workflow

Use this workflow for changes that touch simulation behavior, rendering, agents, or CLI output.

## Branching

Use short-lived feature branches:

```text
main
feature/agent-eval-logs
feature/native-sensor-scorer
fix/collision-edge-case
```

## Pull Requests

Each pull request should include:

- A short summary of behavior changed.
- Screenshots or evaluation output when the visual simulation changes.
- Test results from `python -m unittest discover`.
- Notes about determinism, performance, or compatibility risks.

## Review Focus

Reviewers should look for:

- Deterministic behavior when a seed is provided.
- Clear separation between Panda3D rendering and simulation rules.
- Reasonable reward values and termination conditions.
- Cross-platform path handling.
- Native module fallback behavior.

## CI

The included GitHub Actions workflow installs dependencies, runs Ruff, compiles Python files, runs
unit tests, and executes small CLI smoke checks.
