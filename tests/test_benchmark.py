"""Metric denominators and lifecycle protocol tests need no model or Metal."""

import json

import pytest

from benchmarks.common import load_fixtures, request_from_dict, sanitize
from benchmarks.metrics import grouped_summary, outcome, percentile, summarize
from benchmarks.run import attempt, exit_code, parity_attempt, run_summary
from jevkit_mlx import BackendOutput


def trial(expected="pause", predicted="pause", *, error=None, schema_valid=True, **extra):
    def result(value):
        return {
            "status": value if value in {"no_match", "abstain", "invalid"} else "selected",
            "candidate_id": value if value not in {"no_match", "abstain", "invalid"} else None,
        }

    return {
        "expected": result(expected),
        "prediction": {**result(predicted), "schema_valid": schema_valid},
        "error": error,
        "wall_ms": 10,
        **extra,
    }


def test_percentile_small_and_empty_cohorts():
    assert percentile([], 0.95) is None
    assert percentile([100], 0.95) == 100
    assert percentile([0, 10], 0.95) == 9.5
    assert percentile([float("nan"), 1], 0.5) == 1
    with pytest.raises(ValueError):
        percentile([1], 2)


def test_host_gate_does_not_turn_wrong_model_action_into_correct_answer():
    row = trial("no_match", "close", host_rejected=True)
    assert outcome(row)["false_action"]
    assert not outcome(row)["correct"]


def test_coverage_requires_correct_action_not_merely_any_selection():
    summary = summarize(
        [trial("pause", "close"), trial("pause", "pause"), trial("resume", "abstain")]
    )
    assert summary["executable_request_coverage"] == 1 / 3
    assert summary["selection_rate_on_executable_requests"] == 2 / 3
    assert summary["false_action_rate"] == 1 / 3


def test_failures_and_schema_invalid_outputs_stay_in_quality_denominator():
    rows = [trial(), trial(error={"message": "failed"}), trial(schema_valid=False)]
    summary = summarize(rows)
    assert summary["attempts"] == 3
    assert summary["accuracy"] == 1 / 3
    assert summary["schema_validity"] == 1 / 3
    assert summary["latency_ms"]["successful_attempts"] == 2
    assert summary["failure_latency_ms"]["attempts"] == 1


def test_no_match_and_abstain_distinct_but_neither_is_false_action():
    summary = summarize([trial("no_match", "abstain"), trial("abstain", "abstain")])
    assert summary["accuracy"] == 0.5
    assert summary["false_action_rate"] == 0
    assert summary["rejection_rate"] == 1
    assert summary["executable_request_coverage"] is None


def test_groups_keep_generation_and_cache_conditions_separate():
    rows = [trial(mode="direct", condition="kv_cold"), trial(mode="json", condition="page_update")]
    assert set(grouped_summary(rows)) == {"direct/kv_cold", "json/page_update"}


@pytest.mark.parametrize("split,count", [("dev", 16), ("test", 28)])
def test_frozen_fixture_integrity_and_executable_ground_truth(split, count):
    cases, manifest = load_fixtures(split)
    assert len(cases) == count
    assert manifest["test_frozen_before_inference"]
    for case in cases:
        request = request_from_dict(case["request"])
        previous = request_from_dict(case["previous_request"])
        assert request.state != previous.state
        if case["expected"]["status"] == "selected":
            assert case["expected"]["candidate_id"] in {
                candidate.id for candidate in request.candidates
            }
        else:
            assert case["expected"]["candidate_id"] is None


def test_split_ids_and_utterances_are_disjoint():
    dev, _ = load_fixtures("dev")
    test, _ = load_fixtures("test")
    assert not {case["id"] for case in dev} & {case["id"] for case in test}
    assert not {case["request"]["utterance"] for case in dev} & {
        case["request"]["utterance"] for case in test
    }


class RecordingBackend:
    """An explicit test double, never used by the benchmark command."""

    def __init__(self):
        self.calls = []
        self.fail = False

    def score(self, request, *, cache_key=None, use_cache=True):
        self.calls.append((request, cache_key, use_cache))
        if self.fail:
            raise RuntimeError("synthetic failure")
        return BackendOutput(
            raw_scores={"pause": 5.0, "__no_match__": 1.0, "__abstain__": 0.0},
            cache={"hit": use_cache},
        )

    def generate_baseline(self, request, *, mode, cache_key=None, use_cache=True):
        self.score(request, cache_key=cache_key, use_cache=use_cache)
        return {
            "candidate_id": "pause",
            "status": "selected",
            "schema_valid": True,
            "raw_text": "A" if mode == "code" else '{"candidate_id":"pause"}',
        }


