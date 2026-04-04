# Naive bench — usage

## Behavior (short)

1. Compile **only** your assembly, run **IO tests** if provided; on failure the run stops (no `O0`–`O3`, no timing).
2. If tests pass (or there are no tests), compile reference **`O0`–`O3`** (when `--reference` is set) and **time** assembly + baselines **N times** inside one benchmark phase (local bash or Docker).

## Install

From the `naive/` directory (or `pip install` a wheel/sdist you build):

```bash
pip install -e .
```

Console entry point: `naive-bench`. Module: `python -m naive_bench`.

---

## CLI: `naive-bench`

### Positional

| Argument | Description |
|----------|-------------|
| `assembly` | Path to assembly source (`.s`). Copied into the workspace as `asm.s` and compiled with `gcc`. |

### Inputs and correctness

| Flag | Description |
|------|-------------|
| `--reference PATH` | Optional C or C++ file; produces `bench_O0` … `bench_O3` for timing comparison. |
| `--language {c,cpp}` | Treat `--reference` as C (`.c` + `gcc`) or C++ (`.cpp` + `g++`). Default: `cpp`. |
| `--tests PATH` | File containing Codeforces-style tests: JSON array of `{ "input": "...", "output": "..." }`, a single object, or a Python literal with the same shape. |
| `--strict-output` | Compare stdout to expected **exactly**. Default: strip trailing newlines on both sides (common judge behavior). |
| `--timing-input PATH` | File copied to `timing.in` and used as stdin for every **timing** iteration (not for IO tests). Default: empty stdin. |

### Timing and limits

| Flag | Description |
|------|-------------|
| `--runs N` | Number of timed iterations **per binary** in the benchmark phase (default: `30`, minimum `1`). |
| `--timeout SECONDS` | Per-run timeout for **each test** and **each timing iteration** (default: `10`). Passed to GNU `timeout` inside the script; floored to at least `0.001` in Python. |
| `--docker-timeout SECONDS` | Wall-clock limit for **each** subprocess that runs a phase script (default: `600`). |

### Compile tuning

| Flag | Description |
|------|-------------|
| `--extra-asm-flags "..."` | Extra tokens for `gcc … asm.s -o bench_asm …`, after shell-style splitting (`shlex.split`). |
| `--extra-cflags "..."` | Extra tokens when compiling the reference with `gcc`/`g++`. |
| `--extra-ldflags "..."` | Extra tokens appended to **both** assembly and reference link commands. |
| `--std-c FLAG` | `-std=…` for C (default: `-std=c17`). Used when `--language c`. |
| `--std-cxx FLAG` | `-std=…` for C++ (default: `-std=c++20`). Used when `--language cpp`. |

### Modes

| Flag | Description |
|------|-------------|
| `--only-compile` | Compile assembly and, if given, all baseline binaries; **no** tests and **no** timing. |
| `--skip-compile` | Do not run compiler lines in the scripts; you must supply binaries under `--workspace`. **Requires** `--workspace`. Incompatible with `--only-compile`. |

### Docker

| Flag | Description |
|------|-------------|
| `--use-docker` | Run each phase script inside `docker run` instead of host `bash`. |
| `--docker-image NAME` | Image tag (default: `gcc:13`). |
| `--docker-platform PLATFORM` | `docker run --platform` (default: `linux/amd64`). |

### Workspace and output

| Flag | Description |
|------|-------------|
| `--workspace PATH` | Use this directory as the workspace; it is **not** deleted after the run. If `--skip-compile` is **off**, the directory is **cleared** before each run. If `--skip-compile` is **on**, the directory is **not** cleared (you must place `bench_asm` and any `bench_O*` there yourself). |
| `--pretty` | Pretty-print JSON on stdout. |
| `--exit-zero` | Process exit code is always `0`; use JSON `ok` / `script_exit_code` / `phases` for success/failure. |

### Exit codes (CLI)

- `0` — success (`ok` true), or `--exit-zero` was set.
- `1` — failure (`ok` false).
- `2` — bad arguments, missing Docker, invalid tests file, or other usage/runtime error before a normal report.

---

## Python API

Import from the installed package `naive_bench` (same options as the CLI, via `BenchConfig`).

### Core calls

