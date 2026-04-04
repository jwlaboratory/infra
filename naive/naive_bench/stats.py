"""Simple summaries for timing samples (nanoseconds as integers)."""

from __future__ import annotations

from pathlib import Path


def summarize_nanoseconds(samples: list[int]) -> dict[str, float | int]:
    if not samples:
        return {"count": 0}

    ordered = sorted(samples)
    n = len(ordered)
    total = sum(ordered)
    mean_ns = total / n
    if n % 2 == 1:
        median_ns = float(ordered[n // 2])
    else:
        median_ns = (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0

    return {
        "count": n,
        "median_ns": median_ns,
        "mean_ns": mean_ns,
        "median_s": median_ns / 1_000_000_000.0,
        "mean_s": mean_ns / 1_000_000_000.0,
        "min_ns": float(ordered[0]),
        "max_ns": float(ordered[-1]),
    }


def read_ns_samples(path: Path) -> list[int]:
    p = Path(path)
    if not p.is_file():
        return []
    values: list[int] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        values.append(int(line))
    return values
