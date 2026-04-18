#!/usr/bin/env python3
"""
Measure Docker overhead vs local execution on a simple assembly binary.

Compiles a minimal "hello world" assembly and times it locally and inside Docker
at different platforms, printing overhead ratios. Helps identify QEMU emulation
problems (5–20× overhead vs native 1.05–1.15×).

Usage (from repo root, after `pip install -e naive/`):

  python3 scripts/docker_overhead_study.py \\
    --reference examples/abc_ref.cpp \\
    --tests examples/abc_tests.json \\
    --assembly examples/abc_user_arm64.s \\
    --repeats 5 --runs 10

Requires Docker to be running.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any


REPO_ROOT = Path(__file__).parent.parent


def _run_naive_bench(
    asm: Path,
    reference: Path | None,
    tests: Path | None,
    runs: int,
    warmup_runs: int,
    use_docker: bool,
    docker_platform: str,
    docker_image: str,
    language: str,
    extra_ldflags: str,
) -> dict[str, Any] | None:
    cmd = [
        "naive-bench", str(asm),
        "--runs", str(runs),
        "--warmup-runs", str(warmup_runs),
        "--language", language,
    ]
    if reference:
        cmd += ["--reference", str(reference)]
    if tests:
        cmd += ["--tests", str(tests)]
    if extra_ldflags:
        cmd += [f"--extra-ldflags={extra_ldflags}"]
    if use_docker:
        cmd += [
            "--use-docker",
            "--docker-image", docker_image,
            "--docker-platform", docker_platform,
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(proc.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_median_ms(report: dict[str, Any]) -> float | None:
    timing = report.get("timing") or {}
    if not timing.get("enabled"):
        return None
    asm = timing.get("assembly") or {}
    med_s = asm.get("median_s")
    if med_s is None:
        return None
    return float(med_s) * 1000.0


def _collect_medians(
    asm: Path,
    reference: Path | None,
    tests: Path | None,
    repeats: int,
    runs: int,
    warmup_runs: int,
    use_docker: bool,
    docker_platform: str,
    docker_image: str,
    language: str,
    extra_ldflags: str,
    label: str,
) -> list[float]:
    medians: list[float] = []
    for i in range(repeats):
        print(f"    run {i+1}/{repeats}...", end=" ", flush=True, file=sys.stderr)
        report = _run_naive_bench(
            asm, reference, tests, runs, warmup_runs,
            use_docker, docker_platform, docker_image, language, extra_ldflags,
        )
        if report is None:
            print("FAILED (no JSON)", file=sys.stderr)
            continue
        if not report.get("ok"):
            print(f"FAILED (ok=False)", file=sys.stderr)
            continue
        med = _extract_median_ms(report)
        if med is None:
            print("FAILED (no timing)", file=sys.stderr)
            continue
        medians.append(med)
        print(f"{med:.3f} ms", file=sys.stderr)
    return medians


def _summarize(vals: list[float]) -> dict[str, Any]:
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "mean_ms": mean(vals),
        "median_ms": median(vals),
        "min_ms": min(vals),
        "max_ms": max(vals),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure Docker overhead vs local execution.")
    ap.add_argument("--assembly", type=Path, default=REPO_ROOT / "examples" / "abc_user_arm64.s")
    ap.add_argument("--reference", type=Path, default=REPO_ROOT / "examples" / "abc_ref.cpp")
    ap.add_argument("--tests", type=Path, default=REPO_ROOT / "examples" / "abc_tests.json")
    ap.add_argument("--language", default="cpp", choices=("c", "cpp"))
    ap.add_argument("--extra-ldflags", default="-lstdc++")
    ap.add_argument("--repeats", type=int, default=5, help="Outer repeats per mode (default: 5).")
    ap.add_argument("--runs", type=int, default=10, help="Timed iterations per naive-bench call (default: 10).")
    ap.add_argument("--warmup-runs", type=int, default=3, help="Warmup iterations (default: 3).")
    ap.add_argument("--docker-image", default="gcc:13")
    ap.add_argument("--arm64-platform", default="linux/arm64")
    ap.add_argument("--amd64-platform", default="linux/amd64")
    ap.add_argument("--skip-local", action="store_true", help="Skip local (non-Docker) timing.")
    ap.add_argument("--skip-amd64", action="store_true", help="Skip linux/amd64 Docker timing (QEMU).")
    ap.add_argument("--json-out", type=str, default="")
    args = ap.parse_args()

    asm = args.assembly
    if not asm.is_file():
        print(f"error: assembly not found: {asm}", file=sys.stderr)
        return 2

    modes: list[tuple[str, bool, str]] = []
    if not args.skip_local:
        modes.append(("local (no Docker)", False, ""))
    modes.append(("Docker linux/arm64 (native)", True, args.arm64_platform))
    if not args.skip_amd64:
        modes.append(("Docker linux/amd64 (QEMU on ARM host)", True, args.amd64_platform))

    results: dict[str, Any] = {}
    baseline_median: float | None = None

    for label, use_docker, platform in modes:
        print(f"\n[{label}]", file=sys.stderr)
        medians = _collect_medians(
            asm, args.reference, args.tests,
            args.repeats, args.runs, args.warmup_runs,
            use_docker, platform, args.docker_image, args.language, args.extra_ldflags,
            label,
        )
        summary = _summarize(medians)
        if baseline_median is None and summary.get("n", 0) > 0:
            baseline_median = summary["median_ms"]
        overhead: float | None = None
        if baseline_median and summary.get("n", 0) > 0:
            overhead = summary["median_ms"] / baseline_median
        summary["overhead_vs_baseline"] = overhead
        results[label] = summary

    # Print summary table
    print(f"\n{'='*72}", file=sys.stderr)
    print("  DOCKER OVERHEAD STUDY RESULTS", file=sys.stderr)
    print(f"{'='*72}", file=sys.stderr)
    print(f"  {'Mode':<38} {'Median ms':>10} {'Overhead':>10}  {'N':>3}", file=sys.stderr)
    print(f"  {'-'*38} {'-'*10} {'-'*10}  {'-'*3}", file=sys.stderr)
    for label, summary in results.items():
        if summary.get("n", 0) == 0:
            print(f"  {label:<38} {'N/A':>10} {'N/A':>10}  {0:>3}", file=sys.stderr)
        else:
            ov = summary.get("overhead_vs_baseline")
            ov_str = f"{ov:.2f}×" if ov is not None else "N/A"
            print(
                f"  {label:<38} {summary['median_ms']:>10.3f} {ov_str:>10}  {summary['n']:>3}",
                file=sys.stderr,
            )
    print(f"{'='*72}", file=sys.stderr)
    print(f"\nNote: overhead > 5× suggests QEMU emulation (platform mismatch).", file=sys.stderr)
    print(f"      overhead 1.05–1.15× is acceptable for Docker native runs.\n", file=sys.stderr)

    output = {
        "assembly": str(asm),
        "repeats": args.repeats,
        "runs": args.runs,
        "warmup_runs": args.warmup_runs,
        "modes": results,
    }
    print(json.dumps(output, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(output, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
