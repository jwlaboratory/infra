# llvm-mca (tool brief, one-pager)

**References:** [LLVM Command Guide: llvm-mca](https://llvm.org/docs/CommandGuide/llvm-mca.html) · Original RFC [D43951](https://reviews.llvm.org/D43951).

## What it does

llvm-mca ingests **assembly** (often compiler-produced) and uses LLVM’s **scheduling models** to estimate **IPC, resource pressure, and bottlenecks** for out-of-order cores — **without executing** the binary.

## Strengths

- **Deterministic** for a given input + target CPU model (`-mcpu`, triple).
- Fast enough for CI-style regression on **small kernels**.
- Well-maintained inside the LLVM ecosystem.

## Limits

- Models intentionally omit some µarch details (see RFC): retirement, dispatch width, queue sizes, etc.
- Best on **straight-line** basic blocks; whole programs need manual slicing.
- **AArch64** support depends on the LLVM version and CPU model you select — validate on our Docker image.

## Why benchmarking team cares

Complements **Hyperfine / naive-bench** wall-clock: use llvm-mca when Docker-on-Mac noise dominates; correlate before trusting as an RL reward (see [static_metrics_correlation.md](../static_metrics_correlation.md) and `naive_bench.llvm_mca`).
