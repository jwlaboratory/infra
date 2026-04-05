# CompilerGym (one-pager for team sync)

**Reference:** [CompilerGym: Robust, Performant Compiler Optimization Environments for AI Research](https://arxiv.org/abs/2109.08267) (also IEEE 9741258).

## Problem

Compiler autotuning and RL need **repeatable environments** with realistic search spaces. Ad-hoc scripts per paper make comparisons unfair and slow iteration.

## Idea

Expose **production LLVM (and related) optimization tasks** through a Gym-style API: observation, action (e.g. pass flags), reward (IR metrics, code size, runtime proxies). Ships datasets and baselines so agents are comparable.

## Why benchmark this

- Sets expectations for **what a “compiler RL benchmark” documents**: reward definition, episode length, deterministic builds.
- **Not** a drop-in for our assembly-text pipeline, but the **evaluation discipline** (version pinning, leaderboards, regression tests) is the template for `naive-bench` + `score_candidate`.

## Takeaway - LOOK AT LATER

Use CompilerGym as a **reference for rigor**, not as the primary scorer for Codeforces ARM64 assembly until we explicitly bridge representations (IR vs asm).
