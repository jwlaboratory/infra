"""Orchestrate workspace setup, correctness-first phases, then hyperfine benchmarking."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from hyperfine_bench import constants as C
from hyperfine_bench.compare_outputs import outputs_match
from hyperfine_bench.runner import docker_daemon_reachable, run_docker_script, run_local_script
from hyperfine_bench.script_builder import (
    CompileCommands,
    build_asm_only_commands,
    build_baseline_only_commands,
    build_benchmark_phase_script,
    build_compile_only_script,
    build_correctness_phase_script,
    build_full_compile_commands,
)


Language = Literal["c", "cpp"]


@dataclass(frozen=True)
class BenchConfig:
    assembly_path: Path
    reference_path: Path | None
    language: Language
    tests: tuple[dict[str, str], ...]
    runs: int
    only_compile: bool
    skip_compile: bool
    use_docker: bool
    docker_image: str
    docker_platform: str
    docker_timeout_s: float
    exec_timeout_s: float
    extra_asm: tuple[str, ...] = ()
    extra_c: tuple[str, ...] = ()
    extra_ld: tuple[str, ...] = ()
    std_c_flag: str = "-std=c17"
    std_cxx_flag: str = "-std=c++20"
    strict_output_compare: bool = False
    timing_input_path: Path | None = None
    keep_workspace: Path | None = None
    hyperfine_warmup: int = 0


@dataclass
class BenchOutcome:
    report: dict[str, Any]
    workspace: Path
    _cleanup: Any = field(default=None, repr=False)


def _ref_filename(language: Language) -> str:
    return C.REF_C if language == "c" else C.REF_CPP


def _prepare_workspace(cfg: BenchConfig) -> Path:
    if cfg.keep_workspace is not None:
        root = cfg.keep_workspace
        root.mkdir(parents=True, exist_ok=True)
        if not cfg.skip_compile:
            for child in root.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        return root

    return Path(tempfile.mkdtemp(prefix="hyperfine-bench-"))


def _populate_workspace(root: Path, cfg: BenchConfig) -> None:
    asm_dest = root / C.ASM_SOURCE
    shutil.copyfile(cfg.assembly_path, asm_dest)
    # Some assemblers complain if file has no final newline; normalize at copy time.
    raw = asm_dest.read_bytes()
    if raw and not raw.endswith(b"\n"):
        asm_dest.write_bytes(raw + b"\n")

    if cfg.reference_path is not None:
        dest = root / _ref_filename(cfg.language)
        shutil.copyfile(cfg.reference_path, dest)

    tests_dir = root / C.TESTS_DIR
    tests_dir.mkdir(parents=True, exist_ok=True)
    for idx, case in enumerate(cfg.tests):
        (tests_dir / f"{idx}.in").write_text(case["input"], encoding="utf-8")

    timing_path = root / C.TIMING_INPUT
    if cfg.timing_input_path is not None:
        shutil.copyfile(cfg.timing_input_path, timing_path)
    else:
        timing_path.write_bytes(b"")


def _binary_exists(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _collect_compile_report(root: Path, cfg: BenchConfig) -> dict[str, Any]:
    asm_path = root / C.ASM_BINARY
    assembly = {
        "binary": C.ASM_BINARY,
        "ok": _binary_exists(asm_path),
    }
    baselines: dict[str, Any] = {}
    if cfg.reference_path is not None:
        for label in C.OPT_LEVELS:
            p = root / f"bench_{label}"
            baselines[label] = {"binary": p.name, "ok": _binary_exists(p)}
    return {
        "skipped": cfg.skip_compile,
        "assembly": assembly,
        "baselines": baselines,
    }


def _collect_correctness(root: Path, cfg: BenchConfig) -> dict[str, Any]:
    if not cfg.tests:
        return {
            "enabled": False,
            "strict": cfg.strict_output_compare,
            "cases": [],
            "all_passed": None,
        }

    cases: list[dict[str, Any]] = []
    all_passed = True
    tests_dir = root / C.TESTS_DIR

    for idx, expected_case in enumerate(cfg.tests):
        rc_path = tests_dir / f"{idx}.rc"
        actual_path = tests_dir / f"{idx}.actual"
        err_path = tests_dir / f"{idx}.err"

        exit_code = -1
        if rc_path.is_file():
            try:
                exit_code = int(rc_path.read_text(encoding="utf-8").strip())
            except ValueError:
                exit_code = -1

        actual = actual_path.read_text(encoding="utf-8") if actual_path.is_file() else ""
        stderr = err_path.read_text(encoding="utf-8") if err_path.is_file() else ""
        expected_out = expected_case["output"]

        output_ok = outputs_match(
            actual,
            expected_out,
            strict=cfg.strict_output_compare,
        )
        passed = exit_code == 0 and output_ok
        if not passed:
            all_passed = False

        cases.append(
            {
                "index": idx,
                "exit_code": exit_code,
                "passed": passed,
                "output_ok": output_ok,
                "expected": expected_out,
                "actual": actual,
                "stderr": stderr,
            }
        )

    return {
        "enabled": True,
        "strict": cfg.strict_output_compare,
        "cases": cases,
        "all_passed": all_passed,
    }


def _timing_skipped(reason: str) -> dict[str, Any]:
    return {"enabled": False, "skipped": True, "reason": reason}


def _load_hyperfine_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"count": 0}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        results = payload.get("results", [])
        if not isinstance(results, list) or not results:
            return {"count": 0}
        row = results[0]
        times = row.get("times", [])
        samples_s = [float(x) for x in times] if isinstance(times, list) else []
        samples_ns = [int(round(x * 1_000_000_000.0)) for x in samples_s]
        count = int(row.get("runs", len(samples_s)))
        mean_s = float(row.get("mean", 0.0))
        median_s = float(row.get("median", 0.0))
        out: dict[str, Any] = {
            "count": count,
            "source": "hyperfine",
            "command": row.get("command"),
            "mean_s": mean_s,
            "median_s": median_s,
            "min_s": float(row.get("min", 0.0)),
            "max_s": float(row.get("max", 0.0)),
            "stddev_s": float(row.get("stddev", 0.0)),
            "samples_s": samples_s,
            "samples_ns": samples_ns,
            "mean_ns": mean_s * 1_000_000_000.0,
            "median_ns": median_s * 1_000_000_000.0,
            "min_ns": float(row.get("min", 0.0)) * 1_000_000_000.0,
            "max_ns": float(row.get("max", 0.0)) * 1_000_000_000.0,
        }
        return out
    except (OSError, ValueError, TypeError):
        return {"count": 0}


def _collect_timing(root: Path, cfg: BenchConfig) -> dict[str, Any]:
    if cfg.only_compile:
        return _timing_skipped("only_compile")

    out: dict[str, Any] = {
        "enabled": True,
        "runs_requested": cfg.runs,
        "hyperfine_warmup": cfg.hyperfine_warmup,
        "assembly": _load_hyperfine_summary(root / C.timing_json_for_label("asm")),
    }

    baselines: dict[str, Any] = {}
    if cfg.reference_path is not None:
        for label in C.OPT_LEVELS:
            baselines[label] = _load_hyperfine_summary(root / C.timing_json_for_label(label))
    out["baselines"] = baselines
    return out


def _write_and_run_script(
    root: Path,
    script_name: str,
    body: str,
    cfg: BenchConfig,
) -> Any:
    path = root / script_name
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    if cfg.use_docker:
        return run_docker_script(
            root,
            script_name,
            image=cfg.docker_image,
            platform=cfg.docker_platform,
            timeout_s=cfg.docker_timeout_s,
        )
    return run_local_script(
        root,
        script_name,
        timeout_s=cfg.docker_timeout_s,
    )


def run_benchmark(cfg: BenchConfig) -> BenchOutcome:
    if cfg.use_docker:
        ok, msg = docker_daemon_reachable()
        if not ok:
            raise RuntimeError(f"Docker is not available: {msg}")

    if cfg.skip_compile and cfg.only_compile:
        raise ValueError("skip_compile and only_compile together are not useful.")

    if cfg.skip_compile and cfg.keep_workspace is None:
        raise ValueError(
            "skip_compile requires keep_workspace: point it at a directory that "
            f"already contains {C.ASM_BINARY} (and bench_O0..bench_O3 if you use a reference)."
        )

    root = _prepare_workspace(cfg)
    cleanup = None
    if cfg.keep_workspace is None:

        def _cleanup() -> None:
            shutil.rmtree(root, ignore_errors=True)

        cleanup = _cleanup

    try:
        _populate_workspace(root, cfg)

        ref_name: str | None = None
        if cfg.reference_path is not None:
            ref_name = _ref_filename(cfg.language)

        std_flag = cfg.std_c_flag if cfg.language == "c" else cfg.std_cxx_flag

        phases: list[dict[str, Any]] = []

        if cfg.only_compile:
            full_cmds = build_full_compile_commands(
                asm_source=C.ASM_SOURCE,
                asm_binary=C.ASM_BINARY,
                extra_asm=list(cfg.extra_asm),
                extra_ld=list(cfg.extra_ld),
                language=cfg.language,
                ref_source=ref_name,
                ref_std_flag=std_flag,
                extra_c=list(cfg.extra_c),
            )
            script = build_compile_only_script(
                compile_cmds=full_cmds,
                skip_compile=cfg.skip_compile,
            )
            proc = _write_and_run_script(root, C.RUN_SCRIPT, script, cfg)
            phases.append(
                {
                    "name": "compile_only",
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            )
            compile_report = _collect_compile_report(root, cfg)
            correctness = {
                "enabled": False,
                "strict": cfg.strict_output_compare,
                "cases": [],
                "all_passed": None,
                "note": "skipped for --only-compile",
            }
            timing = _collect_timing(root, cfg)
            report: dict[str, Any] = {
                "ok": proc.returncode == 0,
                "script_exit_code": proc.returncode,
                "phases": phases,
                "script_stdout": proc.stdout,
                "script_stderr": proc.stderr,
                "compile": compile_report,
                "correctness": correctness,
                "timing": timing,
            }
            return BenchOutcome(report=report, workspace=root, _cleanup=cleanup)

        asm_cmds = build_asm_only_commands(
            asm_source=C.ASM_SOURCE,
            asm_binary=C.ASM_BINARY,
            extra_asm=list(cfg.extra_asm),
            extra_ld=list(cfg.extra_ld),
        )
        correctness_script = build_correctness_phase_script(
            asm_compile=asm_cmds,
            n_tests=len(cfg.tests),
            exec_timeout_s=cfg.exec_timeout_s,
            skip_compile=cfg.skip_compile,
        )
        proc_correctness = _write_and_run_script(
            root, C.PHASE_CORRECTNESS_SCRIPT, correctness_script, cfg
        )
        phases.append(
            {
                "name": "correctness",
                "exit_code": proc_correctness.returncode,
                "stdout": proc_correctness.stdout,
                "stderr": proc_correctness.stderr,
            }
        )

        correctness = _collect_correctness(root, cfg)
        compile_report = _collect_compile_report(root, cfg)

        if proc_correctness.returncode != 0:
            reason = (
                "assembly_tests_failed"
                if proc_correctness.returncode == 3
                else "correctness_phase_failed"
            )
            timing = _timing_skipped(reason)
            report = {
                "ok": False,
                "script_exit_code": proc_correctness.returncode,
                "phases": phases,
                "script_stdout": proc_correctness.stdout,
                "script_stderr": proc_correctness.stderr,
                "compile": compile_report,
                "correctness": correctness,
                "timing": timing,
            }
            return BenchOutcome(report=report, workspace=root, _cleanup=cleanup)

        if correctness.get("enabled") and correctness.get("all_passed") is False:
            timing = _timing_skipped("assembly_output_mismatch")
            report = {
                "ok": False,
                "script_exit_code": 3,
                "phases": phases,
                "script_stdout": proc_correctness.stdout,
                "script_stderr": proc_correctness.stderr,
                "compile": compile_report,
                "correctness": correctness,
                "timing": timing,
            }
            return BenchOutcome(report=report, workspace=root, _cleanup=cleanup)

        if ref_name is not None:
            baseline_cmds = build_baseline_only_commands(
                language=cfg.language,
                ref_source=ref_name,
                ref_std_flag=std_flag,
                extra_c=list(cfg.extra_c),
                extra_ld=list(cfg.extra_ld),
            )
        else:
            baseline_cmds = CompileCommands(lines=())

        benchmark_script = build_benchmark_phase_script(
            baseline_compile=baseline_cmds,
            runs=cfg.runs,
            n_tests=len(cfg.tests),
            exec_timeout_s=cfg.exec_timeout_s,
            skip_compile=cfg.skip_compile,
            has_reference=cfg.reference_path is not None,
            hyperfine_warmup=max(0, int(cfg.hyperfine_warmup)),
        )
        proc_benchmark = _write_and_run_script(
            root, C.PHASE_BENCHMARK_SCRIPT, benchmark_script, cfg
        )
        phases.append(
            {
                "name": "benchmark",
                "exit_code": proc_benchmark.returncode,
                "stdout": proc_benchmark.stdout,
                "stderr": proc_benchmark.stderr,
            }
        )

        compile_report = _collect_compile_report(root, cfg)
        timing = _collect_timing(root, cfg)

        overall_ok = proc_benchmark.returncode == 0
        report = {
            "ok": overall_ok,
            "script_exit_code": proc_benchmark.returncode,
            "phases": phases,
            "script_stdout": proc_benchmark.stdout,
            "script_stderr": proc_benchmark.stderr,
            "compile": compile_report,
            "correctness": correctness,
            "timing": timing,
        }
        return BenchOutcome(report=report, workspace=root, _cleanup=cleanup)
    except Exception:
        if cleanup:
            cleanup()
        raise


def finish(outcome: BenchOutcome) -> None:
    """Remove temporary workspace when used."""
    if outcome._cleanup is not None:
        outcome._cleanup()