```python
from pathlib import Path

from naive_bench.bench import BenchConfig, finish, run_benchmark
from naive_bench.parse_tests import parse_tests_file, parse_tests_payload

tests = tuple(parse_tests_file(Path("tests.json")))
# Or: tests = tuple(parse_tests_payload('[{"input":"1","output":"2"}]'))

cfg = BenchConfig(
    assembly_path=Path("solution.s"),
    reference_path=Path("ref.cpp"),       # or None
    language="cpp",                       # "c" | "cpp"
    tests=tests,                          # tuple[dict[str, str]], keys "input"/"output"
    runs=30,
    only_compile=False,
    skip_compile=False,
    use_docker=True,
    docker_image="gcc:13",
    docker_platform="linux/amd64",
    docker_timeout_s=600.0,
    exec_timeout_s=10.0,
    extra_asm=(),
    extra_c=(),
    extra_ld=(),
    std_c_flag="-std=c17",
    std_cxx_flag="-std=c++20",
    strict_output_compare=False,
    timing_input_path=None,               # Path | None
    keep_workspace=None,                 # Path | None — same as CLI --workspace
)

outcome = run_benchmark(cfg)
report = outcome.report          # dict: ok, phases, compile, correctness, timing, …
# outcome.workspace              # Path to workspace (temp or keep_workspace)

finish(outcome)                  # deletes temp workspace if keep_workspace was None
```

### `BenchConfig` fields (map to CLI)

| Field | CLI equivalent | Notes |
|-------|----------------|--------|
| `assembly_path` | positional `assembly` | |
| `reference_path` | `--reference` | `None` = no baselines |
| `language` | `--language` | `"c"` or `"cpp"` |
| `tests` | `--tests` | Build with `parse_tests_file` / `parse_tests_payload` |
| `runs` | `--runs` | ≥ 1 |
| `only_compile` | `--only-compile` | |
| `skip_compile` | `--skip-compile` | Requires `keep_workspace` |
| `use_docker` | `--use-docker` | |
| `docker_image` | `--docker-image` | |
| `docker_platform` | `--docker-platform` | |
| `docker_timeout_s` | `--docker-timeout` | Per phase subprocess |
| `exec_timeout_s` | `--timeout` | Per test / per timing iteration |
| `extra_asm` | `--extra-asm-flags` | `tuple[str, ...]` of tokens |
| `extra_c` | `--extra-cflags` | |
| `extra_ld` | `--extra-ldflags` | |
| `std_c_flag` | `--std-c` | |
| `std_cxx_flag` | `--std-cxx` | |
| `strict_output_compare` | `--strict-output` | |
| `timing_input_path` | `--timing-input` | |
| `keep_workspace` | `--workspace` | |

### Report shape (high level)

- `ok` — overall success of the last relevant phase.
- `script_exit_code` — last phase’s exit code (or the failing phase when short-circuited).
- `phases` — list of `{ "name", "exit_code", "stdout", "stderr" }` (`correctness`, optionally `benchmark`, or `compile_only`).
- `compile` — `assembly` / `baselines` with `ok` and binary names.
- `correctness` — `enabled`, `all_passed`, per-case `exit_code`, `passed`, `expected`, `actual`, …
- `timing` — `enabled` or `skipped` + `reason`; summaries include `mean_s`, `median_s`, `samples_ns`, etc.

### Optional: stdout comparison helper

```python
from naive_bench.compare_outputs import outputs_match

outputs_match("42\n", "42", strict=False)  # True (trailing newline)
outputs_match("42\n", "42", strict=True)   # False
```

### Tests parsing only

```python
from naive_bench.parse_tests import parse_tests_file, parse_tests_payload, TestsParseError
```

---

## Real Example Dataset (ABC)

Files under `examples/`:

- `examples/abc_tests.json` — provided Codeforces-style IO tests
- `examples/abc_ref.cpp` — provided C++ reference solution
- `examples/abc_user_arm64.s` — provided ARM64 assembly sample

Run with Docker ARM64 (important for this assembly):

```bash
naive-bench examples/abc_user_arm64.s \
  --reference examples/abc_ref.cpp \
  --tests examples/abc_tests.json \
  --language cpp \
  --use-docker \
  --docker-image gcc:13 \
  --docker-platform linux/arm64 \
  --extra-ldflags "-lstdc++" \
  --runs 10 \
  --pretty
```

---

## Original notes (inputs / outputs)

1. Assembly code (required)
2. Reference source (optional) — compare timing against `-O0` … `-O3`
3. Number of timed iterations (default 30)
4. Test cases (optional) — correctness; Codeforces-style `input` / `output`
5. Compiler / Docker options via flags or `BenchConfig`

**Outputs:** correctness (optional), timing (assembly + optional baselines), compile status; JSON from CLI or `outcome.report` in Python.

- Python pip-installable package for use from other repos
- Runs in Docker optionally to isolate Linux + toolchain
- Naive by design — for teams that need a working benchmark quickly
