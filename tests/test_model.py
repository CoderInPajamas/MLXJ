"""Opt-in numerical invariants; semantic quality belongs in the frozen evaluation."""

import os
from dataclasses import replace

import pytest

from jev_mlx import Candidate, DecisionRequest, MLXDecisionEngine
from jev_mlx.prompt import prepare_prompt

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


def test_real_cache_parity_beyond_1024_token_prefix(real_engine, record_property):
    """Exercise a complete snapshot after Gemma 4's 1,024-token window wraps.

    This remains an opt-in numerical test on other checkpoints too. The synthetic
    reference text is shared by both pages; the changed visible order follows it,
    so reusing an arbitrary common prefix would be a different cache boundary.
    """
    engine = real_engine
    candidates = (
        Candidate("play_amber", "Play the visible course Amber Maps"),
        Candidate("play_cloud", "Play the visible course Cloud Songs"),
        Candidate("close_library", "Close the course library"),
    )
    reference = "Amber glass, moss paper, quiet rivers, and silver leaves. "
    request = DecisionRequest(
        state={
            "archive_reference": "",
            "view": "library",
            "visible_titles": ["Amber Maps", "Cloud Songs"],
        },
        utterance="Play the first one",
        candidates=candidates,
        state_version=0,
    )
    # Choose a token-length boundary, rather than assuming every tokenizer splits
    # this text alike. More than 1,536 cached tokens ensures a window has rotated.
    prompt = prepare_prompt(engine.backend.tokenizer, request)
    while len(prompt.state_tokens) <= 1536:
        request = replace(
            request,
            state={
                **request.state,
                "archive_reference": request.state["archive_reference"] + reference * 16,
            },
        )
        prompt = prepare_prompt(engine.backend.tokenizer, request)
    assert len(prompt.tokens) < engine.backend.max_prompt_tokens
    record_property("long_prefix_tokens", len(prompt.state_tokens))

    engine.backend.clear_cache()
    key = "long-prefix-parity"
    engine.decide(replace(request, utterance="Close the course library"), cache_key=key)
    same_page = engine.decide(request, cache_key=key)
    fresh_same_page = engine.decide(request, use_cache=False)
    assert same_page.cache["scope"] == "state"
    assert same_page.cache["reused_tokens"] > 1536
    assert same_page.cache["prefill_tokens"] > 0

    updated_request = replace(
        request,
        state={**request.state, "visible_titles": ["Cloud Songs", "Amber Maps"]},
        state_version=1,
    )
    updated_page = engine.decide(updated_request, cache_key=key)
    fresh_updated_page = engine.decide(updated_request, use_cache=False)
    assert updated_page.cache["scope"] == "prefix"
    assert updated_page.cache["reused_tokens"] == updated_page.cache["system_tokens"]
    assert updated_page.cache["state_tokens"] > 1536

    for condition, cached, fresh in (
        ("same_page", same_page, fresh_same_page),
        ("page_update", updated_page, fresh_updated_page),
    ):
        assert cached.raw_selected_id == fresh.raw_selected_id, condition
        logit_delta = max(
            abs(cached.raw_scores[k] - fresh.raw_scores[k]) for k in cached.raw_scores
        )
        score_delta = max(abs(cached.scores[k] - fresh.scores[k]) for k in cached.scores)
        record_property(f"{condition}_max_logit_difference", logit_delta)
        record_property(f"{condition}_max_score_difference", score_delta)
        assert logit_delta <= 0.5, (condition, logit_delta)
        assert score_delta <= 0.1, (condition, score_delta)
