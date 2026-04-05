"""Generate bash scripts: correctness-first phase, then hyperfine benchmark phase."""

from __future__ import annotations

import shlex
from dataclasses import dataclass

from hyperfine_bench import constants as C


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
  echo "hyperfine-bench: assembly failed tests (nonzero exit or timeout 124)" >&2
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
    hyperfine_warmup: int,
    hyperfine_prepare: str | None,
) -> str:
    """
    Build O0..O3 from reference (if any), then benchmark assembly + baselines with hyperfine.
    Expects ./bench_asm to already exist.
    """
    skip_compile_flag = "1" if skip_compile else "0"
    compile_block = _compile_block(baseline_compile, skip_compile=skip_compile)

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

    baseline_block = ""
    prepare_arg = (
        f" --prepare {shlex.quote(hyperfine_prepare)}"
        if hyperfine_prepare and hyperfine_prepare.strip()
        else ""
    )
    if has_reference:
        baseline_block = f"""
for label in O0 O1 O2 O3; do
  bin="./bench_${{label}}"
  if [[ -x "${{bin}}" ]]; then
    hyperfine --runs "${{RUNS}}" --warmup "${{HYPERFINE_WARMUP}}"{prepare_arg} \
      --export-json "timing_${{label}}.json" -- \
      "./run_one_binary.sh ${{bin}}" >/dev/null || exit 4
  fi
done
""".strip()

    return f"""#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"

EXEC_TIMEOUT={exec_timeout_s}
RUNS={runs}
N_TESTS={n_tests}
SKIP_COMPILE_FLAG={skip_compile_flag}
HYPERFINE_WARMUP={hyperfine_warmup}

{compile_block}

if ! command -v hyperfine >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update >/dev/null 2>&1 && apt-get install -y hyperfine >/dev/null 2>&1
  fi
fi

if ! command -v hyperfine >/dev/null 2>&1; then
  echo "hyperfine-bench: hyperfine not found. Install hyperfine or use an image with hyperfine preinstalled." >&2
  exit 5
fi

cat > ./run_one_binary.sh <<'EOF'
#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$ROOT"
EXEC_TIMEOUT={exec_timeout_s}
N_TESTS={n_tests}
BINARY="$1"

run_one_binary() {{
{run_one_binary_body}
}}

run_one_binary "$BINARY"
EOF
chmod +x ./run_one_binary.sh

if [[ ! -x "./{C.ASM_BINARY}" ]]; then
  echo "hyperfine-bench: missing ./{C.ASM_BINARY}" >&2
  exit 4
fi

hyperfine --runs "${{RUNS}}" --warmup "${{HYPERFINE_WARMUP}}"{prepare_arg} \
  --export-json "{C.timing_json_for_label('asm')}" -- \
  "./run_one_binary.sh ./{C.ASM_BINARY}" >/dev/null || exit 4

{baseline_block}

exit 0
"""
