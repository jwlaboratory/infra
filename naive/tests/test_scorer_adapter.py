"""Unit tests for scorer_adapter (no Docker required for reward math)."""

from __future__ import annotations

import math
import os
import unittest
from pathlib import Path

from naive_bench.scorer_adapter import (
    ScoreCandidateConfig,
    compute_reward,
    log_speedup,
    score_candidate,
)


class TestComputeReward(unittest.TestCase):
    def test_partial_correctness(self) -> None:
        r = compute_reward(0.5, 1.0, 1.0, 1.0, 100, 100)
        self.assertAlmostEqual(r, -1000.0 + 250.0 * 0.5)

    def test_full_correctness_speedup(self) -> None:
        # candidate 2x faster than O3 and O0 -> log(2) each
        r = compute_reward(1.0, 0.5, 1.0, 1.0, 100, 400)
        expect = (
            100.0
            + 50.0 * math.log(1.0 / 0.5)
            + 15.0 * math.log(1.0 / 0.5)
            + 5.0 * math.log(400 / 100)
        )
        self.assertAlmostEqual(r, expect)

    def test_log_speedup_guard(self) -> None:
        self.assertEqual(log_speedup(None, 1.0), 0.0)
        self.assertEqual(log_speedup(1.0, None), 0.0)
        self.assertEqual(log_speedup(0.0, 1.0), 0.0)


class TestScoreCandidateEdges(unittest.TestCase):
    def test_no_tests(self) -> None:
        out = score_candidate("nop", "", reference_source=None, cfg=ScoreCandidateConfig(use_docker=False))
        self.assertEqual(out["status"], "no_tests")
        self.assertLess(out["reward"], 0)

    def test_docker_unavailable_returns_negative_reward(self) -> None:
        # On hosts without Docker daemon this should short-circuit.
        out = score_candidate(
            ".text\n.globl main\nmain:\n  ret\n",
            '[{"input":"","output":""}]',
            None,
            cfg=ScoreCandidateConfig(use_docker=True),
        )
        if out["status"] == "docker_unavailable":
            self.assertEqual(out["reward"], -1500.0)
            self.assertIn("message", out)


@unittest.skipUnless(
    os.environ.get("RUN_DOCKER_SCORER_TESTS") == "1",
    "set RUN_DOCKER_SCORER_TESTS=1 with Docker running (linux/arm64 image pulled)",
)
class TestScoreCandidateDockerIntegration(unittest.TestCase):
    """End-to-end ABC example; requires Docker + gcc:13 arm64."""

    def test_abc_example(self) -> None:
        root = Path(__file__).resolve().parents[1]
        asm = (root / "examples" / "abc_user_arm64.s").read_text(encoding="utf-8")
        tests = (root / "examples" / "abc_tests.json").read_text(encoding="utf-8")
        ref = (root / "examples" / "abc_ref.cpp").read_text(encoding="utf-8")
        out = score_candidate(
            asm,
            tests,
            ref,
            cfg=ScoreCandidateConfig(runs=3, use_docker=True),
        )
        self.assertIn(out["status"], ("ok", "correctness_failed", "candidate_compile_failed"))


if __name__ == "__main__":
    unittest.main()
