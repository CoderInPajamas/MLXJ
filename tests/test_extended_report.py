import hashlib
import json

import pytest

from benchmarks.common import load_fixtures
from benchmarks.run import run_summary
from scripts.summarize_extended import build_report, main, summarize_directory


def make_run(tmp_path, *, kinds=True, complete=True):
    directory = tmp_path / "recorded-run"
    directory.mkdir()
    suite = tmp_path / "independent-suite"
    suite.mkdir()
    fixtures, _ = load_fixtures("test")
    cases = [fixtures[0], next(case for case in fixtures if case["request"]["kind"] == "boolean")]
    data = "".join(json.dumps(case) + "\n" for case in cases).encode()
    (suite / "test.jsonl").write_bytes(data)
    manifest = {"files": {"test.jsonl": {"rows": 2, "sha256": hashlib.sha256(data).hexdigest()}}}
    (suite / "manifest.json").write_text(json.dumps(manifest))
    rows = []
    for index, case in enumerate(cases, 1):
        selected = case["expected"]["candidate_id"] if index == 1 else "disable"
        row = {
            "case_id": case["id"],
            "mode": "direct",
            "condition": "kv_cold",
            "repeat": 0,
            "trial_index": index,
            "expected": case["expected"],
            "error": None,
            "wall_ms": index * 10,
            "candidate_count": len(case["request"]["candidates"]),
            "utterance_chars": len(case["request"]["utterance"]),
            "state_chars": 100,
            "preparation": None,
            "memory": {"process_peak_rss_bytes": index * 100, "peak_memory_bytes": index * 50},
            "prediction": {
                "candidate_id": selected,
                "raw_selected_id": selected,
                "status": "selected",
                "schema_valid": True,
                "cache": {
                    "scope": "cold",
                    "reused_tokens": 0,
                    "prompt_tokens": 300 + index,
                    "bytes": index * 20,
                },
            },
        }
        if kinds:
            row["kind"] = case["request"]["kind"]
        rows.append(row)
    metadata = {
        "model_name": "unit-test-double",
        "scope": "full",
        "split": "test",
        "fixtures": manifest,
        "modes": ["direct"],
        "conditions": ["kv_cold"],
        "repeats": 1,
        "case_count": 2,
    }
    summary = run_summary(rows, 2, [], 0)
    summary["complete"] = complete
    (directory / "metadata.json").write_text(json.dumps(metadata))
    (directory / "summary.json").write_text(json.dumps(summary))
    (directory / "trials.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return directory, suite


def test_boolean_error_is_separate_from_enum_action_rates_and_coverage(tmp_path):
    directory, suite = make_run(tmp_path)
    report = summarize_directory(directory, fixtures_dir=suite)
    group = report["groups"]["direct/kv_cold"]
    assert report["complete"] and report["audit_passed"]
    assert group["overall"]["accuracy"] == 0.5
    assert group["overall"]["wrong_returned_choice_count"] == 1
    assert group["enum"]["wrong_action_count"] == 0
    assert group["enum"]["correct_action_choices"] == 1
    assert group["enum"]["executable_request_coverage"] == 1
    assert group["boolean"]["wrong_returned_choice_count"] == 1
    assert group["boolean"]["accuracy"] == 0
    assert group["input_ranges"]["prompt_tokens"] == {"min": 301, "max": 302, "observations": 2}
    assert report["memory_maxima"]["process_peak_rss_bytes"] == 200
    assert report["memory_maxima"]["mlx_peak_memory_bytes"] == 100
    assert report["memory_maxima"]["saved_prefix_cache_max_bytes"] == 40
    assert report == summarize_directory(directory, fixtures_dir=suite)


def test_legacy_kind_stays_unknown_unless_verified_resolution_is_requested(tmp_path):
    directory, suite = make_run(tmp_path, kinds=False)
    evidence = (directory / "trials.jsonl").read_bytes()
    original = summarize_directory(directory, fixtures_dir=suite)
    assert original["groups"]["direct/kv_cold"]["unknown_kind_attempts"] == 2
    assert original["groups"]["direct/kv_cold"]["enum"]["attempts"] == 0
    resolved = summarize_directory(directory, fixtures_dir=suite, resolve_legacy_kind=True)
    assert resolved["groups"]["direct/kv_cold"]["enum"]["attempts"] == 1
    assert resolved["groups"]["direct/kv_cold"]["boolean"]["attempts"] == 1
    assert resolved["kind_resolution"]["resolved_rows"] == 2
    assert any("hash-verified" in note for note in resolved["notes"])
    assert resolved["source_trials_sha256"] == hashlib.sha256(evidence).hexdigest()
    assert (directory / "trials.jsonl").read_bytes() == evidence


def test_changed_fixture_refuses_report_derivation_and_wrong_suite_is_not_guessed(tmp_path):
    directory, suite = make_run(tmp_path, kinds=False)
    wrong_suite = build_report([directory], resolve_legacy_kind=True)
    assert not wrong_suite["audit_passed"]
    assert wrong_suite["runs"][0]["kind_resolution"]["resolved_rows"] == 0
    with (suite / "test.jsonl").open("a") as stream:
        stream.write("\n")
    changed = build_report([directory], fixtures_dir=suite)
    assert not changed["audit_passed"]
    assert "hash mismatch" in changed["runs"][0]["errors"][0]


def test_incomplete_runs_remain_incomplete_and_output_cannot_overwrite_evidence(tmp_path):
    directory, suite = make_run(tmp_path, complete=False)
    evidence = (directory / "summary.json").read_bytes()
    report = build_report([directory], fixtures_dir=suite)
    assert not report["complete"]
    assert report["runs"][0]["warnings"]
    output = tmp_path / "report.json"
    assert main([str(directory), "--fixtures-dir", str(suite), "--output", str(output)]) == 1
    with pytest.raises(SystemExit):
        main(
            [
                str(directory),
                "--fixtures-dir",
                str(suite),
                "--output",
                str(directory / "summary.json"),
            ]
        )
    assert (directory / "summary.json").read_bytes() == evidence


def test_original_fixture_suite_can_resolve_matching_legacy_records(tmp_path):
    directory, _ = make_run(tmp_path, kinds=False)
    metadata_path = directory / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["fixtures"] = load_fixtures("test")[1]
    # Omit schedule metadata: these explicitly selected rows are a historical subset.
    for key in ("modes", "conditions", "case_count", "repeats"):
        metadata.pop(key)
    metadata_path.write_text(json.dumps(metadata))
    report = summarize_directory(directory, resolve_legacy_kind=True)
    assert report["fixture_hashes_verified"]
    assert report["audit_passed"]
    assert report["kind_resolution"]["resolved_rows"] == 2
