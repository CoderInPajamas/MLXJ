"""Contract tests exercise validation and scoring without importing MLX."""

import math

import pytest

from jev_mlx import (
    ABSTAIN_ID,
    NO_MATCH_ID,
    BackendOutput,
    Candidate,
    DecisionRequest,
    MLXDecisionEngine,
    boolean_request,
)


class ScoresBackend:
    def __init__(self, scores=None):
        self.scores = scores or {"open": 3.0, "close": 1.0, NO_MATCH_ID: 0.0, ABSTAIN_ID: -1.0}
        self.calls = []

    def score(self, request, *, cache_key=None, use_cache=True):
        self.calls.append((request, cache_key, use_cache))
        return BackendOutput(
            self.scores,
            model={"id": "synthetic-unit-test-backend"},
            timing={"inference_ms": 1.0},
            cache={"hit": False},
        )


def request(**changes):
    fields = {
        "state": {"window": "library"},
        "utterance": "Open the library",
        "candidates": (
            Candidate("open", "Open the course library"),
            Candidate("close", "Close the library"),
        ),
        "state_version": 7,
    }
    fields.update(changes)
    return DecisionRequest(**fields)


def test_contract_roundtrip_and_input_isolation():
    source = {"visible": ["course-a"]}
    value = {"route": ["library"]}
    candidate = Candidate("open", "Open the course library", value)
    original = request(state=source, candidates=[candidate])
    source["visible"].append("course-b")
    value["route"].append("unexpected")
    candidate.value["route"].append("mutated-candidate")
    assert original.state == {"visible": ["course-a"]}
    assert original.candidates[0].value == {"route": ["library"]}
    assert DecisionRequest.from_dict(original.to_dict()) == original
    exported = original.to_dict()
    exported["state"]["visible"].clear()
    assert original.state["visible"] == ["course-a"]


@pytest.mark.parametrize("candidate_id", ["", " ", NO_MATCH_ID, ABSTAIN_ID, "bad\nid", "x" * 129])
def test_rejects_unsafe_or_ambiguous_candidate_ids(candidate_id):
    with pytest.raises(ValueError):
        Candidate(candidate_id, "An action")


@pytest.mark.parametrize(
    "changes",
    [
        {"candidates": (Candidate("same", "One"), Candidate("same", "Two"))},
        {"candidates": tuple(Candidate(str(i), "An action") for i in range(65))},
        {"candidates": [{"id": "open", "description": "Open"}]},
        {"state": []},
        {"state": {1: "not a string key"}},
        {"state": {"bad": float("nan")}},
        {"state": {"bad": float("inf")}},
        {"state": {"bad": object()}},
        {"state": {"too_large": "x" * 131_072}},
        {"state_version": -1},
        {"state_version": True},
        {"state_version": 1.1},
        {"utterance": ""},
        {"utterance": "x" * 16_385},
        {"utterance": "null\x00text"},
        {"question": ""},
        {"kind": "arbitrary-tool-call"},
    ],
)
def test_rejects_invalid_requests(changes):
    with pytest.raises(ValueError):
        request(**changes)


def test_rejects_deep_or_cyclic_state():
    deep = {}
    for _ in range(18):
        deep = {"child": deep}
    cyclic = {}
    cyclic["self"] = cyclic
    for state in (deep, cyclic):
        with pytest.raises(ValueError, match="nesting"):
            request(state=state)


@pytest.mark.parametrize(
    "data",
    [
        {"state": {}, "utterance": "Open", "candidates": [], "unexpected": True},
        {"utterance": "Open", "candidates": []},
        {"state": {}, "utterance": "Open", "candidates": {"a": "b"}},
        {"state": {}, "utterance": "Open", "candidates": [{"id": "a"}]},
        {
            "state": {},
            "utterance": "Open",
            "candidates": [{"id": "a", "description": "A", "execute": True}],
        },
    ],
)
def test_strict_json_request_parser(data):
    with pytest.raises(ValueError):
        DecisionRequest.from_dict(data)


def test_boolean_contract_preserves_typed_values():
    item = boolean_request(
        state={"player": "paused"}, utterance="Is playback paused?", question="Is playback paused?"
    )
    assert item.kind == "boolean"
    assert item.candidates[0].value is True
    assert item.candidates[1].value is False
    assert DecisionRequest.from_dict(item.to_dict()) == item
    with pytest.raises(ValueError, match="boolean requests"):
        request(kind="boolean")
    with pytest.raises(ValueError, match="boolean requests"):
        request(kind="boolean", candidates=(Candidate("yes", "Yes", 1), Candidate("no", "No", 0)))
    backend = ScoresBackend({"true": 0.0, "false": 3.0, NO_MATCH_ID: -1.0, ABSTAIN_ID: -2.0})
    result = MLXDecisionEngine(backend=backend).decide(item)
    assert result.selected_value is False
    assert result.to_dict()["selected_value"] is False


