"""Drop-in style scoring aligned with gen-optimize-assembly `6-scorer.py`."""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from naive_bench import constants as C
from naive_bench.bench import BenchConfig, BenchOutcome, finish, run_benchmark
from naive_bench.parse_tests import parse_tests_payload
from naive_bench.runner import docker_daemon_reachable

DEFAULT_COMPILE_FAILURE_REWARD = -1500.0
DEFAULT_CORRECTNESS_FAILURE_REWARD = -1000.0

Language = Literal["c", "cpp"]


def log_speedup(baseline: float | None, candidate: float | None) -> float:
    if baseline is None or candidate is None or baseline <= 0 or candidate <= 0:
        return 0.0
    return math.log(baseline / candidate)


def compute_reward(
    correctness_fraction: float,
    candidate_runtime: float | None,
    o0_runtime: float | None,
    o3_runtime: float | None,
    candidate_size: int | None,
    o3_size: int | None,
) -> float:
    """Match `6-scorer.py` `compute_reward` (natural log, same coefficients)."""
    if correctness_fraction < 1.0:
        return DEFAULT_CORRECTNESS_FAILURE_REWARD + (250.0 * correctness_fraction)

    reward = 100.0
    reward += 50.0 * log_speedup(o3_runtime, candidate_runtime)
    reward += 15.0 * log_speedup(o0_runtime, candidate_runtime)
    if candidate_size and o3_size and candidate_size > 0 and o3_size > 0:
        reward += 5.0 * math.log(o3_size / candidate_size)
    return reward


def _correctness_fraction_from_report(correctness: dict[str, Any]) -> float:
    if not correctness.get("enabled"):
        return 0.0
    cases = correctness.get("cases") or []
    if not cases:
        return 0.0
    passed = sum(1 for c in cases if c.get("passed"))
    return passed / len(cases)


def _median_seconds(timing: dict[str, Any], key: str) -> float | None:
    block = timing.get(key)
    if not isinstance(block, dict):
        return None
    med = block.get("median_s")
    if med is None:
        return None
    try:
        f = float(med)
    except (TypeError, ValueError):
        return None
    if f <= 0:
        return None
    return f


def _median_from_baseline(baselines: Any, label: str) -> float | None:
    if not isinstance(baselines, dict):
        return None
    return _median_seconds(baselines, label)


@dataclass(frozen=True)
class ScoreCandidateConfig:
    language: Language = "cpp"
    runs: int = 30
    use_docker: bool = True
    docker_image: str = "gcc:13"
    docker_platform: str = "linux/arm64"
    docker_timeout_s: float = 600.0
    exec_timeout_s: float = 10.0
    extra_ld: tuple[str, ...] = ("-lstdc++",)
    std_c_flag: str = "-std=c17"
    std_cxx_flag: str = "-std=c++20"
    strict_output_compare: bool = False


def score_candidate(
    candidate_assembly: str,
    official_tests: str,
    reference_source: str | None = None,
    *,
    cfg: ScoreCandidateConfig | None = None,
) -> dict[str, Any]:
    """
    Run compile → correctness → benchmark and return reward-shaped dict.

    Without ``reference_source``, baseline timings are omitted (O0/O3 log terms
    contribute 0); the O3 size term is also skipped if ``bench_O3`` is missing.
    """
    cfg = cfg or ScoreCandidateConfig()

    if cfg.use_docker:
        ok, msg = docker_daemon_reachable()
        if not ok:
            return {
                "reward": DEFAULT_COMPILE_FAILURE_REWARD,
                "correct": False,
                "status": "docker_unavailable",
                "message": msg,
                "correctness": None,
                "timing": None,
                "compile": None,
            }

    tests_list = parse_tests_payload(official_tests)
    if not tests_list:
        return {
            "reward": DEFAULT_CORRECTNESS_FAILURE_REWARD,
            "correct": False,
            "status": "no_tests",
            "message": "No official tests were available for scoring.",
            "correctness": None,
            "timing": None,
            "compile": None,
        }

    tests = tuple(tests_list)
    outcome: BenchOutcome | None = None

    with tempfile.TemporaryDirectory(prefix="score-cand-") as tmp_str:
        tmp = Path(tmp_str)
        asm_path = tmp / "candidate.s"
        asm_path.write_text(candidate_assembly, encoding="utf-8")

        ref_arg: Path | None = None
        if reference_source is not None:
            suffix = ".cpp" if cfg.language == "cpp" else ".c"
            ref_arg = tmp / f"ref{suffix}"
            ref_arg.write_text(reference_source, encoding="utf-8")

        bench_cfg = BenchConfig(
            assembly_path=asm_path,
            reference_path=ref_arg,
            language=cfg.language,
            tests=tests,
            runs=cfg.runs,
            only_compile=False,
            skip_compile=False,
            use_docker=cfg.use_docker,
            docker_image=cfg.docker_image,
            docker_platform=cfg.docker_platform,
            docker_timeout_s=cfg.docker_timeout_s,
            exec_timeout_s=cfg.exec_timeout_s,
            extra_ld=cfg.extra_ld,
            std_c_flag=cfg.std_c_flag,
            std_cxx_flag=cfg.std_cxx_flag,
            strict_output_compare=cfg.strict_output_compare,
        )
        outcome = run_benchmark(bench_cfg)

    assert outcome is not None
    try:
        report = outcome.report
        workspace = outcome.workspace

        compile_report = report.get("compile") or {}
        assembly_ok = bool((compile_report.get("assembly") or {}).get("ok"))
        if not assembly_ok:
            return {
                "reward": DEFAULT_COMPILE_FAILURE_REWARD,
                "correct": False,
                "status": "candidate_compile_failed",
                "correctness": report.get("correctness"),
                "timing": report.get("timing"),
                "compile": compile_report,
            }

        correctness = report.get("correctness") or {}
        frac = _correctness_fraction_from_report(correctness)
        all_passed = bool(correctness.get("all_passed"))

        timing = report.get("timing") or {}
        candidate_runtime = _median_seconds(timing, "assembly")
        baselines = timing.get("baselines") or {}
        o0_runtime = _median_from_baseline(baselines, "O0")
        o3_runtime = _median_from_baseline(baselines, "O3")

        cand_bin = workspace / C.ASM_BINARY
        o3_bin = workspace / "bench_O3"
        candidate_size = os.path.getsize(cand_bin) if cand_bin.is_file() else None
        o3_size = os.path.getsize(o3_bin) if o3_bin.is_file() else None

        reward = compute_reward(
            correctness_fraction=frac,
            candidate_runtime=candidate_runtime,
            o0_runtime=o0_runtime,
            o3_runtime=o3_runtime,
            candidate_size=candidate_size,
            o3_size=o3_size,
        )

        status = "ok" if all_passed else "correctness_failed"
        return {
            "reward": reward,
            "correct": all_passed,
            "status": status,
            "correctness": correctness,
            "timing": timing,
            "compile": compile_report,
        }
    finally:
        if outcome is not None:
            finish(outcome)
