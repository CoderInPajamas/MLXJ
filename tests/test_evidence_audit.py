import hashlib
import json
import shutil

import pytest

from benchmarks.audit import audit_run
from benchmarks.common import load_fixtures
from benchmarks.metrics import grouped_summary
from benchmarks.recompute import recompute


def make_run(directory, condition="kv_cold"):
    directory.mkdir()
    cases, manifest = load_fixtures("test")
    case = cases[0]
    cache = {"scope": "cold", "reused_tokens": 0, "prompt_tokens": 30, "state_tokens": 20}
    if condition == "same_page_new_utterance":
        cache.update(scope="state", reused_tokens=20)
    row = {
        "case_id": case["id"],
        "mode": "direct",
        "condition": condition,
        "repeat": 0,
        "trial_index": 1,
        "expected": case["expected"],
        "error": None,
        "wall_ms": 10,
        "preparation": None if condition == "kv_cold" else {"wall_ms": 20},
        "prediction": {
            "candidate_id": "close_player",
            "raw_selected_id": "close_player",
            "status": "selected",
            "schema_valid": True,
            "cache": cache,
        },
    }
    metadata = {
        "split": "test",
        "fixtures": manifest,
        "modes": ["direct"],
        "conditions": [condition],
        "case_count": 1,
        "repeats": 1,
    }
    summary = {"completed": 1, "planned": 1, "complete": True, "groups": grouped_summary([row])}
    (directory / "metadata.json").write_text(json.dumps(metadata))
    (directory / "trials.jsonl").write_text(json.dumps(row) + "\n")
    (directory / "summary.json").write_text(json.dumps(summary))
    return row, summary


def test_public_evidence_requires_identical_original_bytes(tmp_path):
    original, public = tmp_path / "original", tmp_path / "public"
    make_run(original)
    shutil.copytree(original, public)
    assert audit_run(original, public=public)["passed"]
    with (public / "trials.jsonl").open("a") as stream:
        stream.write("\n")
    report = audit_run(original, public=public)
    assert not report["passed"]
    assert any("differs from original evidence" in error for error in report["errors"])


def test_inflated_summary_is_detected_from_raw_trials(tmp_path):
    original = tmp_path / "original"
    _, summary = make_run(original)
    summary["groups"]["direct/kv_cold"]["accuracy"] = 0.5
    (original / "summary.json").write_text(json.dumps(summary))
    report = audit_run(original)
    assert not report["passed"]
    assert any("accuracy" in error for error in report["errors"])


def test_declared_warm_cache_must_have_actual_state_prefix_reuse(tmp_path):
    original = tmp_path / "original"
    row, _ = make_run(original, "same_page_new_utterance")
    assert audit_run(original)["passed"]
    row["prediction"]["cache"].update(scope="cold", reused_tokens=0)
    (original / "trials.jsonl").write_text(json.dumps(row) + "\n")
    report = audit_run(original)
    assert not report["passed"]
    assert report["cache_verification"]["same_page_new_utterance/verified_hits"] == 0


def test_derived_metrics_may_be_recomputed_without_replacing_original_evidence(tmp_path):
    original, public = tmp_path / "original", tmp_path / "public"
    make_run(original)
    shutil.copytree(original, public)
    derived = recompute(original)
    (public / "raw-metrics.json").write_text(json.dumps(derived))
    assert audit_run(original, public=public)["passed"]
    derived["source_trials_sha256"] = "wrong hash"
    (public / "raw-metrics.json").write_text(json.dumps(derived))
    assert not audit_run(original, public=public)["passed"]


def test_incomplete_run_cannot_pass_release_audit(tmp_path):
    original = tmp_path / "original"
    _, summary = make_run(original)
    summary["complete"] = False
    (original / "summary.json").write_text(json.dumps(summary))
    assert not audit_run(original)["passed"]
    assert audit_run(original, require_complete=False)["passed"]


def test_separate_frozen_suite_is_audited_against_its_own_ground_truth(tmp_path):
    original = tmp_path / "run"
    row, _ = make_run(original)
    case = load_fixtures("test")[0][0]
    case["id"] = "independent-suite-case"
    suite = tmp_path / "suite"
    suite.mkdir()
    data = (json.dumps(case) + "\n").encode()
    (suite / "test.jsonl").write_bytes(data)
    manifest = {"files": {"test.jsonl": {"sha256": hashlib.sha256(data).hexdigest(), "rows": 1}}}
    (suite / "manifest.json").write_text(json.dumps(manifest))
    row["case_id"] = case["id"]
    (original / "trials.jsonl").write_text(json.dumps(row) + "\n")
    metadata_path = original / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["fixtures"] = manifest
    metadata_path.write_text(json.dumps(metadata))
    assert not audit_run(original)["passed"]
    assert audit_run(original, fixtures_dir=suite)["passed"]
    # A changed utterance must invalidate the frozen suite before it can be used.
    case["request"]["utterance"] = "Different request after the freeze"
    (suite / "test.jsonl").write_text(json.dumps(case) + "\n")
    with pytest.raises(ValueError, match="Frozen fixture hash mismatch"):
        audit_run(original, fixtures_dir=suite)
