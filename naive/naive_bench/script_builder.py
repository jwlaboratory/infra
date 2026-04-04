"""Generate bash scripts: correctness-first phase, then benchmark phase (one Docker run each)."""

from __future__ import annotations

import shlex
from dataclasses import dataclass

from naive_bench import constants as C


@dataclass(frozen=True)
class CompileCommands:
    """Shell lines (already quoted) to run under set -e."""

    lines: tuple[str, ...]


def quote_cmd(argv: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def build_asm_only_commands(
    *,
    asm_source: str,
    asm_binary: str,
    extra_asm: list[str],
    extra_ld: list[str],
) -> CompileCommands:
    asm_argv = ["gcc", *extra_asm, asm_source, "-o", asm_binary, *extra_ld]
    return CompileCommands(lines=(quote_cmd(asm_argv),))


def build_baseline_only_commands(
    *,
    language: str,
    ref_source: str,
    ref_std_flag: str,
    extra_c: list[str],
    extra_ld: list[str],
) -> CompileCommands:
    driver = "gcc" if language == "c" else "g++"
    lines: list[str] = []
    for opt in ("O0", "O1", "O2", "O3"):
        out = f"bench_{opt}"
        argv = [
            driver,
            ref_std_flag,
            f"-{opt}",
            ref_source,
            "-o",
            out,
            *extra_c,
            *extra_ld,
        ]
        lines.append(quote_cmd(argv))
    return CompileCommands(lines=tuple(lines))


def build_full_compile_commands(
    *,
    asm_source: str,
    asm_binary: str,
    extra_asm: list[str],
    extra_ld: list[str],
    language: str,
    ref_source: str | None,
    ref_std_flag: str,
    extra_c: list[str],
) -> CompileCommands:
    """Assembly plus all baseline binaries (for --only-compile)."""
    asm = build_asm_only_commands(
        asm_source=asm_source,
        asm_binary=asm_binary,
        extra_asm=extra_asm,
        extra_ld=extra_ld,
    )
    if ref_source is None:
        return asm
    baseline = build_baseline_only_commands(
        language=language,
        ref_source=ref_source,
        ref_std_flag=ref_std_flag,
        extra_c=extra_c,
        extra_ld=extra_ld,
    )
    return CompileCommands(lines=asm.lines + baseline.lines)


def _compile_block(compile_cmds: CompileCommands, *, skip_compile: bool) -> str:
    if skip_compile:
        return ""
    quoted_lines = "\n".join(f"  {line}" for line in compile_cmds.lines)
    return f"""
if [[ "${{SKIP_COMPILE_FLAG:-0}}" != "1" ]]; then
  set -e
{quoted_lines}
  set +e
fi
""".strip()


def build_compile_only_script(*, compile_cmds: CompileCommands, skip_compile: bool) -> str:
    """Compile everything in compile_cmds (asm + optional baselines), then exit (--only-compile)."""
    skip_compile_flag = "1" if skip_compile else "0"
    compile_block = _compile_block(compile_cmds, skip_compile=skip_compile)
    return f"""#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"

SKIP_COMPILE_FLAG={skip_compile_flag}

{compile_block}

exit 0
"""


def build_correctness_phase_script(
    *,
    asm_compile: CompileCommands,
    n_tests: int,
    exec_timeout_s: float,
    skip_compile: bool,
) -> str:
    """
    Compile user assembly only, then run IO tests if any.
    Exits 3 if a test fails (nonzero exit or timeout 124); 0 on success.
    """
    skip_compile_flag = "1" if skip_compile else "0"
    compile_block = _compile_block(asm_compile, skip_compile=skip_compile)

    test_block = ""
    if n_tests > 0:
        test_block = f"""
mkdir -p tests
TESTS_FAILED=0
for i in $(seq 0 $((N_TESTS - 1))); do
  # Do not use `|| true` here: it would make `$?` always 0 (from `true`).
  timeout "${{EXEC_TIMEOUT}}s" ./{C.ASM_BINARY} < "tests/${{i}}.in" > "tests/${{i}}.actual" 2> "tests/${{i}}.err"
  rc=$?
  echo "${{rc}}" > "tests/${{i}}.rc"
  if [[ "${{rc}}" -ne 0 ]]; then
    TESTS_FAILED=1
  fi
done

if [[ "${{TESTS_FAILED}}" -eq 1 ]]; then
  echo "naive-bench: assembly failed tests (nonzero exit or timeout 124)" >&2
  exit 3
fi
""".strip()

    return f"""#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"

N_TESTS={n_tests}
EXEC_TIMEOUT={exec_timeout_s}
SKIP_COMPILE_FLAG={skip_compile_flag}

{compile_block}

{test_block}

exit 0
"""


def build_benchmark_phase_script(
    *,
    baseline_compile: CompileCommands,
    runs: int,
    n_tests: int,
    exec_timeout_s: float,
    skip_compile: bool,
    has_reference: bool,
) -> str:
    """
    Build O0..O3 from reference (if any), then time assembly + each baseline in one container.
    Expects ./bench_asm to already exist.
    """
    skip_compile_flag = "1" if skip_compile else "0"
    compile_block = _compile_block(baseline_compile, skip_compile=skip_compile)

    opt_labels = ("O0", "O1", "O2", "O3")
    run_one_binary_body = ""
    if n_tests > 0:
        run_one_binary_body = """
for i in $(seq 0 $((N_TESTS - 1))); do
  timeout "${EXEC_TIMEOUT}s" "$1" < "tests/${i}.in" > /dev/null 2>&1 || return 1
done
""".strip()
    else:
        run_one_binary_body = """
timeout "${EXEC_TIMEOUT}s" "$1" < timing.in > /dev/null 2>&1 || return 1
""".strip()

    run_func = f"""
run_one_binary() {{
{run_one_binary_body}
}}
""".strip()

    baseline_timing = ""
    if has_reference:
        parts = []
        for label in opt_labels:
            parts.append(
                f"""
if [[ -x "./bench_{label}" ]]; then
  : > "timing_{label}.txt"
  for j in $(seq 1 "${{RUNS}}"); do
    start=$(date +%s%N)
    run_one_binary "./bench_{label}" || exit 4
    end=$(date +%s%N)
    echo $((end - start)) >> "timing_{label}.txt"
  done
fi
""".strip()
            )
        baseline_timing = "\n".join(parts)

    timing_block = f"""
: > timing_asm.txt
for j in $(seq 1 "${{RUNS}}"); do
  start=$(date +%s%N)
  run_one_binary "./{C.ASM_BINARY}" || exit 4
  end=$(date +%s%N)
  echo $((end - start)) >> timing_asm.txt
done
{baseline_timing}
""".strip()

    return f"""#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"

EXEC_TIMEOUT={exec_timeout_s}
RUNS={runs}
N_TESTS={n_tests}
SKIP_COMPILE_FLAG={skip_compile_flag}

{compile_block}

{run_func}

{timing_block}

exit 0
"""
