"""Read-only report JSON: python -m scripts.summarize_extended RUN [RUN ...]."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from benchmarks.audit import audit_run
from benchmarks.common import FIXTURES, load_fixtures, sanitize
from benchmarks.metrics import outcome, summarize


def number_range(values):
    numbers = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    ]
    return {
        "min": min(numbers, default=None),
        "max": max(numbers, default=None),
        "observations": len(numbers),
    }


def choice_metrics(rows):
    result = summarize(rows)
    counts = result["counts"]
    return {
        "attempts": result["attempts"],
        "correct_choices": counts.get("correct", 0),
        "accuracy": result["accuracy"],
        "rejection_rate": result["rejection_rate"],
        "abstention_rate": result["abstention_rate"],
        "schema_validity": result["schema_validity"],
        "wrong_returned_choice_count": counts.get("false_action", 0),
        "wrong_returned_choice_rate": result["false_action_rate"],
        "raw_choice_accuracy": result["raw_choice_accuracy"],
        "raw_wrong_choice_count": counts.get("raw_false_action", 0),
        "raw_wrong_choice_rate": result["raw_false_action_rate"],
        "runtime_errors": counts.get("failed", 0),
        "schema_invalid_count": result["attempts"] - counts.get("schema_valid", 0),
        "latency_ms": result["latency_ms"],
        "failure_latency_ms": result["failure_latency_ms"],
    }


def enum_metrics(rows):
    metrics = choice_metrics(rows)
    decisions = [outcome(row) for row in rows]
    executable = sum(result["executable"] for result in decisions)
    correct_actions = sum(result["correct"] and result["executable"] for result in decisions)
    metrics.update(
        wrong_action_count=metrics["wrong_returned_choice_count"],
        wrong_action_rate=metrics["wrong_returned_choice_rate"],
        raw_wrong_action_count=metrics["raw_wrong_choice_count"],
        raw_wrong_action_rate=metrics["raw_wrong_choice_rate"],
        executable_requests=executable,
        correct_action_choices=correct_actions,
        executable_request_coverage=correct_actions / executable if executable else None,
    )
    return metrics


def memory_maxima(rows):
    def maximum(field):
        return number_range((row.get("memory") or {}).get(field) for row in rows)["max"]

    return {
        "process_peak_rss_bytes": maximum("process_peak_rss_bytes"),
        "mlx_peak_memory_bytes": maximum("peak_memory_bytes"),
        "mlx_active_memory_max_bytes": maximum("active_memory_bytes"),
        "mlx_allocator_cache_max_bytes": maximum("cache_memory_bytes"),
        "saved_prefix_cache_max_bytes": number_range(
            ((row.get("prediction") or {}).get("cache") or {}).get("bytes") for row in rows
        )["max"],
        "note": "Process-lifetime and allocator maxima, not independent per-call allocations; RSS and MLX memory overlap.",
    }


def input_ranges(rows):
    return {
        "prompt_tokens": number_range(
            ((row.get("prediction") or {}).get("cache") or {}).get("prompt_tokens") for row in rows
        ),
        "reused_tokens": number_range(
            ((row.get("prediction") or {}).get("cache") or {}).get("reused_tokens") for row in rows
        ),
        "candidate_count": number_range(row.get("candidate_count") for row in rows),
        "utterance_chars": number_range(row.get("utterance_chars") for row in rows),
        "state_chars": number_range(row.get("state_chars") for row in rows),
    }


def summarize_directory(directory, *, fixtures_dir=None, resolve_legacy_kind=False):
    directory = Path(directory)
    trial_data = (directory / "trials.jsonl").read_bytes()
    summary_data = (directory / "summary.json").read_bytes()
    metadata = json.loads((directory / "metadata.json").read_text())
    rows = [json.loads(line) for line in trial_data.splitlines() if line.strip()]
    original_summary = json.loads(summary_data)
    fixture_rows, manifest = load_fixtures(metadata.get("split", "test"), fixtures_dir)
    fixtures_verified = metadata.get("fixtures", {}).get("files") == manifest["files"]
    audit = audit_run(directory, fixtures_dir=fixtures_dir, require_complete=False)
    errors = list(audit["errors"])
    source_hash = hashlib.sha256(trial_data).hexdigest()
    if (
        source_hash != audit["source_trials_sha256"]
        or summary_data != (directory / "summary.json").read_bytes()
    ):
        errors.append("Run evidence changed during aggregation; retry after the run is stable")
    derived_rows, resolved = [], 0
    cases = {case["id"]: case for case in fixture_rows}
    for row in rows:
        derived = dict(row)
        if "kind" not in row and resolve_legacy_kind:
            case = cases.get(row["case_id"])
            if not fixtures_verified or case is None or row["expected"] != case["expected"]:
                errors.append(
                    f"{row['case_id']}: cannot resolve kind without exact verified fixture evidence"
                )
            else:
                derived["kind"] = case["request"].get("kind", "enum")
                resolved += 1
        derived_rows.append(derived)
    groups = defaultdict(list)
    for row in derived_rows:
        groups[f"{row['mode']}/{row['condition']}"].append(row)
    group_reports = {}
    for key, members in sorted(groups.items()):
        enums = [row for row in members if row.get("kind") == "enum"]
        booleans = [row for row in members if row.get("kind") == "boolean"]
        group_reports[key] = {
            "overall": choice_metrics(members),
            "enum": enum_metrics(enums),
            "boolean": choice_metrics(booleans),
            "unknown_kind_attempts": len(members) - len(enums) - len(booleans),
            "input_ranges": input_ranges(members),
            "memory_maxima": memory_maxima(members),
        }
    notes = [
        "No raw evidence was modified. Mode/condition groups are reported separately; repetitions are not independent quality cases.",
        "Wrong returned choices include enum and boolean choices. Wrong actions and executable coverage use enum rows only.",
        "Correct executable choices are model selections before any executor; this does not establish actual execution.",
        "Loaded-model decision latency excludes recorded preparation and loading. process_cold_start latency instead includes interpreter startup, loading, the first decision, and shutdown; it does not flush OS file caches.",
        "audit_passed refers to evidence integrity, not semantic accuracy or numerical parity acceptance; failure counts and parity outcomes are reported separately.",
    ]
    if resolved:
        notes.append(
            f"Resolved {resolved} missing legacy kinds from exact hash-verified fixtures in this derived report only."
        )
    elif not resolve_legacy_kind:
        notes.append(
            "Missing legacy kinds remain unknown; no fixture-based inference was requested."
        )
    return {
        "run_name": directory.name,
        "model_name": metadata.get("model_name"),
        "split": metadata.get("split"),
        "scope": metadata.get("scope"),
        "complete": bool(original_summary.get("complete")),
        "measurements_complete": original_summary.get(
            "measurements_complete", original_summary.get("complete", False)
        ),
        "attempts": len(rows),
        "planned": original_summary.get("planned"),
        "audit_passed": not errors,
        "errors": errors,
        "warnings": audit["warnings"],
        "source_trials_sha256": source_hash,
        "source_summary_sha256": hashlib.sha256(summary_data).hexdigest(),
        "fixture_files": manifest["files"],
        "fixture_hashes_verified": fixtures_verified,
        "kind_resolution": {"requested": resolve_legacy_kind, "resolved_rows": resolved},
        "groups": group_reports,
        "input_ranges": input_ranges(derived_rows),
        "memory_maxima": memory_maxima(derived_rows),
        "parity": audit["parity"],
        "cache_verification": audit["cache_verification"],
        "failure_counts": audit["failure_counts"],
        "environment": metadata.get("environment"),
        "supplementary_output_format_control": metadata.get("supplementary_output_format_control"),
        "notes": notes,
    }


def build_report(directories, *, fixtures_dir=None, resolve_legacy_kind=False):
    runs = []
    for directory in directories:
        try:
            runs.append(
                summarize_directory(
                    directory, fixtures_dir=fixtures_dir, resolve_legacy_kind=resolve_legacy_kind
                )
            )
        except (OSError, ValueError, TypeError, KeyError) as exc:
            runs.append(
                {
                    "run_name": Path(directory).name,
                    "complete": False,
                    "audit_passed": False,
                    "errors": [f"{type(exc).__name__}: {exc}"],
                }
            )
    return sanitize(
        {
            "schema_version": 1,
            "derivation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "metrics_source_sha256": hashlib.sha256(
                (FIXTURES.parent / "metrics.py").read_bytes()
            ).hexdigest(),
            "audit_source_sha256": hashlib.sha256(
                (FIXTURES.parent / "audit.py").read_bytes()
            ).hexdigest(),
            "complete": all(run["complete"] for run in runs),
            "audit_passed": all(run["audit_passed"] for run in runs),
            "runs": runs,
        }
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "runs", nargs="+", type=Path, help="Explicit run directories; no automatic discovery"
    )
    parser.add_argument(
        "--fixtures-dir", type=Path, help="Hash-verified original or extended fixture directory"
    )
    parser.add_argument(
        "--resolve-legacy-kind",
        action="store_true",
        help="Resolve missing kinds only from exact verified fixtures and label the derivation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New output file; defaults to stdout and never overwrites evidence",
    )
    args = parser.parse_args(argv)
    report = build_report(
        args.runs, fixtures_dir=args.fixtures_dir, resolve_legacy_kind=args.resolve_legacy_kind
    )
    serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(serialized, end="")
    else:
        try:
            with args.output.open("x") as stream:
                stream.write(serialized)
        except FileExistsError:
            parser.error("Output already exists; use a new derived report filename")
    return 0 if report["complete"] and report["audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
