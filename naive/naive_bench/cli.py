"""Command-line entry for naive-bench."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from naive_bench.bench import BenchConfig, finish, run_benchmark
from naive_bench.parse_tests import TestsParseError, parse_tests_file


def _split_extra_flags(raw: str | None) -> tuple[str, ...]:
    if not raw or not raw.strip():
        return ()
    return tuple(shlex.split(raw, posix=True))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="naive-bench",
        description="Compile assembly (and optional C/C++ baselines), run IO tests, "
        "and time binaries in one bash script (local or single Docker run).",
    )
    p.add_argument(
        "assembly",
        type=Path,
        help="Path to the assembly source file (.s) to copy into the workspace.",
    )
    p.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Optional reference C or C++ file; builds bench_O0..bench_O3 for timing comparison.",
    )
    p.add_argument(
        "--language",
        choices=("c", "cpp"),
        default="cpp",
        help="Language for --reference (default: cpp).",
    )
    p.add_argument(
        "--tests",
        type=Path,
        default=None,
        help="File with Codeforces-style official_tests JSON or Python literal.",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=30,
        help="Timed iterations per binary inside one script (default: 30).",
    )
    # -----------------------------------------------------------------------
    # Warmup: untimed iterations before the timed loop to prime caches.
    # Matches the SuperCoder paper methodology (discard first 3 runs).
    # Reduces coefficient of variation (CV) on short-running programs.
    # Use 0 to disable (e.g., for programs > 100 ms per iteration where
    # cold-cache overhead is negligible relative to total runtime).
    # -----------------------------------------------------------------------
    p.add_argument(
        "--warmup-runs",
        type=int,
        default=3,
        help="Untimed warmup iterations before timing loop (default: 3). "
        "Primes caches to reduce timing variance. Use 0 to disable.",
    )
    p.add_argument(
        "--warmup-runs",
        type=int,
        default=3,
        help="Untimed warmup iterations before the timed loop (default: 3). "
        "Primes instruction/data cache. Set 0 to disable. "
        "Matches SuperCoder methodology (arXiv:2505.11480v3).",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-execution timeout in seconds for tests and each timed iteration (default: 10).",
    )
    p.add_argument(
        "--timing-input",
        type=Path,
        default=None,
        help="File copied to timing.in for the timing loop stdin (default: empty stdin).",
    )
    p.add_argument(
        "--strict-output",
        action="store_true",
        help="Require exact stdout match; default strips trailing newlines like many judges.",
    )
    p.add_argument(
        "--only-compile",
        action="store_true",
        help="Compile only; skip tests and timing.",
    )
    p.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip compile steps; requires --workspace with existing bench_asm (and baselines if used).",
    )
    p.add_argument(
        "--extra-asm-flags",
        default=None,
        help="Extra tokens passed to gcc when assembling (shell-quoted split).",
    )
    p.add_argument(
        "--extra-cflags",
        default=None,
        help="Extra tokens when compiling the reference source.",
    )
    p.add_argument(
        "--extra-ldflags",
        default=None,
        help="Extra tokens appended to assembly and reference link lines.",
    )
    p.add_argument(
        "--std-c",
        default="-std=c17",
        help="Standard flag when --language c (default: -std=c17).",
    )
    p.add_argument(
        "--std-cxx",
        default="-std=c++20",
        help="Standard flag when --language cpp (default: -std=c++20).",
    )
    p.add_argument(
        "--use-docker",
        action="store_true",
        help="Run the generated script inside Docker instead of the host.",
    )
    p.add_argument(
        "--docker-image",
        default="gcc:13",
        help="Image for --use-docker (default: gcc:13).",
    )
    p.add_argument(
        "--docker-platform",
        default="linux/amd64",
        help="Docker --platform (default: linux/amd64).",
    )
    p.add_argument(
        "--docker-timeout",
        type=float,
        default=600.0,
        help="Wall-clock cap for the whole script subprocess (default: 600s).",
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Reuse this directory as the workspace (not deleted afterward). "
        "Without --skip-compile it is cleared before each run.",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON to stdout.",
    )
    p.add_argument(
        "--timing-summary",
        action="store_true",
        help="Attach compact timing sums/means/medians under timing_summary in JSON output.",
    )
    p.add_argument(
        "--timing-chart",
        action="store_true",
        help="Add timing_chart_lines to JSON and print a readable table + bar chart on stderr.",
    )
    p.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0; inspect JSON for ok / script_exit_code.",
    )
    return p


def _collect_timing_rows(report: dict) -> list[tuple[str, dict]]:
    timing = report.get("timing", {})
    if not timing.get("enabled"):
        return []

    rows: list[tuple[str, dict]] = []
    assembly = timing.get("assembly")
    if isinstance(assembly, dict) and assembly.get("count", 0):
        rows.append(("assembly", assembly))

    baselines = timing.get("baselines", {})
    for label in ("O0", "O1", "O2", "O3"):
        entry = baselines.get(label)
        if isinstance(entry, dict) and entry.get("count", 0):
            rows.append((label, entry))
    return rows


def _build_timing_summary(report: dict) -> dict:
    rows = _collect_timing_rows(report)
    if not rows:
        return {"enabled": False}

    summary_rows = []
    for label, entry in rows:
        samples = entry.get("samples_ns", [])
        total_ns = int(sum(samples)) if isinstance(samples, list) else None
        summary_rows.append(
            {
                "label": label,
                "count": entry.get("count"),
                "total_ns": total_ns,
                "mean_ns": entry.get("mean_ns"),
                "median_ns": entry.get("median_ns"),
                "mean_s": entry.get("mean_s"),
                "median_s": entry.get("median_s"),
            }
        )

    best_by_mean = min(
        summary_rows,
        key=lambda x: float(x["mean_ns"]) if x.get("mean_ns") is not None else float("inf"),
    )
    return {
        "enabled": True,
        "rows": summary_rows,
        "best_mean_label": best_by_mean["label"],
    }


def _build_timing_chart_lines(report: dict, *, bar_width: int = 44) -> list[str]:
    """Readable multi-line chart: fixed columns + bar scaled to slowest mean."""
    rows = _collect_timing_rows(report)
    if not rows:
        return [
            "",
            "(timing chart: timing disabled or no samples)",
            "",
        ]

    table: list[tuple[str, float, float]] = []
    for label, entry in rows:
        mean_ns = float(entry.get("mean_ns", 0.0))
        median_ns = float(entry.get("median_ns", 0.0))
        table.append((label, mean_ns, median_ns))

    min_mean = min(t[1] for t in table)
    max_mean = max(t[1] for t in table)
    min_mean = max(min_mean, 1e-9)
    max_mean = max(max_mean, min_mean)

    lines: list[str] = [
        "",
        "=" * 78,
        "  TIMING CHART",
        "  Mean / median = wall time for one full timing iteration (see timing.runs_requested).",
        "  vs fastest = mean / smallest mean in this run. Bar length is proportional to mean (slowest = full width).",
        "=" * 78,
        "",
        f"  {'Label':<12} {'Mean ms':>10} {'Median ms':>11} {'vs fastest':>12}   Bar",
        f"  {'-' * 12} {'-' * 10} {'-' * 11} {'-' * 12}   {'-' * bar_width}",
    ]

    for label, mean_ns, median_ns in table:
        mean_ms = mean_ns / 1_000_000.0
        median_ms = median_ns / 1_000_000.0
        vs = mean_ns / min_mean
        frac = mean_ns / max_mean
        filled = max(1, min(bar_width, int(round(frac * bar_width))))
        bar = "#" * filled + "." * (bar_width - filled)
        lines.append(
            f"  {label:<12} {mean_ms:10.3f} {median_ms:11.3f} {vs:11.3f}x   {bar}"
        )

    lines.extend(
        [
            "",
            "=" * 78,
            "",
        ]
    )
    return lines


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    tests: tuple[dict[str, str], ...] = ()
    if args.tests is not None:
        try:
            tests = tuple(parse_tests_file(args.tests))
        except TestsParseError as exc:
            print(f"naive-bench: invalid tests file: {exc}", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"naive-bench: cannot read tests: {exc}", file=sys.stderr)
            return 2

    exec_timeout = max(float(args.timeout), 0.001)

    cfg = BenchConfig(
        assembly_path=args.assembly,
        reference_path=args.reference,
        language=args.language,
        tests=tests,
        runs=max(1, int(args.runs)),
        warmup_runs=max(0, int(args.warmup_runs)),
        only_compile=bool(args.only_compile),
        skip_compile=bool(args.skip_compile),
        use_docker=bool(args.use_docker),
        docker_image=args.docker_image,
        docker_platform=args.docker_platform,
        docker_timeout_s=float(args.docker_timeout),
        exec_timeout_s=exec_timeout,
        extra_asm=_split_extra_flags(args.extra_asm_flags),
        extra_c=_split_extra_flags(args.extra_cflags),
        extra_ld=_split_extra_flags(args.extra_ldflags),
        std_c_flag=args.std_c,
        std_cxx_flag=args.std_cxx,
        strict_output_compare=bool(args.strict_output),
        timing_input_path=args.timing_input,
        keep_workspace=args.workspace,
        warmup_runs=max(0, int(args.warmup_runs)),
    )

    try:
        outcome = run_benchmark(cfg)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"naive-bench: {exc}", file=sys.stderr)
        return 2

    if args.timing_summary:
        outcome.report["timing_summary"] = _build_timing_summary(outcome.report)
    chart_lines: list[str] | None = None
    if args.timing_chart:
        chart_lines = _build_timing_chart_lines(outcome.report)
        outcome.report["timing_chart_lines"] = chart_lines

    indent = 2 if args.pretty else None
    print(json.dumps(outcome.report, indent=indent))

    if chart_lines is not None:
        print("\n".join(chart_lines), file=sys.stderr)

    finish(outcome)

    if args.exit_zero:
        return 0
    return 0 if outcome.report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
