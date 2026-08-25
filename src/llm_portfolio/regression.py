"""Evaluate simple, auditable metric regression rules."""

from __future__ import annotations

import math
from typing import Any

OPERATORS = {
    "ge": lambda actual, threshold: actual >= threshold,
    "gt": lambda actual, threshold: actual > threshold,
    "le": lambda actual, threshold: actual <= threshold,
    "lt": lambda actual, threshold: actual < threshold,
    "eq": lambda actual, threshold: actual == threshold,
}


def evaluate_rules(metrics: Any, specification: Any) -> dict[str, Any]:
    """Evaluate flat numeric metrics against explicit threshold rules."""
    if not isinstance(metrics, dict):
        raise ValueError("metrics must be an object")
    if not isinstance(specification, dict) or specification.get("schema") != "llm-portfolio-regression-v1":
        raise ValueError("invalid regression specification schema")
    rules = specification.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("rules must be a nonempty list")
    results: list[dict[str, Any]] = []
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"rules[{index}] must be an object")
        metric = rule.get("metric")
        operator = rule.get("operator")
        threshold = rule.get("threshold")
        severity = rule.get("severity", "block")
        if not isinstance(metric, str) or operator not in OPERATORS or severity not in {"block", "warn"}:
            raise ValueError(f"rules[{index}] has invalid metric/operator/severity")
        if not isinstance(threshold, (int, float)) or not math.isfinite(float(threshold)):
            raise ValueError(f"rules[{index}].threshold must be finite numeric")
        actual = metrics.get(metric)
        if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
            passed = False
            reason = "metric missing or nonfinite"
        else:
            passed = bool(OPERATORS[operator](float(actual), float(threshold)))
            reason = "threshold satisfied" if passed else "threshold not satisfied"
        results.append(
            {
                "metric": metric,
                "operator": operator,
                "threshold": threshold,
                "actual": actual,
                "severity": severity,
                "passed": passed,
                "reason": reason,
            }
        )
    return {
        "schema": "llm-portfolio-regression-result-v1",
        "passed": not any(not item["passed"] and item["severity"] == "block" for item in results),
        "rules": results,
    }
