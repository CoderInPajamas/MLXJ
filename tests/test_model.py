"""Opt-in numerical invariants; semantic quality belongs in the frozen evaluation."""

import os

import pytest

from jev_mlx import Candidate, DecisionRequest, MLXDecisionEngine

pytestmark = pytest.mark.model


@pytest.fixture(scope="module")
def real_engine():
    model = os.environ.get("JEV_TEST_MODEL")
    if not model:
        pytest.skip("set JEV_TEST_MODEL to a local checkpoint for real Metal tests")
    return MLXDecisionEngine(model)


def test_real_cache_parity_and_changed_middle(real_engine):
    engine = real_engine
    requests = [
        DecisionRequest(
            {"view": "notes", "focused_window": "notes"},
            "Close it",
            (Candidate("close_notes", "Close the currently open notes window"),),
        ),
        DecisionRequest(
            {"view": "library", "visible_titles": ["Amber Maps", "Cloud Songs"]},
            "Play the first one",
            (Candidate("amber", "Play Amber Maps"), Candidate("cloud", "Play Cloud Songs")),
        ),
        DecisionRequest(
            {"view": "library", "visible_titles": ["Cloud Songs", "Amber Maps"]},
            "Play the first one",
            (Candidate("amber", "Play Amber Maps"), Candidate("cloud", "Play Cloud Songs")),
        ),
    ]
    for request in requests:
        cached = engine.decide(request, cache_key="parity")
        again = engine.decide(request, cache_key="parity")
        fresh = engine.decide(request, use_cache=False)
        assert again.cache["scope"] == "state"
        assert again.cache["prefill_tokens"] > 0
        for result in (cached, again):
            assert result.raw_selected_id == fresh.raw_selected_id
            assert (
                max(abs(result.raw_scores[k] - fresh.raw_scores[k]) for k in result.raw_scores)
                <= 0.5
            )
            assert max(abs(result.scores[k] - fresh.scores[k]) for k in result.scores) <= 0.1


def test_real_scores_and_generation_baselines(real_engine):
    request = DecisionRequest(
        {"open_window": "notes"},
        "Close it",
        (Candidate("close_notes", "Close the currently open notes window"),),
    )
    result = real_engine.decide(request)
    assert result.candidate_id == "close_notes"
    assert result.model["dependencies"]["mlx-lm"] == "0.31.3"
    for mode in ("code", "json", "json_code"):
        output = real_engine.backend.generate_baseline(request, mode=mode)
        # An unconstrained model can emit invalid JSON/codes. That is measured as
        # a quality failure by the benchmark, not a broken inference contract.
        assert isinstance(output["raw_text"], str)
        assert output["generation_tokens"] > 0
        assert output["schema_valid"] is (output["status"] != "invalid")
        if output["status"] == "selected":
            assert output["candidate_id"] == "close_notes"
        else:
            assert output["candidate_id"] is None
        assert output["timing"]["total_ms"] > 0
