"""Metrics computed from every attempted decision, before any executor gate."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any


def percentile(values: Iterable[float], q: float) -> float | None:
    """Linear interpolation, including the endpoints; empty cohorts return None."""
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    ordered = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not ordered:
        return None
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def outcome(row: dict[str, Any]) -> dict[str, bool]:
    """Never upgrade a wrong model answer because a host rejected execution."""
    expected = row["expected"]
    predicted = row.get("prediction") or {}
    success = row.get("error") is None
    schema_valid = success and bool(predicted.get("schema_valid", True))
    selected = schema_valid and predicted.get("status") == "selected"
    executable = expected["status"] == "selected"
    correct = schema_valid and predicted.get("status") == expected["status"]
    if executable:
        correct = correct and predicted.get("candidate_id") == expected["candidate_id"]
    return {
        "correct": bool(correct),
        "selected": bool(selected),
        "executable": executable,
        "false_action": bool(selected and not correct),
        "rejected": bool(schema_valid and predicted.get("status") in {"no_match", "abstain"}),
        "abstained": bool(schema_valid and predicted.get("status") == "abstain"),
        "schema_valid": bool(schema_valid),
        "failed": not success,
    }


def summarize(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    counts = Counter()
    for row in rows:
        counts.update({key: int(value) for key, value in outcome(row).items()})
    n = len(rows)
    correct_actions = sum(outcome(row)["correct"] and outcome(row)["executable"] for row in rows)
    latencies = [row["wall_ms"] for row in rows if row.get("error") is None]
    failed_latencies = [row["wall_ms"] for row in rows if row.get("error") is not None]
    return {
        "attempts": n,
        "counts": dict(counts),
        "accuracy": counts["correct"] / n if n else None,
        "false_action_rate": counts["false_action"] / n if n else None,
        "false_action_rate_among_selections": counts["false_action"] / counts["selected"]
        if counts["selected"]
        else None,
        "rejection_rate": counts["rejected"] / n if n else None,
        "abstention_rate": counts["abstained"] / n if n else None,
        "executable_request_coverage": correct_actions / counts["executable"]
        if counts["executable"]
        else None,
        "selection_rate_on_executable_requests": sum(
            outcome(row)["selected"] and outcome(row)["executable"] for row in rows
        )
        / counts["executable"]
        if counts["executable"]
        else None,
        "schema_validity": counts["schema_valid"] / n if n else None,
        "latency_ms": {
            "successful_attempts": len(latencies),
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
        },
        "failure_latency_ms": {
            "attempts": len(failed_latencies),
            "p50": percentile(failed_latencies, 0.5),
            "p95": percentile(failed_latencies, 0.95),
        },
    }


def grouped_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[f"{row['mode']}/{row['condition']}"].append(row)
    return {key: summarize(value) for key, value in sorted(groups.items())}
