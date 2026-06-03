"""Command-line entry points for RoverForge Arena."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from game.agents import make_agent
from game.agents.factory import AGENT_CHOICES
from game.core import ArenaConfig, TrainingArenaEnv, average_metric, run_episode
from game.core.types import EpisodeMetrics
from game.native import native_status


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RoverForge Arena")
    subparsers = parser.add_subparsers(dest="command", required=True)

    play = subparsers.add_parser("play", help="launch the Panda3D interactive simulation")
    play.add_argument("--seed", type=int, default=7)
    play.add_argument("--agent", choices=AGENT_CHOICES, default="planner")
    play.add_argument("--autopilot", action="store_true", help="start with autonomous control enabled")

    evaluate = subparsers.add_parser("eval", help="run headless evaluation episodes")
    evaluate.add_argument("--episodes", type=positive_int, default=12)
    evaluate.add_argument("--seed", type=int, default=7)
    evaluate.add_argument("--max-steps", type=positive_int, help="override max simulation steps per episode")
    evaluate.add_argument("--agent", choices=AGENT_CHOICES, default="planner")
    evaluate.add_argument("--jsonl", type=Path, help="optional file for episode metrics")

    benchmark = subparsers.add_parser("benchmark", help="measure simulation step throughput")
    benchmark.add_argument("--steps", type=positive_int, default=5000)
    benchmark.add_argument("--seed", type=int, default=7)
    benchmark.add_argument("--agent", choices=AGENT_CHOICES, default="rule")
    benchmark.add_argument(
        "--render-frames",
        type=positive_int,
        default=0,
        help="also launch Panda3D and measure rendered frame FPS",
    )

    return parser


def command_eval(args: argparse.Namespace) -> int:
    rows: list[EpisodeMetrics] = []
    env = TrainingArenaEnv(ArenaConfig(seed=args.seed))
    agent = make_agent(args.agent, env, seed=args.seed)

    writer = None
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True, exist_ok=True)
        writer = args.jsonl.open("w", encoding="utf-8")

    try:
        for index in range(args.episodes):
            row = run_episode(env, agent, seed=args.seed + index, max_steps=args.max_steps)
            rows.append(row)
            if writer:
                writer.write(json.dumps(row, sort_keys=True) + "\n")
    finally:
        if writer:
            writer.close()

    success_rate = average_metric(rows, "success")
    completion = average_metric(rows, "completion")
    reward = average_metric(rows, "reward")
    collisions = average_metric(rows, "collisions")
    steps = average_metric(rows, "steps")
    timeout_rate = average_metric(rows, "timed_out")

    print(f"agent={args.agent} episodes={args.episodes} seed={args.seed}")
    print(native_status())
    print(
        "success_rate={:.0%} timeout_rate={:.0%} avg_completion={:.0%} "
        "avg_steps={:.1f} avg_reward={:.2f} avg_collisions={:.2f}".format(
            success_rate, timeout_rate, completion, steps, reward, collisions
        )
    )
    if args.jsonl:
        print(f"wrote episode metrics to {args.jsonl}")
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    env = TrainingArenaEnv(ArenaConfig(seed=args.seed))
    agent = make_agent(args.agent, env, seed=args.seed)
    observation = env.reset(args.seed)

    wall_start = perf_counter()
    step_time_total = 0.0
    max_step_seconds = 0.0
    for index in range(args.steps):
        step_start = perf_counter()
        result = env.step(agent.act(observation))
        step_seconds = perf_counter() - step_start
        step_time_total += step_seconds
        max_step_seconds = max(max_step_seconds, step_seconds)
        observation = result.observation
        if result.done:
            observation = env.reset(args.seed + index + 1)
    elapsed = perf_counter() - wall_start

    throughput = args.steps / elapsed
    avg_step_ms = step_time_total / args.steps * 1000.0
    max_step_ms = max_step_seconds * 1000.0
    target_fps = 1.0 / env.config.step_seconds
    print(native_status())
    print(
        "simulation: agent={} steps={} wall_time={:.3f}s target_fps={:.1f} "
        "throughput_fps={:.0f} avg_step_ms={:.3f} max_step_ms={:.3f}".format(
            args.agent,
            args.steps,
            elapsed,
            target_fps,
            throughput,
            avg_step_ms,
            max_step_ms,
        )
    )
    if args.render_frames > 0:
        frame_result = run_render_benchmark(args.render_frames, args.seed, args.agent)
        print(
            "render: frames={frames} wall_time={elapsed:.3f}s fps={fps:.1f} "
            "avg_frame_ms={avg_frame_ms:.3f}".format(**frame_result)
        )
    return 0


def run_render_benchmark(frames: int, seed: int, agent_name: str = "planner") -> dict[str, float | int]:
    from game.rendering import ArenaApp

    app = ArenaApp(seed=seed, autopilot=True, agent_name=agent_name)
    start = perf_counter()
    try:
        for _ in range(frames):
            app.taskMgr.step()
    finally:
        elapsed = perf_counter() - start
        app.destroy()

    fps = frames / elapsed if elapsed > 0.0 else 0.0
    return {
        "frames": frames,
        "elapsed": elapsed,
        "fps": fps,
        "avg_frame_ms": 1000.0 / fps if fps > 0.0 else 0.0,
    }


def command_play(args: argparse.Namespace) -> int:
    from game.rendering import ArenaApp

    app = ArenaApp(seed=args.seed, autopilot=args.autopilot, agent_name=args.agent)
    app.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "eval":
        return command_eval(args)
    if args.command == "benchmark":
        return command_benchmark(args)
    if args.command == "play":
        return command_play(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
