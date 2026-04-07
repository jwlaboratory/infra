#!/usr/bin/env python3
"""
Measure Docker container overhead vs host-native execution.

Runs naive-bench on the same assembly file both locally (no Docker) and inside
Docker, then compares the timing to quantify the container overhead ratio.

This answers Team 1's deliverable: "Benchmark Docker overhead (host vs.
container timing delta)."

The overhead ratio tells us whether Docker isolation is worth the cost:
  - 1.0–1.15×: negligible overhead — Docker is the right default for
    reproducibility (standardized Linux ARM64 toolchain across all devs).
  - 1.15–2.0×: moderate overhead — acceptable for most programs, but
    short-running programs (< 1 ms) may see inflated CV.
  - > 2.0×: significant overhead — likely indicates QEMU emulation
    (wrong --docker-platform) or Docker Desktop performance issues.

IMPORTANT: The local mode uses ``date +%s%N`` which only works on Linux.
On macOS, ``date +%s%N`` gives seconds-only resolution (BSD date), making
local timing useless.  This script is designed for Linux hosts or for
comparing two Docker modes (e.g., native ARM64 vs QEMU-emulated AMD64).

Usage (from repo root):

  # Compare local vs Docker on a Linux host:
  python3 scripts/docker_overhead_study.py examples/abc_user_arm64.s \\
    --repeats 5 \\
    -- --reference examples/abc_ref.cpp \\
       --tests examples/abc_tests.json \\
       --language cpp --docker-image gcc:13 \\
       --docker-platform linux/arm64 --extra-ldflags=-lstdc++ --runs 30

  # Compare two Docker platforms (e.g., native ARM64 vs QEMU AMD64):
  python3 scripts/docker_overhead_study.py examples/abc_user_arm64.s \\
    --mode platform-compare \\
    --platform-a linux/arm64 --platform-b linux/amd64 \\
    --repeats 5 \\
    -- --reference examples/abc_ref.cpp \\
       --tests examples/abc_tests.json \\
       --language cpp --docker-image gcc:13 --extra-ldflags=-lstdc++ --runs 30
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from statistics import mean, median, pstdev
from typing import Any


def _cv(values: list[float]) -> float | None:
    """Coefficient of variation = stdev / mean.  None if < 2 values."""
    if len(values) < 2:
        return None
    m = mean(values)
    if m == 0:
        return None
    return pstdev(values) / m


def _run_bench(
    bench_args: list[str],
    *,
    repeats: int,
    label: str,
) -> list[float]:
    """Run naive-bench ``repeats`` times and collect assembly median_s values.

    Returns a list of median_s floats (one per invocation).
    """
    medians: list[float] = []
    for i in range(repeats):
        print(
            f"  [{i + 1}/{repeats}] {label}...",
            file=sys.stderr,
            end="",
            flush=True,
        )
        try:
            proc = subprocess.run(
                ["naive-bench", *bench_args],
                capture_output=True,
                text=True,
                timeout=1200,
            )
        except subprocess.TimeoutExpired:
            print(" TIMEOUT", file=sys.stderr)
            continue
        except FileNotFoundError:
            print("\nerror: naive-bench not found. Install with: pip install -e naive/", file=sys.stderr)
            sys.exit(2)

        if proc.returncode != 0 and not proc.stdout.strip():
            print(f" FAILED (exit {proc.returncode})", file=sys.stderr)
            continue

        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print(" invalid JSON", file=sys.stderr)
            continue

        timing = report.get("timing", {})
        asm = timing.get("assembly", {})
        med = asm.get("median_s")
        if med is not None:
            medians.append(float(med))
            print(f" {float(med)*1000:.3f} ms", file=sys.stderr)
        else:
            print(" no timing", file=sys.stderr)

    return medians


def _print_comparison(
    label_a: str,
    medians_a: list[float],
    label_b: str,
    medians_b: list[float],
    threshold: float,
) -> bool:
    """Print a comparison table and return True if both CVs pass."""
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  DOCKER OVERHEAD STUDY", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    all_pass = True

    for label, medians in [(label_a, medians_a), (label_b, medians_b)]:
        if not medians:
            print(f"  {label:<20} NO DATA", file=sys.stderr)
            all_pass = False
            continue
        med = median(medians)
        avg = mean(medians)
        cv = _cv(medians)
        cv_str = f"{cv:.4f}" if cv is not None else "N/A"
        cv_pass = cv is not None and cv < threshold
        verdict = "PASS" if cv_pass else "FAIL"
        if not cv_pass:
            all_pass = False
        print(
            f"  {label:<20} median={med*1000:8.3f} ms  "
            f"mean={avg*1000:8.3f} ms  CV={cv_str}  {verdict}",
            file=sys.stderr,
        )

    # Overhead ratio.
    if medians_a and medians_b:
        ratio = median(medians_b) / median(medians_a) if median(medians_a) > 0 else float("inf")
        print(file=sys.stderr)
        print(f"  Overhead ratio ({label_b} / {label_a}): {ratio:.3f}x", file=sys.stderr)
        if ratio < 1.15:
            print(f"  → Negligible overhead — Docker isolation recommended.", file=sys.stderr)
        elif ratio < 2.0:
            print(f"  → Moderate overhead — acceptable for most programs.", file=sys.stderr)
        else:
            print(
                f"  → Significant overhead — check --docker-platform for QEMU emulation.",
                file=sys.stderr,
            )

    print(f"\n{'='*60}\n", file=sys.stderr)

    # Also emit JSON to stdout for machine consumption.
    output: dict[str, Any] = {}
    for label, medians in [(label_a, medians_a), (label_b, medians_b)]:
        output[label] = {
            "medians_s": medians,
            "median_s": median(medians) if medians else None,
            "mean_s": mean(medians) if medians else None,
            "cv": _cv(medians),
            "n": len(medians),
        }
    if medians_a and medians_b:
        output["overhead_ratio"] = median(medians_b) / median(medians_a) if median(medians_a) > 0 else None
    print(json.dumps(output, indent=2))

    return all_pass


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Measure Docker overhead by comparing local vs Docker execution, "
            "or two different Docker platforms."
        ),
    )
    ap.add_argument(
        "assembly",
        type=str,
        help="Path to assembly file.",
    )
    ap.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Number of naive-bench invocations per mode (default: 5).",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="CV threshold for PASS/FAIL (default: 0.05 = 5%%).",
    )
    # -----------------------------------------------------------------------
    # Mode selection:
    #   "host-vs-docker" (default): run locally vs Docker.
    #   "platform-compare": run Docker with two different --docker-platform
    #     values to measure the impact of QEMU emulation.
    # -----------------------------------------------------------------------
    ap.add_argument(
        "--mode",
        choices=("host-vs-docker", "platform-compare"),
        default="host-vs-docker",
        help="Comparison mode (default: host-vs-docker).",
    )
    ap.add_argument(
        "--platform-a",
        default="linux/arm64",
        help="First Docker platform for platform-compare mode (default: linux/arm64).",
    )
    ap.add_argument(
        "--platform-b",
        default="linux/amd64",
        help="Second Docker platform for platform-compare mode (default: linux/amd64).",
    )
    ap.add_argument(
        "bench_args",
        nargs=argparse.REMAINDER,
        help="Arguments after -- forwarded to naive-bench.",
    )
    args = ap.parse_args()

    fwd = args.bench_args
    if fwd and fwd[0] == "--":
        fwd = fwd[1:]

    # We always prepend the assembly file to the forwarded args.
    base_args = [args.assembly, *fwd]

    if args.mode == "host-vs-docker":
        # -----------------------------------------------------------------
        # Mode 1: Host (local, no Docker) vs Docker.
        #
        # Local args: remove --use-docker if present, ensure it's absent.
        # Docker args: add --use-docker if not present.
        # -----------------------------------------------------------------
        local_args = [a for a in base_args if a != "--use-docker"]
        docker_args = base_args if "--use-docker" in base_args else ["--use-docker", *base_args]

        print("\n  Phase 1: Local (no Docker) execution\n", file=sys.stderr)
        local_medians = _run_bench(local_args, repeats=args.repeats, label="local")

        print("\n  Phase 2: Docker execution\n", file=sys.stderr)
        docker_medians = _run_bench(docker_args, repeats=args.repeats, label="docker")

        ok = _print_comparison("local", local_medians, "docker", docker_medians, args.threshold)

    elif args.mode == "platform-compare":
        # -----------------------------------------------------------------
        # Mode 2: Compare two Docker platforms.
        # Useful for measuring QEMU emulation overhead:
        #   linux/arm64 (native on Apple Silicon) vs linux/amd64 (QEMU).
        # -----------------------------------------------------------------
        # Ensure --use-docker is in the args.
        if "--use-docker" not in base_args:
            base_args = ["--use-docker", *base_args]

        # Replace or add --docker-platform for each run.
        def _set_platform(args_list: list[str], platform: str) -> list[str]:
            result = []
            skip_next = False
            for a in args_list:
                if skip_next:
                    skip_next = False
                    continue
                if a == "--docker-platform":
                    skip_next = True
                    continue
                result.append(a)
            result.extend(["--docker-platform", platform])
            return result

        args_a = _set_platform(base_args, args.platform_a)
        args_b = _set_platform(base_args, args.platform_b)

        print(f"\n  Phase 1: Docker with {args.platform_a}\n", file=sys.stderr)
        medians_a = _run_bench(args_a, repeats=args.repeats, label=args.platform_a)

        print(f"\n  Phase 2: Docker with {args.platform_b}\n", file=sys.stderr)
        medians_b = _run_bench(args_b, repeats=args.repeats, label=args.platform_b)

        ok = _print_comparison(
            args.platform_a, medians_a,
            args.platform_b, medians_b,
            args.threshold,
        )

    else:
        print(f"error: unknown mode {args.mode}", file=sys.stderr)
        return 2

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
