from __future__ import annotations

import unittest

from game.rendering.hud import (
    format_button_label,
    format_debug_mode,
    format_metric_tiles,
    format_native_badge,
    format_progress_line,
    format_reward_breakdown,
    guide_text,
)


class HudFormattingTests(unittest.TestCase):
    def test_progress_line_explains_targets_steps_and_completion(self) -> None:
        text = format_progress_line(
            {"targets_remaining": 2, "completion_ratio": 0.6, "step": 120},
            target_count=5,
            max_steps=900,
        )

        self.assertEqual(text, "beacons 3/5 | steps 120/900 | complete 60%")

    def test_reward_breakdown_labels_score_changes(self) -> None:
        text = format_reward_breakdown(
            {
                "last_reward_breakdown": {
                    "time": -0.01,
                    "progress": 0.03,
                    "target": 1.0,
                    "collision": -0.35,
                    "success": 0.0,
                }
            }
        )

        self.assertIn("time -0.01", text)
        self.assertIn("progress +0.03", text)
        self.assertIn("beacon +1.00", text)
        self.assertIn("collision -0.35", text)
        self.assertIn("\n", text)

    def test_metric_tiles_show_current_run_values(self) -> None:
        tiles = dict(
            format_metric_tiles(
                {
                    "targets_remaining": 1,
                    "speed": -2.5,
                    "step": 42,
                    "path_score": 0.82,
                },
                target_count=5,
                max_steps=900,
                total_reward=3.25,
            )
        )

        self.assertEqual(tiles["Score"], "+3.25")
        self.assertEqual(tiles["Beacons"], "4/5")
        self.assertEqual(tiles["Speed"], "-2.5")
        self.assertNotIn("FPS", tiles)

    def test_button_and_status_labels_stay_compact(self) -> None:
        self.assertEqual(format_button_label("Auto", "Planner"), "Auto: Planner")
        self.assertEqual(format_button_label("Step", ""), "Step")
        self.assertEqual(
            format_debug_mode({"sensors": True, "bounds": False, "path": True}),
            "mixed",
        )
        self.assertEqual(format_native_badge("native C++ scorer: fallback"), "python scorer")

    def test_guide_text_names_goal_and_score_rules(self) -> None:
        text = guide_text("planner")

        self.assertIn("green beacons", text)
        self.assertIn("Score rewards", text)
        self.assertIn("planner", text)


if __name__ == "__main__":
    unittest.main()
