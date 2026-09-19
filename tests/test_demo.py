"""Executor/state tests with explicitly fake scores; these prove no model quality."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from jevkit_mlx.demo import DemoController, DemoError, Desktop
from jevkit_mlx.engine import MLXDecisionEngine
from jevkit_mlx.session import StaleDecisionError
from jevkit_mlx.types import ABSTAIN_ID, NO_MATCH_ID, BackendOutput


class StubBackend:
    def __init__(self, choice="open.library"):
        self.identity = {"name": "test-only fake scoring backend"}
        self.choice = choice
        self.requests = []
        self.started = None
        self.release = None

    def score(self, request, **kwargs):
        self.requests.append(request)
        if self.started:
            self.started.set()
            assert self.release.wait(4)
        ids = [c.id for c in request.candidates] + [NO_MATCH_ID, ABSTAIN_ID]
        return BackendOutput(
            {key: 6.0 if key == self.choice else 0.0 for key in ids}, model=self.identity
        )


def controller(choice="open.library"):
    backend = StubBackend(choice)
    return DemoController(MLXDecisionEngine(backend=backend)), backend


def act(demo, action):
    return demo.action(action, demo.snapshot()["state_version"])


def ids(desktop):
    return {candidate.id for candidate in desktop.candidates()}


def test_desktop_has_no_close_and_feature_does_not_play():
    desktop = Desktop()
    assert ids(desktop) == {"open.library", "open.notes"}
    desktop.apply("open.library")
    assert desktop.view == "library"
    assert desktop.player_status is None
    assert desktop.state()["focused_object"] == "course library"


def test_close_is_bound_to_current_object():
    desktop = Desktop()
    with pytest.raises(DemoError):
        desktop.apply("close.player")
    desktop.apply("open.notes")
    assert ids(desktop) == {"close.notes"}
    desktop.apply("close.notes")
    desktop.apply("open.library")
    assert "close.library" in ids(desktop)
    desktop.apply("play.color")
    assert ids(desktop) == {"close.player"}
    desktop.apply("close.player")
    assert desktop.view == "library"


def test_first_item_uses_current_filtered_order():
    desktop = Desktop()
    desktop.apply("open.library")
    desktop.apply("filter.science")
    assert [c["title"] for c in desktop.visible_courses()] == [
        "Lunar Gardening",
        "Orbit Field Notes",
    ]
    desktop.apply("sort.za")
    assert [c["title"] for c in desktop.visible_courses()] == [
        "Orbit Field Notes",
        "Lunar Gardening",
    ]
    play_choices = [c for c in desktop.candidates() if c.id.startswith("play.")]
    assert play_choices[0].id == "play.orbit"
    assert "number 1" in play_choices[0].description
    assert desktop.state()["library"]["visible_courses"][0]["id"] == "orbit"
    assert "play.color" not in ids(desktop)


def test_loading_ready_pause_resume_rewind_and_close():
    demo, _ = controller()
    act(demo, "open.library")
    loading = act(demo, "play.motion")
    assert [c["id"] for c in loading["candidates"]] == ["close.player"]
    with pytest.raises(DemoError):
        act(demo, "player.pause")
    ready = demo.player_ready(loading["state_version"])
    assert ready["state"]["player"]["status"] == "playing"
    assert "player.pause" in {c["id"] for c in ready["candidates"]}
    paused = act(demo, "player.pause")
    assert paused["state"]["player"]["status"] == "paused"
    assert "player.resume" in {c["id"] for c in paused["candidates"]}
    assert "player.pause" not in {c["id"] for c in paused["candidates"]}
    assert act(demo, "player.rewind")["state"]["player"]["position_seconds"] == 50
    assert act(demo, "player.resume")["state"]["player"]["status"] == "playing"
    assert act(demo, "close.player")["state"]["view"] == "library"


def test_obsolete_loading_event_cannot_reopen_closed_player():
    demo, _ = controller()
    act(demo, "open.library")
    loading = act(demo, "play.color")
    act(demo, "close.player")
    with pytest.raises(DemoError, match="stale"):
        demo.player_ready(loading["state_version"])
    assert demo.snapshot()["state"]["view"] == "library"


def test_model_choice_becomes_current_button_click_with_single_use_ticket():
    demo, backend = controller()
    response = demo.decide("This utterance is deliberately not interpreted by a fake backend.")
    op = response["browser_operation"]
    assert op["type"] == "click"
    assert op["selector"] == '[data-action="open.library"]'
    assert response["state"]["view"] == "desktop"  # deciding alone applies nothing
    receipt = demo.execute(op["ticket"], op["action_id"])
    assert receipt["receipt"]["source"] == "model"
    assert receipt["receipt"]["executed"]
    assert receipt["state"]["view"] == "library"
    assert backend.requests[0].state_version == 0
    with pytest.raises(DemoError, match="consumed"):
        demo.execute(op["ticket"], op["action_id"])


@pytest.mark.parametrize("choice,status", [(NO_MATCH_ID, "no_match"), (ABSTAIN_ID, "abstain")])
def test_reserved_choice_never_produces_browser_operation(choice, status):
    demo, _ = controller(choice)
    response = demo.decide("A test utterance")
    assert response["result"]["status"] == status
    assert response["browser_operation"] is None
    assert response["state_version"] == 0


def test_ticket_cannot_authorize_a_different_action():
    demo, _ = controller()
    op = demo.decide("Test request")["browser_operation"]
    with pytest.raises(DemoError, match="does not match"):
        demo.execute(op["ticket"], "open.notes")
    assert demo.snapshot()["state_version"] == 0


def test_page_change_after_decision_rejects_old_ticket():
    demo, _ = controller()
    op = demo.decide("Test request")["browser_operation"]
    act(demo, "open.notes")
    with pytest.raises(StaleDecisionError):
        demo.execute(op["ticket"], op["action_id"])
    assert demo.snapshot()["state"]["view"] == "notes"


def test_manual_page_changes_while_model_is_working():
    demo, backend = controller()
    backend.started, backend.release = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(demo.decide, "Test request")
        assert backend.started.wait(2)
        act(demo, "open.notes")
        backend.release.set()
        response = future.result(timeout=2)
    assert response["result"]["status"] == "stale"
    assert response["result"]["raw_selected_id"] == "open.library"
    assert response["browser_operation"] is None
    assert response["state"]["view"] == "notes"


def test_manual_action_requires_exact_version():
    demo, _ = controller()
    act(demo, "open.library")
    with pytest.raises(DemoError, match="State changed"):
        demo.action("close.library", 0)
