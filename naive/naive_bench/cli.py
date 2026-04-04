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
        "--exit-zero",
        action="store_true",
        help="Always exit 0; inspect JSON for ok / script_exit_code.",
    )
    return p


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
    )

    try:
        outcome = run_benchmark(cfg)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"naive-bench: {exc}", file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    print(json.dumps(outcome.report, indent=indent))

    finish(outcome)

    if args.exit_zero:
        return 0
    return 0 if outcome.report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