class RecordingEngine:
    def __init__(self):
        self.backend = RecordingBackend()

    def decide(self, request, **kwargs):
        self.backend.score(request, **kwargs)
        return {"candidate_id": "pause", "status": "selected"}


@pytest.mark.parametrize("mode", ["direct", "code", "json"])
def test_kv_cold_disables_cache_without_warmup(mode):
    engine = RecordingEngine()
    case = load_fixtures("test")[0][0]
    row = attempt(engine, case, mode, "kv_cold", 0)
    assert row["error"] is None
    assert len(engine.backend.calls) == 1
    assert engine.backend.calls[0][2] is False
    assert row["preparation"] is None


def test_warm_state_uses_same_context_and_different_utterance():
    engine = RecordingEngine()
    case = load_fixtures("test")[0][0]
    row = attempt(engine, case, "direct", "same_page_new_utterance", 0)
    before, after = engine.backend.calls
    assert before[0].state == after[0].state
    assert before[0].utterance != after[0].utterance
    assert before[1] == after[1]
    assert before[2] and after[2]
    assert row["preparation"]["wall_ms"] >= 0


def test_page_update_reuses_namespace_but_changes_context_and_version():
    engine = RecordingEngine()
    case = load_fixtures("test")[0][0]
    attempt(engine, case, "json", "page_update", 0)
    before, after = engine.backend.calls
    assert before[0].state != after[0].state
    assert before[0].state_version != after[0].state_version
    assert before[1] == after[1]


def test_preparation_failures_are_recorded():
    engine = RecordingEngine()
    engine.backend.fail = True
    case = load_fixtures("test")[0][0]
    row = attempt(engine, case, "direct", "page_update", 0)
    assert row["error"]["phase"] == "preparation"
    assert row["prediction"] is None
    assert summarize([row])["accuracy"] == 0


def test_parity_runs_independent_fresh_warm_and_updated_calls():
    engine = RecordingEngine()
    case = load_fixtures("test")[0][0]
    result = parity_attempt(engine, case, atol=0.1, rtol=0.01)
    assert len(engine.backend.calls) == 5
    assert engine.backend.calls[0][2] is False
    assert result["same_page"]["allclose"]
    assert result["page_update"]["same_top_choice"]
    assert result["same_page"]["max_score_difference"] == 0
    assert result["passed"]


def test_parity_failure_cannot_exit_successfully_or_mark_pending_check_complete():
    rows = [trial(mode="direct", condition="kv_cold")]
    assert not run_summary(rows, 1, [], 1)["complete"]
    failed = [{"passed": False, "error": None}]
    summary = run_summary(rows, 1, failed, 1)
    assert summary["complete"]
    assert summary["parity"]["failed"] == 1
    assert exit_code(rows, failed) == 1
    assert exit_code(rows, [{"passed": True}]) == 0


def test_parity_top_choice_change_fails_even_with_small_logit_difference():
    engine = RecordingEngine()
    original = engine.backend.score

    def nearly_tied(request, **kwargs):
        value = original(request, **kwargs)
        raw = {"a": 1.01, "b": 1.0} if not kwargs.get("use_cache", True) else {"a": 1.0, "b": 1.01}
        return BackendOutput(raw_scores=raw, cache=value.cache)

    engine.backend.score = nearly_tied
    result = parity_attempt(engine, load_fixtures("test")[0][0], atol=0.5, rtol=0.0)
    assert result["same_page"]["allclose"]
    assert result["same_page"]["scores_close"]
    assert not result["same_page"]["same_top_choice"]
    assert not result["passed"]


def test_parity_exception_is_a_failed_check():
    engine = RecordingEngine()
    engine.backend.fail = True
    result = parity_attempt(engine, load_fixtures("test")[0][0], atol=0.5, rtol=0.0)
    assert result["error"]["type"] == "RuntimeError"
    assert not result["passed"]


def test_artifact_sanitization_scrubs_home_and_model_path(tmp_path):
    from pathlib import Path

    model = tmp_path / "fictional-model"
    value = {
        "model": str(model),
        "message": f"Failure at {Path.home()}/private/file",
        "items": [str(model)],
    }
    clean = sanitize(value, str(model))
    assert clean["model"] == "fictional-model"
    assert str(Path.home()) not in json.dumps(clean)
