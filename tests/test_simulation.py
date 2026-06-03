from __future__ import annotations

import math
import unittest

from game.core.actions import normalize_action
from game.agents import GridPlannerAgent, RuleBasedAgent
from game.core import ArenaConfig, RectObstacle, Target, TrainingArenaEnv, run_episode


class TrainingArenaEnvTests(unittest.TestCase):
    def test_reset_is_deterministic_for_same_seed(self) -> None:
        config = ArenaConfig(seed=42, obstacle_count=4, target_count=3)
        env_a = TrainingArenaEnv(config)
        env_b = TrainingArenaEnv(config)

        env_a.reset(11)
        env_b.reset(11)

        self.assertEqual(env_a.obstacles, env_b.obstacles)
        self.assertEqual([(t.x, t.y) for t in env_a.targets], [(t.x, t.y) for t in env_b.targets])

    def test_invalid_config_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ArenaConfig(width=0)
        with self.assertRaises(ValueError):
            ArenaConfig(obstacle_count=-1)

    def test_action_normalization_rejects_non_finite_values(self) -> None:
        action = normalize_action({"turn": math.nan, "throttle": "bad"})

        self.assertEqual(action, {"turn": 0.0, "throttle": 0.0})

    def test_target_collection_produces_reward_and_done(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(width=8, depth=8, obstacle_count=0, target_count=1))
        env.reset(1)
        env.targets = [Target(env.agent.x, env.agent.y + 0.35)]

        result = env.step({"turn": 0.0, "throttle": 0.0})

        self.assertTrue(result.done)
        self.assertEqual(result.info["collected"], 1)
        self.assertGreater(result.reward, 5.0)
        self.assertAlmostEqual(sum(result.reward_breakdown.values()), result.reward)
        self.assertEqual([event.label for event in result.reward_events], ["target x1", "episode success"])

    def test_terminal_episode_does_not_reaward_success(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(width=8, depth=8, obstacle_count=0, target_count=1))
        env.reset(1)
        env.targets = [Target(env.agent.x, env.agent.y + 0.35)]

        first = env.step({"turn": 0.0, "throttle": 0.0})
        second = env.step({"turn": 0.0, "throttle": 0.0})

        self.assertTrue(first.done)
        self.assertTrue(second.done)
        self.assertEqual(second.reward, 0.0)
        self.assertTrue(second.info["already_done"])
        self.assertEqual(env.total_reward, first.reward)

    def test_collision_blocks_agent_motion(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(width=8, depth=8, obstacle_count=0, target_count=1))
        env.reset(2)
        env.obstacles = [RectObstacle(env.agent.x, env.agent.y + 0.50, 1.0, 1.0, 1.0)]
        original_position = (env.agent.x, env.agent.y)

        result = env.step({"turn": 0.0, "throttle": 1.0})

        self.assertTrue(result.info["collided"])
        self.assertEqual((env.agent.x, env.agent.y), original_position)
        self.assertEqual(result.reward_events[0].label, "collision")
        self.assertLess(result.reward_breakdown["collision"], 0.0)

    def test_rule_agent_episode_returns_metrics(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(seed=5, obstacle_count=2, target_count=2, max_steps=60))
        row = run_episode(env, RuleBasedAgent(), seed=5)

        self.assertEqual(row["seed"], 5)
        self.assertIn("reward", row)
        self.assertIn(row["terminal_reason"], {"running", "success", "timeout"})
        self.assertGreaterEqual(row["completion"], 0.0)
        self.assertLessEqual(row["completion"], 1.0)

    def test_grid_planner_can_finish_simple_episode(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(seed=5, obstacle_count=2, target_count=2, max_steps=300))
        row = run_episode(env, GridPlannerAgent(env), seed=5)

        self.assertTrue(row["success"])
        self.assertEqual(row["collisions"], 0)

    def test_grid_planner_exposes_debug_path(self) -> None:
        env = TrainingArenaEnv(ArenaConfig(seed=5, obstacle_count=2, target_count=2, max_steps=300))
        observation = env.reset(5)
        agent = GridPlannerAgent(env)

        agent.act(observation)

        self.assertGreater(len(agent.path), 0)

    def test_legacy_import_paths_remain_available(self) -> None:
        from game.agent import GridPlannerAgent as LegacyGridPlannerAgent
        from game.simulation import TrainingArenaEnv as LegacyTrainingArenaEnv

        self.assertIs(LegacyGridPlannerAgent, GridPlannerAgent)
        self.assertIs(LegacyTrainingArenaEnv, TrainingArenaEnv)


if __name__ == "__main__":
    unittest.main()
