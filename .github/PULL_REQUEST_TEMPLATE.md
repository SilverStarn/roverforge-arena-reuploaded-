## Summary

- 

## Verification

- [ ] `python -m unittest discover -v`
- [ ] `python -m ruff check .`
- [ ] `python -m compileall -q game tests`
- [ ] `python -m game.main eval --episodes 5 --seed 7 --max-steps 900`
- [ ] `python -m game.main benchmark --steps 1000 --seed 7 --agent rule`

## Review Notes

- Determinism or seed behavior:
- Performance impact:
- Rendering/debug-view impact:
- Native C++ fallback impact:
