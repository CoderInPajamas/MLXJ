"""A fictional desktop whose actual allowed actions change with its state.

The controller contains no language matching. Every utterance goes to the supplied
decision engine; the browser and executor can only apply a current allowed action.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from threading import RLock
from typing import Any

from .session import DecisionSession
from .types import Candidate

COURSES = (
    {
        "id": "color",
        "title": "Color & Contrast",
        "category": "Design",
        "minutes": 18,
        "symbol": "◒",
        "color": "peach",
    },
    {
        "id": "motion",
        "title": "Motion Basics",
        "category": "Design",
        "minutes": 24,
        "symbol": "↗",
        "color": "lavender",
    },
    {
        "id": "lunar",
        "title": "Lunar Gardening",
        "category": "Science",
        "minutes": 32,
        "symbol": "☽",
        "color": "sage",
    },
    {
        "id": "sound",
        "title": "Sound Sketches",
        "category": "Music",
        "minutes": 16,
        "symbol": "≋",
        "color": "blue",
    },
    {
        "id": "orbit",
        "title": "Orbit Field Notes",
        "category": "Science",
        "minutes": 21,
        "symbol": "◎",
        "color": "butter",
    },
    {
        "id": "rhythm",
        "title": "Rhythm Workshop",
        "category": "Music",
        "minutes": 27,
        "symbol": "▥",
        "color": "rose",
    },
)


class DemoError(ValueError):
    """An invalid or stale desktop operation."""


@dataclass
class Desktop:
    view: str = "desktop"
    category: str = "All"
    order: str = "featured"
    course_id: str | None = None
    player_status: str | None = None
    position_seconds: int = 60

    def visible_courses(self) -> list[dict[str, Any]]:
        courses = [
            dict(c) for c in COURSES if self.category == "All" or c["category"] == self.category
        ]
        if self.order in ("az", "za"):
            courses.sort(key=lambda c: c["title"], reverse=self.order == "za")
        return courses

    def state(self) -> dict[str, Any]:
        opened = {
            "desktop": None,
            "library": "course library",
            "notes": "field notes",
            "player": "course player",
        }[self.view]
        return {
            "application": "Morrow Studio (fictional local demo)",
            "view": self.view,
            "focused_object": opened,
            "library": {
                "filter": self.category,
                "sort": self.order,
                "visible_courses": [
                    {
                        "position": i + 1,
                        "id": c["id"],
                        "title": c["title"],
                        "category": c["category"],
                    }
                    for i, c in enumerate(self.visible_courses())
                ]
                if self.view == "library"
                else [],
            },
            "player": {
                "course": next((c["title"] for c in COURSES if c["id"] == self.course_id), None),
                "status": self.player_status,
                "position_seconds": self.position_seconds,
            }
            if self.view == "player"
            else None,
        }

    def candidates(self) -> tuple[Candidate, ...]:
        if self.view == "desktop":
            return (
                Candidate(
                    "open.library",
                    "Open the course library feature. This does not play any course.",
                ),
                Candidate("open.notes", "Open the Field Notes window."),
            )
        if self.view == "notes":
            return (
                Candidate(
                    "close.notes",
                    "Close the currently open Field Notes window and return to the desktop.",
                ),
            )
        if self.view == "player":
            actions = [
                Candidate(
                    "close.player",
                    "Close the current course player and return to the course library.",
                )
            ]
            if self.player_status == "loading":
                return tuple(actions)
            if self.player_status == "playing":
                actions.append(
                    Candidate("player.pause", "Pause the currently playing course video.")
                )
            else:
                actions.append(Candidate("player.resume", "Resume the paused course video."))
            actions.append(
                Candidate("player.rewind", "Rewind the current course video by ten seconds.")
            )
            return tuple(actions)
        actions = [
            Candidate("close.library", "Close the course library and return to the desktop.")
        ]
        actions.extend(
            Candidate(
                f"filter.{category.lower()}",
                f"Filter the visible course list to {category} courses."
                if category != "All"
                else "Show all course categories; clear the category filter.",
            )
            for category in ("All", "Design", "Science", "Music")
            if category != self.category
        )
        actions.extend(
            Candidate(f"sort.{order}", description)
            for order, description in (
                ("featured", "Sort courses in their original featured order."),
                ("az", "Sort visible courses alphabetically by title, A to Z."),
                ("za", "Sort visible courses by title in reverse alphabetical order, Z to A."),
            )
            if order != self.order
        )
        actions.extend(
            Candidate(
                f"play.{course['id']}",
                f"Play visible course number {i + 1}: {course['title']} ({course['category']}). Open its video in the player.",
            )
            for i, course in enumerate(self.visible_courses())
        )
        return tuple(actions)

    def apply(self, action_id: str) -> str:
        if action_id not in {candidate.id for candidate in self.candidates()}:
            raise DemoError("Action is not allowed in the current state.")
        if action_id == "open.library":
            self.view = "library"
        elif action_id == "open.notes":
            self.view = "notes"
        elif action_id.startswith("close."):
            self.view = "library" if action_id == "close.player" else "desktop"
            self.course_id, self.player_status = None, None
        elif action_id.startswith("filter."):
            self.category = action_id.split(".", 1)[1].title()
        elif action_id.startswith("sort."):
            self.order = action_id.split(".", 1)[1]
        elif action_id.startswith("play."):
            self.course_id = action_id.split(".", 1)[1]
            self.view, self.player_status, self.position_seconds = "player", "loading", 60
        elif action_id == "player.pause":
            self.player_status = "paused"
        elif action_id == "player.resume":
            self.player_status = "playing"
        elif action_id == "player.rewind":
            self.position_seconds = max(0, self.position_seconds - 10)
        return action_id


class DemoController:
    """Versioned, single-user localhost demo with single-use execution tickets."""

    def __init__(self, engine: Any):
        self.engine = engine
        self.desktop = Desktop()
        self._lock = RLock()
        self._session = DecisionSession(
            engine, state=self.desktop.state(), candidates=self.desktop.candidates()
        )
        self._tickets: OrderedDict[str, Any] = OrderedDict()
        self._version = 0

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            state = self.desktop.state()
            return {
                "state": state,
                "state_version": self._version,
                "candidates": [
                    {"id": c.id, "description": c.description} for c in self.desktop.candidates()
                ],
                "courses": self.desktop.visible_courses() if self.desktop.view == "library" else [],
                "model": getattr(self.engine, "model_identity", None)
                or getattr(self.engine, "model_path", "local MLX model"),
            }

    def _publish(self) -> None:
        self._version = self._session.update_state(
            self.desktop.state(), candidates=self.desktop.candidates()
        )

    def action(self, action_id: str, expected_version: int) -> dict[str, Any]:
        with self._lock:
            if expected_version != self._version:
                raise DemoError("State changed; refresh before applying this action.")
            before = self._version
            self.desktop.apply(action_id)
            self._publish()
            return {
                "receipt": {
                    "executed": True,
                    "action_id": action_id,
                    "source": "manual",
                    "from_version": before,
                    "to_version": self._version,
                },
                **self.snapshot(),
            }

    def player_ready(self, expected_version: int) -> dict[str, Any]:
        with self._lock:
            if (
                expected_version != self._version
                or self.desktop.view != "player"
                or self.desktop.player_status != "loading"
            ):
                raise DemoError("Player loading event is stale.")
            self.desktop.player_status = "playing"
            self._publish()
            return self.snapshot()

    def decide(self, utterance: str) -> dict[str, Any]:
        # Inference deliberately does not hold the desktop lock: manual page updates
        # can happen while the model works, and the session marks those results stale.
        result = self._session.decide(utterance)
        operation = None
        with self._lock:
            # A manual request may update state after Session.decide returns
            # but before this response acquires the desktop lock. Reconcile
            # once more while publishing its state and possible operation.
            if result.state_version != self._version:
                result = replace(result, status="stale", candidate_id=None, selected_value=None)
            if result.status == "selected" and result.candidate_id:
                self._tickets[result.request_id] = result
                while len(self._tickets) > 128:
                    self._tickets.popitem(last=False)
                operation = {
                    "type": "click",
                    "action_id": result.candidate_id,
                    "selector": f'[data-action="{result.candidate_id}"]',
                    "ticket": result.request_id,
                    "state_version": result.state_version,
                }
            return {"result": result.to_dict(), "browser_operation": operation, **self.snapshot()}

    def execute(self, ticket: str, action_id: str) -> dict[str, Any]:
        with self._lock:
            result = self._tickets.get(ticket)
            if result is None:
                raise DemoError("Unknown or already consumed decision ticket.")
            if result.candidate_id != action_id:
                raise DemoError("Browser action does not match the issued decision.")
            # Consume before attempting execution, including a stale result.
            del self._tickets[ticket]

            def apply(candidate: Candidate) -> dict[str, Any]:
                before = self._version
                self.desktop.apply(candidate.id)
                self._publish()
                return {
                    "executed": True,
                    "action_id": candidate.id,
                    "source": "model",
                    "from_version": before,
                    "to_version": self._version,
                    "decision_id": ticket,
                }

            receipt = self._session.execute(result, apply)
            return {"receipt": receipt, **self.snapshot()}
