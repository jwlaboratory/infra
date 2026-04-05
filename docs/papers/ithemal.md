# Ithemal (one-pager for team sync)

**Reference:** Mendis et al., *IThemal: Accurate, Portable and Fast Basic Block Throughput Estimation using Deep Neural Networks*, ICML 2019. [PDF](https://proceedings.mlr.press/v97/mendis19a/mendis19a.pdf) · [arXiv:1808.07412](https://arxiv.org/abs/1808.07412).

## Problem

Analytical models (including LLVM’s schedulers) are **tedious to extend** for new µarchs and can mis-estimate throughput on complex x86-64 basic blocks.

## Idea

Train a **hierarchical LSTM** on basic blocks to predict **throughput (cycles)**, competing with llvm-mca / IACA-style tools. Reported **<50% error** of analytical baselines on their benchmarks.

## Why

- Shows when **learned static predictors** beat hand-built models — relevant if we want a **low-noise reward** or offline dataset labeling.
- Scope is **basic blocks**, same structural limit as llvm-mca: need loop extraction for whole-program stories.

## Takeaway

Short term: **llvm-mca in Docker** is the cheap deterministic probe. Long term: Ithemal-style models are optional if we need **better correlation** on AArch64-heavy kernels after we measure llvm-mca vs wall-clock (see [static_metrics_correlation.md](../static_metrics_correlation.md)).
