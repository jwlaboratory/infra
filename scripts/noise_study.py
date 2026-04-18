#!/usr/bin/env python3
"""
Repeat naive-bench and summarize timing variance (coefficient of variation of medians).

Usage (from repo root, after `pip install -e naive/`):

  python3 scripts/noise_study.py --repeats 10 -- naive/examples/abc_user_arm64.s \\
    --reference naive/examples/abc_ref.cpp \\
    --tests naive/examples/abc_tests.json \\
    --language cpp --use-docker --docker-image gcc:13 \\
    --docker-platform linux/arm64 --extra-ldflags=-lstdc++ --runs 10 --warmup-runs 3

Everything after `--` is forwarded to naive-bench.

PASS/FAIL: a binary PASSES if the assembly CV is below --threshold (default 0.05 = 5%).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


def _median_s(timing: dict[str, Any], *path: str) -> float | None:
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
    if len(values) < 2:
        return None
    m = mean(values)
    if m == 0:
        return None
    return pstdev(values) / m


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Measure naive-bench timing variance across repeats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--repeats", type=int, default=10, help="Number of naive-bench invocations.")
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="CV threshold for PASS verdict on assembly timing (default: 0.05 = 5%%).",
    )
    ap.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Optional path to write full table JSON.",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable summary table; only print JSON.",
    )
    ap.add_argument("naive_bench_args", nargs=argparse.REMAINDER, help="Arguments after --")
    args = ap.parse_args()
    fwd = args.naive_bench_args
    if fwd and fwd[0] == "--":
        fwd = fwd[1:]
    if not fwd:
        print("error: pass naive-bench arguments after --", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    docker_errors: list[str] = []
    for i in range(args.repeats):
        proc = subprocess.run(
            ["naive-bench", *fwd],
            capture_output=True,
            text=True,
        )
        # Detect Docker-level errors (not JSON output at all)
        if proc.returncode != 0 and not proc.stdout.strip().startswith("{"):
            err_snippet = (proc.stderr or proc.stdout or "")[:500].strip()
            docker_errors.append(f"run {i + 1}: non-JSON exit {proc.returncode}: {err_snippet}")
            print(f"run {i + 1}: Docker/subprocess error (exit {proc.returncode})", file=sys.stderr)
            print(err_snippet, file=sys.stderr)
            continue

        raw = proc.stdout.strip()
        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            print(f"run {i + 1}: invalid JSON (exit {proc.returncode})", file=sys.stderr)
            print(proc.stdout[-2000:], file=sys.stderr)
            print(proc.stderr[-2000:], file=sys.stderr)
            return 1

        med = _collect_medians(report)
        med["ok"] = bool(report.get("ok"))
        med["run"] = i + 1
        rows.append(med)

    if not rows:
        print("error: all runs failed — check Docker availability and assembly path", file=sys.stderr)
        return 1

    keys = sorted({k for r in rows for k in r if k not in ("ok", "run")})
    summary: dict[str, dict[str, float | None]] = {}
    for k in keys:
        vals = [float(r[k]) for r in rows if k in r and r[k] is not None and isinstance(r[k], (int, float))]
        if vals:
            summary[k] = {
                "n": len(vals),
                "mean": mean(vals),
                "median": median(vals),
                "cv": _cv(vals),
                "min": min(vals),
                "max": max(vals),
            }
        else:
            summary[k] = {"n": 0, "mean": float("nan"), "median": float("nan"), "cv": None, "min": float("nan"), "max": float("nan")}

    # PASS/FAIL verdict: based on assembly CV vs threshold
    asm_cv = (summary.get("assembly") or {}).get("cv")
    if asm_cv is None:
        verdict = "FAIL"
        verdict_reason = "assembly timing unavailable (correctness failure?)"
    elif asm_cv <= args.threshold:
        verdict = "PASS"
        verdict_reason = f"assembly CV {asm_cv:.4f} <= threshold {args.threshold:.4f}"
    else:
        verdict = "FAIL"
        verdict_reason = f"assembly CV {asm_cv:.4f} > threshold {args.threshold:.4f}"

    result = {
        "threshold": args.threshold,
        "repeats": args.repeats,
        "completed_runs": len(rows),
        "docker_errors": docker_errors,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "runs": rows,
        "summary": summary,
    }

    if not args.quiet:
        # Human-readable summary table
        print(f"\n{'='*70}", file=sys.stderr)
        print(f"  NOISE STUDY RESULTS  ({len(rows)}/{args.repeats} runs completed)", file=sys.stderr)
        print(f"{'='*70}", file=sys.stderr)
        header = f"  {'Metric':<12} {'N':>4} {'Mean ms':>10} {'Median ms':>11} {'CV':>8} {'Min ms':>9} {'Max ms':>9}"
        print(header, file=sys.stderr)
        print(f"  {'-'*12} {'-'*4} {'-'*10} {'-'*11} {'-'*8} {'-'*9} {'-'*9}", file=sys.stderr)
        for k in ["assembly", "O0", "O1", "O2", "O3"]:
            s = summary.get(k)
            if s is None or s.get("n", 0) == 0:
                continue
            cv_str = f"{s['cv']:.4f}" if s["cv"] is not None else "  N/A "
            flag = " <FAIL>" if k == "assembly" and verdict == "FAIL" and s.get("cv") is not None else ""
            print(
                f"  {k:<12} {s['n']:>4} {s['mean']*1000:>10.3f} {s['median']*1000:>11.3f} "
                f"{cv_str:>8} {s['min']*1000:>9.3f} {s['max']*1000:>9.3f}{flag}",
                file=sys.stderr,
            )
        print(f"{'='*70}", file=sys.stderr)
        print(f"  Verdict: {verdict}  —  {verdict_reason}", file=sys.stderr)
        if docker_errors:
            print(f"  Docker errors: {len(docker_errors)}", file=sys.stderr)
        print(f"{'='*70}\n", file=sys.stderr)

    print(json.dumps(result, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
