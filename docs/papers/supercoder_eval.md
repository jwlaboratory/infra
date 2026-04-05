# SuperCoder-style superoptimization (eval lens, one-pager)

**Reference:** [arXiv:2505.11480](https://arxiv.org/abs/2505.11480) — large-scale C/assembly work (8M programs cited in project NOTES); read especially **methodology / evaluation**.

## Problem

Superoptimization and assembly generation explode in search space; models need **clear success criteria** beyond “looks like asm.”

## Evaluation patterns to steal

- **Correctness:** I/O or executable behavior checks on held-out tests (aligns with our Codeforces harness).
- **Performance:** compare against strong compiler baselines (`-O3`, etc.) with repeated timing — same family as `6-scorer.py` / `score_candidate`.
- **Data ablation:** papers in this line often show **what supervision helps** (C only vs C+asm); informs whether SFT targets should be `-O3` dumps or richer signals.

## Why benchmarking team cares

Our `score_candidate` reward intentionally **mirrors** the scalar mix in `6-scorer.py` (compile fail, partial correctness, log-speedups vs O0/O3, optional size). SuperCoder-class papers justify **multi-term rewards** and careful baseline choice.

## Takeaway for JW Labs

Document **exact reward components and baselines** next to every experiment table; when we add llvm-mca or other static metrics, report **whether rankings agree** with wall-clock, not only headline speedups.
