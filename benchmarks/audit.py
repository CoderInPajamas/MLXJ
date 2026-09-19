"""Read-only audit of recorded benchmark evidence and reviewed public copies."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from .common import load_fixtures
from .metrics import grouped_summary, outcome

EVIDENCE_FILES = ("metadata.json", "summary.json", "trials.jsonl", "parity.jsonl")


def _subset_differences(recorded, calculated, path="summary"):
    """Older immutable summaries may omit subsequently added raw-choice metrics."""
    if isinstance(recorded, dict):
        errors = []
        for key, value in recorded.items():
            if not isinstance(calculated, dict) or key not in calculated:
                errors.append(f"{path}.{key}: missing recomputed field")
            else:
                errors.extend(_subset_differences(value, calculated[key], f"{path}.{key}"))
        return errors
    return [] if recorded == calculated else [f"{path}: recorded value differs from trials"]


def audit_run(
    directory: Path,
    *,
    public: Path | None = None,
    source_revision: str | None = None,
    require_complete: bool = True,
) -> dict:
    data = (directory / "trials.jsonl").read_bytes()
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    metadata = json.loads((directory / "metadata.json").read_text())
    summary = json.loads((directory / "summary.json").read_text())
    errors, warnings = [], []
    if not summary.get("complete"):
        (errors if require_complete else warnings).append(
            "Run is incomplete; no complete-release claim is supported"
        )
    if summary.get("completed") != len(rows):
        errors.append("Recorded trial count differs from summary.completed")
    if [row.get("trial_index") for row in rows] != list(range(1, len(rows) + 1)):
        errors.append("Trial indices are not consecutive and unique")
    keys = [(row["case_id"], row["mode"], row["condition"], row["repeat"]) for row in rows]
    if len(set(keys)) != len(keys):
        errors.append("Duplicate case/mode/condition/repeat trial")
    fixtures, manifest = load_fixtures(metadata.get("split", "test"))
    expected_cases = {case["id"]: case for case in fixtures}
    if metadata.get("fixtures", {}).get("files") != manifest["files"]:
        errors.append("Recorded fixture hashes differ from the frozen public manifest")
    for row in rows:
        case = expected_cases.get(row["case_id"])
        if case is None or row["expected"] != case["expected"]:
            errors.append(f"{row['case_id']}: ground truth differs from frozen fixture")
    if all(field in metadata for field in ("modes", "conditions", "case_count", "repeats")):
        fixture_ids = [case["id"] for case in fixtures[: metadata["case_count"]]]
        scheduled = {
            (case_id, mode, condition, repeat)
            for case_id in fixture_ids
            for mode in metadata["modes"]
            for condition in metadata["conditions"]
            for repeat in range(metadata["repeats"])
        }
        if summary.get("planned") != len(scheduled):
            errors.append("Planned trial count differs from metadata schedule")
        if set(keys) - scheduled or (
            summary.get("measurements_complete", summary.get("complete")) and set(keys) != scheduled
        ):
            errors.append("Measured trials do not match the declared schedule")
    groups = grouped_summary(rows)
    errors.extend(_subset_differences(summary.get("groups", {}), groups))
    cache_counts = Counter()
    failure_counts = Counter()
    for row in rows:
        result = row.get("prediction") or {}
        preparation = row.get("preparation")
        condition = row["condition"]
        cache = result.get("cache") or {}
        valid = outcome(row)
        failure_counts["runtime_errors"] += bool(row.get("error"))
        failure_counts["schema_invalid"] += not valid["schema_valid"]
        failure_counts["raw_false_actions"] += valid["raw_false_action"]
        failure_counts["returned_false_actions"] += valid["false_action"]
        if not row.get("error") and not valid["schema_valid"] and "raw_text" not in result:
            errors.append(f"{row['trial_index']}: invalid generation has no retained raw text")
        if condition == "kv_cold":
            if preparation is not None:
                errors.append(f"{row['trial_index']}: cold-KV trial contains preparation")
            if result and (cache.get("scope") != "cold" or cache.get("reused_tokens") != 0):
                errors.append(f"{row['trial_index']}: cold-KV trial reused a prefix")
        elif condition in ("same_page_new_utterance", "page_update"):
            if preparation is None or "wall_ms" not in preparation:
                errors.append(
                    f"{row['trial_index']}: cache cohort has no recorded preparation cost"
                )
            if result:
                expected_scope = "state" if condition == "same_page_new_utterance" else "prefix"
                reused = cache.get("reused_tokens", 0)
                actual_hit = cache.get("scope") == expected_scope and 0 < reused < cache.get(
                    "prompt_tokens", 0
                )
                if condition == "same_page_new_utterance":
                    actual_hit = actual_hit and reused == cache.get("state_tokens")
                else:
                    actual_hit = actual_hit and reused < cache.get("state_tokens", 0)
                cache_counts[f"{condition}/attempts"] += 1
                cache_counts[f"{condition}/verified_hits"] += actual_hit
                if not actual_hit:
                    errors.append(
                        f"{row['trial_index']}: declared {condition} cohort did not reuse its expected prefix"
                    )
    parity_rows = []
    if (directory / "parity.jsonl").exists():
        parity_rows = [
            json.loads(line)
            for line in (directory / "parity.jsonl").read_text().splitlines()
            if line.strip()
        ]
        for row in parity_rows:
            if not row.get("passed"):
                warnings.append(f"{row['case_id']}: numerical parity failed (retained in evidence)")
            for label, scope in (("same_page", "state"), ("page_update", "prefix")):
                cache = (row.get(label) or {}).get("cache") or {}
                if not row.get("error") and (
                    cache.get("scope") != scope or cache.get("reused_tokens", 0) <= 0
                ):
                    errors.append(
                        f"{row['case_id']}: parity {label} comparison did not hit its expected cache"
                    )
        if summary.get("parity", {}).get("completed") != len(parity_rows):
            errors.append("Parity row count differs from summary")
    copy_checks = {}
    if public is not None:
        for name in EVIDENCE_FILES:
            original, target = directory / name, public / name
            if original.exists():
                matches = target.exists() and original.read_bytes() == target.read_bytes()
                copy_checks[name] = {
                    "identical": matches,
                    "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                }
                if not matches:
                    errors.append(f"Public {name} is missing or differs from original evidence")
        for derived in public.glob("*metrics.json"):
            report = json.loads(derived.read_text())
            if report.get("source_trials_sha256") != hashlib.sha256(data).hexdigest():
                errors.append(f"Derived {derived.name} refers to different trial evidence")
            errors.extend(_subset_differences(report.get("groups", {}), groups, derived.name))
            # A report recomputed after parity finishes can legitimately differ
            # from an earlier local derivative; it is not an evidence copy.
    source_checks = {}
    if source_revision:
        recorded_hashes = metadata.get("environment", {}).get("source_sha256", {})
        if not recorded_hashes:
            errors.append(
                "No recorded source hashes are available to verify the requested revision"
            )
        for path, digest in recorded_hashes.items():
            result = subprocess.run(
                ["git", "show", f"{source_revision}:{path}"], capture_output=True, check=False
            )
            match = result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == digest
            source_checks[path] = match
            if not match:
                errors.append(f"{path}: recorded source hash differs from {source_revision}")
    return {
        "passed": not errors,
        "complete": bool(summary.get("complete")),
        "attempts": len(rows),
        "planned": summary.get("planned"),
        "source_trials_sha256": hashlib.sha256(data).hexdigest(),
        "errors": errors,
        "warnings": warnings,
        "failure_counts": dict(failure_counts),
        "cache_verification": dict(cache_counts),
        "parity": {
            "attempts": len(parity_rows),
            "passed": sum(row.get("passed", False) for row in parity_rows),
        },
        "public_evidence": copy_checks,
        "source_revision": source_revision,
        "source_hash_matches": source_checks,
        "groups": groups,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--public", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    report = audit_run(
        args.run_directory,
        public=args.public,
        source_revision=args.source_revision,
        require_complete=not args.allow_incomplete,
    )
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