def test_model_identity_is_a_defensive_copy():
    backend = ScoresBackend()
    backend.identity = {"id": "fake", "quantization": {"bits": 4}}
    engine = MLXDecisionEngine(backend=backend)
    assert engine.model_identity == backend.identity
    engine.model_identity["quantization"]["bits"] = 2
    assert backend.identity["quantization"]["bits"] == 4


def test_selection_reports_uncalibrated_scores_metadata_and_margin():
    backend = ScoresBackend()
    result = MLXDecisionEngine(backend=backend).decide(request(), cache_key="page", use_cache=False)
    assert result.candidate_id == result.raw_selected_id == "open"
    assert result.status == "selected"
    assert result.margin == 2.0
    assert result.state_version == 7
    assert result.raw_scores == backend.scores
    assert sum(result.scores.values()) == pytest.approx(1.0)
    assert result.scores["open"] > result.scores["close"]
    assert result.model["id"] == "synthetic-unit-test-backend"
    assert result.timing["decision_ms"] >= 0
    assert result.timing["inference_ms"] == 1.0
    assert backend.calls[0][1:] == ("page", False)
    assert "probability" not in result.to_dict()
    exported = result.to_dict()
    exported["scores"]["open"] = -100
    assert result.scores["open"] > 0


@pytest.mark.parametrize("sentinel,status", [(NO_MATCH_ID, "no_match"), (ABSTAIN_ID, "abstain")])
def test_sentinel_selection_never_authorizes_an_action(sentinel, status):
    scores = {"open": 1.0, "close": 0.0, NO_MATCH_ID: -1.0, ABSTAIN_ID: -2.0}
    scores[sentinel] = 5.0
    result = MLXDecisionEngine(backend=ScoresBackend(scores)).decide(request())
    assert result.status == status
    assert result.candidate_id is None
    assert result.raw_selected_id == sentinel


def test_threshold_and_exact_tie_abstain_without_overwriting_raw_selection():
    scores = {"open": 2.0, "close": 1.9, NO_MATCH_ID: 0.0, ABSTAIN_ID: -1.0}
    result = MLXDecisionEngine(backend=ScoresBackend(scores), margin_threshold=0.2).decide(
        request()
    )
    assert result.status == "abstain"
    assert result.candidate_id is None
    assert result.raw_selected_id == "open"
    scores["close"] = 2.0
    result = MLXDecisionEngine(backend=ScoresBackend(scores)).decide(request())
    assert result.status == "abstain"
    assert result.margin == 0


def test_numerically_stable_restricted_softmax():
    scores = {"open": 10000.0, "close": 9999.0, NO_MATCH_ID: -10000.0, ABSTAIN_ID: -9999.0}
    result = MLXDecisionEngine(backend=ScoresBackend(scores)).decide(request())
    assert all(math.isfinite(score) for score in result.scores.values())
    assert result.scores["open"] == pytest.approx(1 / (1 + math.exp(-1)))


def test_empty_candidates_can_still_report_no_match():
    backend = ScoresBackend({NO_MATCH_ID: 3.0, ABSTAIN_ID: 1.0})
    result = MLXDecisionEngine(backend=backend).decide(request(candidates=()))
    assert result.status == "no_match"


@pytest.mark.parametrize(
    "scores",
    [
        {"open": 3.0, "close": 1.0},
        {"open": 3.0, "close": 1.0, NO_MATCH_ID: 0, ABSTAIN_ID: 0, "invented": 99},
        {"open": float("nan"), "close": 1.0, NO_MATCH_ID: 0, ABSTAIN_ID: 0},
        {"open": float("inf"), "close": 1.0, NO_MATCH_ID: 0, ABSTAIN_ID: 0},
        {"open": True, "close": 1.0, NO_MATCH_ID: 0, ABSTAIN_ID: 0},
    ],
)
def test_rejects_invalid_backend_scores(scores):
    with pytest.raises(ValueError, match="backend scores"):
        MLXDecisionEngine(backend=ScoresBackend(scores)).decide(request())


@pytest.mark.parametrize("threshold", [-1, float("nan"), float("inf"), True, "0"])
def test_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="margin_threshold"):
        MLXDecisionEngine(backend=ScoresBackend(), margin_threshold=threshold)


def test_injected_backend_is_unambiguous_and_model_loading_is_lazy():
    with pytest.raises(ValueError, match="model path"):
        MLXDecisionEngine()
    with pytest.raises(ValueError, match="either"):
        MLXDecisionEngine("unused-path", backend=ScoresBackend())
    with pytest.raises(TypeError, match="DecisionRequest"):
        MLXDecisionEngine(backend=ScoresBackend()).decide({})
