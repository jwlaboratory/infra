#!/usr/bin/env python3
"""Run score_candidate on the bundled ABC example (requires Docker + gcc:13 arm64)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from naive_bench.scorer_adapter import ScoreCandidateConfig, score_candidate


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    asm = (root / "examples" / "abc_user_arm64.s").read_text(encoding="utf-8")
    tests = (root / "examples" / "abc_tests.json").read_text(encoding="utf-8")
    ref = (root / "examples" / "abc_ref.cpp").read_text(encoding="utf-8")
    cfg = ScoreCandidateConfig(
        runs=int(sys.argv[1]) if len(sys.argv) > 1 else 10,
        use_docker=True,
        docker_image="gcc:13",
        docker_platform="linux/arm64",
    )
    out = score_candidate(asm, tests, ref, cfg=cfg)
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
