#!/usr/bin/env python3
"""
Repeat naive-bench and summarize timing variance (coefficient of variation of medians).

Usage (from repo root, after `pip install -e naive/`):

  python3 scripts/noise_study.py --repeats 10 -- naive/examples/abc_user_arm64.s \\
    --reference naive/examples/abc_ref.cpp \\
    --tests naive/examples/abc_tests.json \\
    --language cpp --use-docker --docker-image gcc:13 \\
    --docker-platform linux/arm64 --extra-ldflags=-lstdc++ --runs 10

Everything after `--` is forwarded to naive-bench.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, pstdev
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
    ap = argparse.ArgumentParser(description="Measure naive-bench timing variance across repeats.")
    ap.add_argument("--repeats", type=int, default=10, help="Number of naive-bench invocations.")
    ap.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Optional path to write full table JSON.",
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
    for i in range(args.repeats):
        proc = subprocess.run(
            ["naive-bench", *fwd],
            capture_output=True,
            text=True,
        )
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

    keys = sorted({k for r in rows for k in r if k not in ("ok", "run")})
    summary: dict[str, dict[str, float | None]] = {}
    for k in keys:
        vals = [float(r[k]) for r in rows if k in r and r[k] is not None and isinstance(r[k], (int, float))]
        summary[k] = {
            "mean": mean(vals) if vals else float("nan"),
            "cv": _cv(vals),
            "min": min(vals) if vals else float("nan"),
            "max": max(vals) if vals else float("nan"),
        }

    print(json.dumps({"runs": rows, "summary": summary}, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps({"runs": rows, "summary": summary}, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
