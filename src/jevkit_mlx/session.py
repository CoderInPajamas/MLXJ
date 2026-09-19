"""Versioned state snapshots and atomic, single-use action authorization."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import replace
from typing import Any, TypeVar
from uuid import uuid4

from .engine import MLXDecisionEngine
from .types import DEFAULT_QUESTION, Candidate, DecisionRequest, DecisionResult


class DecisionExecutionError(ValueError):
    """A result cannot authorize an action in this session."""


class StaleDecisionError(DecisionExecutionError):
    """Application state changed after the result's snapshot."""


class InvalidDecisionError(DecisionExecutionError):
    """The result was not issued intact by this session or selects no action."""


class ReplayDecisionError(DecisionExecutionError):
    """This result has already been consumed."""


T = TypeVar("T")


def _fingerprint(result: DecisionResult) -> str:
    data = json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class DecisionSession:
    """Keep state versions and reject stale, forged and replayed decisions.

    Inference runs outside the state lock. The callback passed to ``execute``
    runs under that lock and may call ``update_state`` reentrantly. An external
    application lock, if any, must always be acquired before this session lock.
    Pending authorization is bounded to the latest 256 selected results.
    """

    def __init__(
        self,
        engine: MLXDecisionEngine,
        *,
        state: dict[str, Any],
        candidates: tuple[Candidate, ...] | list[Candidate],
        question: str = DEFAULT_QUESTION,
        kind: str = "enum",
        state_version: int = 0,
    ) -> None:
        validated = DecisionRequest(
            state, "Initialize session", tuple(candidates), state_version, question, kind
        )
        self.engine = engine
        self._state = validated.state
        self._candidates = validated.candidates
        self._version = state_version
        self._question = question
        self._kind = kind
        self._lock = threading.RLock()
        self._cache_key = "session-" + uuid4().hex
        self._issued: OrderedDict[str, tuple[DecisionResult, Candidate, str]] = OrderedDict()
        self._consumed: OrderedDict[str, None] = OrderedDict()

    @property
    def state_version(self) -> int:
        with self._lock:
            return self._version

    @property
    def version(self) -> int:
        return self.state_version

    @property
    def state(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    @property
    def candidates(self) -> tuple[Candidate, ...]:
        with self._lock:
            return tuple(Candidate(c.id, c.description, c.value) for c in self._candidates)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": copy.deepcopy(self._state),
                "state_version": self._version,
                "candidates": [candidate.to_dict() for candidate in self._candidates],
                "question": self._question,
                "kind": self._kind,
            }

    def update_state(
        self,
        state: dict[str, Any],
        candidates: tuple[Candidate, ...] | list[Candidate] | None = None,
    ) -> int:
        """Atomically replace state/choices and invalidate all pending actions."""
        with self._lock:
            validated = DecisionRequest(
                state,
                "Update session",
                self._candidates if candidates is None else tuple(candidates),
                self._version + 1,
                self._question,
                self._kind,
            )
            self._state = validated.state
            self._candidates = validated.candidates
            self._version = validated.state_version
            self._issued.clear()
            return self._version

    def decide(self, utterance: str, *, use_cache: bool = True) -> DecisionResult:
        with self._lock:
            request = DecisionRequest(
                self._state,
                utterance,
                self._candidates,
                self._version,
                self._question,
                self._kind,
            )
        result = self.engine.decide(request, use_cache=use_cache, cache_key=self._cache_key)
        with self._lock:
            if result.state_version != request.state_version:
                raise InvalidDecisionError("engine returned a different state version")
            if self._version != request.state_version:
                return replace(result, status="stale", candidate_id=None, selected_value=None)
            if result.status == "selected":
                candidate = next(
                    (c for c in request.candidates if c.id == result.candidate_id), None
                )
                if candidate is None:
                    raise InvalidDecisionError("engine selected a candidate outside this snapshot")
                self._issued[result.request_id] = (result, candidate, _fingerprint(result))
                while len(self._issued) > 256:
                    self._issued.popitem(last=False)
            return result

    def prewarm(self) -> dict[str, Any]:
        """Prefill the current stable prefix, reporting concurrent state changes.

        This creates no decision or execution authorization. Backends without
        prefix prefill support raise ``NotImplementedError``.
        """
        prewarm = getattr(self.engine.backend, "prewarm", None)
        if not callable(prewarm):
            raise NotImplementedError("this backend does not implement prefix prewarming")
        with self._lock:
            request = DecisionRequest(
                self._state,
                "Prewarm stable state",
                self._candidates,
                self._version,
                self._question,
                self._kind,
            )
        metadata = copy.deepcopy(prewarm(request, cache_key=self._cache_key))
        with self._lock:
            metadata.update(
                {
                    "state_version": request.state_version,
                    "current_state_version": self._version,
                    "status": "ready" if self._version == request.state_version else "stale",
                }
            )
        return metadata

    def execute(self, result: DecisionResult, callback: Callable[[Candidate], T]) -> T:
        """Consume an authentic result and apply its action atomically.

        Consumption occurs before calling application code: a failed callback
        must be handled by the application and cannot silently repeat an action.
        The callback's return value is the execution receipt, not model accuracy.
        """
        if not isinstance(result, DecisionResult):
            raise InvalidDecisionError("result must be a DecisionResult issued by this session")
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            if result.state_version != self._version or result.status == "stale":
                raise StaleDecisionError("state changed; obtain a new decision before executing")
            if result.request_id in self._consumed:
                raise ReplayDecisionError("decision has already been consumed")
            issued = self._issued.get(result.request_id)
            if result.status != "selected" or issued is None or issued[0] is not result:
                raise InvalidDecisionError(
                    "result is not an executable decision issued by this session"
                )
            try:
                intact = _fingerprint(result) == issued[2]
            except (TypeError, ValueError):
                intact = False
            if not intact:
                raise InvalidDecisionError("decision result was modified after issuance")
            self._issued.pop(result.request_id)
            self._consumed[result.request_id] = None
            while len(self._consumed) > 1024:
                self._consumed.popitem(last=False)
            candidate = Candidate(issued[1].id, issued[1].description, issued[1].value)
            return callback(candidate)
