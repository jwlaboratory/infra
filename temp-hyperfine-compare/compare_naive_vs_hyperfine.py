#!/usr/bin/env python3
"""
Compare naive-bench wall-clock timing with hyperfine on the same *logical* workload.

naive-bench (see infra/README.md) measures nanoseconds via `date +%s%N` around a bash
loop inside one Docker container — one `docker run` for the whole benchmark phase.

If hyperfine is installed, this script can benchmark `docker run ... ./run_workload.sh`
per iteration. Those means include container startup each time, so they will not match
naive-bench's inner means; the script prints both and explains the difference.

hyperfine: https://github.com/sharkdp/hyperfine

Usage (from repo root or this directory):
  python3 compare_naive_vs_hyperfine.py
  python3 compare_naive_vs_hyperfine.py --runs 10 --warmup 0
  python3 compare_naive_vs_hyperfine.py --no-docker   # host gcc only (Linux asm friendly)
"""

from __future__ import annotations

import argparse
import json
import math
import shlex
import shutil
import statistics
import subprocess
import sys
from pathlib import Path


def _repo_infra_naive() -> Path:
    return Path(__file__).resolve().parent.parent / "naive"


def _naive_bench_exe(naive_root: Path) -> list[str]:
    venv_py = naive_root / ".venv" / "bin" / "python"
    if venv_py.is_file():
        return [str(venv_py), "-m", "naive_bench.cli"]
    return ["naive-bench"]


