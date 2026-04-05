# hyperfine

Copy of `infra/naive` that keeps the same compile + correctness flow, but uses
[hyperfine](https://github.com/sharkdp/hyperfine) for benchmark statistics.

## What stays the same

- compile assembly and optional C/C++ baselines (`O0`..`O3`)
- run correctness tests before benchmarking
- support local or Docker execution
- return JSON report with compile/correctness/timing sections

## What changes

- benchmark phase uses `hyperfine --export-json`
- timing data is read from `timing_*.json` instead of `timing_*.txt`
- timing entries include hyperfine metrics like `stddev_s` and per-run `samples_s`
- warmup defaults to 3 via `--hyperfine-warmup` (override as needed)
- optional cache/setup strategy via `--hyperfine-prepare "<cmd>"`

## Install

From `infra/hyperfine`:

```bash
pip install -e .
```

CLI entry point: `hyperfine-bench`  
Module entry point: `python -m hyperfine_bench`

## Example

Use the shared sample files from `infra/examples`:

```bash
hyperfine-bench ../examples/abc_user_arm64.s \
  --reference ../examples/abc_ref.cpp \
  --tests ../examples/abc_tests.json \
  --language cpp \
  --use-docker \
  --docker-image gcc:13 \
  --docker-platform linux/arm64 \
  --extra-ldflags=-lstdc++ \
  --runs 10 \
  --hyperfine-warmup 3 \
  --hyperfine-prepare "sync" \
  --timing-summary \
  --timing-chart \
  --pretty
```

## Notes

- If `hyperfine` is missing inside the runtime environment, the benchmark phase tries
  to install it via `apt-get` when available.
- For reproducible runs, prefer a Docker image that already contains both `gcc` and
  `hyperfine`.
