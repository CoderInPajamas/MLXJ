"""Validated public values for bounded, single-step local decisions."""

from __future__ import annotations

import copy
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

NO_MATCH_ID = "__no_match__"
ABSTAIN_ID = "__abstain__"
RESERVED_IDS = (NO_MATCH_ID, ABSTAIN_ID)
MAX_CANDIDATES = 64
MAX_STATE_BYTES = 131_072
DEFAULT_QUESTION = "Select the single allowed action requested by the user."


def _text(value: Any, name: str, limit: int, *, empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")  # noqa: TRY004 - consistent schema errors
    if len(value) > limit or (not empty and not value.strip()):
        raise ValueError(f"{name} must contain 1 to {limit} characters")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{name} must contain valid Unicode") from exc
    return value


def _json_copy(value: Any, name: str, *, max_bytes: int = MAX_STATE_BYTES) -> Any:
    """Check real JSON types, depth, finite numbers and size before copying."""

    def check(item: Any, depth: int) -> None:
        if depth > 16:
            raise ValueError(f"{name} JSON nesting exceeds 16 levels")
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"{name} must contain only finite numbers")
            return
        if isinstance(item, list):
            for child in item:
                check(child, depth + 1)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ValueError(f"{name} object keys must be strings")  # noqa: TRY004
                check(child, depth + 1)
            return
        raise ValueError(f"{name} contains a non-JSON value: {type(item).__name__}")

    check(value, 0)
    try:
        serialized = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > max_bytes:
            raise ValueError(f"{name} exceeds {max_bytes} UTF-8 bytes")
    except (UnicodeError, OverflowError, RecursionError) as exc:
        raise ValueError(f"{name} cannot be represented as bounded JSON") from exc
    return copy.deepcopy(value)


@dataclass(frozen=True)
class Candidate:
    """A stable application ID and a semantic description of an allowed choice."""

    id: str
    description: str
    value: Any = None

    def __post_init__(self) -> None:
        _text(self.id, "candidate id", 128)
        if self.id in RESERVED_IDS or any(ord(char) < 32 or ord(char) == 127 for char in self.id):
            raise ValueError("candidate id is reserved or contains a control character")
        _text(self.description, "candidate description", 2048)
        object.__setattr__(
            self, "value", _json_copy(self.value, "candidate value", max_bytes=16_384)
        )

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description, "value": copy.deepcopy(self.value)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Candidate:
        if not isinstance(data, Mapping) or set(data) - {"id", "description", "value"}:
            raise ValueError("candidate must contain only id, description and optional value")
        if not {"id", "description"} <= set(data):
            raise ValueError("candidate requires id and description")
        return cls(**dict(data))


@dataclass(frozen=True)
class DecisionRequest:
    state: dict[str, Any]
    utterance: str
    candidates: tuple[Candidate, ...]
    state_version: int = 0
    question: str = DEFAULT_QUESTION
    kind: str = "enum"

    def __post_init__(self) -> None:
        if not isinstance(self.state, dict):
            raise ValueError("state must be a JSON object")  # noqa: TRY004 - schema error
        object.__setattr__(self, "state", _json_copy(self.state, "state"))
        _text(self.utterance, "utterance", 16_384)
        _text(self.question, "question", 2048)
        if type(self.state_version) is not int or self.state_version < 0:
            raise ValueError("state_version must be a nonnegative integer")
        if self.kind not in ("enum", "boolean"):
            raise ValueError("kind must be enum or boolean")
        if not isinstance(self.candidates, (tuple, list)) or len(self.candidates) > MAX_CANDIDATES:
            raise ValueError(f"candidates must be a sequence of at most {MAX_CANDIDATES} choices")
        if not all(isinstance(candidate, Candidate) for candidate in self.candidates):
            raise ValueError("candidates must contain Candidate objects")
        candidates = tuple(Candidate(c.id, c.description, c.value) for c in self.candidates)
        if len({candidate.id for candidate in candidates}) != len(candidates):
            raise ValueError("candidate ids must be unique")
        object.__setattr__(self, "candidates", candidates)
        if self.kind == "boolean" and (
            len(candidates) != 2
            or not all(type(candidate.value) is bool for candidate in candidates)
            or {candidate.value for candidate in candidates} != {True, False}
        ):
            raise ValueError(
                "boolean requests require exactly one true and one false candidate value"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": copy.deepcopy(self.state),
            "utterance": self.utterance,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "state_version": self.state_version,
            "question": self.question,
            "kind": self.kind,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DecisionRequest:
        allowed = {"state", "utterance", "candidates", "state_version", "question", "kind"}
        if not isinstance(data, Mapping) or set(data) - allowed:
            raise ValueError("request contains unknown fields")
        if not {"state", "utterance", "candidates"} <= set(data):
            raise ValueError("request requires state, utterance and candidates")
        fields = dict(data)
        if (
            not isinstance(fields["candidates"], (list, tuple))
            or len(fields["candidates"]) > MAX_CANDIDATES
        ):
            raise ValueError(f"candidates must be an array of at most {MAX_CANDIDATES} choices")
        fields["candidates"] = tuple(Candidate.from_dict(item) for item in fields["candidates"])
        return cls(**fields)

    @classmethod
    def boolean(
        cls,
        *,
        state: dict[str, Any],
        utterance: str,
        question: str,
        state_version: int = 0,
        true_description: str = "True: the proposition is supported by the provided context.",
        false_description: str = "False: the proposition is contradicted by the provided context.",
    ) -> DecisionRequest:
        """Create typed boolean choices; insufficient context may still abstain."""
        return cls(
            state=state,
            utterance=utterance,
            question=question,
            state_version=state_version,
            kind="boolean",
            candidates=(
                Candidate("true", true_description, True),
                Candidate("false", false_description, False),
            ),
        )


def boolean_request(**kwargs: Any) -> DecisionRequest:
    return DecisionRequest.boolean(**kwargs)


@dataclass(frozen=True)
class BackendOutput:
    raw_scores: dict[str, float]
    model: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionResult:
    candidate_id: str | None
    status: str
    raw_selected_id: str
    raw_scores: dict[str, float]
    scores: dict[str, float]
    margin: float
    state_version: int
    model: dict[str, Any]
    timing: dict[str, Any]
    cache: dict[str, Any]
    request_id: str
    selected_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible data; scores are uncalibrated restricted softmax."""
        return copy.deepcopy(self.__dict__)
