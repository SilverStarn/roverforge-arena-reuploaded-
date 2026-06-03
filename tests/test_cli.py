from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from game.main import main


class CliTests(unittest.TestCase):
    def test_eval_writes_jsonl_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.jsonl"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "eval",
                        "--episodes",
                        "2",
                        "--seed",
                        "7",
                        "--jsonl",
                        str(output_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertIn("terminal_reason", rows[0])
            self.assertIn("timeout_rate", stdout.getvalue())

    def test_benchmark_rejects_zero_steps(self) -> None:
        with self.assertRaises(SystemExit) as error:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                main(["benchmark", "--steps", "0"])

        self.assertNotEqual(error.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
