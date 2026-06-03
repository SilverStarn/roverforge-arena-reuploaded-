"""Optional C++ acceleration hooks with a pure-Python fallback."""

from __future__ import annotations

import ctypes
import os
import platform
from pathlib import Path
from typing import Iterable, Sequence


_LIB = None
_LOAD_ERROR: str | None = None


def _candidate_library_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    env_path = os.environ.get("PANDA_ARENA_NATIVE")
    names: list[str]
    if platform.system() == "Windows":
        names = ["arena_native.dll"]
        config_dirs = ["Release", "Debug", ""]
    elif platform.system() == "Darwin":
        names = ["libarena_native.dylib"]
        config_dirs = [""]
    else:
        names = ["libarena_native.so"]
        config_dirs = [""]

    paths: list[Path] = []
    if env_path:
        paths.append(Path(env_path))
    for config_dir in config_dirs:
        for name in names:
            paths.append(root / "cpp" / "build" / config_dir / name)
    return paths


def _load_library():
    global _LIB, _LOAD_ERROR
    if _LIB is not None or _LOAD_ERROR is not None:
        return _LIB

    for path in _candidate_library_paths():
        if not path.exists():
            continue
        try:
            lib = ctypes.CDLL(str(path))
            lib.score_path.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_int,
                ctypes.c_double,
                ctypes.c_double,
            ]
            lib.score_path.restype = ctypes.c_double
            _LIB = lib
            return _LIB
        except OSError as exc:
            _LOAD_ERROR = str(exc)
            return None

    _LOAD_ERROR = "native library not found"
    return None


def native_status() -> str:
    """Return a short status string for debug overlays and benchmark output."""
    lib = _load_library()
    if lib is not None:
        return "native C++ scorer: enabled"
    return f"native C++ scorer: fallback ({_LOAD_ERROR})"


def _fallback_score_path(sensors: Sequence[float], target_delta: tuple[float, float]) -> float:
    if not sensors:
        return 0.0

    front_start = max(0, len(sensors) // 2 - 1)
    front = sensors[front_start : front_start + 3]
    front_clearance = sum(front) / len(front)
    average_clearance = sum(sensors) / len(sensors)

    target_x, target_y = target_delta
    target_distance = max((target_x * target_x + target_y * target_y) ** 0.5, 0.001)
    forward_alignment = target_y / target_distance

    return 0.55 * front_clearance + 0.25 * average_clearance + 0.20 * forward_alignment


def score_path(sensors: Iterable[float], target_delta: tuple[float, float]) -> float:
    """Score the current path from sensor distances and target direction.

    The C++ implementation is intentionally small and optional. The Python fallback
    keeps the project runnable on machines without a compiler.
    """
    sensor_values = tuple(float(value) for value in sensors)
    lib = _load_library()
    if lib is None:
        return _fallback_score_path(sensor_values, target_delta)

    array_type = ctypes.c_double * len(sensor_values)
    sensor_array = array_type(*sensor_values)
    return float(lib.score_path(sensor_array, len(sensor_values), target_delta[0], target_delta[1]))