def _write_run_workload_script(workspace: Path, *, exec_timeout_s: float, n_tests: int) -> Path:
    """Mirror naive_bench.script_builder.run_one_binary body for assembly (tests/*.in)."""
    body = f"""#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"
EXEC_TIMEOUT={exec_timeout_s}
N_TESTS={n_tests}
"""
    if n_tests > 0:
        body += """
for i in $(seq 0 $((N_TESTS - 1))); do
  timeout "${EXEC_TIMEOUT}s" ./bench_asm < "tests/${i}.in" > /dev/null 2>&1 || exit 1
done
"""
    else:
        body += """
timeout "${EXEC_TIMEOUT}s" ./bench_asm < timing.in > /dev/null 2>&1 || exit 1
"""
    path = workspace / "run_workload.sh"
    path.write_text(body.lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    return path


def _count_tests(tests_file: Path) -> int:
    data = json.loads(tests_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"expected JSON array in {tests_file}")
    return len(data)


def _run_naive_bench(
    *,
    naive_root: Path,
    workspace: Path,
    assembly: Path,
    reference: Path,
    tests: Path,
    language: str,
    use_docker: bool,
    docker_image: str,
    docker_platform: str,
    extra_ldflags: str,
    runs: int,
    timeout_s: float,
    report_path: Path,
) -> dict:
    exe = _naive_bench_exe(naive_root)
    cmd = [
        *exe,
        str(assembly),
        "--reference",
        str(reference),
        "--tests",
        str(tests),
        "--language",
        language,
        "--runs",
        str(runs),
        "--timeout",
        str(timeout_s),
        "--timing-summary",
        "--workspace",
        str(workspace),
        f"--extra-ldflags={extra_ldflags}",
    ]
    if use_docker:
        cmd.extend(
            [
                "--use-docker",
                "--docker-image",
                docker_image,
                "--docker-platform",
                docker_platform,
            ]
        )

    proc = subprocess.run(
        cmd,
        cwd=naive_root,
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        report_path.write_text(proc.stdout, encoding="utf-8")
    try:
        report: dict = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit("naive-bench did not emit valid JSON") from None

    if proc.returncode != 0 and not proc.stdout.strip():
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"naive-bench failed (exit {proc.returncode}), no JSON on stdout")
    return report


def _pop_stdev_seconds(seconds: list[float]) -> float:
    if len(seconds) < 2:
        return float("nan")
    return statistics.pstdev(seconds)


def _run_hyperfine_docker_per_iter(
    *,
    workspace: Path,
    docker_image: str,
    docker_platform: str,
    runs: int,
    warmup: int,
    export_path: Path,
) -> dict | None:
    if not shutil.which("hyperfine"):
        return None
    if not shutil.which("docker"):
        return None

    ws = str(workspace.resolve())
    # hyperfine treats each argv after `--` as a separate benchmark; use one shell string.
    bench_cmd = (
        f"docker run --rm --platform {shlex.quote(docker_platform)} "
        f"-v {shlex.quote(ws + ':/work')} -w /work "
        f"{shlex.quote(docker_image)} bash /work/run_workload.sh"
    )

    proc = subprocess.run(
        [
            "hyperfine",
            "--runs",
            str(runs),
            "--warmup",
            str(warmup),
            "--export-json",
            str(export_path),
            "--",
            bench_cmd,
        ],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        raise SystemExit(f"hyperfine failed (exit {proc.returncode})")

    return json.loads(export_path.read_text(encoding="utf-8"))


def main() -> None:
    naive_root = _repo_infra_naive()
    if not naive_root.is_dir():
        raise SystemExit(f"expected naive-bench package at {naive_root}")

    default_examples = naive_root / "examples"
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assembly", type=Path, default=default_examples / "abc_user_arm64.s")
    p.add_argument("--reference", type=Path, default=default_examples / "abc_ref.cpp")
    p.add_argument("--tests", type=Path, default=default_examples / "abc_tests.json")
    p.add_argument("--language", default="cpp")
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--timeout", type=float, default=10.0, help="naive-bench per-exec timeout (s)")
    p.add_argument("--warmup", type=int, default=0, help="hyperfine warmup runs")
    p.add_argument("--docker-image", default="gcc:13")
    p.add_argument("--docker-platform", default="linux/arm64")
    p.add_argument(
        "--no-docker",
        action="store_true",
        help="Run naive-bench on the host (needs a toolchain that accepts the .s file).",
    )
    p.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parent / "_workspace",
    )
    p.add_argument("--extra-ldflags", default="-lstdc++")
    args = p.parse_args()

    workspace: Path = args.workspace
    workspace.parent.mkdir(parents=True, exist_ok=True)

    report_path = Path(__file__).resolve().parent / "naive_report.json"
    hf_path = Path(__file__).resolve().parent / "hyperfine_report.json"

    n_tests = _count_tests(args.tests)

    print("== naive-bench ==")
    print(f"  workspace: {workspace}")
    print(f"  docker:    {not args.no_docker}")
    print(f"  runs:      {args.runs}")
    print()

    report = _run_naive_bench(
        naive_root=naive_root,
        workspace=workspace,
        assembly=args.assembly.resolve(),
        reference=args.reference.resolve(),
        tests=args.tests.resolve(),
        language=args.language,
        use_docker=not args.no_docker,
        docker_image=args.docker_image,
        docker_platform=args.docker_platform,
        extra_ldflags=args.extra_ldflags,
        runs=args.runs,
        timeout_s=args.timeout,
        report_path=report_path,
    )

    if not report.get("ok"):
        print(json.dumps(report, indent=2))
        raise SystemExit("naive-bench reported ok=false (see JSON above)")

    timing = report.get("timing") or {}
    asm = timing.get("assembly") or {}
    samples_ns = asm.get("samples_ns") or []
    mean_s = asm.get("mean_s")
    median_s = asm.get("median_s")

    print("naive-bench assembly timing (inside single container phase):")
    print(f"  mean_s:   {mean_s}")
    print(f"  median_s: {median_s}")
    print(f"  count:    {asm.get('count')}")
    if samples_ns:
        secs = [x / 1e9 for x in samples_ns]
        sd = _pop_stdev_seconds(secs)
        rel = (sd / statistics.mean(secs)) if secs and math.isfinite(sd) and statistics.mean(secs) > 0 else float("nan")
        print(f"  stdev_s (population): {sd:.6f}")
        print(f"  CV (stdev/mean):       {rel:.4f}")
    print()
    print(f"Full JSON written to {report_path}")

    _write_run_workload_script(workspace, exec_timeout_s=args.timeout, n_tests=n_tests)

    print()
    print("== hyperfine ==")
    if args.no_docker:
        print(
            "  Skipping automatic hyperfine invocation in --no-docker mode "
            "(ELF/linux binaries may not match host). Install hyperfine and run manually, e.g.:"
        )
        print(f"    cd {workspace} && hyperfine --runs {args.runs} --warmup {args.warmup} 'bash ./run_workload.sh'")
        return

    hf = _run_hyperfine_docker_per_iter(
        workspace=workspace,
        docker_image=args.docker_image,
        docker_platform=args.docker_platform,
        runs=args.runs,
        warmup=args.warmup,
        export_path=hf_path,
    )
    if hf is None:
        if not shutil.which("hyperfine"):
            print("  hyperfine not found. Install: https://github.com/sharkdp/hyperfine")
            print("    macOS: brew install hyperfine")
        else:
            print("  docker not found; cannot run containerized hyperfine benchmark.")
        return

    results = hf.get("results") or []
    if not results:
        print(json.dumps(hf, indent=2))
        raise SystemExit("hyperfine JSON missing results")

    r0 = results[0]
    hf_mean = float(r0["mean"])
    hf_std = float(r0.get("stddev", float("nan")))
    hf_times = [float(x) for x in r0.get("times", [])]
    hf_cv = (hf_std / hf_mean) if hf_mean > 0 and math.isfinite(hf_std) else float("nan")

    print("hyperfine (each run = fresh `docker run` + same workload as naive inner loop):")
    print(f"  mean_s:   {hf_mean:.6f}")
    print(f"  stddev_s: {hf_std:.6f}")
    print(f"  CV:       {hf_cv:.4f}")
    print(f"JSON written to {hf_path}")

    print()
    print("== interpretation ==")
    print(
        "  • naive-bench times only the workload (all test cases once per iteration) inside "
        "one already-running container."
    )
    print(
        "  • This hyperfine setup times `docker run ...` for every iteration, so the mean is "
        "workload + container startup/teardown + image entry — typically much larger than naive mean_s."
    )
    print(
        "  • For methodology comparison (outliers, shell overhead correction, export formats), see "
        "hyperfine's docs: https://github.com/sharkdp/hyperfine"
    )
    if mean_s is not None and hf_mean > 0:
        print(f"  • Ratio hyperfine_mean / naive_mean ≈ {hf_mean / float(mean_s):.2f}x (dominated by per-run Docker cost).")


if __name__ == "__main__":
    main()
