# Timing Best Practices

How we get stable wall-clock timing for `naive-bench` and RL scoring.

Goal:
- Keep coefficient of variation (CV) under `5%`.
- Use reproducible settings across machines.
- Avoid platform mistakes that add large noise.

## Core Defaults

Use these unless you have a specific reason not to:
- `runs=30`
- `warmup_runs=3`
- `use_docker=True`
- `docker_image="gcc:13"`
- `docker_platform="linux/arm64"` for ARM64 assembly
- primary metric = median runtime (not mean)

CV definition:
- `CV = stddev(medians) / mean(medians)`

## Why Timing Gets Noisy

Main sources of jitter:
- OS scheduling and background processes
- CPU frequency changes (turbo/throttling)
- cold caches on first run
- shell timing overhead from `date +%s%N`
- Docker emulation when platform mismatches host

Important:
- For very short programs (`<10ms`), overhead and cold-start effects can basically like take over
- Warmup + enough runs matters more than being a pet peeve on one dang command.

## Warmup Policy

Warmup should prime instruction/caches, etc.

Recommendation:
- default `--warmup-runs 3`
- set to `0` only when single-run time is large (roughly `>100ms`) or you're measuring raw start

Why 3:
- usually enough to stabilize after 1-2 runs
- aligns with SuperCoder-style benchmarking (`warmup 3`)

## Runs and Repeats

Use:
- `--runs 30` minimum per invocation (`50` if you need close medians)
- `--repeats 10-20` for noise studies

Interpretation:
- more `runs` reduces per-invocation median noise
- more `repeats` improves confidence in measured CV
- repeats do not fix bad configuration (e.g., wrong Docker platform)

## Docker Platform Rules - CLAUDE GENERATED (review)

Critical rule:
- Docker platform must match the ISA of the generated assembly.

For our pipeline:
- generated assembly is ARM64
- always pass `--docker-platform linux/arm64` unless testing another ISA on purpose

Symptoms of platform mismatch (QEMU path):
- runtime is `5-20x` slower than expected
- CV spikes (often `>20%` on short binaries)
- Docker warning about requested image platform

Note:
- CLI default may not match scorer defaults.
- Do not rely on defaults for ARM benchmarking; pass platform explicitly.

## Docker Overhead Expectations

Typical ranges:
- native Docker (matched platform): around `1.05-1.15x` overhead
- emulated Docker (mismatched platform): often `5-20x` overhead

Why Docker anyway:
- consistent toolchain
- isolated execution environment
- reproducible results across developers

Measure locally with:
- `scripts/docker_overhead_study.py`

## Cache Controls

Most of our workloads:
- small inputs
- steady-state performance is the target
- no need to force cache drops

`drop_caches` guidance:
- only for explicit cold-cache studies
- requires privileged container and is not default-safe

If using hyperfine:
- use `--prepare "sync"` as lightweight pre-run stabilization

## Tool Choice

Use `naive-bench` for:
- daily scoring in RL loop
- low dependency surface
- fast operational usage

Use `hyperfine-bench` for:
- methodology validation
- publication-style benchmark reporting
- direct comparability with papers using hyperfine

## Fallback for High-Noise Cases

If CV stays above `5%` despite correct setup:
- consider `llvm-mca` as deterministic supplemental signal
- treat it as a proxy (basic-block analysis), not wall-clock replacement

Reference implementation:
- `naive_bench/llvm_mca.py`

## Batch Study Template

Run:
- `scripts/run_noise_batch.py --repeats 20 --threshold 0.05`

Track:
- per-binary CV for candidate assembly and baselines
- pass/fail against threshold
- platform and run settings used for each record

## Quick Commands

RL scorer config target:

```python
ScoreCandidateConfig(
    runs=30,
    warmup_runs=3,
    use_docker=True,
    docker_image="gcc:13",
    docker_platform="linux/arm64",
)
```

CLI benchmark example:

```bash
naive-bench assembly.s \
  --reference ref.cpp \
  --tests tests.json \
  --language cpp \
  --runs 30 \
  --warmup-runs 3 \
  --use-docker \
  --docker-image gcc:13 \
  --docker-platform linux/arm64 \
  --extra-ldflags=-lstdc++ \
  --timing-summary \
  --timing-chart \
  --pretty
```
