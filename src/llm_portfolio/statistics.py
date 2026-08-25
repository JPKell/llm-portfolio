"""Small dependency-free statistical helpers for experiment reports."""

from __future__ import annotations

import math
import random
from statistics import mean, median, stdev
from typing import Iterable


def _numbers(values: Iterable[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result or not all(math.isfinite(value) for value in result):
        raise ValueError("values must be a nonempty collection of finite numbers")
    return result


def summarize(values: Iterable[float]) -> dict[str, float | int]:
    """Return transparent descriptive statistics over raw observations."""
    data = sorted(_numbers(values))
    return {
        "n": len(data),
        "mean": mean(data),
        "median": median(data),
        "sample_stdev": stdev(data) if len(data) > 1 else 0.0,
        "min": data[0],
        "max": data[-1],
    }


def bootstrap_mean_interval(
    values: Iterable[float], *, confidence: float = 0.95, resamples: int = 10_000, seed: int = 1234
) -> dict[str, float | int]:
    """Return a deterministic percentile bootstrap interval for the mean."""
    data = _numbers(values)
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between zero and one")
    if resamples < 100:
        raise ValueError("resamples must be at least 100")
    rng = random.Random(seed)
    size = len(data)
    estimates = sorted(mean(data[rng.randrange(size)] for _ in range(size)) for _ in range(resamples))
    alpha = (1.0 - confidence) / 2.0
    low_index = max(0, min(resamples - 1, math.floor(alpha * resamples)))
    high_index = max(0, min(resamples - 1, math.ceil((1.0 - alpha) * resamples) - 1))
    return {
        "confidence": confidence,
        "resamples": resamples,
        "seed": seed,
        "lower": estimates[low_index],
        "upper": estimates[high_index],
    }


def paired_differences(control: Iterable[float], treatment: Iterable[float]) -> list[float]:
    """Return treatment-minus-control differences for paired observations."""
    left = _numbers(control)
    right = _numbers(treatment)
    if len(left) != len(right):
        raise ValueError("paired inputs must have equal length")
    return [candidate - baseline for baseline, candidate in zip(left, right, strict=True)]
