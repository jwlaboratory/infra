#!/usr/bin/env python3
"""
Batch noise study runner — runs noise_study.py across a list of assembly files
and prints a summary table with PASS/FAIL verdicts.

Usage (from repo root):

  python3 scripts/run_noise_batch.py \\
    --asm-dir generated_assemblies \\
    --reference examples/abc_ref.cpp \\
    --tests examples/abc_tests.json \\
    --repeats 20 --threshold 0.05 \\
    --runs 30 --warmup-runs 3 \\
    --docker-platform linux/arm64 \\
    --json-out batch_noise_results.json

Exit code is 0 if all binaries PASS, 1 if any FAIL.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any


def _find_tests_for(asm_path: Path, fallback: Path | None, tests_dir: Path | None) -> Path | None:
    """Auto-discover per-problem test file from tests_dir, or fall back to global tests."""
    if tests_dir is None:
        return fallback
    stem = asm_path.stem  # e.g. "abc_ref_O0" or "example2_deepseek"
    # Try progressively shorter prefixes: abc_ref_O0 → abc_ref → abc
    parts = stem.split("_")
    for i in range(len(parts), 0, -1):
        candidate = tests_dir / f"{'_'.join(parts[:i])}_tests.json"
        if candidate.is_file():
            return candidate
    return fallback


def run_noise_study(
    asm_path: Path,
    *,
    reference: Path | None,
    tests: Path | None,
    repeats: int,
    threshold: float,
    runs: int,
    warmup_runs: int,
    docker_image: str,
    docker_platform: str,
    extra_ldflags: str,
    language: str,
) -> dict[str, Any]:
    """Run noise_study.py for one assembly and return the parsed result dict."""
    fwd: list[str] = [str(asm_path)]
    if reference:
        fwd += ["--reference", str(reference)]
    if tests:
        fwd += ["--tests", str(tests)]
    fwd += [
        "--language", language,
        "--use-docker",
        "--docker-image", docker_image,
        "--docker-platform", docker_platform,
        "--runs", str(runs),
        "--warmup-runs", str(warmup_runs),
    ]
    if extra_ldflags:
        fwd += [f"--extra-ldflags={extra_ldflags}"]

    noise_script = Path(__file__).parent / "noise_study.py"
    cmd = [
        sys.executable, str(noise_script),
        "--repeats", str(repeats),
        "--threshold", str(threshold),
        "--quiet",
        "--",
        *fwd,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = proc.stdout.strip()
    if not raw:
        return {
            "verdict": "FAIL",
            "verdict_reason": f"noise_study returned no output (exit {proc.returncode}): {proc.stderr[:500]}",
            "summary": {},
            "runs": [],
            "completed_runs": 0,
        }
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "verdict": "FAIL",
            "verdict_reason": f"noise_study returned invalid JSON: {raw[:300]}",
            "summary": {},
            "runs": [],
            "completed_runs": 0,
        }


def _cv_str(summary: dict, key: str) -> str:
    s = summary.get(key)
    if not s or s.get("n", 0) == 0:
        return "  —   "
    cv = s.get("cv")
    if cv is None:
        return "  N/A "
    return f"{cv:.4f}"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run noise study across multiple assembly files and report PASS/FAIL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--asm-dir",
        type=Path,
        help="Directory containing .s files to test (mutually exclusive with --asm-files).",
    )
    ap.add_argument(
        "--asm-files",
        type=Path,
        nargs="+",
        help="Explicit list of .s files to test.",
    )
    ap.add_argument("--reference", type=Path, default=None, help="Reference C/C++ source.")
    ap.add_argument("--tests", type=Path, default=None, help="JSON test cases file (global fallback).")
    ap.add_argument(
        "--tests-dir",
        type=Path,
        default=None,
        help="Directory containing per-problem test files named {prefix}_tests.json. "
             "E.g. examples/ will find examples/abc_tests.json for abc_ref_O0.s.",
    )
    ap.add_argument("--language", default="cpp", choices=("c", "cpp"))
    ap.add_argument("--repeats", type=int, default=20, help="Repeats per binary (default: 20).")
    ap.add_argument("--threshold", type=float, default=0.05, help="CV threshold (default: 0.05).")
    ap.add_argument("--runs", type=int, default=30, help="Timed iterations per naive-bench call (default: 30).")
    ap.add_argument("--warmup-runs", type=int, default=3, help="Warmup iterations (default: 3).")
    ap.add_argument("--docker-image", default="gcc:13", help="Docker image (default: gcc:13).")
    ap.add_argument("--docker-platform", default="linux/arm64", help="Docker platform (default: linux/arm64).")
    ap.add_argument("--extra-ldflags", default="-lstdc++", help="Extra linker flags (default: -lstdc++).")
    ap.add_argument("--json-out", type=str, default="", help="Path to write full JSON results.")
    args = ap.parse_args()

    # Collect assembly files
    asm_files: list[Path] = []
    if args.asm_files:
        asm_files = list(args.asm_files)
    elif args.asm_dir:
        asm_files = sorted(args.asm_dir.glob("*.s"))
    else:
        ap.error("one of --asm-dir or --asm-files is required")

    if not asm_files:
        print("error: no .s files found", file=sys.stderr)
        return 2

    print(f"\nBatch noise study: {len(asm_files)} binaries, {args.repeats} repeats each, threshold={args.threshold:.1%}", file=sys.stderr)
    print(f"Platform: {args.docker_platform}  Image: {args.docker_image}  Runs/binary: {args.runs}  Warmup: {args.warmup_runs}\n", file=sys.stderr)

    results: list[dict[str, Any]] = []
    pass_count = 0
    fail_count = 0

    for asm in asm_files:
        label = asm.stem
        tests_for_asm = _find_tests_for(asm, args.tests, args.tests_dir)
        print(f"  [{label}] running...", end=" ", flush=True, file=sys.stderr)
        result = run_noise_study(
            asm,
            reference=args.reference,
            tests=tests_for_asm,
            repeats=args.repeats,
            threshold=args.threshold,
            runs=args.runs,
            warmup_runs=args.warmup_runs,
            docker_image=args.docker_image,
            docker_platform=args.docker_platform,
            extra_ldflags=args.extra_ldflags,
            language=args.language,
        )
        verdict = result.get("verdict", "FAIL")
        asm_cv = (result.get("summary") or {}).get("assembly", {}).get("cv")
        cv_display = f"{asm_cv:.4f}" if asm_cv is not None else "N/A"
        print(f"{verdict}  (assembly CV={cv_display})", file=sys.stderr)

        if verdict == "PASS":
            pass_count += 1
        else:
            fail_count += 1

        results.append({
            "label": label,
            "asm": str(asm),
            "verdict": verdict,
            "verdict_reason": result.get("verdict_reason", ""),
            "completed_runs": result.get("completed_runs", 0),
            "summary": result.get("summary", {}),
        })

    # Summary table
    print(f"\n{'='*90}", file=sys.stderr)
    print(f"  BATCH NOISE STUDY SUMMARY", file=sys.stderr)
    print(f"{'='*90}", file=sys.stderr)
    hdr = f"  {'Binary':<32} {'asm CV':>8} {'O0 CV':>8} {'O1 CV':>8} {'O2 CV':>8} {'O3 CV':>8}  {'Verdict'}"
    print(hdr, file=sys.stderr)
    print(f"  {'-'*32} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}  {'-'*7}", file=sys.stderr)
    for r in results:
        s = r.get("summary", {})
        row = (
            f"  {r['label']:<32} "
            f"{_cv_str(s, 'assembly'):>8} "
            f"{_cv_str(s, 'O0'):>8} "
            f"{_cv_str(s, 'O1'):>8} "
            f"{_cv_str(s, 'O2'):>8} "
            f"{_cv_str(s, 'O3'):>8}  "
            f"{r['verdict']}"
        )
        print(row, file=sys.stderr)
    print(f"{'='*90}", file=sys.stderr)
    print(f"  Passed: {pass_count}/{len(results)}  Failed: {fail_count}/{len(results)}", file=sys.stderr)
    print(f"{'='*90}\n", file=sys.stderr)

    output = {
        "threshold": args.threshold,
        "repeats": args.repeats,
        "runs": args.runs,
        "warmup_runs": args.warmup_runs,
        "docker_platform": args.docker_platform,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "binaries": results,
    }
    print(json.dumps(output, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Results written to {args.json_out}", file=sys.stderr)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
