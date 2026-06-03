# Contributing

Keep changes small, testable, and scoped to the layer they affect.

## Before Opening A Pull Request

Run:

```powershell
.\.venv\Scripts\python -m unittest discover -v
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m compileall -q game tests
.\.venv\Scripts\python -m game.main eval --episodes 5 --seed 7 --max-steps 900
.\.venv\Scripts\python -m game.main benchmark --steps 1000 --seed 7 --agent rule
```

For rendering changes, also run:

```powershell
.\.venv\Scripts\python -m game.main benchmark --steps 100 --seed 7 --render-frames 30
```

## Engineering Guidelines

- Keep simulation logic in `game/core`, not in Panda3D rendering classes.
- Keep agents in `game/agents` and expose reusable public state for debug views.
- Add tests for deterministic behavior, terminal conditions, and CLI output when behavior changes.
- Preserve compatibility shims unless a breaking-change migration is planned.
- Prefer explicit metrics and logs over behavior that can only be inspected visually.

## Optional Dev Tools

The runtime dependency list stays small. Extra tooling is declared in `pyproject.toml`:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```
