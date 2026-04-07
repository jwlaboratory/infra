#!/usr/bin/env python3
"""
Repeat naive-bench (or hyperfine-bench) and summarize timing variance.

Measures the **coefficient of variation (CV)** of medians across repeated
benchmark invocations.  CV < 5% is the target for reliable RL reward signals
(see docs/timing_best_practices.md).

The SuperCoder paper (arXiv:2505.11480v3) discards the first 3 hyperfine runs
and averages the next 10 — effectively a warmup + multi-sample approach.  Our
naive-bench now has built-in warmup (--warmup-runs), so each invocation should
already produce a stable median.  This script measures *between-invocation*
variance: how much does the median_s jitter when you re-run the whole
benchmark from scratch?

Usage (from repo root, after ``pip install -e naive/``):

  python3 scripts/noise_study.py --repeats 10 --threshold 0.05 \\
    -- naive/examples/abc_user_arm64.s \\
    --reference naive/examples/abc_ref.cpp \\
    --tests naive/examples/abc_tests.json \\
    --language cpp --use-docker --docker-image gcc:13 \\
    --docker-platform linux/arm64 --extra-ldflags=-lstdc++ --runs 10

Everything after ``--`` is forwarded to the benchmark tool (naive-bench or
hyperfine-bench, controlled by ``--use-hyperfine``).

Output:
  - **stdout**: JSON with full per-run data, summary, and metadata.
  - **stderr**: human-readable PASS/FAIL table for quick inspection.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _median_s(timing: dict[str, Any], *path: str) -> float | None:
    """Walk a nested dict by *path* keys and return a float, or None."""
    cur: Any = timing
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    if cur is None:
        return None
    try:
        v = float(cur)
    except (TypeError, ValueError):
        return None
    return v


def _collect_medians(report: dict[str, Any]) -> dict[str, float | None]:
    """Extract median_s for assembly + each baseline from a benchmark report."""
    timing = report.get("timing") or {}
    if not timing.get("enabled"):
        return {}
    out: dict[str, float | None] = {
        "assembly": _median_s(timing, "assembly", "median_s"),
    }
    baselines = timing.get("baselines") or {}
    if isinstance(baselines, dict):
        for label in ("O0", "O1", "O2", "O3"):
            blk = baselines.get(label)
            if isinstance(blk, dict):
                out[label] = blk.get("median_s") if blk.get("median_s") is not None else None
            else:
                out[label] = None
    return out


def _cv(values: list[float]) -> float | None:
    """Coefficient of variation = population stdev / mean.

    Returns None if fewer than 2 values (CV is undefined for n < 2).
    A CV of 0.05 means the standard deviation is 5% of the mean — our
    target threshold for timing reliability.
    """
    if len(values) < 2:
        return None
    m = mean(values)
    if m == 0:
        return None
    return pstdev(values) / m


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Measure naive-bench (or hyperfine-bench) timing variance across "
            "repeated invocations.  Reports coefficient of variation (CV) of "
            "medians and a PASS/FAIL verdict against --threshold."
        ),
    )
    ap.add_argument(
        "--repeats",
        type=int,
        default=10,
        help="Number of benchmark invocations (default: 10).",
    )
    # -----------------------------------------------------------------------
    # CV threshold: the target coefficient of variation.
    # CV < 5%% means the timing is stable enough for RL reward signals.
    # Team 1's key deliverable is demonstrating this on 20 binaries.
    # -----------------------------------------------------------------------
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="CV threshold for PASS/FAIL verdict (default: 0.05 = 5%%).  "
        "A binary passes if ALL of its labels (assembly, O0..O3) have "
        "CV below this threshold.",
    )
    # -----------------------------------------------------------------------
    # Tool selection: naive-bench (default) vs hyperfine-bench.
    # naive-bench uses a bash timing loop with date +%%s%%N; hyperfine-bench
    # delegates to the hyperfine CLI for warmup + statistical benchmarking.
    # SuperCoder uses hyperfine; we support both for comparison.
    # -----------------------------------------------------------------------
    ap.add_argument(
        "--use-hyperfine",
        action="store_true",
        help="Invoke hyperfine-bench instead of naive-bench.",
    )
    ap.add_argument(
        "--label",
        type=str,
        default=None,
        help="Human-readable name for this binary (used in output).",
    )
    ap.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Optional path to write full JSON output.",
    )
    ap.add_argument(
        "bench_args",
        nargs=argparse.REMAINDER,
        help="Arguments after -- forwarded to the benchmark tool.",
    )
    args = ap.parse_args()

    # Strip the leading "--" separator if present.
    fwd = args.bench_args
    if fwd and fwd[0] == "--":
        fwd = fwd[1:]
    if not fwd:
        print("error: pass benchmark arguments after --", file=sys.stderr)
        return 2

    # -----------------------------------------------------------------------
    # Select the benchmark command.
    # Both naive-bench and hyperfine-bench produce the same JSON report
    # shape with timing.assembly.median_s and timing.baselines.{O0..O3}.
    # -----------------------------------------------------------------------
    bench_cmd = "hyperfine-bench" if args.use_hyperfine else "naive-bench"
    tool_name = bench_cmd

    # -----------------------------------------------------------------------
    # Run the benchmark --repeats times, collecting the median_s from each.
    # Each invocation is a full benchmark cycle (compile → correctness →
    # timing) inside a fresh Docker container, so between-invocation
    # variance captures real-world jitter (OS scheduling, cache state,
    # Docker overhead, etc.).
    # -----------------------------------------------------------------------
    rows: list[dict[str, Any]] = []
    for i in range(args.repeats):
        print(
            f"  [{i + 1}/{args.repeats}] Running {bench_cmd}...",
            file=sys.stderr,
            end="",
            flush=True,
        )
        try:
            proc = subprocess.run(
                [bench_cmd, *fwd],
                capture_output=True,
                text=True,
                timeout=1200,  # generous 20-minute cap per invocation
            )
        except subprocess.TimeoutExpired:
            print(f" TIMEOUT (>1200s)", file=sys.stderr)
            return 1
        except FileNotFoundError:
            print(
                f"\nerror: '{bench_cmd}' not found.  "
                f"Install with: pip install -e naive/ (or hyperfine/)",
                file=sys.stderr,
            )
            return 2

        raw = proc.stdout.strip()
        # -----------------------------------------------------------------
        # Robust error handling for Docker failures:
        # If the benchmark exits non-zero with no stdout, it usually means
        # Docker daemon is unreachable or the image pull failed.
        # -----------------------------------------------------------------
        if proc.returncode != 0 and not raw:
            stderr_tail = (proc.stderr or "")[-500:]
            print(f" FAILED (exit {proc.returncode})", file=sys.stderr)
            print(
                f"  Hint: if Docker is unreachable, try: docker info\n"
                f"  stderr (last 500 chars): {stderr_tail}",
                file=sys.stderr,
            )
            return 1

        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            print(f" invalid JSON (exit {proc.returncode})", file=sys.stderr)
            print(proc.stdout[-2000:], file=sys.stderr)
            print(proc.stderr[-2000:], file=sys.stderr)
            return 1

        med = _collect_medians(report)
        med["ok"] = bool(report.get("ok"))
        med["run"] = i + 1
        rows.append(med)
        print(" done", file=sys.stderr)

    # -----------------------------------------------------------------------
    # Compute summary statistics for each label (assembly, O0, O1, O2, O3).
    # CV = population_stdev / mean, computed over the medians from each run.
    # -----------------------------------------------------------------------
    keys = sorted({k for r in rows for k in r if k not in ("ok", "run")})
    summary: dict[str, dict[str, float | None]] = {}
    for k in keys:
        vals = [
            float(r[k])
            for r in rows
            if k in r and r[k] is not None and isinstance(r[k], (int, float))
        ]
        cv_val = _cv(vals)
        summary[k] = {
            "mean": mean(vals) if vals else float("nan"),
            "median": median(vals) if vals else float("nan"),
            "cv": cv_val,
            "min": min(vals) if vals else float("nan"),
            "max": max(vals) if vals else float("nan"),
            "n": len(vals),
        }

    # -----------------------------------------------------------------------
    # JSON output (stdout) — structured data for downstream consumers.
    # Includes metadata (tool, threshold, label) for traceability.
    # -----------------------------------------------------------------------
    output = {
        "tool": tool_name,
        "threshold": args.threshold,
        "label": args.label,
        "repeats": args.repeats,
        "runs": rows,
        "summary": summary,
    }
    print(json.dumps(output, indent=2))

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(output, indent=2), encoding="utf-8"
        )

    # -----------------------------------------------------------------------
    # Human-readable PASS/FAIL table (stderr) — for quick inspection.
    # A label passes if its CV is below --threshold.  The overall verdict
    # is PASS only if ALL labels pass.
    # -----------------------------------------------------------------------
    any_fail = False
    print(file=sys.stderr)
    print("== Noise Study Results ==", file=sys.stderr)
    if args.label:
        print(f"  Binary: {args.label}", file=sys.stderr)
    print(
        f"  Tool: {tool_name}  |  Repeats: {args.repeats}  |  Threshold: {args.threshold:.2%}",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    header = f"  {'Label':<12} {'Mean ms':>10} {'Median ms':>11} {'CV':>8}  Verdict"
    print(header, file=sys.stderr)
    print("  " + "-" * 65, file=sys.stderr)

    for k in keys:
        s = summary[k]
        cv = s.get("cv")
        mean_ms = (s.get("mean") or 0) * 1000
        median_ms = (s.get("median") or 0) * 1000
        if cv is None:
            verdict = "N/A (need >=2 runs)"
        elif cv < args.threshold:
            verdict = f"PASS  (CV={cv:.4f} < {args.threshold})"
        else:
            verdict = f"FAIL  (CV={cv:.4f} >= {args.threshold})"
            any_fail = True
        cv_str = f"{cv:.4f}" if cv is not None else "   N/A"
        print(
            f"  {k:<12} {mean_ms:10.3f} {median_ms:11.3f} {cv_str:>8}  {verdict}",
            file=sys.stderr,
        )

    print(file=sys.stderr)
    overall = "FAIL" if any_fail else "PASS"
    print(f"  Overall: {overall}", file=sys.stderr)
    print(file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
