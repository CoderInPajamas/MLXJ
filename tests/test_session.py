"""Execution authorization tests: the executor is not a semantic oracle."""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from jevkit_mlx import (
    ABSTAIN_ID,
    NO_MATCH_ID,
    BackendOutput,
    Candidate,
    DecisionSession,
    InvalidDecisionError,
    MLXDecisionEngine,
    ReplayDecisionError,
    StaleDecisionError,
)


class Backend:
    def __init__(self, *, started=None, proceed=None, winner="close"):
        self.started = started
        self.proceed = proceed
        self.winner = winner
        self.calls = []

    def score(self, request, *, cache_key=None, use_cache=True):
        self.calls.append((request, cache_key, use_cache))
        if self.started is not None:
            self.started.set()
            assert self.proceed.wait(3), "test did not release blocked inference"
        scores = {candidate.id: 0.0 for candidate in request.candidates}
        scores.update({NO_MATCH_ID: -1.0, ABSTAIN_ID: -2.0})
        scores[self.winner] = 5.0
        return BackendOutput(scores)


def session(backend=None, **kwargs):
    return DecisionSession(
        MLXDecisionEngine(backend=backend or Backend()),
        state={"window": "library", "visible": ["course-a"]},
        candidates=[Candidate("close", "Close the open course library")],
        **kwargs,
    )


def test_snapshot_and_state_are_defensive_copies():
    current = session()
    state = current.state
    state["visible"].clear()
    snapshot = current.snapshot()
    snapshot["state"]["visible"].clear()
    assert current.state["visible"] == ["course-a"]
    assert current.version == current.state_version == 0
    assert current.update_state({"window": "player"}, [Candidate("close", "Close the player")]) == 1
    assert current.candidates[0].description == "Close the player"
    with pytest.raises(ValueError):
        current.update_state({"bad": object()})
    assert current.version == 1
    assert current.state == {"window": "player"}


def test_session_uses_stable_cache_namespace_but_never_caches_answers():
    backend = Backend()
    current = session(backend)
    first = current.decide("Close it")
    second = current.decide("Close the library", use_cache=False)
    current.update_state({"window": "player"})
    third = current.decide("Close it")
    assert len(backend.calls) == 3
    assert len({call[1] for call in backend.calls}) == 1
    assert backend.calls[1][2] is False
    assert first.request_id != second.request_id != third.request_id
    assert [call[0].state_version for call in backend.calls] == [0, 0, 1]
    assert backend.calls[0][0].state["window"] == "library"
    assert backend.calls[2][0].state["window"] == "player"


def test_concurrent_page_update_marks_inflight_result_stale():
    started, proceed = threading.Event(), threading.Event()
    current = session(Backend(started=started, proceed=proceed))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(current.decide, "Close it")
        try:
            assert started.wait(2)
            current.update_state({"window": "player"}, [Candidate("close", "Close the player")])
        finally:
            proceed.set()
        result = future.result(timeout=2)
    assert result.status == "stale"
    assert result.candidate_id is None
    assert result.raw_selected_id == "close"
    assert result.state_version == 0
    called = []
    with pytest.raises(StaleDecisionError):
        current.execute(result, lambda candidate: called.append(candidate.id))
    assert called == []


def test_completed_decision_cannot_execute_after_state_change():
    current = session()
    result = current.decide("Close it")
    current.update_state({"window": None}, [])
    with pytest.raises(StaleDecisionError):
        current.execute(result, lambda candidate: pytest.fail("stale action executed"))


def test_execute_returns_receipt_once_and_does_not_claim_semantic_correctness():
    current = session()
    result = current.decide("This fake backend always closes")
    called = []
    receipt = current.execute(
        result, lambda candidate: called.append(candidate.id) or {"executed": candidate.id}
    )
    assert receipt == {"executed": "close"}
    with pytest.raises(ReplayDecisionError):
        current.execute(result, lambda candidate: called.append(candidate.id))
    assert called == ["close"]


def test_rejects_foreign_copied_and_modified_results():
    current = session()
    result = current.decide("Close it")
    foreign = session().decide("Close it")
    for forged in [foreign, replace(result), replace(result, candidate_id="invented")]:
        with pytest.raises(InvalidDecisionError):
            current.execute(forged, lambda candidate: pytest.fail("forged action executed"))
    result.scores["close"] = 0.0
    with pytest.raises(InvalidDecisionError, match="modified"):
        current.execute(result, lambda candidate: pytest.fail("modified result executed"))


@pytest.mark.parametrize("winner", [NO_MATCH_ID, ABSTAIN_ID])
def test_nonactions_are_never_executable(winner):
    current = session(Backend(winner=winner))
    result = current.decide("What happened?")
    with pytest.raises(InvalidDecisionError):
        current.execute(result, lambda candidate: pytest.fail("nonaction executed"))


def test_failed_callback_is_consumed_to_prevent_repeating_partial_effects():
    current = session()
    result = current.decide("Close it")

    def failing_action(candidate):
        raise RuntimeError("application action failed after a possible partial effect")

    with pytest.raises(RuntimeError, match="partial effect"):
        current.execute(result, failing_action)
    with pytest.raises(ReplayDecisionError):
        current.execute(result, lambda candidate: None)


def test_action_can_update_session_reentrantly():
    current = session()
    result = current.decide("Close it")

    def close(candidate):
        assert candidate.id == "close"
        new_version = current.update_state({"window": None}, [])
        return {"executed": True, "state_version": new_version}

    assert current.execute(result, close) == {"executed": True, "state_version": 1}
    assert current.candidates == ()


def test_update_cannot_interleave_with_action_callback():
    current = session()
    result = current.decide("Close it")
    entered, release, updater_ready = threading.Event(), threading.Event(), threading.Event()

    def apply(candidate):
        entered.set()
        assert release.wait(3)
        assert current.state_version == 0
        return candidate.id

    def update():
        updater_ready.set()
        return current.update_state({"window": "player"})

    with ThreadPoolExecutor(max_workers=2) as pool:
        action = pool.submit(current.execute, result, apply)
        try:
            assert entered.wait(2)
            updater = pool.submit(update)
            assert updater_ready.wait(2)
            assert not updater.done()
        finally:
            release.set()
        assert action.result(timeout=2) == "close"
        assert updater.result(timeout=2) == 1


def test_pending_authorizations_are_bounded():
    current = session()
    old = current.decide("Close it")
    newest = None
    for _ in range(256):
        newest = current.decide("Close it")
    with pytest.raises(InvalidDecisionError):
        current.execute(old, lambda candidate: pytest.fail("expired authorization executed"))
    assert current.execute(newest, lambda candidate: candidate.id) == "close"


def test_prewarm_reuses_namespace_and_does_not_issue_decisions():
    backend = Backend()
    observed = []

    def prewarm(request, *, cache_key=None):
        observed.append((request, cache_key))
        return {"cache": {"hit": False}, "total_ms": 1.0}

    backend.prewarm = prewarm
    current = session(backend)
    result = current.prewarm()
    current.decide("Close it")
    assert result == {
        "cache": {"hit": False},
        "total_ms": 1.0,
        "state_version": 0,
        "current_state_version": 0,
        "status": "ready",
    }
    assert observed[0][1] == backend.calls[0][1]
    assert observed[0][0].state == current.state


def test_prewarm_reports_a_concurrently_updated_snapshot_as_stale():
    backend = Backend()
    current = session(backend)

    def prewarm(request, *, cache_key=None):
        current.update_state({"window": "player"})
        return {"cache": {"hit": False}, "total_ms": 1.0}

    backend.prewarm = prewarm
    result = current.prewarm()
    assert result["status"] == "stale"
    assert result["state_version"] == 0
    assert result["current_state_version"] == 1


def test_prewarm_requires_backend_support():
    with pytest.raises(NotImplementedError):
        session().prewarm()
